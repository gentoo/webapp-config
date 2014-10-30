# -*- coding: utf-8 -*-
################################################################################
# EXTERNAL WEBAPP-CONFIG TESTS
################################################################################
# File:       external.py
#
#             Runs external (non-doctest) test cases.
#
# Copyright:
#             (c) 2014        Devan Franchini
#             Distributed under the terms of the GNU General Public License v2
#
# Author(s):
#             Devan Franchini <twitch153@gentoo.org>
#

from __future__ import print_function

'''Runs external (non-doctest) test cases.'''

import os
import unittest
import sys

from  WebappConfig.content import Contents
from  WebappConfig.debug   import OUT
from  warnings             import filterwarnings, resetwarnings

HERE = os.path.dirname(os.path.realpath(__file__))

class ContentsTest(unittest.TestCase):
    def test_add_pretend(self):
        loc = '/'.join((HERE, 'testfiles', 'contents', 'app'))
        contents = Contents(loc, package = 'test', version = '1.0',
                            pretend = True)
        OUT.color_off()
        contents.add('file', 'config_owned', destination = loc, path = '/test1',
                     real_path = loc + '/test1', relative = True)

        output = sys.stdout.getvalue().strip('\n')
        self.assertEqual(output,
                       '*     pretending to add: file 1 config_owned "test1"')

    def test_add(self):
        loc = '/'.join((HERE, 'testfiles', 'contents', 'app'))
        contents = Contents(loc, package = 'test', version = '1.0')
        OUT.color_off()
        contents.add('file', 'config_owned', destination = loc, path = '/test1',
                     real_path = loc + '/test1', relative = True)

        # Now trigger an error by adding a file that doesn't exist!
        contents.add('file', 'config_owned', destination = loc, path = '/test0',
                     real_path = loc + '/test0', relative = True)

        output = sys.stdout.getvalue().strip('\n')

        self.assertTrue('WebappConfig/tests/testfiles/contents/app/test0 to '\
                        'add it as installation content. This should not '\
                        'happen!' in output)

        # Test adding hardlinks:
        contents.add('hardlink', 'config_owned', destination = loc,
                     path = '/test2', real_path = loc + '/test2', relative = True)
        self.assertTrue('file 1 config_owned "test2" ' in contents.entry(loc +
                                                                      '/test2'))
        # Test adding dirs:
        contents.add('dir', 'default_owned', destination = loc, path = '/dir1',
                     real_path = loc + '/dir1', relative = True)
        self.assertTrue('dir 1 default_owned "dir1" ' in contents.entry(loc +
                                                                       '/dir1'))

        # Test adding symlinks:
        contents.add('sym', 'virtual', destination = loc, path = '/test3',
                     real_path = loc + '/test3', relative = True)
        self.assertTrue('sym 1 virtual "test3" ' in contents.entry(loc +
                                                                   '/test3'))

        # Printing out the db after adding these entries:
        contents.db_print()
        output = sys.stdout.getvalue().split('\n')
        self.assertTrue('file 1 config_owned "test1" ' in output[1])

    def test_can_rm(self):
        contents = Contents('/'.join((HERE, 'testfiles', 'contents')),
                            package = 'test', version = '1.0')
        contents.read()
        contents.ignore += ['.svn']

        self.assertEqual(contents.get_canremove('/'.join((HERE, 'testfiles',
                         'contents', 'inc'))), '!found inc')

        self.assertEqual(contents.get_canremove('/'.join((HERE, 'testfiles',
                         'contents', 'inc', 'prefs.php'))),
                         '!found inc/prefs.php')

    def test_read_clean(self):
        contents = Contents('/'.join((HERE, 'testfiles', 'contents')),
                            package = 'test', version = '1.0')
        contents.read()
        contents.db_print()

        output = sys.stdout.getvalue().split('\n')

        self.assertTrue('file 1 virtual signup.php ' in output[3])
        self.assertEqual(contents.get_directories()[1], '/'.join((HERE,
                                                                  'testfiles',
                                                                  'contents',
                                                                  'inc')))

    def test_read_corrupt(self):
        contents = Contents('/'.join((HERE, 'testfiles', 'contents')),
                            package = 'test', version = '1.1')

        OUT.color_off()
        contents.read()
        output = sys.stdout.getvalue().split('\n')
        self.assertEqual(output[12], '* Not enough entries.')

    def test_write(self):
        contents = Contents('/'.join((HERE, 'testfiles', 'contents')),
                            package = 'test', version = '1.0', pretend = True)
        OUT.color_off()
        contents.read()

        contents.write()
        output = sys.stdout.getvalue().split('\n')

        expected = '* Would have written content file ' + '/'.join((HERE,
                                                          'testfiles',
                                                          'contents',
                                                          '.webapp-test-1.0!'))
        self.assertEqual(output[0], expected)


if __name__ == '__main__':
    filterwarnings('ignore')
    unittest.main(module=__name__, buffer=True)
    resetwarnings()
