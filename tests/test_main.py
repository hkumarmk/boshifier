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
    ]
}


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

    def test_render_j2_release_from_git(self):
        self.assertEqual(
            main.render_j2(variables=deployment_config),
            {
                'resource_types': [{
                    'source': {
                        'repository': 'cloudfoundry/bosh-deployment-resource'
                    },
                    'type': 'docker-image',
                    'name': 'bosh-deployment'
                }],
                'jobs': [{
                    'name': '((deployment_name))-deploy',
                    'plan': [{
                        'aggregate': [{
                            'get': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                        }, {
                            'get': 'bosh-deployment-manifest'
                        }, {
                            'get': 'stemcell-bosh-warden-boshlite-ubuntu-xenial-go_agent'
                        }, {
                            'get': 'bosh-deployment-manifest'
                        }, {
                            'get': 'bosh-release-get-foo'
                        }, {
                            'get': 'bosh-release-get-bar'
                        }]
                    }, {
                        'aggregate': None
                    }, {
                        'put': 'bosh-deployment',
                        'params': {
                            'stemcells': ['stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent/*.tgz', 'stemcell-bosh-warden-boshlite-ubuntu-xenial-go_agent/*.tgz'],
                            'releases': ['bosh-release-get-foo/*.tgz', 'bosh-release-get-bar/*.tgz'],
                            'manifest': 'bosh-deployment-manifest/manifests/test_manifest.yml'
                        }
                    }]
                }],
                'resources': [{
                    'source': {
                        'client_secret': '((director_password))',
                        'client': '((director_username))',
                        'target': '((director_address))',
                        'ca_cert': '((director_ca_cert))',
                        'deployment': '((deployment_name))'
                    },
                    'type': 'bosh-deployment',
                    'name': 'bosh-deployment'
                }, {
                    'source': {
                        'repository': 'foo_release_repo'
                    },
                    'type': 'bosh-io-release',
                    'name': 'bosh-release-get-foo'
                }, {
                    'source': {
                        'repository': 'repo_bar'
                    },
                    'type': 'bosh-io-release',
                    'name': 'bosh-release-get-bar'
                }, {
                    'source': {
                        'name': 'bosh-warden-boshlite-ubuntu-trusty-go_agent'
                    },
                    'type': 'bosh-io-stemcell',
                    'name': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                }, {
                    'source': {
                        'name': 'bosh-warden-boshlite-ubuntu-xenial-go_agent'
                    },
                    'type': 'bosh-io-stemcell',
                    'name': 'stemcell-bosh-warden-boshlite-ubuntu-xenial-go_agent'
                }, {
                    'source': {
                        'uri': 'manifest_repo',
                        'branch': 'master'
                    },
                    'type': 'git',
                    'name': 'bosh-deployment-manifest'
                }]
            }
        )

    def test_render_j2_multi_release(self):
        deployment_config_multi = deployment_config.copy()
        deployment_config_multi['releases'].update({'bar': {"repo": "repo_bar", "boshio_release": True}})
        deployment_config_multi['stemcells'].append('bosh-warden-boshlite-ubuntu-xenial-go_agent')
        self.assertEqual(
            main.render_j2(variables=deployment_config_multi),
            {
                'resource_types': [{
                    'source': {
                        'repository': 'cloudfoundry/bosh-deployment-resource'
                    },
                    'type': 'docker-image',
                    'name': 'bosh-deployment'
                }],
                'jobs': [{
                    'name': '((deployment_name))-deploy',
                    'plan': [{
                        'aggregate': [{
                            'get': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                        }, {
                            'get': 'bosh-deployment-manifest'
                        }, {
                            'get': 'stemcell-bosh-warden-boshlite-ubuntu-xenial-go_agent'
                        }, {
                            'get': 'bosh-deployment-manifest'
                        }, {
                            'get': 'bosh-release-get-foo'
                        }, {
                            'get': 'bosh-release-get-bar'
                        }]
                    }, {
                        'aggregate': None
                    }, {
                        'put': 'bosh-deployment',
                        'params': {
                            'stemcells': ['stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent/*.tgz', 'stemcell-bosh-warden-boshlite-ubuntu-xenial-go_agent/*.tgz'],
                            'releases': ['bosh-release-get-foo/*.tgz', 'bosh-release-get-bar/*.tgz'],
                            'manifest': 'bosh-deployment-manifest/manifests/test_manifest.yml'
                        }
                    }]
                }],
                'resources': [{
                    'source': {
                        'client_secret': '((director_password))',
                        'client': '((director_username))',
                        'target': '((director_address))',
                        'ca_cert': '((director_ca_cert))',
                        'deployment': '((deployment_name))'
                    },
                    'type': 'bosh-deployment',
                    'name': 'bosh-deployment'
                }, {
                    'source': {
                        'repository': 'foo_release_repo'
                    },
                    'type': 'bosh-io-release',
                    'name': 'bosh-release-get-foo'
                }, {
                    'source': {
                        'repository': 'repo_bar'
                    },
                    'type': 'bosh-io-release',
                    'name': 'bosh-release-get-bar'
                }, {
                    'source': {
                        'name': 'bosh-warden-boshlite-ubuntu-trusty-go_agent'
                    },
                    'type': 'bosh-io-stemcell',
                    'name': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                }, {
                    'source': {
                        'name': 'bosh-warden-boshlite-ubuntu-xenial-go_agent'
                    },
                    'type': 'bosh-io-stemcell',
                    'name': 'stemcell-bosh-warden-boshlite-ubuntu-xenial-go_agent'
                }, {
                    'source': {
                        'uri': 'manifest_repo',
                        'branch': 'master'
                    },
                    'type': 'git',
                    'name': 'bosh-deployment-manifest'
                }]
            }
        )

    def test_render_j2_bosh_release(self):
        deployment_config_bosh = deployment_config.copy()
        deployment_config_bosh['releases']['foo'].update({"boshio_release": True})
        del deployment_config_bosh['releases']['foo']['branch']

        self.assertEqual(
            main.render_j2(variables=deployment_config_bosh),
            {
                'resource_types': [{
                    'source': {
                        'repository': 'cloudfoundry/bosh-deployment-resource'
                    },
                    'type': 'docker-image',
                    'name': 'bosh-deployment'
                }],
                'jobs': [{
                    'name': '((deployment_name))-deploy',
                    'plan': [{
                        'aggregate': [{
                            'get': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                        }, {
                            'get': 'bosh-deployment-manifest'
                        }, {
                            'get': 'bosh-release-get-foo'
                        }]
                    }, {
                        'aggregate': None
                    }, {
                        'put': 'bosh-deployment',
                        'params': {
                            'stemcells': ['stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent/*.tgz'],
                            'releases': ['bosh-release-get-foo/*.tgz'],
                            'manifest': 'bosh-deployment-manifest/manifests/test_manifest.yml'
                        }
                    }]
                }],
                'resources': [{
                    'source': {
                        'client_secret': '((director_password))',
                        'client': '((director_username))',
                        'target': '((director_address))',
                        'ca_cert': '((director_ca_cert))',
                        'deployment': '((deployment_name))'
                    },
                    'type': 'bosh-deployment',
                    'name': 'bosh-deployment'
                }, {
                    'source': {
                        'repository': 'foo_release_repo'
                    },
                    'type': 'bosh-io-release',
                    'name': 'bosh-release-get-foo'
                }, {
                    'source': {
                        'name': 'bosh-warden-boshlite-ubuntu-trusty-go_agent'
                    },
                    'type': 'bosh-io-stemcell',
                    'name': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                }, {
                    'source': {
                        'uri': 'manifest_repo',
                        'branch': 'master'
                    },
                    'type': 'git',
                    'name': 'bosh-deployment-manifest'
                }]
            }
        )

    def test_render_j2_bosh_release_tarball(self):
        deployment_config_tarball = deployment_config.copy()
        deployment_config_tarball.update({"boshio_release": True, "release_tarball": True})

        self.assertEqual(
            main.render_j2(variables=deployment_config_tarball),
            {
                'resource_types': [{
                    'source': {
                        'repository': 'cloudfoundry/bosh-deployment-resource'
                    },
                    'type': 'docker-image',
                    'name': 'bosh-deployment'
                }],
                'jobs': [{
                    'name': '((deployment_name))-deploy',
                    'plan': [{
                        'aggregate': [{
                            'get': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                        }, {
                            'get': 'bosh-deployment-manifest'
                        }, {
                            'get': 'bosh-release-get-foo'
                        }]
                    }, {
                        'aggregate': None
                    }, {
                        'put': 'bosh-deployment',
                        'params': {
                            'stemcells': ['stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent/*.tgz'],
                            'releases': ['bosh-release-get-foo/*.tgz'],
                            'manifest': 'bosh-deployment-manifest/manifests/test_manifest.yml'
                        }
                    }]
                }],
                'resources': [{
                    'source': {
                        'client_secret': '((director_password))',
                        'client': '((director_username))',
                        'target': '((director_address))',
                        'ca_cert': '((director_ca_cert))',
                        'deployment': '((deployment_name))'
                    },
                    'type': 'bosh-deployment',
                    'name': 'bosh-deployment'
                }, {
                    'source': {
                        'repository': 'foo_release_repo'
                    },
                    'type': 'bosh-io-release',
                    'name': 'bosh-release-get-foo'
                }, {
                    'source': {
                        'name': 'bosh-warden-boshlite-ubuntu-trusty-go_agent'
                    },
                    'type': 'bosh-io-stemcell',
                    'name': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                }, {
                    'source': {
                        'uri': 'manifest_repo',
                        'branch': 'master'
                    },
                    'type': 'git',
                    'name': 'bosh-deployment-manifest'
                }]
            }
        )

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
