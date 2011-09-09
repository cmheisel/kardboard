#!/usr/bin/env python

# For use by continuous.io

try:
    import unittest_continuous
    unittest_continuous.setup()
except ImportError:
    pass

import unittest2

unittest2.main('kardboard.tests')
