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
            post.append(os.popen('printf "' + i + '"\n').read()[:-1])

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
        '''

        v_root = self.get_config('vhost_root')
        v_cgi  = self.get_config('g_cgibindir')
        v_conf = self.get_config('vhost_config_dir')
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
        for i in list(export_map.keys()):

            value = export_map[i]

            if not value:
                value = self.get_config(i.lower())

            os.putenv(i, str(value))
            result[i] = str(value)

        return result
