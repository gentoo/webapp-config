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
This helper module intends to provide a wrapper for some Gentoo
specific features used by webapp-config. This might make it easier
to use the tool on other distributions.

Currently two parameters and one function are provided:

 - conf_libdir        [directory for libraries]
 - config_protect     [list of configuration protected directories]

 - package_installed  [indicates if the specified package is installed]
'''

__version__ = "$Id: wrapper.py 283 2006-04-20 22:53:04Z wrobel $"

# ========================================================================
# Dependencies
# ------------------------------------------------------------------------

import sys, portage, os, types

from WebappConfig.debug       import OUT

from WebappConfig.debug   import OUT
from WebappConfig.version import WCVERSION

# ========================================================================
# Portage Wrapper
# ------------------------------------------------------------------------

# Variable for config protected files (used by protect.py)
config_protect  = portage.settings['CONFIG_PROTECT']

# Try to derive the correct libdir location by first examining the portage
# variable ABI then using it to determine the appropriate variable to read. For
# example, if ABI == 'amd64' then read LIBDIR_amd64. This routine should work on
# all arches as it sets '/usr/lib' as a fallback. See bugs #125032 and #125156.

config_libdir = '/usr/lib'

if 'ABI' in portage.settings.keys():
    config_abi  = portage.settings['ABI']
    if 'LIBDIR_' + config_abi in portage.settings.keys():
        config_libdir = '/usr/' + portage.settings['LIBDIR_' + config_abi]
    else:
        # This shouldn't happen but we want to know if it ever does
        OUT.warn('Failed to determine libdir from portage.settings[\'LIBDIR_' + config_abi + '\']\n')

protect_prefix  = '._cfg'
update_command  = 'etc-update'

# Link for bug reporting
bugs_link  = 'http://bugs.gentoo.org/'

def get_root():
    '''
    This function returns the $ROOT variable
    '''
    return portage.root

def package_installed(packagename):
    '''
    This function identifies installed packages.
    Stolen from gentoolkit.
    We are not using gentoolkit directly as it doesn't seem to support ${ROOT}
    '''
    if packagename in portage.settings.pprovideddict.keys():
        return True
    try:
        t = portage.db[portage.root]["vartree"].dbapi.match(packagename)
    # catch the "ambiguous package" Exception
    except ValueError, e:
        if type(e[0]) == types.ListType:
            t = []
            for cp in e[0]:
                t += portage.db[portage.root]["vartree"].dbapi.match(cp)
        else:
            raise ValueError(e)
    return t

if __name__ == '__main__':
    OUT.info('\nPORTAGE WRAPPER')
    OUT.info('---------------\n')
    if package_installed('=webapp-config-' + WCVERSION):
        a = 'YES'
    else:
        a = 'NO'

    OUT.info('package_installed("webapp-config-'
             + WCVERSION + '") : ' + a + '\n')
    OUT.info('config_protect : ' + config_protect)
    OUT.info('protect_prefix : ' + protect_prefix)
    OUT.info('update_command : ' + update_command)
    OUT.info('bugs_link : ' + bugs_link)
