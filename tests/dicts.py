exp_render_j2_release_from_git = {
    'resource_types': [{
        'source': {
            'repository': 'cloudfoundry/bosh-deployment-resource'
        },
        'type': 'docker-image',
        'name': 'bosh-deployment'
    }],
    'jobs': [{
        'serial': True,
        'name': 'deploy-region_a-test',
        'plan': [{
            'do': [{
                'aggregate': [{
                    'get': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                }, {
                    'trigger': True,
                    'get': 'bosh-deployment-manifest'
                }, {
                    'trigger': True,
                    'get': 'bosh-release-get-foo'
                }]
            }, {
                'aggregate': [{
                    'task': 'create-release-foo',
                    'config': {
                        'platform': 'linux',
                        'inputs': [{
                            'name': 'bosh-release-get-foo'
                        }],
                        'run': {
                            'path': 'bosh',
                            'args': ['create-release', '--final', '--tarball=../bosh-release-foo/release.tgz'],
                            'dir': 'bosh-release-get-foo'
                        },
                        'outputs': [{
                            'path': '',
                            'name': 'bosh-release-foo'
                        }],
                        'image_resource': {
                            'source': {
                                'repository': 'hkumar/bosh-cli-v2'
                            },
                            'type': 'docker-image'
                        }
                    }
                }]
            }, {
                'put': 'bd-region_a-test',
                'params': {
                    'stemcells': ['stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent/*.tgz'],
                    'releases': ['bosh-release-foo/*.tgz'],
                    'manifest': 'bosh-deployment-manifest/manifests/test_manifest.yml'
                }
            }]
        }]
    }, {
        'serial': True,
        'name': 'deploy-region_a-stage',
        'plan': [{
            'do': [{
                'aggregate': [{
                    'get': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-test'],
                    'get': 'bosh-deployment-manifest'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-test'],
                    'get': 'bosh-release-get-foo'
                }]
            }, {
                'aggregate': [{
                    'task': 'create-release-foo',
                    'config': {
                        'platform': 'linux',
                        'inputs': [{
                            'name': 'bosh-release-get-foo'
                        }],
                        'run': {
                            'path': 'bosh',
                            'args': ['create-release', '--final', '--tarball=../bosh-release-foo/release.tgz'],
                            'dir': 'bosh-release-get-foo'
                        },
                        'outputs': [{
                            'path': '',
                            'name': 'bosh-release-foo'
                        }],
                        'image_resource': {
                            'source': {
                                'repository': 'hkumar/bosh-cli-v2'
                            },
                            'type': 'docker-image'
                        }
                    }
                }]
            }, {
                'put': 'bd-region_a-stage',
                'params': {
                    'stemcells': ['stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent/*.tgz'],
                    'releases': ['bosh-release-foo/*.tgz'],
                    'manifest': 'bosh-deployment-manifest/manifests/test_manifest.yml'
                }
            }]
        }]
    }, {
        'serial': True,
        'name': 'deploy-region_a-prod',
        'plan': [{
            'do': [{
                'aggregate': [{
                    'get': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-stage'],
                    'get': 'bosh-deployment-manifest'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-stage'],
                    'get': 'bosh-release-get-foo'
                }]
            }, {
                'aggregate': [{
                    'task': 'create-release-foo',
                    'config': {
                        'platform': 'linux',
                        'inputs': [{
                            'name': 'bosh-release-get-foo'
                        }],
                        'run': {
                            'path': 'bosh',
                            'args': ['create-release', '--final', '--tarball=../bosh-release-foo/release.tgz'],
                            'dir': 'bosh-release-get-foo'
                        },
                        'outputs': [{
                            'path': '',
                            'name': 'bosh-release-foo'
                        }],
                        'image_resource': {
                            'source': {
                                'repository': 'hkumar/bosh-cli-v2'
                            },
                            'type': 'docker-image'
                        }
                    }
                }]
            }, {
                'put': 'bd-region_a-prod',
                'params': {
                    'stemcells': ['stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent/*.tgz'],
                    'releases': ['bosh-release-foo/*.tgz'],
                    'manifest': 'bosh-deployment-manifest/manifests/test_manifest.yml'
                }
            }]
        }]
    }],
    'resources': [{
        'source': {
            'client_secret': '((region_a.test.director_password))',
            'client': '((region_a.test.director_username))',
            'target': '((region_a.test.director_address))',
            'ca_cert': '((region_a.test.director_ca_cert))',
            'deployment': None
        },
        'type': 'bosh-deployment',
        'name': 'bd-region_a-test'
    }, {
        'source': {
            'client_secret': '((region_a.stage.director_password))',
            'client': '((region_a.stage.director_username))',
            'target': '((region_a.stage.director_address))',
            'ca_cert': '((region_a.stage.director_ca_cert))',
            'deployment': None
        },
        'type': 'bosh-deployment',
        'name': 'bd-region_a-stage'
    }, {
        'source': {
            'client_secret': '((region_a.prod.director_password))',
            'client': '((region_a.prod.director_username))',
            'target': '((region_a.prod.director_address))',
            'ca_cert': '((region_a.prod.director_ca_cert))',
            'deployment': None
        },
        'type': 'bosh-deployment',
        'name': 'bd-region_a-prod'
    }, {
        'source': {
            'uri': 'foo_release_repo',
            'branch': 'master'
        },
        'type': 'git',
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
    }],
    'groups': [{
        'jobs': ['deploy-region_a-test', 'deploy-region_a-stage', 'deploy-region_a-prod'],
        'name': 'deploy-region_a'
    }]
}

