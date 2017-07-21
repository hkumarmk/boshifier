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

from flask import Flask, request, Response
from jinja2 import Environment, FileSystemLoader

import yaml


app = Flask(__name__)

PIPELINE_CONFIG_TEMPLATE = os.path.join(
    os.path.dirname(__file__), "templates", "pipeline.yml.j2")


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


def get_director_creds(creds_file):
    dir_creds = read_yaml(creds_file)
    if not dir_creds:
        return False

    if dir_creds.get('director_ca_cert'):
        director_ca_cert = literal_str(dir_creds['director_ca_cert'])
        dir_creds['director_ca_cert'] = director_ca_cert
    return dir_creds


def get_vars(director_name, **kwargs):
    variables = get_director_creds(director_name)
    variables.update(kwargs)
    return variables


class Flyer(object):

    FLY_CMD = 'fly'

    def __init__(self, cred_file, temp_dir, deployment_config):
        self.creds = self._get_concourse_creds(cred_file)
        self.target = self.creds['name']
        self.pipeline = deployment_config['name']
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

    @staticmethod
    def _get_concourse_creds(creds_file):
        cc_creds = read_yaml(creds_file)
        if not cc_creds:
            return False
        if cc_creds.get('ca_cert'):
            cc_ca_cert = literal_str(cc_creds['ca_cert'])
            cc_creds['ca_cert'] = cc_ca_cert
        if 'name' not in cc_creds:
            cc_creds['name'] = urlparse(cc_creds['url']).hostname
        return cc_creds

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


def deploy_to_bosh(bosh_creds_file, concourse_creds_file, deplyment_config_file):
    variables = get_director_creds(bosh_creds_file)
    deployment_config = read_yaml(deplyment_config_file)
    deployment_name = deployment_config['name']
    variables.update({'deployment_name': deployment_config['name']})
    temp_dir = tempfile.mkdtemp()
    varfile_path = os.path.join(temp_dir, 'vars.yml')
    try:
        with open(varfile_path, 'w') as varfile:
            yaml.dump(variables, varfile)

        fly = Flyer(concourse_creds_file, temp_dir, deployment_config)
        rc = fly.login()
        if rc != 0:
            return "Login to concourse failed", 500
        rc = fly.set_pipeline()
        if rc != 0:
            return "Set pipeline failed for {}".format(deployment_name), 500
        rc = fly.unpause_pipeline()
        if rc != 0:
            return "Unpause pipeline failed for {}".format(
                deployment_name), 500
    finally:
        shutil.rmtree(temp_dir)
    return 'Deployment done', 200


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return Response(open('README.md', 'r'), mimetype='text/plain')

    if 'bosh' not in request.files:
        return 'You must pass a bosh credentials yaml file', 400
    bosh_creds_file = request.files['bosh']

    if 'concourse' not in request.files:
        return 'You must pass a concourse credentials yaml file', 400
    concourse_creds_file = request.files['concourse']

    if 'deployment' not in request.files:
        return 'You must pass a deployment configuration yaml file', 400
    deployment_config_file = request.files['deployment']

    return deploy_to_bosh(bosh_creds_file,
                          concourse_creds_file,
                          deployment_config_file)


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description="Manage bosh deployments")
    ap.add_argument('-b', '--bosh-creds-file', type=argparse.FileType('r'),
                    required=True,
                    help="Yaml file that contain bosh credentials")
    ap.add_argument('-c', '--concourse-creds-file',
                    type=argparse.FileType('r'), required=True,
                    help="Yaml file that contain concourse credentials")
    ap.add_argument('-d', '--deployment-config-file',
                    type=argparse.FileType('r'), required=True,
                    help="Yaml file that contain deployment configurations")
    args = ap.parse_args()

    message, rv = deploy_to_bosh(args.bosh_creds_file,
                                 args.concourse_creds_file,
                                 args.deployment_config_file)
    if rv == 200:
        print message
        sys.exit(0)
    elif rv == 500:
        print message
        sys.exit(1)

"""
Sample files found under examples directory
"""
