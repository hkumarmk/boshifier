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

from jinja2 import Environment, FileSystemLoader
from yaml.representer import SafeRepresenter
from urlparse import urlparse
import os
import shutil
import subprocess
import yaml
import tempfile

from flask import Flask, request, Response

app = Flask(__name__)


class literal_str(str): pass


def change_style(style, representer):
    def new_representer(dumper, data):
        scalar = representer(dumper, data)
        scalar.style = style
        return scalar
    return new_representer

represent_literal_str = change_style('|', SafeRepresenter.represent_str)
yaml.add_representer(literal_str, represent_literal_str)


def render_j2(template=os.path.abspath("./templates/pipeline.yml"), append=False, variables=None):
    variables = variables or {}
    variables.update(os.environ)
    template_abs_path = os.path.abspath(template)
    template_dir = os.path.dirname(template_abs_path)
    template_file = os.path.basename(template_abs_path)
    jenv = Environment(loader=FileSystemLoader(template_dir),
                         trim_blocks=True)
    template = jenv.get_template(template_file)
    rendered = template.render(**variables)

    if append:
        mode = 'a'
    else:
        mode = 'w'
    print (yaml.load(rendered))
    return rendered


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
        dir_creds['director_ca_cert']=director_ca_cert
    return dir_creds


def get_deployment_config(file):
    deployment_config = {}
    config = read_yaml(file)
    deployment_config.update({'deployment': config['name'],
                              'bosh_release_repo': config['release']['repo'],
                              'stemcell': config['stemcell'],
                              'deployment_manifest_repo': config['manifest']['repo'],
                              'deployment_manifest_path': config['manifest']['path']})
    if 'branch' in config['release']:
        deployment_config.update({'bosh_release_branch': config['release']['branch']})

    if 'branch' in config['manifest']:
        deployment_config.update({'deployment_manifest_branch': config['manifest']['branch']})

    return deployment_config


def get_vars(director_name, **kwargs):
    variables = get_director_creds(director_name)
    variables.update(kwargs)
    return variables


class Flyer(object):

    FLY_CMD='fly'
    PIPELINE_CONFIG = 'templates/pipeline.yml'

    def __init__(self, cred_file, pipeline):
        self.creds = self._get_concourse_creds(cred_file)
        self.target = self.creds['name']
        self.pipeline = pipeline

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
            cc_creds['ca_cert']=cc_ca_cert
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
            fly_login_cmd += ['--ca-cert', self.creds['ca_cert']]
    
        proc = self._fly_cmd(*fly_login_cmd)
        print(proc.communicate())
        return proc.returncode

    def set_pipeline(self, varfile):
        fly_sp_cmd = ['set-pipeline',
                      '--target', self.target,
                      '--non-interactive',
                      '--pipeline', self.pipeline,
                      '--config', self.PIPELINE_CONFIG,
                      '--load-vars-from', varfile]
        proc = self._fly_cmd(*fly_sp_cmd)
        print(proc.communicate())
        return proc.returncode

    def unpause_pipeline(self):
        fly_up_cmd = ['unpause-pipeline',
                      '--target', self.target,
                      '--pipeline', self.pipeline]
        proc = self._fly_cmd(*fly_up_cmd)
        print(proc.communicate())
        return proc.returncode