exp_render_j2_multi_release = {
    'resource_types': [{
        'source': {
            'repository': 'cloudfoundry/bosh-deployment-resource'
        },
        'type': 'docker-image',
        'name': 'bosh-deployment'
    }],
    'jobs': [{
        'serial': True,
        'name': 'deploy-region_a-test',
        'plan': [{
            'do': [{
                'aggregate': [{
                    'get': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                }, {
                    'get': 'stemcell-bosh-warden-boshlite-ubuntu-xenial-go_agent'
                }, {
                    'trigger': True,
                    'get': 'bosh-deployment-manifest'
                }, {
                    'trigger': True,
                    'get': 'bosh-release-get-foo'
                }, {
                    'trigger': True,
                    'get': 'bosh-release-get-bar'
                }]
            }, {
                'aggregate': [{
                    'task': 'create-release-foo',
                    'config': {
                        'platform': 'linux',
                        'inputs': [{
                            'name': 'bosh-release-get-foo'
                        }],
                        'run': {
                            'path': 'bosh',
                            'args': ['create-release', '--final', '--tarball=../bosh-release-foo/release.tgz'],
                            'dir': 'bosh-release-get-foo'
                        },
                        'outputs': [{
                            'path': '',
                            'name': 'bosh-release-foo'
                        }],
                        'image_resource': {
                            'source': {
                                'repository': 'hkumar/bosh-cli-v2'
                            },
                            'type': 'docker-image'
                        }
                    }
                }]
            }, {
                'put': 'bd-region_a-test',
                'params': {
                    'stemcells': ['stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent/*.tgz', 'stemcell-bosh-warden-boshlite-ubuntu-xenial-go_agent/*.tgz'],
                    'releases': ['bosh-release-foo/*.tgz', 'bosh-release-get-bar/*.tgz'],
                    'manifest': 'bosh-deployment-manifest/manifests/test_manifest.yml'
                }
            }]
        }]
    }, {
        'serial': True,
        'name': 'deploy-region_a-stage',
        'plan': [{
            'do': [{
                'aggregate': [{
                    'get': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                }, {
                    'get': 'stemcell-bosh-warden-boshlite-ubuntu-xenial-go_agent'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-test'],
                    'get': 'bosh-deployment-manifest'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-test'],
                    'get': 'bosh-release-get-foo'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-test'],
                    'get': 'bosh-release-get-bar'
                }]
            }, {
                'aggregate': [{
                    'task': 'create-release-foo',
                    'config': {
                        'platform': 'linux',
                        'inputs': [{
                            'name': 'bosh-release-get-foo'
                        }],
                        'run': {
                            'path': 'bosh',
                            'args': ['create-release', '--final', '--tarball=../bosh-release-foo/release.tgz'],
                            'dir': 'bosh-release-get-foo'
                        },
                        'outputs': [{
                            'path': '',
                            'name': 'bosh-release-foo'
                        }],
                        'image_resource': {
                            'source': {
                                'repository': 'hkumar/bosh-cli-v2'
                            },
                            'type': 'docker-image'
                        }
                    }
                }]
            }, {
                'put': 'bd-region_a-stage',
                'params': {
                    'stemcells': ['stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent/*.tgz', 'stemcell-bosh-warden-boshlite-ubuntu-xenial-go_agent/*.tgz'],
                    'releases': ['bosh-release-foo/*.tgz', 'bosh-release-get-bar/*.tgz'],
                    'manifest': 'bosh-deployment-manifest/manifests/test_manifest.yml'
                }
            }]
        }]
    }, {
        'serial': True,
        'name': 'deploy-region_a-prod',
        'plan': [{
            'do': [{
                'aggregate': [{
                    'get': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                }, {
                    'get': 'stemcell-bosh-warden-boshlite-ubuntu-xenial-go_agent'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-stage'],
                    'get': 'bosh-deployment-manifest'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-stage'],
                    'get': 'bosh-release-get-foo'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-stage'],
                    'get': 'bosh-release-get-bar'
                }]
            }, {
                'aggregate': [{
                    'task': 'create-release-foo',
                    'config': {
                        'platform': 'linux',
                        'inputs': [{
                            'name': 'bosh-release-get-foo'
                        }],
                        'run': {
                            'path': 'bosh',
                            'args': ['create-release', '--final', '--tarball=../bosh-release-foo/release.tgz'],
                            'dir': 'bosh-release-get-foo'
                        },
                        'outputs': [{
                            'path': '',
                            'name': 'bosh-release-foo'
                        }],
                        'image_resource': {
                            'source': {
                                'repository': 'hkumar/bosh-cli-v2'
                            },
                            'type': 'docker-image'
                        }
                    }
                }]
            }, {
                'put': 'bd-region_a-prod',
                'params': {
                    'stemcells': ['stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent/*.tgz', 'stemcell-bosh-warden-boshlite-ubuntu-xenial-go_agent/*.tgz'],
                    'releases': ['bosh-release-foo/*.tgz', 'bosh-release-get-bar/*.tgz'],
                    'manifest': 'bosh-deployment-manifest/manifests/test_manifest.yml'
                }
            }]
        }]
    }],
    'resources': [{
        'source': {
            'client_secret': '((region_a.test.director_password))',
            'client': '((region_a.test.director_username))',
            'target': '((region_a.test.director_address))',
            'ca_cert': '((region_a.test.director_ca_cert))',
            'deployment': None
        },
        'type': 'bosh-deployment',
        'name': 'bd-region_a-test'
    }, {
        'source': {
            'client_secret': '((region_a.stage.director_password))',
            'client': '((region_a.stage.director_username))',
            'target': '((region_a.stage.director_address))',
            'ca_cert': '((region_a.stage.director_ca_cert))',
            'deployment': None
        },
        'type': 'bosh-deployment',
        'name': 'bd-region_a-stage'
    }, {
        'source': {
            'client_secret': '((region_a.prod.director_password))',
            'client': '((region_a.prod.director_username))',
            'target': '((region_a.prod.director_address))',
            'ca_cert': '((region_a.prod.director_ca_cert))',
            'deployment': None
        },
        'type': 'bosh-deployment',
        'name': 'bd-region_a-prod'
    }, {
        'source': {
            'uri': 'foo_release_repo',
            'branch': 'master'
        },
        'type': 'git',
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
    }],
    'groups': [{
        'jobs': ['deploy-region_a-test', 'deploy-region_a-stage', 'deploy-region_a-prod'],
        'name': 'deploy-region_a'
    }]
}

