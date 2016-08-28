#!/usr/bin/env python

# Copyright (c) 2009, Giampaolo Rodola'. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os

import psutil
from psutil.tests import unittest
from psutil.tests import pyrun
from psutil.tests import TESTFN
from psutil.tests import PYTHON
from psutil.tests import POSIX
from psutil.tests import run_test_module_by_name
from psutil.tests import sh
from psutil.tests import reap_children
from psutil.tests import get_test_subprocess
from psutil.tests import get_kernel_version


class TestTestUtils(unittest.TestCase):

    def test_pyrun(self):
        with open(TESTFN, 'w'):
            pass
        subp = pyrun("import os; os.remove('%s')" % TESTFN)
        subp.communicate()
        assert not os.path.exists(TESTFN)

    def test_sh(self):
        out = sh("%s -c 'print(1)'" % PYTHON)
        self.assertEqual(out, '1')

    def test_reap_children(self):
        subp = get_test_subprocess()
        assert psutil.pid_exists(subp.pid)
        reap_children()
        assert not psutil.pid_exists(subp.pid)

    def test_get_kernel_version(self):
        if not POSIX:
            self.assertEqual(get_kernel_version(), tuple())
        else:
            kernel = get_kernel_version()
            assert kernel, kernel
            self.assertIn('.'.join(map(str, kernel)), sh("uname -a"))


if __name__ == '__main__':
    run_test_module_by_name(__file__)
