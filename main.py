# Copyright 2017 Mastercard
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import shutil
import subprocess
import sys
import tempfile

from urlparse import urlparse

from flask import abort, Flask, jsonify, request, Response
from jinja2 import Environment, FileSystemLoader

import yaml


app = Flask(__name__)

PIPELINE_CONFIG_TEMPLATE = os.path.join(
    os.path.dirname(__file__), "templates", "pipeline.yml.j2")

CONFIG_FILE = os.getenv('BOSHIFIER_CONFIG_FILE', '/etc/boshifier/config.yml')

rv_message = {
    'login_failed': 'Concourse login failed',
    'sp_failed': 'Concourse Set pipeline failed',
    'up_failed': 'Concourse unpause pipeline failed',
}


class literal_str(str):
    pass


def change_style(style, representer):
    def new_representer(dumper, data):
        scalar = representer(dumper, data)
        scalar.style = style
        return scalar
    return new_representer


represent_literal_str = change_style(
    '|', yaml.representer.SafeRepresenter.represent_str)
yaml.add_representer(literal_str, represent_literal_str)


def render_j2(template=PIPELINE_CONFIG_TEMPLATE, variables=None):
    """
    Render jinja2 yaml template and return dictionary form of the same.
    :param template: Template path
    :param variables: Variables to be substituted to the template
    :return: Dictionary form of resultant yaml
    """
    variables = variables or {}
    variables.update(os.environ)
    template_abs_path = os.path.abspath(template)
    template_dir = os.path.dirname(template_abs_path)
    template_file = os.path.basename(template_abs_path)
    jenv = Environment(loader=FileSystemLoader(template_dir),
                       trim_blocks=True)
    template = jenv.get_template(template_file)
    rendered = template.render(**variables)
    return yaml.load(rendered)


def read_yaml(file):
    try:
        dict = yaml.load(file)
    except yaml.YAMLError as exc:
        print(exc)
        return False
    return dict


def get_config(config_file):
    my_config = read_yaml(config_file)
    if not my_config:
        return {}
    if 'bosh' in my_config.keys():
        bosh_config = my_config.values()[0]
        for dir, creds in bosh_config.items():
            if creds.get('director_ca_cert'):
                director_ca_cert = literal_str(creds['director_ca_cert'])
                my_config['bosh'][dir]['director_ca_cert'] = director_ca_cert
    if 'concourse' in my_config.keys():
        cc_config = my_config.values()[0]
        for cc, creds in cc_config.items():
            if creds.get('ca_cert'):
                cc_ca_cert = literal_str(creds['ca_cert'])
                my_config['concourse'][cc]['ca_cert'] = cc_ca_cert
            if 'name' not in creds:
                my_config['concourse'][cc]['name'] = urlparse(creds['url']).hostname

    if 'deployments' in my_config.keys():
        for deployment, deployment_config in my_config['deployments'].items():
            if 'deploy_job_name' not in my_config['deployments'][deployment].keys():
                my_config['deployments'][deployment]['deploy_job_name'] = deployment + '-deploy'

    return my_config


