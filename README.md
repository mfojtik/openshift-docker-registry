# docker-registry quickstart for OpenShift #

This quickstart will allow you to run your own [Docker](http://docker.io)
repository for Docker images (see [docker-registry](https://github.com/dotcloud/docker-registry).

## ! Bugs !

* This quickstart does not work at the present because `xz-devel` dependency is
  not available. This should be fixed shortly.

## Installation

Docker registry is a Python application, so to start we need to create a python
app:

```
rhc app create registry python-2.7
```

Now, we need to setup some environment variables that Docker registry needs in
order to upload your images. This quickstart is configured to store your images
in [Amazon S3](http://aws.amazon.com/s3/), so first you need to create an
Amazon account and create a bucket in S3 where your images will be stored.
You will also need your Amazon API key and Amazon Secret key. You can obtain
those under the 'Security Credentials' page in Amazon.

Then just run these commands:

```
rhc env set AWS_BUCKET=bucketname -a registry
rhc env set AWS_KEY=<amazon api key> -a registry
rhc env set AWS_SECRET=<amazon secret key> -a registry
rhc env set SETTINGS_FLAVOR=prod
```

Now is the time to install the quickstart:

```
cd registry/
git remote add upstream -m master git://github.com/mfojtik/openshift-docker-registry.git
git pull -s recursive -X theirs upstream master
git push
```

Installing dependencies will take some time, but when it finished, you should
have the Docker registry running at `http://registry-NAMESPACE.rhcloud.com`.

## License

Same as the [docker-registry](https://github.com/dotcloud/docker-registry)
license.
