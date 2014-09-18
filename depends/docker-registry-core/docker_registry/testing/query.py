# -*- coding: utf-8 -*-
# Copyright (c) 2014 Docker.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from nose import tools

from ..core import driver
from ..core import exceptions


class Query(object):

    def __init__(self, scheme=None):
        self.scheme = scheme

    def testDriverIsAvailable(self):
        drvs = driver.available()
        assert self.scheme in drvs

    def testFetchingDriver(self):
        resultdriver = driver.fetch(self.scheme)
        # XXX hacking is sick
        storage = __import__('docker_registry.drivers.%s' % self.scheme,
                             globals(), locals(), ['Storage'], 0)  # noqa

        assert resultdriver == storage.Storage
        assert issubclass(resultdriver, driver.Base)
        assert resultdriver.scheme == self.scheme

    @tools.raises(exceptions.NotImplementedError)
    def testFetchingNonExistentDriver(self):
        driver.fetch("nonexistentstupidlynameddriver")
