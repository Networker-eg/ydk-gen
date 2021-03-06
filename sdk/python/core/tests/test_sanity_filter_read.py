#  ----------------------------------------------------------------
# Copyright 2016 Cisco Systems
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------

"""test_sanity_fitler_read.py
read API according to discussion
"""
from __future__ import absolute_import

import sys
import unittest

from ydk.filters import YFilter
from ydk.services import CRUDService
from ydk.models.ydktest import ydktest_filterread as ysanity
from ydk.models.ydktest import oc_pattern
from ydk.providers import NetconfServiceProvider

from test_utils import ParametrizedTestCase
from test_utils import get_device_info


class SanityYang(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ncc = NetconfServiceProvider(
            cls.hostname,
            cls.username,
            cls.password,
            cls.port,
            cls.protocol,
            cls.on_demand,
            cls.common_cache,
            cls.timeout)
        cls.crud = CRUDService()
        # config device with entity a
        a = cls.getInitEntity()
        cls.crud.delete(cls.ncc, ysanity.A())
        cls.crud.create(cls.ncc, a)

    @classmethod
    def getInitEntity(self):
        """ Set and return entity with following XML:

        <a>
          <a1>some value</a1>
          <a2>value of a2</a2>
          <a3>value of a3</a3>
          <b>
            <b1>some value</b1>
            <b2>value of b2</b2>
            <b3>value of b3</b3>
            <c/>
            <f>
              <f1>f</f1>
            </f>
            <d>
              <d1>some value d1</d1>
              <d2>value of d2</d2>
              <d3>value of d3</d3>
              <e>
                <e1>some value e1</e1>
                <e2>value of e2</e2>
              </e>
            </d>
          </b>
          <lst>
            <number>1</number>
            <value>one</value>
          </lst>
          <lst>
            <number>2</number>
            <value>two</value>
          </lst>
          <lst>
            <number>3</number>
            <value>three</value>
          </lst>
        </a>
        """
        a = ysanity.A()
        a.a1, a.a2, a.a3 = "some value", "value of a2", "value of a3"
        a.b.b1, a.b.b2, a.b.b3 = "some value", "value of b2", "value of b3"
        # config presence container
        a.b.f = a.b.F()
        a.b.f.f1 = 'f'
        a.b.c = a.b.C()
        a.b.d.d1 = "some value d1"
        a.b.d.d2 = "value of d2"
        a.b.d.d3 = "value of d3"
        a.b.d.e.e1, a.b.d.e.e2 = "some value e1", "value of e2"
        l1, l2, l3 = a.Lst(), a.Lst(), a.Lst()
        l1.number, l1.value = 1, "one"
        l2.number, l2.value = 2, "two"
        l3.number, l3.value = 3, "three"
        a.lst.extend([l1, l2, l3])
        return a


    def test_CASE1(self):
        """Use crud read with top level entity returns all data."""
        a = ysanity.A()
        a_read = self.crud.read(self.ncc, a)
        preconfig_a = self.getInitEntity()

        a_read == preconfig_a

    def test_CASE2(self):
        """ According to https://tools.ietf.org/html/rfc6241#section-6.2.5,
        `a.a1` is a content match node. Uses crud read on `a` returns all data.
        """
        a = ysanity.A()
        a.a1 = "some value"
        a_read = self.crud.read(self.ncc, a)
        preconfig_a = self.getInitEntity()

        a_read == preconfig_a

    def test_CASE3(self):
        """Assign a READ object to `a.a1` should only return data on this leaf."""
        a = ysanity.A()
        a.a1 = YFilter.read
        a_read = self.crud.read(self.ncc, a)
        preconfig_a = ysanity.A()
        preconfig_a.a1 = "some value"

        a_read == preconfig_a

    def test_CASE4(self):
        """Now `a.b.b1` serves as a content match node."""
        a = ysanity.A()
        a.b.b1 = "some value"
        a_read = self.crud.read(self.ncc, a)
        preconfig_a = ysanity.A()

        preconfig_a.b.b1 = "some value"
        preconfig_a.b.b2 = "value of b2"
        preconfig_a.b.b3 = "value of b3"
        preconfig_a.b.f = preconfig_a.b.F()
        preconfig_a.b.f.f1 = 'f'
        preconfig_a.b.c = preconfig_a.b.C()
        preconfig_a.b.d.d1 = "some value d1"
        preconfig_a.b.d.d2 = "value of d2"
        preconfig_a.b.d.d3 = "value of d3"
        preconfig_a.b.d.e.e1 = "some value e1"
        preconfig_a.b.d.e.e2 = "value of e2"

        a_read == preconfig_a

    def test_CASE5(self):
        """Now `a.b.d.e` serves as a content match node."""
        a = ysanity.A()
        e = a.b.d.e
        e.e1 = "some value e1"
        a_read = self.crud.read(self.ncc, a)
        preconfig_a = ysanity.A()
        preconfig_a.b.d.e.e1 = "some value e1"
        preconfig_a.b.d.e.e2 = "value of e2"

        a_read == preconfig_a

    def test_CASE6(self):
        """Assign `a.b.c` serves as an empty presence container."""
        a = ysanity.A()
        a.b.c = a.b.C()
        a_read = self.crud.read(self.ncc, a)
        preconfig_a = ysanity.A()
        preconfig_a.b.c = preconfig_a.b.C()

        a_read == preconfig_a

    def test_CASE7(self):
        """`item1.number` and `item2.number` serves as content match nodes."""
        a = ysanity.A()
        item1, item2 = a.Lst(), a.Lst()
        item1.number, item2.number = 1, 2
        a.lst.extend([item1, item2])
        a_read = self.crud.read(self.ncc, a)
        preconfig_a = ysanity.A()
        item1.value, item2.value = "one", "two"
        preconfig_a.lst.extend([item1, item2])

        a_read == preconfig_a

    def test_CASE8(self):
        """Assign presence class F to `a.b.f`."""
        a = ysanity.A()
        a.b.f = a.b.F()
        a.b.f.f1 = 'f'
        a_read = self.crud.read(self.ncc, a)
        preconfig_a = a

        a_read == preconfig_a

    # @unittest.skip("Libyang ERROR: Schema node not found. Path: 'B'")
    def test_read_oc_pattern(self):
        obj_A = oc_pattern.OcA()
        obj_A.a = 'hello'
        obj_A.b.b = obj_A.a # 'world' --> YServiceProviderError: illegal reference
        self.crud.create(self.ncc, obj_A)

        obj_A_read = self.crud.read(self.ncc, oc_pattern.OcA())


if __name__ == '__main__':
    device, non_demand, common_cache, timeout = get_device_info()

    suite = unittest.TestSuite()
    suite.addTest(ParametrizedTestCase.parametrize(
        SanityYang,
        device=device,
        non_demand=non_demand,
        common_cache=common_cache,
        timeout=timeout))
    ret = not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()
    sys.exit(ret)
