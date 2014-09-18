import subprocess
import os

try:
    gunicorn_cmd="gunicorn -k gevent --max-requests 100 --graceful-timeout 3600 -t 3600 -b %s:8080 -w 8 docker_registry.wsgi:application" % os.environ['OPENSHIFT_PYTHON_IP']
    subprocess.check_output(gunicorn_cmd, stderr=subprocess.STDOUT, shell=True)
except subprocess.CalledProcessError, e:
    print "[ERROR] %s" % e.output

