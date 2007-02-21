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
''' A class that returns the file type for a given path.'''

__version__ = "$Id: filetype.py 245 2006-01-13 16:57:29Z wrobel $"

# ========================================================================
# Dependencies
# ------------------------------------------------------------------------

import os.path, re

from WebappConfig.debug     import OUT

# ========================================================================
# Handler for File Types
# ------------------------------------------------------------------------

class FileType:
    '''
    A helper class to determine file and directory types.

    The file type is determined based on two initial lists:

    - a list of all files and directories owned by the config user
    - a list of all files and directories owned by the server user

    This creates such lists:

    >>> config_owned = [ 'a', 'a/b/c/d', '/e', '/f/', '/g/h/', 'i\\n']
    >>> server_owned = [ 'j', 'k/l/m/n', '/o', '/p/', '/q/r/', 's\\n']

    The class is initialized with these two arrays:

    >>> a = FileType(config_owned, server_owned)

    This class provides three functions to retrieve information about
    the file or directory type.

    File types
    ----------

    >>> a.filetype('a')
    'config-owned'
    >>> a.filetype('a/b/c/d')
    'config-owned'

    >>> a.filetype('j')
    'server-owned'
    >>> a.filetype('/o')
    'server-owned'

    File names - whether specified as input in the
    {config,server}_owned lists or as key for retrieving the type - may
    have leading or trailing whitespace. It will be removed. Trailing

    >>> a.filetype('\\n s')
    'server-owned'
    >>> a.filetype('/g/h\\n')
    'config-owned'

    Unspecified files will result in a virtual type:

    >>> a.filetype('unspecified.txt')
    'virtual'

    This behaviour can be influenced by setting the 'virtual_files'
    option for the class (which corresponds to the --virtual-files command
    line option):

    >>> b = FileType(config_owned, server_owned,
    ...              virtual_files = 'server-owned')
    >>> b.filetype('unspecified.txt')
    'server-owned'

    Directory types
    ---------------

    The class does not know if the given keys are files or directories.
    This is specified using the correct function for them. So the same
    keys that were used above can also be used here:

    >>> a.dirtype('a')
    'config-owned'
    >>> a.dirtype('j')
    'server-owned'

    The same whitespace and trailing slash fixing rules apply for
    directory names:

    >>> a.dirtype('\\n s')
    'server-owned'
    >>> a.dirtype('/g/h\\n')
    'config-owned'

    Unspecified directories are 'default-owned' and not marked 'virtual':

    >>> a.dirtype('unspecified.txt')
    'default-owned'

    '''

    def __init__(self,
                 config_owned,
                 server_owned,
                 virtual_files = 'virtual',
                 default_dirs  = 'default-owned'):
        '''
        Populates the cache with the file types as provided by the
        ebuild.
        '''

        self.__cache = {}

        # Validity of entries are checked by the command line parser
        self.__virtual_files = virtual_files
        self.__default_dirs  = default_dirs

        # populate cache
        for i in config_owned:

            OUT.debug('Adding config-owned file', 8)

            self.__cache[self.__fix(i)] = 'config-owned'

        for i in server_owned:

            if self.__fix(i) in self.__cache.keys():

                OUT.debug('Adding config-server-owned file', 8)

                self.__cache[self.__fix(i).strip()] = 'config-server-owned'

            else:

                OUT.debug('Adding server-owned file', 8)

                self.__cache[self.__fix(i).strip()] = 'server-owned'


    def filetype(self, filename):
        '''
        Inputs:

          filename      - the file that we need a decision about

        returns one of these:

          server-owned  - file needs to be owned by the webserver user
                          (and needs to be a local copy)
          config-owned  - file needs to be owned by the config user
                          (and needs to be a local copy)
          virtual       - we do not need a local copy of the file

        NOTE:
          Use get_dirtype(directory) for directories

        NOTE:
          the user can use --virtual-files on the command-line to change
          what type virtual files are really reported as
        '''

        # remove any whitespace and trailing /
        filename = self.__fix(filename)

        # look for config-protected files in the cache
        if filename in self.__cache.keys():
            return self.__cache[filename]

        # unspecified file (and thus virtual)
        return self.__virtual_files

    def dirtype(self, directory):
        '''
        Inputs:

          directory     - the directory that we need a decision about

        returns one of these:

          server-owned  - dir needs to be owned by the webserver user
          config-owned  - dir needs to be owned by the config user
          default-owned - we need a local copy, owned by root

        NOTE:
          Use get_filetype(filename) for files

        NOTE:
          the user can use --default-dirs on the command-line to change
          what type default directories are really reported as
        '''

        # remove any whitespace and trailing /
        directory = self.__fix(directory)

        # check the cache
        if directory in self.__cache.keys():
            return self.__cache[directory]

        # unspecified directories are default-owned
        return self.__default_dirs

    def __fix(self, filename):
        ''' Removes trailing slash and whitespace from a path '''
        filename = filename.strip()
        while filename[-1] == '/':
            filename = filename[:-1]

        # Fix double slashes
        filename = re.compile('/+').sub('/', filename) 

        return filename


if __name__ == '__main__':
    import doctest, sys
    doctest.testmod(sys.modules[__name__])
