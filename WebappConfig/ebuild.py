#!/usr/bin/python -O
#
# /usr/sbin/webapp-config
#       Python script for managing the deployment of web-based
#       applications
#
#       Originally written for the Gentoo Linux distribution
#
# Copyright (c) 1999-2007 Authors
#       Released under v2 of the GNU GPL
#
# Author(s)     Stuart Herbert
#               Renat Lumpau   <rl03@gentoo.org>
#               Gunnar Wrobel  <wrobel@gentoo.org>
#
# ========================================================================
''' Provides a class that handles ebuild related tasks.  '''

__version__ = "$Id: ebuild.py 260 2006-01-29 23:21:56Z wrobel $"

# ========================================================================
# Dependencies
# ------------------------------------------------------------------------

import os.path, re, pwd, grp

from WebappConfig.debug     import OUT
import WebappConfig.wrapper as wrapper
from WebappConfig.sandbox   import Sandbox

# ========================================================================
# Handler for ebuild related tasks
# ------------------------------------------------------------------------

class Ebuild:
    '''
    This class handles all ebuild related task. Currently this includes
    displaying the post install instruction as well as running hooks
    provided by the ebuild.

    This creates the basic configuration defaults:

    >>> import WebappConfig.config
    >>> config = WebappConfig.config.Config()

    This needs to be completed with some parameters
    that would be usually provided when parsing the
    commandline:

    >>> config.config.set('USER', 'my_htdocsbase',  'htdocs')
    >>> config.config.set('USER', 'pn',   'horde')
    >>> config.config.set('USER', 'pvr',  '3.0.5')
    >>> config.config.set('USER', 'vhost_server_uid', 'apache')
    >>> config.config.set('USER', 'vhost_server_gid', 'apache')

    And the application directory needs to be set
    to the testfile reporitory

    >>> import os.path
    >>> here = os.path.dirname(os.path.realpath(__file__))
    >>> config.config.set('USER', 'my_approot', here +
    ...                   '/tests/testfiles/share-webapps')

    Time to create the ebuild handler:

    >>> my_approot = config.config.get('USER', 'my_approot')
    >>> my_appdir = my_approot + "/horde/3.0.5"
    >>> config.config.set('USER', 'my_appdir', my_appdir)
    >>> config.config.set('USER', 'my_hookscriptsdir', my_appdir + '/hooks')
    >>> config.config.set('USER', 'my_cgibinbase', 'cgi-bin')
    >>> config.config.set('USER', 'my_errorsbase', 'error')
    >>> config.config.set('USER', 'my_iconsbase', 'icons')
    >>> config.config.set('USER', 'my_serverconfigdir', '/'.join([my_appdir,'conf']))
    >>> config.config.set('USER', 'my_hostrootdir', '/'.join([my_appdir,'hostroot']))
    >>> config.config.set('USER', 'my_htdocsdir', '/'.join([my_appdir,'htdocs']))
    >>> config.config.set('USER', 'my_sqlscriptsdir', '/'.join([my_appdir,'sqlscripts']))
    >>> a = Ebuild(config)

    Run a hook script:

    >>> from WebappConfig.server import Basic
    >>> basic = Basic({'source': '', 'destination': '', 'hostroot': '', 'vhostroot':''},
    ...               config.create_permissions(),
    ...               {'source':'','content':'','protect':'','dotconfig':'','ebuild':'','db':''},
    ...               {'verbose':False,'pretend':True}, 'portage')
    >>> a.run_hooks('test', basic)

    The same on a directory that misses a hook dir:

    >>> config.config.set('USER', 'pn',   'empty')
    >>> config.config.set('USER', 'pvr',  '1.0')
    >>> a = Ebuild(config)
    >>> a.run_hooks('test', basic)

    This app has a hook dir but no script:

    >>> config.config.set('USER', 'pn',   'uninstalled')
    >>> config.config.set('USER', 'pvr',  '6.6.6')
    >>> a = Ebuild(config)
    >>> a.run_hooks('test', basic)


    '''

    def __init__(self, config):

        self.config    = config
        self.__root    = wrapper.get_root(self.config)
        self.__re      = re.compile('/+')
        self.__sourced = self.__re.sub('/', self.__root
                           + self.get_config('my_appdir'))
        self.__hooksd  = self.__re.sub('/', self.__root
                           + self.get_config('my_hookscriptsdir'))

    def get_config(self, option):
        ''' Return a config option.'''
        return self.config.config.get('USER', option)

    def run_hooks(self, type, server):
        '''
        Run the hook scripts - if there are any
        '''

        if self.config.pretend():
            return

        sandbox = Sandbox(self.config)

        # save list of environment variables to set
        env_map = self.run_vars(server)

        if os.path.isdir(self.__hooksd):
            for x in os.listdir(self.__hooksd):

                if (os.path.isfile(self.__hooksd + '/' + x) and
                    os.access(self.__hooksd + '/' + x, os.X_OK)):

                    OUT.debug('Running hook script', 7)

                    sandbox.spawn(self.__hooksd + '/' + x + ' ' + type, env_map)

    def show_post(self, filename, ptype, server = None):
        '''
        Display one of the post files.
        '''

        post_file =  self.__sourced + '/' + filename

        OUT.debug('Check for instruction file', 7)

        if not os.path.isfile(post_file):
            return

        self.run_vars(server)

        post_instructions = open(post_file).readlines()

        OUT.debug('Read post instructions', 7)

        post = [
            '',
            '=================================================================',
            'POST-' + ptype.upper() + ' INSTRUCTIONS',
            '=================================================================',
            '']

        for i in post_instructions:
            i = i.replace('"', '\\"')
            post.append(os.popen('echo -n "' + i + '"\n').read()[:-1])

        post = post + [
            '',
            '=================================================================',
            '']

        for i in post:
            OUT.notice(i)

    def show_postinst(self, server = None):
        '''
        Display any post-installation instructions, if there are any.
        '''

        OUT.debug('Running show_postinst', 6)

        self.show_post(filename = 'postinst-en.txt', ptype = 'install', server = server)

    def show_postupgrade(self, server = None):
        '''
        Display any post-upgrade instructions, if there are any.
        '''

        OUT.debug('Running show_postupgrade', 6)

        self.show_post(filename = 'postupgrade-en.txt', ptype = 'upgrade', server = server)

    def run_vars(self, server = None):
        '''
        This function exports the necessary variables to the shell
        environment so that they are accessible within the shell scripts
        and/or files provided by the ebuild.

        The procedure from above is repeated to set up the default
        environment:

        >>> import WebappConfig.config
        >>> config = WebappConfig.config.Config()
        >>> config.config.set('USER', 'my_htdocsbase',  'htdocs')
        >>> config.config.set('USER', 'pn',   'horde')
        >>> config.config.set('USER', 'pvr',  '3.0.5')
        >>> import os.path
        >>> here = os.path.dirname(os.path.realpath(__file__))
        >>> config.config.set('USER', 'my_approot', here +
        ...                   '/tests/testfiles/share-webapps')
        >>> my_approot = config.config.get('USER', 'my_approot')
        >>> my_appdir = my_approot + "/horde/3.0.5"
        >>> config.config.set('USER', 'my_appdir', my_appdir)
        >>> config.config.set('USER', 'my_hookscriptsdir', my_appdir + '/hooks')
        >>> config.config.set('USER', 'my_cgibinbase', 'cgi-bin')
        >>> config.config.set('USER', 'my_errorsbase', 'error')
        >>> config.config.set('USER', 'my_iconsbase', 'icons')
        >>> config.config.set('USER', 'my_serverconfigdir', '/'.join([my_appdir,'conf']))
        >>> config.config.set('USER', 'my_hostrootdir', '/'.join([my_appdir,'hostroot']))
        >>> config.config.set('USER', 'my_htdocsdir', '/'.join([my_appdir,'htdocs']))
        >>> config.config.set('USER', 'my_sqlscriptsdir', '/'.join([my_appdir,'sqlscripts']))

        Time to create the ebuild handler:

        >>> a = Ebuild(config)

        The dummy post-install file should display all the variables
        that are exported here:

        >>> a.show_postinst() #doctest: +ELLIPSIS
        <BLANKLINE>
        =================================================================
        POST-INSTALL INSTRUCTIONS
        =================================================================
        <BLANKLINE>
        MY_HOSTROOTDIR: .../tests/testfiles/share-webapps/horde/3.0.5/hostroot
        MY_HTDOCSDIR: .../tests/testfiles/share-webapps/horde/3.0.5/htdocs
        MY_CGIBINDIR: .../tests/testfiles/share-webapps/horde/3.0.5/hostroot/cgi-bin
        MY_INSTALLDIR: /
        MY_ICONSDIR: .../tests/testfiles/share-webapps/horde/3.0.5/hostroot/icons
        MY_SERVERCONFIGDIR: .../tests/testfiles/share-webapps/horde/3.0.5/conf
        MY_ERRORSDIR: .../tests/testfiles/share-webapps/horde/3.0.5/hostroot/error
        MY_SQLSCRIPTSDIR: .../tests/testfiles/share-webapps/horde/3.0.5/sqlscripts
        VHOST_ROOT: /var/www/...
        VHOST_HTDOCSDIR: /var/www/.../htdocs
        VHOST_CGIBINDIR: /var/www/.../cgi-bin
        VHOST_CONFDIR: /var/www/.../
        VHOST_ERRORSDIR: /var/www/.../error
        VHOST_ICONSDIR: /var/www/.../icons
        VHOST_HOSTNAME: ...
        VHOST_SERVER: apache
        VHOST_APPDIR: /
        VHOST_CONFIG_UID: ...
        VHOST_CONFIG_GID: ...
        VHOST_SERVER_UID: ...
        VHOST_SERVER_GID: ...
        VHOST_DEFAULT_UID: 0
        VHOST_DEFAULT_GID: 0
        VHOST_PERMS_SERVEROWNED_DIR: 0775
        VHOST_PERMS_SERVEROWNED_FILE: 0664
        VHOST_PERMS_CONFIGOWNED_DIR: 0755
        VHOST_PERMS_CONFIGOWNED_FILE: 0644
        VHOST_PERMS_DEFAULTOWNED_DIR: 0755
        VHOST_PERMS_VIRTUALOWNED_FILE: o-w
        VHOST_PERMS_INSTALLDIR: 0755
        ROOT: /
        PN: horde
        PVR: 3.0.5
        <BLANKLINE>
        =================================================================
        <BLANKLINE>        
        '''

        v_root = self.get_config('vhost_root')
        v_cgi  = self.get_config('g_cgibindir')
        v_conf = v_root + '/'
        v_err  = v_root + '/' + self.get_config('my_errorsbase')
        v_icon = v_root + '/' + self.get_config('my_iconsbase')

        g_inst = self.get_config('g_installdir')
        g_htd  = self.get_config('g_htdocsdir')
        g_orig = self.get_config('g_orig_installdir')

        vsu = None
        vsg = None
        if server:
            vsu = pwd.getpwuid(server.vhost_server_uid)[0]
            vsg = grp.getgrgid(server.vhost_server_gid)[0]

        OUT.debug('Exporting variables', 7)

        export_map = {'MY_HOSTROOTDIR'     : None,
                      'MY_HTDOCSDIR'       : None,
                      'MY_CGIBINDIR'       : None,
                      'MY_INSTALLDIR'      : g_inst,
                      'MY_ICONSDIR'        : None,
                      'MY_SERVERCONFIGDIR' : None,
                      'MY_ERRORSDIR'       : None,
                      'MY_SQLSCRIPTSDIR'   : None,
                      'VHOST_ROOT'         : None,
                      'VHOST_HTDOCSDIR'    : g_htd,
                      'VHOST_CGIBINDIR'    : v_cgi,
                      'VHOST_CONFDIR'      : v_conf,
                      'VHOST_ERRORSDIR'    : v_err,
                      'VHOST_ICONSDIR'     : v_icon,
                      'VHOST_HOSTNAME'     : None,
                      'VHOST_SERVER'       : None,
                      'VHOST_APPDIR'       : g_orig,
                      'VHOST_CONFIG_UID'   : None,
                      'VHOST_CONFIG_GID'   : None,
                      'VHOST_SERVER_UID'   : vsu,
                      'VHOST_SERVER_GID'   : vsg,
                      'VHOST_DEFAULT_UID'  : None,
                      'VHOST_DEFAULT_GID'  : None,
                      'VHOST_PERMS_SERVEROWNED_DIR'  : None,
                      'VHOST_PERMS_SERVEROWNED_FILE' : None,
                      'VHOST_PERMS_CONFIGOWNED_DIR'  : None,
                      'VHOST_PERMS_CONFIGOWNED_FILE' : None,
                      'VHOST_PERMS_DEFAULTOWNED_DIR' : None,
                      'VHOST_PERMS_VIRTUALOWNED_FILE': None,
                      'VHOST_PERMS_INSTALLDIR'       : None,
                      'ROOT'                         : self.__root,
                      'PN' : None,
                      'PVR': None}

        result = {}
        for i in export_map.keys():

            value = export_map[i]

            if not value:
                value = self.get_config(i.lower())

            os.putenv(i, str(value))
            result[i] = str(value)

        return result

if __name__ == '__main__':
    import doctest, sys
    doctest.testmod(sys.modules[__name__])
