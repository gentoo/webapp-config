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
''' Handles the information stored within the virtual install location
about the type of package installed.  '''

# ========================================================================
# Dependencies
# ------------------------------------------------------------------------

import pwd, shlex, os.path

from time                     import strftime
from WebappConfig.debug       import OUT
from WebappConfig.permissions import PermissionMap

# ========================================================================
# Handler for dotConfig files
# ------------------------------------------------------------------------

class DotConfig:
    '''
    This class handles the dotconfig file that will be written to all
    virtual install locations.
    '''

    def __init__(self,
                 installdir,
                 dot_config = '.webapp',
                 permission = PermissionMap('0600'),
                 pretend    = False):

        self.__instdir = installdir
        self.__file    = dot_config
        self.__perm    = permission
        self.__p       = pretend
        self.__data    = {}
        self.__tokens  = ['WEB_CATEGORY',
                          'WEB_PN',
                          'WEB_PVR',
                          'WEB_INSTALLEDBY',
                          'WEB_INSTALLEDDATE',
                          'WEB_INSTALLEDFOR',
                          'WEB_HOSTNAME',
                          'WEB_INSTALLDIR']

    def __getitem__(self, key):
        if key in list(self.__data.keys()):
            return self.__data[key]
        # this key didn't exist in old versions, but new versions
        # expect it. fix bug 355295
        elif key == 'WEB_CATEGORY':
            return ''

    def __dot_config(self):
        ''' Returns the full path to the dot config file.'''
        return self.__instdir + '/' + self.__file

    def has_dotconfig(self):
        ''' Return True if the install location already has a dotconfig
        file.'''
        dotconfig = self.__dot_config()

        OUT.debug('Verifying path', 7)

        if not os.path.isfile(dotconfig):
            return False

        if not os.access(dotconfig, os.R_OK):
            return False

        return True

    def is_empty(self):
        '''
        Checks if there are more files '.webapp-*' in the directory.
        Returns empty if there are none.
        '''
        if not os.path.isdir(self.__instdir):
            return '!dir ' + self.__instdir

        # get a directory listing
        entries = os.listdir(self.__instdir)

        for i in entries:
            if i[:len(self.__file)] == self.__file and i != self.__file:
                return '!morecontents ' + i

    def show_installed(self):
        ''' Show which application has been installed in the install 
        location.'''
        if not self.has_dotconfig():
            OUT.die('No ' + self.__file + ' file in ' + self.__instdir
                    + '; unable to continue')

        self.read()

        if 'WEB_CATEGORY' in self.__data:
            OUT.notice(self.__data['WEB_CATEGORY'] + ' ' +
                   self.__data['WEB_PN'] + ' ' +
                   self.__data['WEB_PVR'])
        else:
            OUT.notice(
                   self.__data['WEB_PN'] + ' ' +
                   self.__data['WEB_PVR'])

    def packagename(self):
        ''' Retrieve the package name from the values specified in the dot
        config file'''

        OUT.debug('Trying to retrieve package name', 6)

        if 'WEB_PN' in list(self.__data.keys()) and 'WEB_PVR' in list(self.__data.keys()):
            if 'WEB_CATEGORY' in list(self.__data.keys()):
                return self.__data['WEB_CATEGORY'] + '/' + \
                    self.__data['WEB_PN'] + '-' + self.__data['WEB_PVR']
            else:
                return self.__data['WEB_PN'] + '-' + self.__data['WEB_PVR']
        return ''

    def read(self):
        ''' Read the contents of the dot config file.'''
        dotconfig = self.__dot_config()

        OUT.debug('Checking for dotconfig ', 6)

        if not self.has_dotconfig():
            raise Exception('Cannot read file ' + dotconfig)

        tokens = shlex.shlex(open(dotconfig))

        while True:
            a = tokens.get_token()
            b = tokens.get_token()
            c = tokens.get_token()

            OUT.debug('Reading token', 8)

            if (a in self.__tokens and
                b == '=' and c):

                if c[0] == '"':
                    c = c[1:]

                if c[-1] == '"':
                    c = c[:-1]

                self.__data[a] = c

            else:
                break

    def write(self,
              category,
              package,
              version,
              host,
              original_installdir,
              user_group):
        '''
        Output the .webapp file, that tells us in future what has been installed
        into this directory.
        '''
        self.__data['WEB_CATEGORY']      = category
        self.__data['WEB_PN']            = package
        self.__data['WEB_PVR']           = version
        self.__data['WEB_INSTALLEDBY']   = pwd.getpwuid(os.getuid())[0]
        self.__data['WEB_INSTALLEDDATE'] = strftime('%Y-%m-%d %H:%M:%S')
        self.__data['WEB_INSTALLEDFOR']  = user_group
        self.__data['WEB_HOSTNAME']      = host
        self.__data['WEB_INSTALLDIR']    = original_installdir


        info = ['# ' + self.__file,
                '#	config file for this copy of '
                + package + '-' + version,
                '#',
                '#	automatically created by Gentoo\'s webapp-config',
                '#	do NOT edit this file by hand',
                '',]
        for i in self.__tokens:
            info.append(i + '="' + self.__data[i] + '"')

        if not self.__p:
            try:

                fd = os.open(self.__dot_config(),
                             os.O_WRONLY | os.O_CREAT,
                             self.__perm(0o600))

                os.write(fd, ('\n'.join(info)).encode('utf-8'))
                os.close(fd)

            except Exception as e:

                OUT.die('Unable to write to ' + self.__dot_config()
                        + '\nError was: ' + str(e))
        else:
            OUT.info('Would have written the following information into '
                     + self.__dot_config() + ':\n' + '\n'.join(info))

    def kill(self):
        ''' Remove the dot config file.'''

        empty = self.is_empty()

        OUT.debug('Trying to removing .webapp file', 7)

        if not empty:
            if not self.__p:
                try:
                    os.unlink(self.__dot_config())
                except:
                    OUT.warn('Failed to remove '
                             + self.__dot_config() + '!')
                    return False
            else:
                OUT.info('Would have removed ' + self.__dot_config())
            return True
        else:
            OUT.notice('--- ' + empty)
            return False
