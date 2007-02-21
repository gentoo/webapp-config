#!/usr/bin/python -O
#
# /usr/sbin/webapp-config
#       Python script for managing the deployment of web-based
#       applications
#
#       Originally written for the Gentoo Linux distribution
#
# Copyright (c) 1999-2006 Gentoo Foundation
#       Released under v2 of the GNU GPL
#
# Author(s)     Stuart Herbert <stuart@gentoo.org>
#               Renat Lumpau   <rl03@gentoo.org>
#               Gunnar Wrobel  <php@gunnarwrobel.de>
#
# ========================================================================
'''
Sandbox operations
'''

__version__ = "$Id: permissions.py 129 2005-11-06 12:46:31Z wrobel $"

# ========================================================================
# Dependencies
# ------------------------------------------------------------------------

import os, string, time

from WebappConfig.wrapper   import config_libdir

from WebappConfig.debug     import OUT

class Sandbox:
    '''
    Basic class for handling sandbox stuff
    Concept stolen from app-shells/sandboxshell
    '''

    def __init__(self, config):

        self.config     = config
        self.__path     =  [config_libdir + '/libsandbox.so',
                           '/usr/lib/libsandbox.so', '/lib/libsandbox.so']
        self.__export   = {}
        self.__write    = ['g_installdir',
                           'g_htdocsdir',
                           'g_cgibindir',
                           'vhost_root']
        self.__read     =  '/'

        self.__syswrite = ':/dev/tty:/dev/pts:/dev/null:/tmp'

        self.sandbox    = ''

        self.log        = '/tmp/w-c.sandbox-' \
                            + time.strftime("%Y-%m-%d-%H.%M.%S",time.gmtime())\
                            + '.log'
        self.debug_log        = self.log + '.debug'

    def get_write(self):
        '''Return write paths.'''
        return string.join ( map ( self.get_config, self.__write ), ':' ) \
                + self.__syswrite

    def get_config(self, option):
        ''' Return a config option.'''
        return self.config.config.get('USER', option)

    def start(self):
        '''
        Start sandbox. Return 1 if failed.
        '''

        OUT.debug('Initializing sandbox', 7)
        for i in self.__path:
            if os.access(i, os.R_OK):
                self.sandbox = i
                break

        if not self.sandbox:
            OUT.warn("Could not find a sandbox, disabling hooks")
            return 1

        try:
            self.__ld     = os.environ['LD_PRELOAD']
        except KeyError, e:
            self.__ld     = ""

        self.__export = {'LD_PRELOAD'         : self.sandbox,
                         'SANDBOX_WRITE'      : self.get_write(),
                         'SANDBOX_READ'       : self.__read,
                         'SANDBOX_LOG'        : self.log,
                         'SANDBOX_DEBUG_LOG'  : self.debug_log,
                         'SANDBOX_ON'         : "1",
                         'SANDBOX_ACTIVE'     : "armedandready"}
        self.run_vars()

    def stop(self):
        '''Stop sandbox'''

        self.__export = {'LD_PRELOAD'         : self.__ld,
                         'SANDBOX_WRITE'      : "",
                         'SANDBOX_READ'       : "",
                         'SANDBOX_LOG'        : "",
                         'SANDBOX_DEBUG_LOG'  : "",
                         'SANDBOX_ON'         : "0",
                         'SANDBOX_ACTIVE'     : ""}
        self.run_vars()

    def run_vars(self):

        for i in self.__export.keys():
            value = self.__export[i]
            os.putenv(i, value)
