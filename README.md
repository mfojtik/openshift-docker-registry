# docker-registry quickstart for OpenShift #

This quickstart will allow you to run your own [Docker](http://docker.io)
repository for Docker images (see [docker-registry](https://github.com/dotcloud/docker-registry)).

## ! Bugs !

* This quickstart does not work at the present because `xz-devel` dependency is
  not available. This should be fixed shortly.

## Installation

First you need to have the [OpenShift](https://openshift.redhat.com/app/account/new)
account.
Since docker-registry is a Python application, for the start we need to create
the python app:

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
$ docker pull busybox
$ docker tag busybox registry-mfojtik.rhcloud.com:8000/busybox
$ docker push registry-mfojtik.rhcloud.com:8000/busybox
```

The output should be following:

```
The push refers to a repository [registry-mfojtik.rhcloud.com:8000/busybox] (len: 1)
Sending image list
Pushing repository registry-mfojtik.rhcloud.com:8000/busybox (1 tags)
511136ea3c5a: Image successfully pushed
bf747efa0e2f: Image successfully pushed
48e5f45168b9: Image successfully pushed
769b9341d937: Image successfully pushed
Pushing tag for rev [769b9341d937] on {http://registry-mfojtik.rhcloud.com:8000/v1/repositories/busybox/tags/latest}
```

Now to pull your image from repository you can do:

```
$ docker pull registry-mfojtik.dev.rhcloud.com:8000/busybox
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