class Flyer(object):

    FLY_CMD = 'fly'

    def __init__(self, creds, temp_dir, deployment_config):
        self.creds = creds
        self.deployment_config = deployment_config
        self.target = self.creds['name']
        self.pipeline = deployment_config['deployment_name']
        self.varfile_path = os.path.join(temp_dir, 'vars.yml')
        self.pipeline_config = os.path.join(temp_dir, '.pipeline.yml')
        pipeline_cfg_dict = render_j2(
            PIPELINE_CONFIG_TEMPLATE, deployment_config)
        with open(self.pipeline_config, 'w') as f:
            yaml.dump(pipeline_cfg_dict, f, default_flow_style=False)
        subprocess.check_output(['cat', self.pipeline_config])
        if self.creds.get('ca_cert'):
            self.ca_cert_file = os.path.join(temp_dir, 'concourse_ca_cert.crt')
            with open(self.ca_cert_file, 'w') as f:
                f.write(self.creds['ca_cert'])

    @staticmethod
    def _fly_cmd(*args, **kwargs):
        return subprocess.Popen([Flyer.FLY_CMD] + list(args), **kwargs)

    def login(self):
        fly_login_cmd = ['login',
                         '--target', self.creds['name'],
                         '--concourse-url', self.creds['url']]
        if self.creds.get('insecure'):
            fly_login_cmd += ['--insecure']
        if self.creds.get('username'):
            fly_login_cmd += ['--username', self.creds['username']]
        if self.creds.get('password'):
            fly_login_cmd += ['--password', self.creds['password']]
        if self.creds.get('team'):
            fly_login_cmd += ['--team-name', self.creds['team']]
        if self.creds.get('ca_cert'):
            fly_login_cmd += ['--ca-cert', self.ca_cert_file]

        proc = self._fly_cmd(*fly_login_cmd)
        proc.communicate()
        return proc.returncode

    def set_pipeline(self):
        fly_sp_cmd = ['set-pipeline',
                      '--target', self.target,
                      '--non-interactive',
                      '--pipeline', self.pipeline,
                      '--config', self.pipeline_config,
                      '--load-vars-from', self.varfile_path]
        proc = self._fly_cmd(*fly_sp_cmd)
        proc.communicate()
        return proc.returncode

    def unpause_pipeline(self):
        fly_up_cmd = ['unpause-pipeline',
                      '--target', self.target,
                      '--pipeline', self.pipeline]
        proc = self._fly_cmd(*fly_up_cmd)
        proc.communicate()
        return proc.returncode

    def trigger_job(self):
        fly_tj_cmd = ['trigger-job',
                      '--target', self.target,
                      '--watch',
                      '--job', "{}/{}".format(self.pipeline,
                                              self.deployment_config[
                                                  'deploy_job_name'])]
        proc = self._fly_cmd(*fly_tj_cmd)
        proc.communicate()
        return proc.returncode


