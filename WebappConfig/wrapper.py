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
'''
This helper module intends to provide a wrapper for some Gentoo
specific features used by webapp-config. This might make it easier
to use the tool on other distributions.
'''

# ========================================================================
# Dependencies
# ------------------------------------------------------------------------

import os

from WebappConfig.debug       import OUT

from WebappConfig.debug   import OUT
from WebappConfig.version import WCVERSION

# ========================================================================
# Portage Wrapper
# ------------------------------------------------------------------------

protect_prefix  = '._cfg'
update_command  = 'etc-update'

# Link for bug reporting
bugs_link  = 'http://bugs.gentoo.org/'

def config_protect(cat, pn, pvr, pm):
    '''Return CONFIG_PROTECT (used by protect.py)'''
    if pm == "portage":
        try:
            import portage
        except ImportError as e:
            OUT.die("Portage libraries not found, quitting:\n%s" % e)

        return portage.settings['CONFIG_PROTECT']

    elif pm == "paludis":
        cmd="cave print-id-environment-variable -b --format '%%v\n' --variable-name CONFIG_PROTECT %s/%s" % (cat,pn)

        fi, fo, fe = os.popen3(cmd)
        fi.close()
        result_lines = fo.readlines()
        fo.close()
        fe.close()

        return ' '.join(result_lines).strip()
    else:
        OUT.die("Unknown package manager: " + pm)

def config_libdir(pm):
    OUT.die("I shouldn't get called at all")

def want_category(config):
    '''Check if the package manager requires category info

    Portage: optional
    Paludis: mandatory
    '''

    if config.config.get('USER', 'package_manager') == "portage":
        return
    elif config.config.get('USER', 'package_manager') == "paludis":
        if not config.config.has_option('USER', 'cat'):
            OUT.die("Package name must be in the form CAT/PN")
    else:
        OUT.die("Unknown package manager: " + pm)

def get_root(config):
    '''Returns the $ROOT variable'''
    if config.config.get('USER', 'package_manager') == "portage":
        try:
            import portage
        except ImportError as e:
            OUT.die("Portage libraries not found, quitting:\n%s" % e)

        return portage.settings['ROOT']

    elif config.config.get('USER', 'package_manager') == "paludis":
        cat = config.maybe_get('cat')
        pn  = config.maybe_get('pn')

        if cat and pn:
            cmd="cave print-id-environment-variable -b --format '%%v\n' --variable-name ROOT %s/%s" % (cat,pn)

            fi, fo, fe = os.popen3(cmd)
            fi.close()
            result_lines = fo.readlines()
            fo.close()
            fe.close()

            if result_lines[0].strip():
                return result_lines[0].strip()
            else:
                return '/'
        else:
            return '/'
    else:
        OUT.die("Unknown package manager: " + pm)

def package_installed(full_name, pm):
    '''
    This function identifies installed packages.
    The Portage part is stolen from gentoolkit.
    We are not using gentoolkit directly as it doesn't seem to support ${ROOT}
    '''

    if pm == "portage":
        try:
            import portage
        except ImportError as e:
            OUT.die("Portage libraries not found, quitting:\n%s" % e)

        try:
             t = portage.db[portage.root]["vartree"].dbapi.match(full_name)
        # catch the "ambiguous package" Exception
        except ValueError as e:
            if isinstance(e[0], list):
                t = []
                for cp in e[0]:
                    t += portage.db[portage.root]["vartree"].dbapi.match(cp)
            else:
                raise ValueError(e)
        return t

    elif pm == "paludis":

        cmd="cave print-best-version '%s'" % (full_name)

        fi, fo, fe = os.popen3(cmd)
        fi.close()
        result_lines = fo.readlines()
        error_lines  = fe.readlines()
        fo.close()
        fe.close()

        if error_lines:
            for i in error_lines:
                OUT.warn(i)

        return ' '.join(result_lines)

    else:
        OUT.die("Unknown package manager: " + pm)

if __name__ == '__main__':
    OUT.info('\nPACKAGE MANAGER WRAPPER')
    OUT.info('---------------\n')
    if package_installed('=app-admin/webapp-config-' + WCVERSION, 'portage'):
        a = 'YES'
    else:
        a = 'NO'

    OUT.info('package_installed("webapp-config-'
             + WCVERSION + '") : ' + a + '\n')
    OUT.info('config_protect : ' + config_protect('app-admin','webapp-config',WCVERSION,'portage'))
    OUT.info('protect_prefix : ' + protect_prefix)
    OUT.info('update_command : ' + update_command)
    OUT.info('bugs_link : ' + bugs_link)