def deploy_to_bosh(bosh_creds, concourse_creds, deplyment_config_file):
    variables = get_director_creds(bosh_creds)
    deployment_config = get_deployment_config(deplyment_config_file)
    deployment_name = deployment_config['deployment']
    variables.update(deployment_config)
    temp = tempfile.mkdtemp()
    varfile_path = os.path.join(temp, 'vars.yml')
    try:
        with open(varfile_path, 'w') as varfile:
            yaml.dump(variables, varfile)

        fly = Flyer(concourse_creds, deployment_name)
        rc = fly.login()
        if rc != 0:
            print("Login to concourse failed")
            return False
        rc = fly.set_pipeline(varfile_path)
        if rc != 0:
            print("Set pipeline failed for {}".format(deployment_name))
            return False
        rc = fly.unpause_pipeline()
        if rc != 0:
            print("Unpause pipeline failed for {}".format(deployment_name))
            return False
    finally:
        shutil.rmtree(temp)
    return True


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description="Manage bosh deployments")
    ap.add_argument('-b', '--bosh-creds-file', type=argparse.FileType('r'),
                    required=True,
                    help="Yaml file that contain bosh credentials")
    ap.add_argument('-c', '--concourse-creds-file', type=argparse.FileType('r'),
                    required=True,
                    help="Yaml file that contain concourse credentials")
    ap.add_argument('-d', '--deployment-config-file', type=argparse.FileType('r'),
                    required=True,
                    help="Yaml file that contain deployment configurations")
    args = ap.parse_args()

    pipeline = deploy_to_bosh(args.bosh_creds_file,
                              args.concourse_creds_file,
                              args.deployment_config_file)