class DeploymentProcessor(object):
    def __init__(self, config_files=None):
        if not config_files:
            config_files = []
        initial_config = self._get_initial_config_file()
        if initial_config:
            config_files.insert(0, initial_config)
        self.config_files = config_files
        self.configs = self._load_config()
        self.cc_target = None

    def targets(self):
        if self.configs.get('targets'):
            print jsonify(self.configs['targets'])
            return jsonify(self.configs['targets'])
        else:
            abort(404, "No targets found")

    @staticmethod
    def _get_initial_config_file():
        if os.path.isfile(CONFIG_FILE):
            return open(CONFIG_FILE, 'r')

    def set_cc_pipeline(self, deployment_config):
        temp_dir = tempfile.mkdtemp()
        varfile_path = os.path.join(temp_dir, 'vars.yml')
        try:
            with open(varfile_path, 'w') as varfile:
                yaml.dump(self.configs['cc_pipeline_vars'], varfile)
            fly = Flyer(self.configs['concourse'][self.cc_target],
                        temp_dir, deployment_config)
            rc = fly.login()
            if rc != 0:
                return 'login_failed'
            rc = fly.set_pipeline()
            if rc != 0:
                return 'sp_failed'
            rc = fly.unpause_pipeline()
            if rc != 0:
                return 'up_failed'
        finally:
            shutil.rmtree(temp_dir)
        return 0

    def _subst_vars(self, variables):
        """Merge vars with targets and return"""
        targets = self.configs['targets'].copy()
        for reg, reg_config in targets.items():
            for stage_config in reg_config['stages']:
                for stage, stg_cfg in stage_config.items():
                    bosh_name = stg_cfg.get('bosh')
                    vars_ = variables.get('default', {}).copy()
                    vars_.update(variables.get(bosh_name, {}))
                    if not stg_cfg.get('vars'):
                        stg_cfg.update({'vars': vars_})
                    else:
                        stg_cfg['vars'].update(vars_)
        return targets

    def _subst_creds(self):
        bosh_names = self.configs['bosh'].keys()
        cc_names = self.configs['concourse'].keys()
        self.cc_target = self.configs['concourse_target']
        unknown_bosh = []
        unknown_cc = None
        self.configs['cc_pipeline_vars'] = {}
        if self.configs['concourse_target'] not in cc_names:
            unknown_cc = self.configs['concourse_target']

        for reg, reg_config in self.configs['targets'].items():
            self.configs['cc_pipeline_vars'].update({reg: {}})
            for stage_config in reg_config['stages']:
                for stage, stg_cfg in stage_config.items():
                    if stg_cfg['bosh'] not in bosh_names:
                        unknown_bosh.append(stg_cfg['bosh'])
                    else:
                        self.configs['cc_pipeline_vars'][reg].update(
                            {stage: self.configs['bosh'][stg_cfg['bosh']]})

        return unknown_bosh, unknown_cc

    def _load_config(self):
        configs = {}
        for config_file in self.config_files:
            cfg = get_config(config_file)
            for cfg_section in cfg.keys():
                if cfg_section in configs.keys():
                    configs[cfg_section].update(cfg[cfg_section])
                else:
                    configs.update(cfg)
        return configs

    def process(self):
        msg = ''
        rv = 200
        unknown_bosh, unknown_cc = self._subst_creds()
        if unknown_bosh:
            msg += "Unknown bosh %s " % ",".join(unknown_bosh)
            rv = 400
        if unknown_cc:
            msg += "Unknown concourse %s " % unknown_cc
            rv = 400
        if unknown_bosh or unknown_cc:
            msg += "configured in the targets"

        if rv != 200:
            return msg, rv

        for deployment, deployment_config in self.configs['deployments'].items():
            if 'deployment_name' not in deployment_config:
                deployment_config['deployment_name'] = deployment
            if deployment_config.get('vars'):
                subst_targets = self._subst_vars(deployment_config['vars'])
                deployment_config.update({'targets': subst_targets})
            else:
                deployment_config.update({'targets': self.configs['targets']})
            if self.configs.get('artifactory'):
                deployment_config.update({'artifactory': self.configs['artifactory']})
            if self.configs.get('bosh_release_versions'):
                deployment_config.update({'bosh_release_versions': self.configs['bosh_release_versions']})
            else:
                deployment_config.update({'bosh_release_versions': {}})
            rv = self.set_cc_pipeline(deployment_config)
            if rv == "login_failed":
                return "Login to concourse failed", 500
            elif rv == "sp_failed":
                return "Set pipeline failed", 500
            elif rv == "up_failed":
                return "Unpause pipeline failed", 500
            else:
                return "Deployment done", 200


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return Response(open('README.md', 'r'), mimetype='text/plain')

    if not request.files:
        abort(400, "You must pass deployment config yaml file")

    config_files = []
    for files in request.files.iterlistvalues():
        for fp in files:
            config_files.append(fp)

    dp = DeploymentProcessor(config_files)
    return dp.process()


@app.route('/targets', methods=['GET'])
def targets():
    dp = DeploymentProcessor()
    return dp.targets()


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description="Manage bosh deployments")
    ap.add_argument(
        'config_files', type=argparse.FileType('r'), nargs='*',
        help="Yaml file[s] that contain bosh and concourse credentials"
             " and deployment config. One may submit single yaml file which"
             " contain all configs or can submit multiple yaml files")
    ap.add_argument('-c', '--command', action='store_true', help="Run boshifier as commandline tool")
    args = ap.parse_args()

    if args.command:
        dp = DeploymentProcessor(args.config_files)
        message, rv = dp.process()
        if rv == 200:
            print message
            sys.exit(0)
        else:
            print message
            sys.exit(1)
    else:
        app.run(debug=True,
                host=os.getenv("BOSHIFIER_LISTEN_ADDR", "127.0.0.1"),
                port=int(os.getenv("BOSHIFIER_LISTEN_PORT", "5000")))
"""
Sample files found under examples directory
"""
