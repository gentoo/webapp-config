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
''' Helper functions for config protected files.'''

__version__ = "$Id: protect.py 133 2005-11-06 14:34:04Z wrobel $"

# ========================================================================
# Dependencies
# ------------------------------------------------------------------------

import re, os, os.path

import WebappConfig.wrapper

from WebappConfig.debug     import OUT

# ========================================================================
# Config protection helper class
# ------------------------------------------------------------------------

class Protection:
    '''
    A small helper class to handle config protection.
    '''

    def __init__(self):
        '''
        This is distribution specific so the information is provided by
        wrapper.py
        '''
        self.config_protect = WebappConfig.wrapper.config_protect
        self.protect_prefix = WebappConfig.wrapper.protect_prefix
        self.update_command = WebappConfig.wrapper.update_command

    # ------------------------------------------------------------------------
    # Outputs:
    #   $my_return = the new mangled name (that you can use instead of
    #       $2)

    def get_protectedname(self,
                          destination,
                          filename):
        '''
        Woh.  Somewhere, we've decided that we're trying to overwrite a file
        that we really want to save.  So, we need a new name for the file that
        we want to install - which is where we come in.

        NOTE:
          The filename that we produce is compatible with Gentoo's
          etc-update tool.  This is deliberate.

        Inputs:
          destination -  the directory that the file is being installed into
          filename    - the original name of the file

        Let's test the code on some examples:

        >>> import os.path
        >>> here = os.path.dirname(os.path.realpath(__file__))

        >>> a = Protection()
        >>> a.get_protectedname(here + '/tests/testfiles/protect/empty',
        ...                     'test')#doctest: +ELLIPSIS
        '.../tests/testfiles/protect/empty//._cfg0000_test'

        >>> a.get_protectedname(here + '/tests/testfiles/protect/simple',
        ...                     'test')#doctest: +ELLIPSIS
        '.../tests/testfiles/protect/simple//._cfg0001_test'

        >>> a.get_protectedname(here + '/tests/testfiles/protect/complex',
        ...                     'test')#doctest: +ELLIPSIS
        '.../tests/testfiles/protect/complex//._cfg0801_test'

        '''

        my_file    = os.path.basename(filename)
        my_filedir = destination + '/' + os.path.dirname(filename)

        # find the highest numbered protected file that already
        # exists, and increment it by one

        entries = os.listdir(my_filedir)

        OUT.debug('Identifying possible file number', 7)

        numbers = []
        prefix  = self.protect_prefix
        rep = re.compile(prefix.replace('.','\.') + '(\d{4})_')

        for i in entries:
            rem = rep.match(i)
            if rem:
                numbers.append(int(rem.group(1)))

        if numbers:
            max_n = max(numbers) + 1
        else:
            max_n = 0

        return  my_filedir + '/%s%.4d_%s' % (prefix, max_n, my_file)


    def dirisconfigprotected(self, installdir):
        '''
        Traverses the path of parent directories for the
        given install dir and checks if any matches the list
        of config protected files.

        >>> a = Protection()

        Add a virtual config protected directory:

        >>> a.config_protect += ' /my/strange/htdocs/'
        >>> a.dirisconfigprotected('/my/strange/htdocs/where/i/installed/x')
        True
        >>> a.dirisconfigprotected('/my/strange/htdocs/where/i/installed/x/')
        True
        >>> a.config_protect += ' /my/strange/htdocs'
        >>> a.dirisconfigprotected('/my/strange/htdocs/where/i/installed/x')
        True
        >>> a.dirisconfigprotected('/my/strange/htdocs/where/i/installed/x/')
        True

        >>> a.config_protect += ' bad_user /my/strange/htdocs'
        >>> a.dirisconfigprotected('/my/bad_user/htdocs/where/i/installed/x')
        False
        >>> a.dirisconfigprotected('/my/strange/htdocs/where/i/installed/x/')
        True

        >>> a.dirisconfigprotected('/')
        False
        '''

        my_master = []
        for i in self.config_protect.split(' '):
            if i[0] == '/':
                if i[-1] == '/':
                    my_master.append(i[:-1])
                else:
                    my_master.append(i)

        if installdir[0] != '/':
            OUT.die('BUG! Don\'t call this with a relative path.')

        if installdir[-1] == '/':
            my_dir = installdir[:-1]
        else:
            my_dir = installdir

        while my_dir:

            if my_dir == '.' or my_dir == '/':
                return False

            for x in my_master:
                if my_dir == x:
                    return True

            my_dir = os.path.dirname(my_dir)

        # nope, the directory isn't config-protected at this time
        return False

    def how_to_update(self, dirs):
        '''
        Instruct the user how to update the application.

        >>> OUT.color_off()
        >>> a = Protection()

        >>> a.how_to_update(['/my/strange/htdocs/where/i/installed/x'])
        * One or more files have been config protected
        * To complete your install, you need to run the following command(s):
        * 
        * CONFIG_PROTECT="/my/strange/htdocs/where/i/installed/x" etc-update
        * 
        >>> a.how_to_update(['/a/','/c/'])
        * One or more files have been config protected
        * To complete your install, you need to run the following command(s):
        * 
        * CONFIG_PROTECT="/a/" etc-update
        * CONFIG_PROTECT="/c/" etc-update
        * 
        >>> a.how_to_update(['/a//test3','/a//test3/abc', '/c/'])
        * One or more files have been config protected
        * To complete your install, you need to run the following command(s):
        * 
        * CONFIG_PROTECT="/a//test3" etc-update
        * CONFIG_PROTECT="/c/" etc-update
        * 

        Add a virtual config protected directory:

        >>> a.config_protect += ' /my/strange/htdocs/'
        >>> a.how_to_update(['/my/strange/htdocs/where/i/installed/x'])
        * One or more files have been config protected
        * To complete your install, you need to run the following command(s):
        * 
        * etc-update
        '''
        my_command = self.update_command

        directories = []

        for i in dirs:
            present = False
            if directories:
                for j in directories:
                    if (i == j[:len(i)] or 
                        j == i[:len(j)]):
                        present = True
                        break
            if not present:
                directories.append(i)

        my_command_list = ''

        for i in directories:
            if not self.dirisconfigprotected(i):
                my_command_list += 'CONFIG_PROTECT="' + i + '" ' + my_command + '\n'

        if not my_command_list:
            my_command_list = my_command

        OUT.warn('One or more files have been config protected\nTo comple'
                 'te your install, you need to run the following command(s):\n\n'
                 + my_command_list)

if __name__ == '__main__':
    import doctest, sys
    doctest.testmod(sys.modules[__name__])