exp_render_j2_bosh_release = {
    'resource_types': [{
        'source': {
            'repository': 'cloudfoundry/bosh-deployment-resource'
        },
        'type': 'docker-image',
        'name': 'bosh-deployment'
    }],
    'jobs': [{
        'serial': True,
        'name': 'deploy-region_a-test',
        'plan': [{
            'do': [{
                'aggregate': [{
                    'get': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                }, {
                    'trigger': True,
                    'get': 'bosh-deployment-manifest'
                }, {
                    'trigger': True,
                    'get': 'bosh-release-get-foo'
                }]
            }, {
                'aggregate': None
            }, {
                'put': 'bd-region_a-test',
                'params': {
                    'stemcells': ['stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent/*.tgz'],
                    'releases': ['bosh-release-get-foo/*.tgz'],
                    'manifest': 'bosh-deployment-manifest/manifests/test_manifest.yml'
                }
            }]
        }]
    }, {
        'serial': True,
        'name': 'deploy-region_a-stage',
        'plan': [{
            'do': [{
                'aggregate': [{
                    'get': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-test'],
                    'get': 'bosh-deployment-manifest'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-test'],
                    'get': 'bosh-release-get-foo'
                }]
            }, {
                'aggregate': None
            }, {
                'put': 'bd-region_a-stage',
                'params': {
                    'stemcells': ['stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent/*.tgz'],
                    'releases': ['bosh-release-get-foo/*.tgz'],
                    'manifest': 'bosh-deployment-manifest/manifests/test_manifest.yml'
                }
            }]
        }]
    }, {
        'serial': True,
        'name': 'deploy-region_a-prod',
        'plan': [{
            'do': [{
                'aggregate': [{
                    'get': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-stage'],
                    'get': 'bosh-deployment-manifest'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-stage'],
                    'get': 'bosh-release-get-foo'
                }]
            }, {
                'aggregate': None
            }, {
                'put': 'bd-region_a-prod',
                'params': {
                    'stemcells': ['stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent/*.tgz'],
                    'releases': ['bosh-release-get-foo/*.tgz'],
                    'manifest': 'bosh-deployment-manifest/manifests/test_manifest.yml'
                }
            }]
        }]
    }],
    'resources': [{
        'source': {
            'client_secret': '((region_a.test.director_password))',
            'client': '((region_a.test.director_username))',
            'target': '((region_a.test.director_address))',
            'ca_cert': '((region_a.test.director_ca_cert))',
            'deployment': None
        },
        'type': 'bosh-deployment',
        'name': 'bd-region_a-test'
    }, {
        'source': {
            'client_secret': '((region_a.stage.director_password))',
            'client': '((region_a.stage.director_username))',
            'target': '((region_a.stage.director_address))',
            'ca_cert': '((region_a.stage.director_ca_cert))',
            'deployment': None
        },
        'type': 'bosh-deployment',
        'name': 'bd-region_a-stage'
    }, {
        'source': {
            'client_secret': '((region_a.prod.director_password))',
            'client': '((region_a.prod.director_username))',
            'target': '((region_a.prod.director_address))',
            'ca_cert': '((region_a.prod.director_ca_cert))',
            'deployment': None
        },
        'type': 'bosh-deployment',
        'name': 'bd-region_a-prod'
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
    }],
    'groups': [{
        'jobs': ['deploy-region_a-test', 'deploy-region_a-stage', 'deploy-region_a-prod'],
        'name': 'deploy-region_a'
    }]
}

