# Boshifier: To help continously deploy bosh releases

Here is the basic workflow at this moment
* User to keep bosh releases and deployment manifests in git repos
* User to run Boshifier any of the supporting modes (see below) providing the following details
  * Credentials to target bosh director
  * Credentials to target concourse
  * Deployment configuration
    * Release[s] git repo urls and branch
    * Bosh deployment manifest repo, branch and path
    * Stemcell[s]

Once boshifier get the request, It create a pipeline to said concourse target which does below stuffs

* Get bosh releases and bosh deployment manifest from provided git repos
* Create bosh release tar.gz out of release source get from the repos
* Get stemcells from bosh.io
* Deploy releases to bosh target provided

# Features
* Deploy release code from any git repo
    * Pull release code from git repo, Create release tarball, and deploy it to provided director
* Deploy bosh release
    * Download bosh release from bosh.io and deploy to provided director
* Deploy multi-release, multi-stemcell manifests


Note: Please refer [Configuration Reference](examples/deployment.yml)

# How to Use

## Install the requirements
```
$ cd boshifier
$ pip install requirements.txt
```

## Execute Commandline mode
```
$ python main.py -b examples/bosh.yml -c examples/concourse.yml -d examples/deployment.yml
logging in to team 'main'

target saved
configuration updated
unpaused 'redis'
Deployment done
$ echo $?
0

$ python main.py -h
usage: main.py [-h] -b BOSH_CREDS_FILE -c CONCOURSE_CREDS_FILE -d
               DEPLOYMENT_CONFIG_FILE

Manage bosh deployments

optional arguments:
  -h, --help            show this help message and exit
  -b BOSH_CREDS_FILE, --bosh-creds-file BOSH_CREDS_FILE
                        Yaml file that contain bosh credentials
  -c CONCOURSE_CREDS_FILE, --concourse-creds-file CONCOURSE_CREDS_FILE
                        Yaml file that contain concourse credentials
  -d DEPLOYMENT_CONFIG_FILE, --deployment-config-file DEPLOYMENT_CONFIG_FILE
                        Yaml file that contain deployment configurations

```

## Webapp mode
It has a tiny flask code to make it a web service

```
$ cd boshifier
$ export FLASK_APP=main.py
$ flask run 
 * Serving Flask app "main"
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
logging in to team 'main'

target saved
configuration updated
unpaused 'redis1'
127.0.0.1 - - [14/Jul/2017 14:30:29] "POST / HTTP/1.1" 200 -

## Use curl to use it
$ curl -v -X POST http://127.0.0.1:5000/ -F bosh=@/tmp/bosh.yml -F concourse=@/tmp/cc.yml -F deployment=@/tmp/dep.yml
* Hostname was NOT found in DNS cache
*   Trying 127.0.0.1...
* Connected to 127.0.0.1 (127.0.0.1) port 5000 (#0)
> POST / HTTP/1.1
> User-Agent: curl/7.35.0
> Host: 127.0.0.1:5000
> Accept: */*
> Content-Length: 2486
> Expect: 100-continue
> Content-Type: multipart/form-data; boundary=------------------------32b8290d72d8cddd
> 
< HTTP/1.1 100 Continue
* HTTP 1.0, assume close after body
< HTTP/1.0 200 OK
< Content-Type: text/html; charset=utf-8
< Content-Length: 15
* Server Werkzeug/0.12.2 Python/2.7.6 is not blacklisted
< Server: Werkzeug/0.12.2 Python/2.7.6
< Date: Fri, 14 Jul 2017 14:30:29 GMT
< 
* Closing connection 0
Deployment done

```


# Sample pipeline screenshot
![Sample Pipeline](images/pipeline.png)

# TODO
* Stemcells map to resolve cpi specific stemcell name from os and get cpi details from bosh director
* To support more complex pipeline for bosh releases like dev build -> test -> push to prod/master branch -> test -> deploy
* Blobstore configurations to populate config/private.yml or use local blobstore in config/final.yml if not there 
* Define bosh and concourse credentials within boshifier may be as a configuration
* Users should just provide deployment config  which should have list of target_regions on which it should be released,
 with default to all regions
* There should be paas_map (map on target_name:concourse:bosh) that map the entire global paas system map which should
have the connectivity details, importance, any sequence required (e.g test, stage, prod) etc based out of which the
deployment would happen.
* Each target should have pipeline setup like deploy -> test -> declare pass/fail and notify
* Way to set cloud-config 
    * Define hardware profiles with set of common names, so that those generic names can be used within bosh deployment
    manifests to make them cloud agnostic
* Way to set runtime-config to have something available to all nodes or nodes in specific profiles
* Notify in case of failure
    * May be config to whom and/or what to be notified



# Sample configs

* [Bosh credentials](examples/bosh.yml)
* [concourse credentials](examples/concourse.yml)
* [Deployment configuration](examples/deployment.yml)