"""
## Sample bosh_creds_file
director_ca_cert: |
    -----BEGIN CERTIFICATE-----
    MIIDtzCCAp+gAwIBAgIJAMZ/qRdRamluMA0GCSqGSIb3DQEBBQUAMEUxCzAJBgNV
    BAYTAkFVMRMwEQYDVQQIEwpTb21lLVN0YXRlMSEwHwYDVQQKExhJbnRlcm5ldCBX
    aWRnaXRzIFB0eSBMdGQwIBcNMTYwODI2MjIzMzE5WhgPMjI5MDA2MTAyMjMzMTla
    MEUxCzAJBgNVBAYTAkFVMRMwEQYDVQQIEwpTb21lLVN0YXRlMSEwHwYDVQQKExhJ
    bnRlcm5ldCBXaWRnaXRzIFB0eSBMdGQwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAw
    ggEKAoIBAQDN/bv70wDn6APMqiJZV7ESZhUyGu8OzuaeEfb+64SNvQIIME0s9+i7
    D9gKAZjtoC2Tr9bJBqsKdVhREd/X6ePTaopxL8shC9GxXmTqJ1+vKT6UxN4kHr3U
    +Y+LK2SGYUAvE44nv7sBbiLxDl580P00ouYTf6RJgW6gOuKpIGcvsTGA4+u0UTc+
    y4pj6sT0+e3xj//Y4wbLdeJ6cfcNTU63jiHpKc9Rgo4Tcy97WeEryXWz93rtRh8d
    pvQKHVDU/26EkNsPSsn9AHNgaa+iOA2glZ2EzZ8xoaMPrHgQhcxoi8maFzfM2dX2
    XB1BOswa/46yqfzc4xAwaW0MLZLg3NffAgMBAAGjgacwgaQwHQYDVR0OBBYEFNRJ
    PYFebixALIR2Ee+yFoSqurxqMHUGA1UdIwRuMGyAFNRJPYFebixALIR2Ee+yFoSq
    urxqoUmkRzBFMQswCQYDVQQGEwJBVTETMBEGA1UECBMKU29tZS1TdGF0ZTEhMB8G
    A1UEChMYSW50ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkggkAxn+pF1FqaW4wDAYDVR0T
    BAUwAwEB/zANBgkqhkiG9w0BAQUFAAOCAQEAoPTwU2rm0ca5b8xMni3vpjYmB9NW
    oSpGcWENbvu/p7NpiPAe143c5EPCuEHue/AbHWWxBzNAZvhVZBeFirYNB3HYnCla
    jP4WI3o2Q0MpGy3kMYigEYG76WeZAM5ovl0qDP6fKuikZofeiygb8lPs7Hv4/88x
    pSsZYBm7UPTS3Pl044oZfRJdqTpyHVPDqwiYD5KQcI0yHUE9v5KC0CnqOrU/83PE
    b0lpHA8bE9gQTQjmIa8MIpaP3UNTxvmKfEQnk5UAZ5xY2at5mmyj3t8woGdzoL98
    yDd2GtrGsguQXM2op+4LqEdHef57g7vwolZejJqN776Xu/lZtCTp01+HTA==
    -----END CERTIFICATE-----
director_address: 192.168.50.4
director_username: admin
director_password: admin

#### bosh_creds_file end

## Sample concourse_creds file

url: http://localhost:8080
team: main
insecure: false
username: admin
password: admin
ca_cert: |
    -----BEGIN CERTIFICATE-----
    MIIDtzCCAp+gAwIBAgIJAMZ/qRdRamluMA0GCSqGSIb3DQEBBQUAMEUxCzAJBgNV
    BAYTAkFVMRMwEQYDVQQIEwpTb21lLVN0YXRlMSEwHwYDVQQKExhJbnRlcm5ldCBX
    aWRnaXRzIFB0eSBMdGQwIBcNMTYwODI2MjIzMzE5WhgPMjI5MDA2MTAyMjMzMTla
    MEUxCzAJBgNVBAYTAkFVMRMwEQYDVQQIEwpTb21lLVN0YXRlMSEwHwYDVQQKExhJ
    bnRlcm5ldCBXaWRnaXRzIFB0eSBMdGQwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAw
    ggEKAoIBAQDN/bv70wDn6APMqiJZV7ESZhUyGu8OzuaeEfb+64SNvQIIME0s9+i7
    D9gKAZjtoC2Tr9bJBqsKdVhREd/X6ePTaopxL8shC9GxXmTqJ1+vKT6UxN4kHr3U
    +Y+LK2SGYUAvE44nv7sBbiLxDl580P00ouYTf6RJgW6gOuKpIGcvsTGA4+u0UTc+
    y4pj6sT0+e3xj//Y4wbLdeJ6cfcNTU63jiHpKc9Rgo4Tcy97WeEryXWz93rtRh8d
    pvQKHVDU/26EkNsPSsn9AHNgaa+iOA2glZ2EzZ8xoaMPrHgQhcxoi8maFzfM2dX2
    XB1BOswa/46yqfzc4xAwaW0MLZLg3NffAgMBAAGjgacwgaQwHQYDVR0OBBYEFNRJ
    PYFebixALIR2Ee+yFoSqurxqMHUGA1UdIwRuMGyAFNRJPYFebixALIR2Ee+yFoSq
    urxqoUmkRzBFMQswCQYDVQQGEwJBVTETMBEGA1UECBMKU29tZS1TdGF0ZTEhMB8G
    A1UEChMYSW50ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkggkAxn+pF1FqaW4wDAYDVR0T
    BAUwAwEB/zANBgkqhkiG9w0BAQUFAAOCAQEAoPTwU2rm0ca5b8xMni3vpjYmB9NW
    oSpGcWENbvu/p7NpiPAe143c5EPCuEHue/AbHWWxBzNAZvhVZBeFirYNB3HYnCla
    jP4WI3o2Q0MpGy3kMYigEYG76WeZAM5ovl0qDP6fKuikZofeiygb8lPs7Hv4/88x
    pSsZYBm7UPTS3Pl044oZfRJdqTpyHVPDqwiYD5KQcI0yHUE9v5KC0CnqOrU/83PE
    b0lpHA8bE9gQTQjmIa8MIpaP3UNTxvmKfEQnk5UAZ5xY2at5mmyj3t8woGdzoL98
    yDd2GtrGsguQXM2op+4LqEdHef57g7vwolZejJqN776Xu/lZtCTp01+HTA==
    -----END CERTIFICATE-----

####### Concourse creds files end

## Sample deployment-config-file

name: redis
release:
    repo: "https://github.com/hkumarmk/redis-boshrelease.git"
    branch: master
# deployment manifest repo. Default to release_repo
manifest:
  repo: "https://github.com/hkumarmk/redis-boshrelease.git"
  # Path to deployment manifest within manifest repo default to manifest.yml
  path: manifests/redis.yml
stemcells:
  - bosh-warden-boshlite-ubuntu-trusty-go_agent
"""
