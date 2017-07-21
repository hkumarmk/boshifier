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

# TODO
* multi-release, multi-stemcell deployments
* Way to add bosh directors
* Way to add concourse targets
    May be user to provide bosh director and concourse creds during deployments
* Way to set cloud-config and runtime-config
* Stemcells map to resolve cpi specific stemcell name from os and get cpi details from bosh director
* To support more complex pipeline for bosh releases like dev build -> test -> push to prod/master branch -> test -> deploy
* Support releases from bosh.io (without creating it)

# Sample configs

## Sample bosh_creds_file
```
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
```

## Sample concourse_creds file

```
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
```

## Sample deployment-config-file

```
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
```
