#
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
#
import os
import unittest

import mock
import yaml
import json
import main
import dicts
from copy import deepcopy

deployment_config = {
    "name": "test_name",
    "releases": {
      "foo": {
        "repo": "foo_release_repo",
        "branch": "master"
      }
    },
    "manifest": {
      "repo": "manifest_repo",
      "path": "manifests/test_manifest.yml"
    },
    "stemcells": [
        "bosh-warden-boshlite-ubuntu-trusty-go_agent"
    ],
    "targets": {
        "region_a": {
            "stages": [
                {"test": {"bosh": "bosh-test"}},
                {"stage": {"bosh": "bosh-stage"}},
                {"prod": {"bosh": "bosh-prod"}},
            ]
        }
    }
}


def get_config_(obj):
    config_file = os.path.join(os.path.dirname(__file__), "..", "examples", obj + ".yml")
    if os.path.isfile(config_file):
        with open(config_file, 'r') as f:
            return yaml.load(f)


class BoshifierTests(unittest.TestCase):

    def setUp(self):
        main.app.testing = True
        self.app = main.app.test_client()
        self.maxDiff = None

    def test_get_index(self):
        resp = self.app.get('/')
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.headers['content-type'],
                          'text/plain; charset=utf-8')

    @mock.patch('main.DeploymentProcessor.process')
    def test_post_success(self, process):
        process.return_value = 'Deployment done', 200
        resp = self.app.post(data={
            "bosh": ("/dev/null",),
            "concourse": ("/dev/null",),
            "deployment": ("/dev/null",),
        })
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.data, "Deployment done")

    @mock.patch('main.DeploymentProcessor._get_initial_config_file')
    def test_get_targets(self, ic):
        ic.return_value = str(get_config_('targets'))
        resp = self.app.get('targets')
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(json.dumps(json.loads(resp.data)),
                          json.dumps(get_config_('targets')['targets']))

    @mock.patch('main.DeploymentProcessor._get_initial_config_file')
    def test_get_no_targets(self, ic):
        ic.return_value = str(get_config_('deployment'))
        resp = self.app.get('targets')
        self.assertEquals(resp.status_code, 404)

    def test_post_no_files(self):
        resp = self.app.post()
        self.assertEquals(resp.status_code, 400)

    def test_render_j2_release_from_git(self):
        self.assertEqual(
            main.render_j2(variables=deployment_config),
            dicts.exp_render_j2_release_from_git)

    def test_render_j2_multi_release(self):
        deployment_config_multi = deepcopy(deployment_config)
        deployment_config_multi['releases'].update({'bar': {"repo": "repo_bar", "boshio_release": True}})
        deployment_config_multi['stemcells'].append('bosh-warden-boshlite-ubuntu-xenial-go_agent')
        self.assertEqual(
            main.render_j2(variables=deployment_config_multi),
            dicts.exp_render_j2_multi_release)

    def test_render_j2_bosh_release(self):
        deployment_config_bosh = deepcopy(deployment_config)
        deployment_config_bosh['releases']['foo'].update({"boshio_release": True})
        del deployment_config_bosh['releases']['foo']['branch']

        self.assertEqual(
            main.render_j2(variables=deployment_config_bosh),
            dicts.exp_render_j2_bosh_release)

    def test_render_j2_bosh_release_tarball(self):
        deployment_config_tarball = deployment_config.copy()
        deployment_config_tarball.update({"boshio_release": True, "release_tarball": True})

        self.assertEqual(
            main.render_j2(variables=deployment_config_tarball),
            dicts.exp_render_j2_bosh_release_tarball)

    def test_read_yaml(self):
        self.assertEqual(
            main.read_yaml(open(os.path.join(
                os.path.dirname(__file__), "samples", "deployment.yml"), "r")),
            {
                'stemcells': ['bosh-warden-boshlite-ubuntu-trusty-go_agent', 'bosh-warden-boshlite-ubuntu-xenial-go_agent'],
                'name': 'test_name',
                'releases': {
                    'foo': {
                        'repo': 'foo_release_repo',
                        'branch': 'master'
                    }
                },
                'manifest': {
                    'repo': 'manifest_repo',
                    'path': 'manifests/test_manifest.yml'
                }
            }
        )

    def test_get_config_deployment(self):
        self.assertEqual(
            main.get_config(open(os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "examples", "deployment.yml"), "r")),
            dicts.exp_get_config_deployment)

    def test_get_config_bosh(self):
        self.assertEqual(
            main.get_config(open(os.path.join(
                os.path.dirname(__file__),
                "samples", "bosh.yml"), "r")),
            dicts.exp_get_config_bosh)

    def test_get_config_concourse(self):
        self.assertEqual(
            main.get_config(open(os.path.join(
                os.path.dirname(__file__),
                "samples", "concourse.yml"), "r")),
            dicts.exp_get_config_concourse)


