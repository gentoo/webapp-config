################################################################################
# KOLAB LIBRARY - TESTING "CONDITION.PY"
################################################################################
# test_condition.py -- Testing condition.py
# Copyright 2005 Gunnar Wrobel
# Distributed under the terms of the GNU General Public License v2
# $Id$

import unittest, doctest, sys

import WebappConfig.filetype
import WebappConfig.protect
import WebappConfig.worker

def test_suite():
    return unittest.TestSuite((
        doctest.DocTestSuite(WebappConfig.filetype),
        doctest.DocTestSuite(WebappConfig.protect),
        doctest.DocTestSuite(WebappConfig.worker),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
