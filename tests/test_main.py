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
from StringIO import StringIO
import unittest
import os
import mock
import main


class BoshifierTests(unittest.TestCase):

    def setUp(self):
        main.app.testing = True
        self.app = main.app.test_client()

    def test_get_index(self):
        resp = self.app.get('/')
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.headers['content-type'],
                          'text/plain; charset=utf-8')

    @mock.patch('main.deploy_to_bosh')
    def test_post_success(self, deploy_to_bosh):
        deploy_to_bosh.return_value = 'Deployment done', 200
        resp = self.app.post(data={
            "bosh": ("/dev/null",),
            "concourse": ("/dev/null",),
            "deployment": ("/dev/null",),
        })
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.data, "Deployment done")

    def test_post_no_files(self):
        resp = self.app.post()
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp.data, "You must pass a bosh credentials yaml file")

    def test_post_no_bosh(self):
        resp = self.app.post(data={
            "concourse": ("/dev/null",),
            "deployment": ("/dev/null",),
        })
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp.data, "You must pass a bosh credentials yaml file")

    def test_post_only_bosh(self):
        resp = self.app.post(data={
            "bosh": ("/dev/null",),
        })
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp.data, "You must pass a concourse credentials yaml file")

    def test_post_bosh_concourse(self):
        resp = self.app.post(data={
            "bosh": ("/dev/null",),
            "concourse": ("/dev/null",),
        })
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp.data, "You must pass a deployment configuration yaml file")

    def test_read_yaml(self):
        self.assertEqual(
            main.read_yaml(open(os.path.join(
                os.path.dirname(__file__), "samples", "deployment.yml"), "r")),
            {
                "name": "test_name",
                "release": {
                    "repo": "release_repo",
                    "branch": "master",
                },
                "manifest": {
                    "repo": "manifest_repo",
                    "path": "manifests/test_manifest.yml"
                },
                "stemcell": "bosh-warden-boshlite-ubuntu-trusty-go_agent"
            }
        )

    def test_get_deployment_config(self):
        self.assertEqual(
            main.get_deployment_config(open(os.path.join(
                os.path.dirname(__file__), "samples", "deployment.yml"), "r")),
            {
                "deployment": "test_name",
                "bosh_release_repo": "release_repo",
                "stemcell": "bosh-warden-boshlite-ubuntu-trusty-go_agent",
                "deployment_manifest_repo": "manifest_repo",
                "deployment_manifest_path": "manifests/test_manifest.yml",
                "bosh_release_branch": "master"
            }
        )

    @mock.patch('main.Flyer.login')
    @mock.patch('main.Flyer.set_pipeline')
    @mock.patch('main.Flyer.unpause_pipeline')
    def test_deploy_to_bosh(self, unpause_pipeline, set_pipeline, login):
        main.Flyer.login.return_value = 0
        main.Flyer.set_pipeline.return_value = 0
        main.Flyer.unpause_pipeline.return_value = 0
        self.assertEqual(
            main.deploy_to_bosh(
                open(os.path.join(
                    os.path.dirname(__file__), "samples", "bosh.yml"), "r"),
                open(os.path.join(
                    os.path.dirname(__file__), "samples", "concourse.yml"), "r"),
                open(os.path.join(
                    os.path.dirname(__file__), "samples", "deployment.yml"), "r")
            ), ('Deployment done', 200)
        )
        login.assert_called_once()
        set_pipeline.assert_called_once()
        unpause_pipeline.assert_called_once()

    @mock.patch('main.Flyer.login')
    @mock.patch('main.Flyer.set_pipeline')
    @mock.patch('main.Flyer.unpause_pipeline')
    def test_deploy_to_bosh_login_failed(self, unpause_pipeline, set_pipeline, login):
        main.Flyer.login.return_value = 127
        self.assertEqual(
            main.deploy_to_bosh(
                open(os.path.join(
                    os.path.dirname(__file__), "samples", "bosh.yml"), "r"),
                open(os.path.join(
                    os.path.dirname(__file__), "samples", "concourse.yml"), "r"),
                open(os.path.join(
                    os.path.dirname(__file__), "samples", "deployment.yml"), "r")
            ), ("Login to concourse failed", 500)
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
            main.deploy_to_bosh(
                open(os.path.join(
                    os.path.dirname(__file__), "samples", "bosh.yml"), "r"),
                open(os.path.join(
                    os.path.dirname(__file__), "samples", "concourse.yml"), "r"),
                open(os.path.join(
                    os.path.dirname(__file__), "samples", "deployment.yml"), "r")
            ), ("Set pipeline failed for test_name", 500)
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
            main.deploy_to_bosh(
                open(os.path.join(
                    os.path.dirname(__file__), "samples", "bosh.yml"), "r"),
                open(os.path.join(
                    os.path.dirname(__file__), "samples", "concourse.yml"), "r"),
                open(os.path.join(
                    os.path.dirname(__file__), "samples", "deployment.yml"), "r")
            ), ("Unpause pipeline failed for test_name", 500)
        )
        login.assert_called_once()
        set_pipeline.assert_called_once()
        unpause_pipeline.assert_called_once()


class FlyerTests(unittest.TestCase):

    def setUp(self):
        self.fly = main.Flyer(
            open(os.path.join(
                os.path.dirname(__file__), "samples", "concourse.yml"), "r"),
            'test_pipeline', "/tmp"
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
            '--pipeline', 'test_pipeline',
            '--config', 'templates/pipeline.yml',
            '--load-vars-from', '/tmp/vars.yml'
        )

    @mock.patch('main.Flyer._fly_cmd')
    def test_unpause_pipeline(self, fly_cmd):
        self.fly.unpause_pipeline()
        fly_cmd.assert_called_with(
            'unpause-pipeline',
            '--target', 'localhost',
            '--pipeline', 'test_pipeline',
        )
