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

from  WebappConfig.config    import Config
from  WebappConfig.content   import Contents
from  WebappConfig.db        import WebappDB, WebappSource
from  WebappConfig.debug     import OUT
from  WebappConfig.dotconfig import DotConfig
from  WebappConfig.ebuild    import Ebuild
from  WebappConfig.filetype  import FileType
from  WebappConfig.server    import Basic
from  warnings               import filterwarnings, resetwarnings

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

class WebappDBTest(unittest.TestCase):
    def test_list_installs(self):
        OUT.color_off()
        db = WebappDB(root = '/'.join((HERE, 'testfiles', 'webapps')))

        db.listinstalls()
        output = sys.stdout.getvalue().split('\n')
        self.assertEqual(output[1], '/var/www/localhost/htdocs/horde')

        # Now test the verbosity:
        db = WebappDB(root = '/'.join((HERE, 'testfiles', 'webapps')),
                      verbose = True)
        db.listinstalls()
        output = sys.stdout.getvalue().split('\n')
        self.assertEqual(output[5], '* Installs for horde-3.0.5')

    def test_list_locations(self):
        OUT.color_off()
        db = WebappDB(root = '/'.join((HERE, 'testfiles', 'webapps')))

        sorted_db = [i[1] for i in db.list_locations().items()]
        sorted_db.sort(key=lambda x: x[0]+x[1]+x[2])

        self.assertEqual(sorted_db[1], ['', 'gallery', '2.0_rc2'])

        # Now test with a specific package and version:
        db = WebappDB(root = '/'.join((HERE, 'testfiles', 'webapps')),
                      package = 'horde', version = '3.0.5')
        sorted_db = [i[1] for i in db.list_locations().items()]
        self.assertEqual(sorted_db, [['', 'horde', '3.0.5']])

        # Now test with an install file that doesn't exist:
        db = WebappDB(root = '/'.join((HERE, 'testfiles', 'webapps')),
                      package = 'nihil', version = '3.0.5')
        sorted_db = [i[1] for i in db.list_locations().items()]
        self.assertEqual(sorted_db, [])
        
    def test_add_rm(self):
        OUT.color_off()
        db = WebappDB(root = '/'.join((HERE, 'testfiles', 'webapps')),
                      pretend = True, package = 'horde', version = '3.0.5')
        # Test adding:
        db.add('/'.join(('/screwy', 'wonky', 'foobar', 'horde', 'hierarchy')),
               user = 'me', group = 'me')
        output = sys.stdout.getvalue().split('\n')
        self.assertEqual(output[0], '* Pretended to append installation '\
                                    '/screwy/wonky/foobar/horde/hierarchy')

        # Test deleting a webapp that is actually in the database:
        db.remove('/'.join(('/var', 'www', 'localhost', 'htdocs', 'horde')))
        output = sys.stdout.getvalue().split('\n')
        self.assertEqual(output[6], '* ')

        # And now test deleting one that isn't:
        db.remove('/'.join(('/screwy', 'wonky', 'foobar', 'horde', 'hierarchy')))
        output = sys.stdout.getvalue().split('\n')
        self.assertEqual(output[11], '* 1124612110 root root '\
                                     '/var/www/localhost/htdocs/horde')


class WebappSourceTest(unittest.TestCase):
        SHARE = '/'.join((HERE, 'testfiles', 'share-webapps'))
        def test_list_unused(self):
            source = WebappSource(root = '/'.join((HERE,
                                                  'testfiles',
                                                  'share-webapps')))
            db = WebappDB(root = '/'.join((HERE, 'testfiles', 'webapps')))
            source.listunused(db)
            output = sys.stdout.getvalue().split('\n')
            self.assertEqual(output[2], 'share-webapps/uninstalled-6.6.6')

        def test_read(self):
            source = WebappSource(root = '/'.join((HERE,
                                                   'testfiles',
                                                   'share-webapps')),
                                  category = '',
                                  package = 'horde',
                                  version = '3.0.5')

            source.read()
            self.assertEqual(source.filetype('test1'), 'config-owned')
            self.assertEqual(source.filetype('test2'), 'server-owned')

        def test_src_exists(self):
            source = WebappSource(root = '/'.join((HERE, 'testfiles',
                                                   'share-webapps')),
                                  category = '',
                                  package = 'horde',
                                  version = '3.0.5')
            self.assertTrue(source.source_exists('htdocs'))
            self.assertFalse(source.source_exists('foobar'))

        def test_get_src_dirs(self):
            source = WebappSource(root = '/'.join((HERE, 'testfiles',
                                                   'share-webapps')),
                                  category = '',
                                  package = 'horde',
                                  version = '3.0.5')
            dirs = source.get_source_directories('htdocs')
            dirs = [i for i in dirs if i != '.svn']
            self.assertEqual(dirs, ['dir1', 'dir2'])

        def test_get_src_files(self):
            source = WebappSource(root = '/'.join((HERE, 'testfiles',
                                                   'share-webapps')),
                                  category = '',
                                  package = 'horde',
                                  version = '3.0.5')
            files = source.get_source_files('htdocs')
            self.assertEqual(files, ['test1', 'test2'])

        def test_pkg_avail(self):
            source = WebappSource(root = '/'.join((HERE, 'testfiles',
                                                   'share-webapps')),
                                  category = '',
                                  package = 'nihil',
                                  version = '3.0.5',
                                  pm = 'portage')
            self.assertEqual(source.packageavail(), 1)


