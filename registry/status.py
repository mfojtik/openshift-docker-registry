__all__ = ['registry_status']

import gevent.monkey
gevent.monkey.patch_all()

import cache
import config
import gevent
import socket
import storage
import sys
import toolkit

from .app import app

_config = config.load()


def redis_status():
    message = ''
    if not cache.redis_conn:
        cache.init()
    if not cache.redis_conn:
        return {'redis': 'unconfigured'}
    key = toolkit.gen_random_string()
    value = toolkit.gen_random_string()
    try:
        cache.redis_conn.setex(key, 5, value)
        if value != cache.redis_conn.get(key):
            message = 'Set value is different from what was received'
    except Exception:
        message = str(sys.exc_info()[1])
    return {'redis': message}


def storage_status():
    message = ''
    try:
        _storage = storage.load(_config.storage)
        key = toolkit.gen_random_string()
        value = toolkit.gen_random_string()
        _storage.put_content(key, value)
        stored_value = _storage.get_content(key)
        _storage.remove(key)
        if value != stored_value:
            message = 'Set value is different from what was received'
    except Exception as e:
        message = str(e)
    return {'storage': message}


@app.route('/_status')
@app.route('/v1/_status')
def registry_status():
    retval = {'services': ['redis', 'storage'], 'failures': {}}
    retval['host'] = socket.gethostname()
    code = 200
    jobs = [gevent.spawn(job) for job in [redis_status, storage_status]]
    gevent.joinall(jobs, timeout=10)
    for job, service in zip(jobs, retval['services']):
        try:
            value = job.get()
            if value[service] != '':
                retval['failures'].update({service: value[service]})
                code = 503
        except Exception as e:
            retval['failures'].update({service: str(e)})
            code = 503
    return toolkit.response(retval, code=code)
