from subprocess import *
import os
import signal
import sys

global unicorn_pid

# You can tweak the gunicorn configuration here
#
gunicorn_cmd = [
    "gunicorn",
    "--worker-class gevent",
    "--max-requests 100",
    "--graceful-timeout 3600",
    "--timeout 3600",
    "--workers 8",
    "-b %s:%s" % os.environ['OPENSHIFT_PYTHON_IP'], os.environ['OPENSHIFT_PYTHON_PORT'],
    "wsgi:application"
]

def exit_handler(signal, frame):
    print "Stopping Gunicorn workers..."
    os.kill(unicorn_pid, signal.SIGTERM)
    sys.exit(0)

try:
    signal.signal(signal.SIGTERM, exit_handler)
    app = Popen(" ".join(gunicorn_cmd), stdout=PIPE, stderr=PIPE, shell=True)
    unicorn_pid = app.pid
    print "Starting Gunicorn(%i) workers" % unicorn_pid
    (output, error) = app.communicate()
    if error:
        print '-------------[ ERRORS ]---------------'
        print error
except CalledProcessError, e:
    print e.output