class DotConfigTest(unittest.TestCase):
    def test_has_dotconfig(self):
        dotconf = DotConfig('/'.join((HERE, 'testfiles', 'htdocs', 'horde')))
        self.assertTrue(dotconf.has_dotconfig())

        dotconf = DotConfig('/'.join((HERE, 'testfiles', 'htdocs', 'empty')))
        self.assertFalse(dotconf.has_dotconfig())

    def test_is_empty(self):
        dotconf = DotConfig('/'.join((HERE, 'testfiles', 'htdocs', 'horde')))
        self.assertEqual(dotconf.is_empty(), None)

        dotconf = DotConfig('/'.join((HERE, 'testfiles', 'htdocs', 'complain')))
        self.assertEqual(dotconf.is_empty(), '!morecontents .webapp-cool-1.1.1')

    def test_show_installed(self):
        dotconf = DotConfig('/'.join((HERE, 'testfiles', 'htdocs', 'horde')))
        dotconf.show_installed()
        output = sys.stdout.getvalue().split('\n')
        self.assertEqual(output[0], 'horde 3.0.5')

    def test_install(self):
        dotconf = DotConfig('/nowhere', pretend=True)
        dotconf.write('www-apps', 'horde', '5.5.5', 'localhost', '/horde3',
                      'me:me')
        output = sys.stdout.getvalue().split('\n')
        self.assertEqual(output[14], '* WEB_INSTALLDIR="/horde3"')

    def test_remove(self):
        dotconf = DotConfig('/'.join((HERE, 'testfiles', 'htdocs', 'horde')),
                            pretend=True)
        self.assertTrue(dotconf.kill())
        output = sys.stdout.getvalue().split('\n')
        self.assertEqual(output[0], '* Would have removed ' +
                         '/'.join((HERE, 'testfiles', 'htdocs', 'horde',
                                   '.webapp')))



class EbuildTest(unittest.TestCase):
    def test_showpostinst(self):
        config = Config()
        approot = '/'.join((HERE, 'testfiles', 'share-webapps'))
        appdir  = '/'.join((approot, 'horde', '3.0.5'))
        conf   = {'my_htdocsbase': 'htdocs', 'pn': 'horde', 'pvr': '3.0.5',
                  'vhost_server_uid': 'apache', 'vhost_server_git': 'apache',
                  'my_approot': approot,
                  'my_appdir': appdir,
                  'my_hookscriptsdir': '/'.join((appdir, 'hooks')),
                  'my_cgibinbase': 'cgi-bin', 'my_errorsbase': 'error',
                  'my_iconsbase': 'icons',
                  'my_serverconfigdir': '/'.join((appdir, 'conf')),
                  'my_hostrootdir': '/'.join((appdir, 'hostroot')),
                  'my_htdocsdir': '/'.join((appdir, 'htdocs')),
                  'my_sqlscriptsdir': '/'.join((appdir, 'sqlscripts')),
                 }

        for key in conf.keys():
            config.config.set('USER', key, conf[key])

        ebuild = Ebuild(config)
        ebuild.show_postinst()
        output = sys.stdout.getvalue().split('\n')

        self.assertEqual(output[5], 'MY_HOSTROOTDIR: ' + '/'.join((HERE,
                                                                 'testfiles',
                                                                 'share-webapps',
                                                                 'horde',
                                                                 '3.0.5',
                                                                 'hostroot')))


class FileTypeTest(unittest.TestCase):
    def test_filetypes(self):
        config_owned = ('a', 'a/b/c/d', '/e', '/f/', '/g/h/', 'i\\n')
        server_owned = ('j', 'k/l/m/n', '/o', '/p/', '/q/r/', 's\\n')

        types = FileType(config_owned, server_owned)

        self.assertEqual(types.filetype('a'),       'config-owned')
        self.assertEqual(types.filetype('a/b/c/d'), 'config-owned')
        self.assertEqual(types.filetype('j'),       'server-owned')
        self.assertEqual(types.filetype('/o'),      'server-owned')

        # It will always remove leading spaces or whitespace:
        self.assertEqual(types.filetype('\t s\\n'), 'server-owned')
        # Unspecified files will be set as virtual:
        self.assertEqual(types.filetype('foo.txt'), 'virtual')
        # However, you can set what you want your virtual-files to be:
        types = FileType(config_owned, server_owned,
                         virtual_files='server-owned')
        self.assertEqual(types.filetype('foo.txt'), 'server-owned')

    def test_dirtypes(self):
        config_owned = ('a', 'a/b/c/d', '/e', '/f/', '/g/h/', 'i\\n')
        server_owned = ('j', 'k/l/m/n', '/o', '/p/', '/q/r/', 's\\n')

        types = FileType(config_owned, server_owned)

        self.assertEqual(types.dirtype('a'),       'config-owned')
        self.assertEqual(types.dirtype('j'),       'server-owned')

        # Same whitespace rules apply for dirtype():
        self.assertEqual(types.dirtype('\t s\\n'), 'server-owned')
        # Unspecified dirs will be set as default-owned:
        self.assertEqual(types.dirtype('foo.txt'), 'default-owned')


if __name__ == '__main__':
    filterwarnings('ignore')
    unittest.main(module=__name__, buffer=True)
    resetwarnings()