class DeploymentProcessorTests(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.app = main.app.test_client()
        self.dp = main.DeploymentProcessor([
            open(os.path.join(
                os.path.dirname(__file__), "samples", "concourse.yml"), "r"),
            open(os.path.join(
                os.path.dirname(__file__), "samples", "bosh.yml"), "r"),
            open(os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "examples", "deployment.yml"), "r"),
            open(os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "examples", "targets.yml"), "r")
        ])

    @mock.patch('main.Flyer.login')
    @mock.patch('main.Flyer.set_pipeline')
    @mock.patch('main.Flyer.unpause_pipeline')
    def test_process_success(self, unpause_pipeline, set_pipeline, login):
        main.Flyer.login.return_value = 0
        main.Flyer.set_pipeline.return_value = 0
        main.Flyer.unpause_pipeline.return_value = 0
        self.assertEqual(
            self.dp.process(), ("Deployment done", 200))
        login.assert_called_once()
        set_pipeline.assert_called_once()
        unpause_pipeline.assert_called_once()

    @mock.patch('main.Flyer.login')
    @mock.patch('main.Flyer.set_pipeline')
    @mock.patch('main.Flyer.unpause_pipeline')
    def test_process_login_failed(self, unpause_pipeline, set_pipeline, login):
        main.Flyer.login.return_value = 127
        self.assertEqual(
            self.dp.process(), ("Login to concourse failed", 500)
        )
        login.assert_called_once()
        set_pipeline.assert_not_called()
        unpause_pipeline.assert_not_called()

    @mock.patch('main.Flyer.login')
    @mock.patch('main.Flyer.set_pipeline')
    @mock.patch('main.Flyer.unpause_pipeline')
    def test_deploy_to_bosh_sp_failed(self, unpause_pipeline, set_pipeline, login):
        main.Flyer.login.return_value = 0
        main.Flyer.set_pipeline.return_value = 127
        self.assertEqual(
            self.dp.process(), ("Set pipeline failed", 500)
        )
        login.assert_called_once()
        set_pipeline.assert_called_once()
        unpause_pipeline.assert_not_called()

    @mock.patch('main.Flyer.login')
    @mock.patch('main.Flyer.set_pipeline')
    @mock.patch('main.Flyer.unpause_pipeline')
    def test_deploy_to_bosh_up_failed(self, unpause_pipeline, set_pipeline, login):
        main.Flyer.login.return_value = 0
        main.Flyer.set_pipeline.return_value = 0
        main.Flyer.unpause_pipeline.return_value = 127
        self.assertEqual(
            self.dp.process(), ("Unpause pipeline failed", 500)
        )
        login.assert_called_once()
        set_pipeline.assert_called_once()
        unpause_pipeline.assert_called_once()


class FlyerTests(unittest.TestCase):

    def setUp(self):
        self.dp = main.DeploymentProcessor([
            open(os.path.join(
                os.path.dirname(__file__), "samples", "concourse.yml"), "r"),
            open(os.path.join(
                os.path.dirname(__file__), "samples", "bosh.yml"), "r"),
            open(os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "examples", "deployment.yml"), "r"),
            open(os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "examples", "targets.yml"), "r")
        ])
        self.dp._subst_creds()
        creds = self.dp.configs['concourse']['cc1']
        deployment_config.update({"deployment_name": "test_name"})
        self.fly = main.Flyer(
            creds,
            '/tmp/',
            deployment_config
        )

    @mock.patch('main.Flyer._fly_cmd')
    def test_login(self, fly_cmd):
        self.fly.login()
        fly_cmd.assert_called_with(
            "login",
            "--target", "localhost",
            "--concourse-url", "http://localhost:8080",
            "--username", "admin",
            "--password", "admin",
            "--team-name", "main",
            "--ca-cert", "/tmp/concourse_ca_cert.crt"
        )

    @mock.patch('main.Flyer._fly_cmd')
    def test_set_pipeline(self, fly_cmd):
        self.fly.set_pipeline()
        fly_cmd.assert_called_with(
            'set-pipeline',
            '--target', 'localhost',
            '--non-interactive',
            '--pipeline', 'test_name',
            '--config', '/tmp/.pipeline.yml',
            '--load-vars-from', '/tmp/vars.yml'
        )

    @mock.patch('main.Flyer._fly_cmd')
    def test_unpause_pipeline(self, fly_cmd):
        self.fly.unpause_pipeline()
        fly_cmd.assert_called_with(
            'unpause-pipeline',
            '--target', 'localhost',
            '--pipeline', 'test_name',
        )


