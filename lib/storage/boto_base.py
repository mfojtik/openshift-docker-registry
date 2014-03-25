
import gevent.monkey
gevent.monkey.patch_all()

import copy
import logging
import math
import os
import tempfile

import cache_lru

from . import Storage

logger = logging.getLogger(__name__)


class ParallelKey(object):

    """This class implements parallel transfer on a key to improve speed."""

    CONCURRENCY = 5

    def __init__(self, key):
        logger.info('ParallelKey: {0}; size={1}'.format(key, key.size))
        self._boto_key = key
        self._cursor = 0
        self._max_completed_byte = 0
        self._max_completed_index = 0
        self._tmpfile = tempfile.NamedTemporaryFile(mode='rb')
        self._completed = [0] * self.CONCURRENCY
        self._spawn_jobs()

    def __del__(self):
        self._tmpfile.close()

    def _generate_bytes_ranges(self, num_parts):
        size = self._boto_key.size
        chunk_size = int(math.ceil(1.0 * size / num_parts))
        for i in range(num_parts):
            yield (i, chunk_size * i, min(chunk_size * (i + 1) - 1, size - 1))

    def _fetch_part(self, fname, index, min_cur, max_cur):
        boto_key = copy.copy(self._boto_key)
        with open(fname, 'wb') as f:
            f.seek(min_cur)
            brange = 'bytes={0}-{1}'.format(min_cur, max_cur)
            boto_key.get_contents_to_file(f, headers={'Range': brange})
            boto_key.close()
        self._completed[index] = (index, max_cur)
        self._refresh_max_completed_byte()

    def _spawn_jobs(self):
        bytes_ranges = self._generate_bytes_ranges(self.CONCURRENCY)
        for i, min_cur, max_cur in bytes_ranges:
            gevent.spawn(self._fetch_part, self._tmpfile.name,
                         i, min_cur, max_cur)

    def _refresh_max_completed_byte(self):
        for v in self._completed[self._max_completed_index:]:
            if v == 0:
                return
            self._max_completed_index = v[0]
            self._max_completed_byte = v[1]
            if self._max_completed_index >= len(self._completed) - 1:
                percent = round(
                    (100.0 * self._cursor) / self._boto_key.size, 1)
                logger.info('ParallelKey: {0}; buffering complete at {1}% of '
                            'the total transfer; now serving straight from '
                            'the tempfile'.format(self._boto_key, percent))

    def read(self, size):
        if self._cursor >= self._boto_key.size:
            # Read completed
            return ''
        sz = size
        if self._max_completed_index < len(self._completed) - 1:
            # Not all data arrived yet
            if self._cursor + size > self._max_completed_byte:
                while self._cursor >= self._max_completed_byte:
                    # We're waiting for more data to arrive
                    gevent.sleep(0.2)
            if self._cursor + sz > self._max_completed_byte:
                sz = self._max_completed_byte - self._cursor
        # Use a low-level read to avoid any buffering (makes sure we don't
        # read more than `sz' bytes).
        buf = os.read(self._tmpfile.file.fileno(), sz)
        self._cursor += len(buf)
        if not buf:
            message = ('ParallelKey: {0}; got en empty read on the buffer! '
                       'cursor={1}, size={2}; Transfer interrupted.'.format(
                           self._boto_key, self._cursor, self._boto_key.size))
            logging.error(message)
            raise RuntimeError(message)
        return buf


class BotoStorage(Storage):

    supports_bytes_range = True

    def __init__(self, config):
        self._config = config
        self._root_path = self._config.storage_path
        self._boto_conn = self.makeConnection()
        self._boto_bucket = self._boto_conn.get_bucket(
            self._config.boto_bucket)

    def _debug_key(self, key):
        """Used for debugging only."""
        orig_meth = key.bucket.connection.make_request

        def new_meth(*args, **kwargs):
            print '#' * 16
            print args
            print kwargs
            print '#' * 16
            return orig_meth(*args, **kwargs)
        key.bucket.connection.make_request = new_meth

    def _init_path(self, path=None):
        path = os.path.join(self._root_path, path) if path else self._root_path
        if path and path[0] == '/':
            return path[1:]
        return path

    def stream_read(self, path, bytes_range=None):
        path = self._init_path(path)
        headers = None
        if bytes_range:
            headers = {'Range': 'bytes={0}-{1}'.format(*bytes_range)}
        key = self._boto_bucket.lookup(path, headers=headers)
        if not key:
            raise IOError('No such key: \'{0}\''.format(path))
        if not bytes_range and key.size > 1024 * 1024:
            # Use the parallel key only if the key size is > 1MB
            # And if bytes_range is not enabled (since ParallelKey is already
            # using bytes range)
            key = ParallelKey(key)
        while True:
            buf = key.read(self.buffer_size)
            if not buf:
                break
            yield buf

    def list_directory(self, path=None):
        path = self._init_path(path)
        if not path.endswith('/'):
            path += '/'
        ln = 0
        if self._root_path != '/':
            ln = len(self._root_path)
        exists = False
        for key in self._boto_bucket.list(prefix=path, delimiter='/'):
            exists = True
            name = key.name
            if name.endswith('/'):
                yield name[ln:-1]
            else:
                yield name[ln:]
        if exists is False:
            # In order to be compliant with the LocalStorage API. Even though
            # GS does not have a concept of folders.
            raise OSError('No such directory: \'{0}\''.format(path))

    def get_size(self, path):
        path = self._init_path(path)
        # Lookup does a HEAD HTTP Request on the object
        key = self._boto_bucket.lookup(path)
        if not key:
            raise OSError('No such key: \'{0}\''.format(path))
        return key.size

    @cache_lru.get
    def get_content(self, path):
        path = self._init_path(path)
        key = self.makeKey(path)
        if not key.exists():
            raise IOError('No such key: \'{0}\''.format(path))
        return key.get_contents_as_string()

    def exists(self, path):
        path = self._init_path(path)
        key = self.makeKey(path)
        return key.exists()

    @cache_lru.remove
    def remove(self, path):
        path = self._init_path(path)
        key = self.makeKey(path)
        if key.exists():
            # It's a file
            key.delete()
            return
        # We assume it's a directory
        if not path.endswith('/'):
            path += '/'
        for key in self._boto_bucket.list(prefix=path, delimiter='/'):
            key.delete()
