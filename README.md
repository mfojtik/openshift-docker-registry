# docker-registry quickstart for OpenShift #

This quickstart will allow you to run your own [Docker](http://docker.io)
repository for Docker images (see [docker-registry](https://github.com/dotcloud/docker-registry)).

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

## How to use it

The process is described in this awesome [blog
post](http://blog.docker.io/2013/07/how-to-use-your-own-registry/). To push
your images into Docker registry running on OpenShift you need to do following:

```
# 4b3c7ee293b0 is the Docker id of the image you want to push

$ docker tag 4b3c7ee293b0 registry-mfojtik.dev.rhcloud.com:8000/redis
$ docker push registry-mfojtik.dev.rhcloud.com:8000/redis
```

The output should be following:

```
The push refers to a repository [registry-mfojtik.dev.rhcloud.com:8000/redis] (len: 1)
Sending image list
Pushing repository registry-mfojtik.dev.rhcloud.com:8000/redis (1 tags)
511136ea3c5a: Image successfully pushed
8abc22fbb042: Image successfully pushed
58394af37342: Image successfully pushed
Pushing tag for rev [4b3c7ee293b0] on {http://registry-mfojtik.dev.rhcloud.com:8000/v1/repositories/redis/tags/latest}
```

## Notes

For now, this quickstart is using [gunicorn](http://gunicorn.org) web server
instead of default Apache/WSGI. The reason is that registry use `gevent`
library that require more complex threading that cannot be handled right now
using the WSGI approach. I found not problems by using this approach, but if
you found some bug, please fill an issue.

## License

Same as the [docker-registry](https://github.com/dotcloud/docker-registry)
license.
