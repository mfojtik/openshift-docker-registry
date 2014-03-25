import subprocess
import os

gunicorn_cmd="gunicorn -k gevent --max-requests 100 --graceful-timeout 3600 -t 3600 -b %s:8000 -w 8 wsgi:application", os.environ['OPENSHIFT_PYTHON_IP']

subprocess.check_output(gunicorn_cmd, stderr=subprocess.STDOUT, shell=True)
