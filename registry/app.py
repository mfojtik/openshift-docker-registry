import logging
import os

try:
    import bugsnag
    import bugsnag.flask
except ImportError as e:
    _bugsnag_import_error = e
    bugsnag = None
import flask

import config
import toolkit


VERSION = '0.6.6'
app = flask.Flask('docker-registry')
cfg = config.load()
loglevel = getattr(logging, cfg.get('loglevel', 'INFO').upper())
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    level=loglevel)


@app.route('/_ping')
@app.route('/v1/_ping')
def ping():
    return toolkit.response(headers={
        'X-Docker-Registry-Standalone': cfg.standalone is not False
    })


@app.route('/')
def root():
    return toolkit.response('docker-registry server ({0})'.format(cfg.flavor))


@app.after_request
def after_request(response):
    response.headers['X-Docker-Registry-Version'] = VERSION
    response.headers['X-Docker-Registry-Config'] = cfg.flavor
    return response


def init():
    # Configure the secret key
    if not cfg.secret_key:
        raise RuntimeError('Config error: `secret_key\' is not set')
    flask.Flask.secret_key = cfg.secret_key
    # Configure the email exceptions
    info = cfg.email_exceptions
    if info:
        mailhost = info['smtp_host']
        mailport = info.get('smtp_port')
        if mailport:
            mailhost = (mailhost, mailport)
        smtp_secure = info.get('smtp_secure', None)
        secure_args = _adapt_smtp_secure(smtp_secure)
        mail_handler = logging.handlers.SMTPHandler(
            mailhost=mailhost,
            fromaddr=info['from_addr'],
            toaddrs=[info['to_addr']],
            subject='Docker registry exception',
            credentials=(info['smtp_login'],
                         info['smtp_password']),
            secure=secure_args)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
    # Configure bugsnag
    info = cfg.bugsnag
    if info:
        if not bugsnag:
            raise _bugsnag_import_error
        root_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                 '..'))
        bugsnag.configure(api_key=info,
                          project_root=root_path,
                          release_stage=cfg.flavor,
                          notify_release_stages=[cfg.flavor],
                          app_version=VERSION
                          )
        bugsnag.flask.handle_exceptions(app)


def _adapt_smtp_secure(value):
    """Adapt the value to arguments of ``SMTP.starttls()``

    .. seealso:: <http://docs.python.org/2/library/smtplib.html\
#smtplib.SMTP.starttls>

    """
    if isinstance(value, basestring):
        # a string - wrap it in the tuple
        return (value,)
    if isinstance(value, dict):
        assert set(value.keys()) <= set(['keyfile', 'certfile'])
        return (value['keyfile'], value.get('certfile', None))
    if value:
        return ()


init()