exp_render_j2_bosh_release_tarball = {
    'resource_types': [{
        'source': {
            'repository': 'cloudfoundry/bosh-deployment-resource'
        },
        'type': 'docker-image',
        'name': 'bosh-deployment'
    }],
    'jobs': [{
        'serial': True,
        'name': 'deploy-region_a-test',
        'plan': [{
            'do': [{
                'aggregate': [{
                    'get': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                }, {
                    'trigger': True,
                    'get': 'bosh-deployment-manifest'
                }, {
                    'trigger': True,
                    'get': 'bosh-release-get-foo'
                }]
            }, {
                'aggregate': [{
                    'task': 'create-release-foo',
                    'config': {
                        'platform': 'linux',
                        'inputs': [{
                            'name': 'bosh-release-get-foo'
                        }],
                        'run': {
                            'path': 'bosh',
                            'args': ['create-release', '--final', '--tarball=../bosh-release-foo/release.tgz'],
                            'dir': 'bosh-release-get-foo'
                        },
                        'outputs': [{
                            'path': '',
                            'name': 'bosh-release-foo'
                        }],
                        'image_resource': {
                            'source': {
                                'repository': 'hkumar/bosh-cli-v2'
                            },
                            'type': 'docker-image'
                        }
                    }
                }]
            }, {
                'put': 'bd-region_a-test',
                'params': {
                    'stemcells': ['stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent/*.tgz'],
                    'releases': ['bosh-release-foo/*.tgz'],
                    'manifest': 'bosh-deployment-manifest/manifests/test_manifest.yml'
                }
            }]
        }]
    }, {
        'serial': True,
        'name': 'deploy-region_a-stage',
        'plan': [{
            'do': [{
                'aggregate': [{
                    'get': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-test'],
                    'get': 'bosh-deployment-manifest'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-test'],
                    'get': 'bosh-release-get-foo'
                }]
            }, {
                'aggregate': [{
                    'task': 'create-release-foo',
                    'config': {
                        'platform': 'linux',
                        'inputs': [{
                            'name': 'bosh-release-get-foo'
                        }],
                        'run': {
                            'path': 'bosh',
                            'args': ['create-release', '--final', '--tarball=../bosh-release-foo/release.tgz'],
                            'dir': 'bosh-release-get-foo'
                        },
                        'outputs': [{
                            'path': '',
                            'name': 'bosh-release-foo'
                        }],
                        'image_resource': {
                            'source': {
                                'repository': 'hkumar/bosh-cli-v2'
                            },
                            'type': 'docker-image'
                        }
                    }
                }]
            }, {
                'put': 'bd-region_a-stage',
                'params': {
                    'stemcells': ['stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent/*.tgz'],
                    'releases': ['bosh-release-foo/*.tgz'],
                    'manifest': 'bosh-deployment-manifest/manifests/test_manifest.yml'
                }
            }]
        }]
    }, {
        'serial': True,
        'name': 'deploy-region_a-prod',
        'plan': [{
            'do': [{
                'aggregate': [{
                    'get': 'stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-stage'],
                    'get': 'bosh-deployment-manifest'
                }, {
                    'trigger': True,
                    'passed': ['deploy-region_a-stage'],
                    'get': 'bosh-release-get-foo'
                }]
            }, {
                'aggregate': [{
                    'task': 'create-release-foo',
                    'config': {
                        'platform': 'linux',
                        'inputs': [{
                            'name': 'bosh-release-get-foo'
                        }],
                        'run': {
                            'path': 'bosh',
                            'args': ['create-release', '--final', '--tarball=../bosh-release-foo/release.tgz'],
                            'dir': 'bosh-release-get-foo'
                        },
                        'outputs': [{
                            'path': '',
                            'name': 'bosh-release-foo'
                        }],
                        'image_resource': {
                            'source': {
                                'repository': 'hkumar/bosh-cli-v2'
                            },
                            'type': 'docker-image'
                        }
                    }
                }]
            }, {
                'put': 'bd-region_a-prod',
                'params': {
                    'stemcells': ['stemcell-bosh-warden-boshlite-ubuntu-trusty-go_agent/*.tgz'],
                    'releases': ['bosh-release-foo/*.tgz'],
                    'manifest': 'bosh-deployment-manifest/manifests/test_manifest.yml'
                }
            }]
        }]
    }],
    'resources': [{
        'source': {
            'client_secret': '((region_a.test.director_password))',
            'client': '((region_a.test.director_username))',
            'target': '((region_a.test.director_address))',
            'ca_cert': '((region_a.test.director_ca_cert))',
            'deployment': None
        },
        'type': 'bosh-deployment',
        'name': 'bd-region_a-test'
    }, {
        'source': {
            'client_secret': '((region_a.stage.director_password))',
            'client': '((region_a.stage.director_username))',
            'target': '((region_a.stage.director_address))',
            'ca_cert': '((region_a.stage.director_ca_cert))',
            'deployment': None
        },
        'type': 'bosh-deployment',
        'name': 'bd-region_a-stage'
    }, {
        'source': {
            'client_secret': '((region_a.prod.director_password))',
            'client': '((region_a.prod.director_username))',
            'target': '((region_a.prod.director_address))',
            'ca_cert': '((region_a.prod.director_ca_cert))',
            'deployment': None
        },
        'type': 'bosh-deployment',
        'name': 'bd-region_a-prod'
    }, {
        'source': {
            'uri': 'foo_release_repo',
            'branch': 'master'
        },
        'type': 'git',
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
    }],
    'groups': [{
        'jobs': ['deploy-region_a-test', 'deploy-region_a-stage', 'deploy-region_a-prod'],
        'name': 'deploy-region_a'
    }]
}

exp_get_config_deployment = {
    'concourse_target': 'cc1',
    'deployments': {
        'redis': {
            'tests': ['sanity-tests'],
            'releases': {
                'redis': {
                    'repo': 'https://github.com/hkumarmk/redis-boshrelease.git',
                    'branch': 'master'
                }
            },
            'deploy_job_name': 'redis-deploy',
            'vars': {
                'default': {
                    'foo': 'bar',
                    'bar': 'baz'
                },
                'bosh_stage_reg_a': {
                    'foo': 'val',
                    'var2': 'val2'
                },
                'bosh_test_reg_a': {
                    'foo': 'baz',
                    'var1': 'value'
                }
            },
            'manifest': {
                'repo': 'https://github.com/hkumarmk/redis-boshrelease.git',
                'path': 'manifests/redis.yml'
            },
            'stemcells': ['bosh-warden-boshlite-ubuntu-trusty-go_agent']
        }
    }
}

exp_get_config_concourse = {
    'concourse': {
        'cc1': {
            'username': 'admin',
            'name': 'localhost',
            'ca_cert': '-----BEGIN CERTIFICATE-----\n'
                       'MIIDtzCCAp+gAwIBAgIJAMZ/qRdRamluMA0GCSqGSIb3DQEBBQUAMEUxCzAJBgNV\n'
                       'BAYTAkFVMRMwEQYDVQQIEwpTb21lLVN0YXRlMSEwHwYDVQQKExhJbnRlcm5ldCBX\n'
                       'aWRnaXRzIFB0eSBMdGQwIBcNMTYwODI2MjIzMzE5WhgPMjI5MDA2MTAyMjMzMTla\n'
                       'MEUxCzAJBgNVBAYTAkFVMRMwEQYDVQQIEwpTb21lLVN0YXRlMSEwHwYDVQQKExhJ\n'
                       'bnRlcm5ldCBXaWRnaXRzIFB0eSBMdGQwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAw\n'
                       'ggEKAoIBAQDN/bv70wDn6APMqiJZV7ESZhUyGu8OzuaeEfb+64SNvQIIME0s9+i7\n'
                       'D9gKAZjtoC2Tr9bJBqsKdVhREd/X6ePTaopxL8shC9GxXmTqJ1+vKT6UxN4kHr3U\n'
                       '+Y+LK2SGYUAvE44nv7sBbiLxDl580P00ouYTf6RJgW6gOuKpIGcvsTGA4+u0UTc+\n'
                       'y4pj6sT0+e3xj//Y4wbLdeJ6cfcNTU63jiHpKc9Rgo4Tcy97WeEryXWz93rtRh8d\n'
                       'pvQKHVDU/26EkNsPSsn9AHNgaa+iOA2glZ2EzZ8xoaMPrHgQhcxoi8maFzfM2dX2\n'
                       'XB1BOswa/46yqfzc4xAwaW0MLZLg3NffAgMBAAGjgacwgaQwHQYDVR0OBBYEFNRJ\n'
                       'PYFebixALIR2Ee+yFoSqurxqMHUGA1UdIwRuMGyAFNRJPYFebixALIR2Ee+yFoSq\n'
                       'urxqoUmkRzBFMQswCQYDVQQGEwJBVTETMBEGA1UECBMKU29tZS1TdGF0ZTEhMB8G\n'
                       'A1UEChMYSW50ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkggkAxn+pF1FqaW4wDAYDVR0T\n'
                       'BAUwAwEB/zANBgkqhkiG9w0BAQUFAAOCAQEAoPTwU2rm0ca5b8xMni3vpjYmB9NW\n'
                       'oSpGcWENbvu/p7NpiPAe143c5EPCuEHue/AbHWWxBzNAZvhVZBeFirYNB3HYnCla\n'
                       'jP4WI3o2Q0MpGy3kMYigEYG76WeZAM5ovl0qDP6fKuikZofeiygb8lPs7Hv4/88x\n'
                       'pSsZYBm7UPTS3Pl044oZfRJdqTpyHVPDqwiYD5KQcI0yHUE9v5KC0CnqOrU/83PE\n'
                       'b0lpHA8bE9gQTQjmIa8MIpaP3UNTxvmKfEQnk5UAZ5xY2at5mmyj3t8woGdzoL98\n'
                       'yDd2GtrGsguQXM2op+4LqEdHef57g7vwolZejJqN776Xu/lZtCTp01+HTA==\n'
                       '-----END CERTIFICATE-----\n',
            'team': 'main',
            'url': 'http://localhost:8080',
            'insecure': False,
            'password': 'admin'
        }
    }
}

exp_get_config_bosh = {
    'bosh': {
        'bosh_stage_reg_a': {
            'director_address': '192.168.50.4',
            'director_username': 'admin',
            'director_ca_cert': '-----BEGIN CERTIFICATE-----\n'
                                'MIIDtzCCAp+gAwIBAgIJAMZ/qRdRamluMA0GCSqGSIb3DQEBBQUAMEUxCzAJBgNV\n'
                                'BAYTAkFVMRMwEQYDVQQIEwpTb21lLVN0YXRlMSEwHwYDVQQKExhJbnRlcm5ldCBX\n'
                                'aWRnaXRzIFB0eSBMdGQwIBcNMTYwODI2MjIzMzE5WhgPMjI5MDA2MTAyMjMzMTla\n'
                                'MEUxCzAJBgNVBAYTAkFVMRMwEQYDVQQIEwpTb21lLVN0YXRlMSEwHwYDVQQKExhJ\n'
                                'bnRlcm5ldCBXaWRnaXRzIFB0eSBMdGQwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAw\n'
                                'ggEKAoIBAQDN/bv70wDn6APMqiJZV7ESZhUyGu8OzuaeEfb+64SNvQIIME0s9+i7\n'
                                'D9gKAZjtoC2Tr9bJBqsKdVhREd/X6ePTaopxL8shC9GxXmTqJ1+vKT6UxN4kHr3U\n'
                                '+Y+LK2SGYUAvE44nv7sBbiLxDl580P00ouYTf6RJgW6gOuKpIGcvsTGA4+u0UTc+\n'
                                'y4pj6sT0+e3xj//Y4wbLdeJ6cfcNTU63jiHpKc9Rgo4Tcy97WeEryXWz93rtRh8d\n'
                                'pvQKHVDU/26EkNsPSsn9AHNgaa+iOA2glZ2EzZ8xoaMPrHgQhcxoi8maFzfM2dX2\n'
                                'XB1BOswa/46yqfzc4xAwaW0MLZLg3NffAgMBAAGjgacwgaQwHQYDVR0OBBYEFNRJ\n'
                                'PYFebixALIR2Ee+yFoSqurxqMHUGA1UdIwRuMGyAFNRJPYFebixALIR2Ee+yFoSq\n'
                                'urxqoUmkRzBFMQswCQYDVQQGEwJBVTETMBEGA1UECBMKU29tZS1TdGF0ZTEhMB8G\n'
                                'A1UEChMYSW50ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkggkAxn+pF1FqaW4wDAYDVR0T\n'
                                'BAUwAwEB/zANBgkqhkiG9w0BAQUFAAOCAQEAoPTwU2rm0ca5b8xMni3vpjYmB9NW\n'
                                'oSpGcWENbvu/p7NpiPAe143c5EPCuEHue/AbHWWxBzNAZvhVZBeFirYNB3HYnCla\n'
                                'jP4WI3o2Q0MpGy3kMYigEYG76WeZAM5ovl0qDP6fKuikZofeiygb8lPs7Hv4/88x\n'
                                'pSsZYBm7UPTS3Pl044oZfRJdqTpyHVPDqwiYD5KQcI0yHUE9v5KC0CnqOrU/83PE\n'
                                'b0lpHA8bE9gQTQjmIa8MIpaP3UNTxvmKfEQnk5UAZ5xY2at5mmyj3t8woGdzoL98\n'
                                'yDd2GtrGsguQXM2op+4LqEdHef57g7vwolZejJqN776Xu/lZtCTp01+HTA==\n'
                                '-----END CERTIFICATE-----\n',
            'director_password': 'admin'
        }
    }
}

exp_targets = ""