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
''' This class handles the contents file of a virtual install
location.  This file records all files and directories of the
installation.  '''

# ========================================================================
# Dependencies
# ------------------------------------------------------------------------

import md5, re, os, os.path

from WebappConfig.debug       import OUT
from WebappConfig.permissions import PermissionMap

# ========================================================================
# Content handler
# ------------------------------------------------------------------------

class Contents:
    '''
    This class records the contents for virtual install locations.
    '''

#self.worker.get_config('g_perms_dotconfig')
    def __init__(self,
                 installdir,
                 category   = '',
                 package    = '',
                 version    = '',
                 permission = PermissionMap('0600'),
                 dbfile     = '.webapp',
                 verbose    = False,
                 pretend    = False,
                 root       = ''):

        self.__root       = root
        self.__re         = re.compile('/+')
        self.__installdir = installdir

        self.__cat        = category
        self.__pn         = package
        self.__pvr        = version
        self.__dbfile     = dbfile

        self.__perm = permission
        self.__v    = verbose
        self.__p    = pretend

        self.__content = {}

        # Ignore specific files while removing contents

        # Added "webapp-test" to the list of ignored files. This
        # type of file will be used to mark directories that should
        # be included into the distutils manifest.
        self.ignore = ['webapp_test']

    def package_name(self):
        ''' Return the package name for the virtual install.'''
        if self.__cat:
            # use _ instead of / because we don't want to create a directory
            return self.__cat + '_' + self.__pn + '-' + self.__pvr
        else:
            return self.__pn + '-' + self.__pvr

    def set_category(self, cat):
        ''' Set category name.'''
        self.__cat = cat

    def set_package(self, package):
        ''' Set the package name.'''
        self.__pn = package

    def set_version(self, version):
        ''' Set the package version.'''
        self.__pvr = version

    def appdb(self):
        ''' Return the full path to the contents file.'''
        return self.__installdir + '/' + self.__dbfile + '-' \
            + self.package_name()

    def db_print(self):
        ''' Print all enties of the contents file.'''
        entries = self.get_sorted_files()
        values = []
        for i in entries:
            # Fix relative entry
            s = self.__content[i]
            s[1] = str(int(s[1]))
            values.append(' '.join(s))
        OUT.notice('\n'.join(values))

    def check_installdir(self):
        if not os.path.isdir(self.__installdir) and not self.__p:
            OUT.die('"' + self.__installdir + '" specifies no directory! '
                    'webapp-config needs a valid directory to store/retri'
                    'eve information. Please correct your settings.')

    def kill(self):
        ''' Remove the contents file.'''
        if not self.__p:
            try:
                dbpath = self.appdb()
                self.check_installdir()
                os.unlink(dbpath)
                self.__content = {}
                return True
            except:
                OUT.warn('Failed to remove ' + self.appdb() + '!')
                return False
        else:
            OUT.info('Would have removed ' + self.appdb())
            return True

    def read(self):
        '''
        Reads the contents database.

        Some content files have been provided for test purposes:

        >>> import os.path
        >>> here = os.path.dirname(os.path.realpath(__file__))

        This one should succeed:

        >>> a = Contents(here + '/tests/testfiles/contents/',
        ...              package = 'test', version = '1.0')
        >>> a.read()
        >>> a.db_print()
        file 1 virtual util/icon_browser.php 1124612216 9ffb2ca9ccd2db656b97cd26a1b06010 
        file 1 config-owned inc/prefs.php 1124612215 ffae752dba7092cd2d1553d04a0f0045 
        file 1 virtual lib/prefs.php 1124612215 ffae752dba7092cd2d1553d04a0f0045 
        file 1 virtual signup.php 1124612220 dc838bc375b3d02dafc414f8e71a2aec 
        file 1 server-owned data.php 1117009618 0 
        sym 1 virtual test 1124612220 dc838bc375b3d02dafc414f8e71a2aec /I link / to a very / strange location
        dir 1 default-owned util 1117009618 0 
        dir 1 config-owned inc 1117009618 0 
        dir 1 default-owned lib 1117009618 0 
        dir 0 default-owned /var/www/localhost/cgi-bin 1124577741 0 
        dir 0 default-owned /var/www/localhost/error 1124577740 0 
        dir 0 default-owned /var/www/localhost/icons 1124577741 0 
        
        >>> a.get_directories() #doctest: +ELLIPSIS
        ['.../contents//util', '.../contents//inc', '.../contents//lib', '/var/www/localhost/cgi-bin', '/var/www/localhost/error', '/var/www/localhost/icons']

        This is a corrupted file that checks all fail safes:

        >>> OUT.color_off()
        >>> a = Contents(here + '/tests/testfiles/contents/',
        ...              package = 'test', version = '1.1')
        >>> a.read() #doctest: +ELLIPSIS
        * Invalid line in content file (dir 1 default-owned). Ignoring!
        * Content file .../tests/testfiles/contents//.webapp-test-1.1 has an invalid line:
        * dir 1 nobody-owned  1117009618 0
        * Invalid owner: nobody-owned
        * Invalid line in content file (dir 1 nobody-owned  1117009618 0). Ignoring!
        * Content file .../tests/testfiles/contents//.webapp-test-1.1 has an invalid line:
        * garbage 1 virtual  1124612215 ffae752dba7092cd2d1553d04a0f0045
        * Invalid file type: garbage
        * Invalid line in content file (garbage 1 virtual  1124612215 ffae752dba7092cd2d1553d04a0f0045). Ignoring!
        * Invalid line in content file (file 1 virtual). Ignoring!
        * Content file .../tests/testfiles/contents//.webapp-test-1.1 has an invalid line:
        * file 1 virtual 
        * Not enough entries.
        * Invalid line in content file (file 1 virtual ). Ignoring!
        * Content file .../tests/testfiles/contents//.webapp-test-1.1 has an invalid line:
        * file 31 config-owned  1124612215 ffae752dba7092cd2d1553d04a0f0045
        * Invalid relative flag: 31
        * Invalid line in content file (file 31 config-owned  1124612215 ffae752dba7092cd2d1553d04a0f0045). Ignoring!
        '''

        dbpath = self.appdb()

        if not dbpath or not os.access(dbpath, os.R_OK):
            OUT.die('Content file ' + dbpath + ' is missing or not accessibl'
                    'e!')

        content = open(dbpath).readlines()

        for i in content:

            i = i.strip()

            rfn = re.compile('"(.*)"')
            rfs = rfn.search(i)
            if not rfs:
                ok = False
            else:
                fn  = rfs.group(1)
                i   = rfn.sub('', i)
                line_split = i.split(' ')
                line_split[3] = fn

                OUT.debug('Adding content line', 10)

                ok = True

                if len(line_split) < 6:
                    ok = False
                    OUT.warn('Content file ' + dbpath + ' has an invalid line'
                             ':\n' + i + '\nNot enough entries.')

                if ok and not line_split[0] in ['file', 'sym', 'dir']:
                    ok = False
                    OUT.warn('Content file ' + dbpath + ' has an invalid line'
                             ':\n' + i + '\nInvalid file type: '
                             + line_split[0])

                if ok and not line_split[1] in ['0', '1']:
                    ok = False
                    OUT.warn('Content file ' + dbpath + ' has an invalid line'
                             ':\n' + i + '\nInvalid relative flag: '
                             + line_split[1])

                if ok and not line_split[2] in ['virtual',
                                                'server-owned',
                                                'config-owned',
                                                'default-owned',
                                                'config-server-owned',
                                                # Still need that in case an 
                                                # application was installed
                                                # with w-c-1.11
                                                'root-owned']:
                    ok = False
                    OUT.warn('Content file ' + dbpath + ' has an invalid line'
                             ':\n' + i + '\nInvalid owner: '
                             + line_split[2])

                if ok and line_split[0] == 'sym' and len(line_split) == 6:
                    OUT.warn('Content file ' + dbpath + ' has an invalid line'
                             ':\n' + i + '\nMissing link target! ')

                if len(line_split) == 6:
                    line_split.append('')

                # I think this could happen if the link target contains
                # spaces
                # -- wrobel
                if len(line_split) > 7:
                    line_split = line_split[0:6]                         \
                                 + [' '.join(line_split[6:])]

            if ok:
                if line_split[1] == '0':
                    self.__content[line_split[3]] = line_split
                else:
                    self.__content[self.__installdir + '/'
                                   + line_split[3]] = line_split

            else:
                OUT.warn('Invalid line in content file (' + i + '). Ignor'
                         'ing!')

    def write(self):
        '''
        Write the contents file.

        A short test:

        >>> import os.path
        >>> here = os.path.dirname(os.path.realpath(__file__))
        >>> a = Contents(here + '/tests/testfiles/contents/',
        ...              package = 'test', version = '1.0',
        ...              pretend = True)
        >>> a.read()
        >>> OUT.color_off()
        >>> a.write() #doctest: +ELLIPSIS
        * Would have written content file .../tests/testfiles/contents//.webapp-test-1.0!
        '''

        dbpath = self.appdb()

        if not dbpath:
            OUT.die('No package specified!')

        self.check_installdir()

        values = [' '.join(i) for i in self.__content.values()]

        if not self.__p:
            try:
                fd = os.open(self.appdb(), os.O_WRONLY | os.O_CREAT,
                             self.__perm(0o600))

                os.write(fd, '\n'.join(values))

                os.close(fd)
            except Exception as e:
                OUT.warn('Failed to write content file ' + dbpath + '!\n' 
                         + 'Error was: ' + str(e))
        else:
            OUT.info('Would have written content file ' + dbpath + '!')

    def delete(self, entry):
        '''
        Delete a database entry.
        '''
        del self.__content[entry]

    def add(self,
            dsttype,
            ctype,
            destination,
            path,
            real_path,
            relative = True):
        '''
        Add an entry to the contents file.

        Just like Portage, when we install an app, we create a contents
        file to say what we installed and when.  We use this contents
        file to help us safely remove & upgrade apps.

        CONTENTS file format:

        <what> <rel> <type> <filename> <timestamp> <sum> [<optional>]

        where

        <what>      is one of dir|sym|file|hardlink

        <rel>       is 1 for relative filenames, 0 for absolute
                        filenames

        <type>      is one of
                        server-owned|default-owned|config-owned|virtual

        <timestamp> is the timestamp when the file was installed

        <sum>       is the md5sum of the file
                        (this is 0 for directories and symlinks)

        <filename>      is the actual name of the file we have installed

        <optional>      is additional data that depends upon <what>

        NOTE:
            Filenames used to be on the end of the line.  This made
                the old bash version more complicated, and
                prone to failure. So I have moved the filename into the
                middle of the line. -- Stuart

        Portage uses absolute names for its files, dirs, and symlinks.
        We do not.
        In theory, you can move a directory containing a web-based app,
        and

        a) the app itself will not break, and
        b) webapp-config will still work on that directory
           for upgrades and cleans.

        Position-independence *is* a design constraint that all future
        changes to this script need to honour.

        Inputs:

          dsttype     - type to add (one of dir|sym|file|hardlink)
          ctype       - internal webapp-config type
                      - (server-owned | config-owned | virtual)
          destination - install dir (normally $G_INSTALLDIR)
          path        - filename inside 'destination'
          real_path   - for config-protected files realpath =! path
                        (and this is important for md5)
          relative    - 1 for storing a relative filename, 0 otherwise

        >>> OUT.color_off()
        >>> import os.path
        >>> here = os.path.dirname(os.path.realpath(__file__))

        One for pretending:

        >>> a = Contents(here + '/tests/testfiles/contents/app/',
        ...              package = 'test', version = '1.0',
        ...              pretend = True)

        And this one is for real:

        >>> b = Contents(here + '/tests/testfiles/contents/app/',
        ...              package = 'test', version = '1.0')

        Pretend to add a file:

        >>> a.add('file', 'config-owned',
        ...       destination = here + '/tests/testfiles/contents/app/',
        ...       path = '/test1', relative = True)
        *     pretending to add: file 1 config-owned "test1"

        Lets not pretend this time:

        >>> b.add('file', 'config-owned',
        ...       destination = here + '/tests/testfiles/contents/app/',
        ...       path = '/test1', relative = True)
        >>> b.entry(here + '/tests/testfiles/contents/app/test1') #doctest: +ELLIPSIS
        'file 1 config-owned "test1" ... d8e8fca2dc0f896fd7cb4cb0031ba249 '

        Lets produce an error with a file that does not exist:

        >>> b.add('file', 'config-owned',
        ...       destination = here + '/tests/testfiles/contents/app/',
        ...       path = '/nothere', relative = True) #doctest: +ELLIPSIS
        * Cannot access file .../tests/testfiles/contents/app/nothere to add it as installation content. This should not happen!

        Other file types:

        >>> b.add('hardlink', 'config-owned',
        ...       destination = here + '/tests/testfiles/contents/app/',
        ...       path = '/test2', relative = True)
        >>> b.entry(here + '/tests/testfiles/contents/app/test2') #doctest: +ELLIPSIS
        'file 1 config-owned "test2" ... d8e8fca2dc0f896fd7cb4cb0031ba249 '
        >>> b.add('dir', 'default-owned',
        ...       destination = here + '/tests/testfiles/contents/app/',
        ...       path = '/dir1', relative = True)
        >>> b.entry(here + '/tests/testfiles/contents/app/dir1') #doctest: +ELLIPSIS
        'dir 1 default-owned "dir1" ... 0 '
        >>> b.add('dir', 'default-owned', destination = here + '/tests/testfiles/contents/app',
        ...       path = '/dir1',
        ...       relative = False)
        >>> b.entry(here + '/tests/testfiles/contents/app/dir1') #doctest: +ELLIPSIS
        'dir 0 default-owned ".../tests/testfiles/contents/app/dir1" ... 0 '

        Q: Is the full link to the target what we want?
        A: Yes, since the link will still be ok even if we move the directory.

        >>> b.add('sym', 'virtual',
        ...       destination = here + '/tests/testfiles/contents/app/',
        ...       path = '/test3', relative = True)
        >>> b.entry(here + '/tests/testfiles/contents/app/test3') #doctest: +ELLIPSIS
        'sym 1 virtual "test3" ... 0 .../tests/testfiles/contents/app/test1'

        >>> b.db_print() #doctest: +ELLIPSIS
        file 1 config-owned "test1" ... d8e8fca2dc0f896fd7cb4cb0031ba249 
        file 1 config-owned "test2" ... d8e8fca2dc0f896fd7cb4cb0031ba249 
        sym 1 virtual "test3" ... 0 .../tests/testfiles/contents/app/test1
        dir 0 default-owned ".../tests/testfiles/contents/app/dir1" ... 0 

        '''

        OUT.debug('Adding entry to content dictionary', 6)

        # Build the full path that we use as index in the contents list
        while path[0] == '/':
            path = path[1:]
        while destination[-1] == '/':
            destination = destination[:-1]

        entry = destination + '/' + path

        # special case - we don't add entries for '.'

        if os.path.basename(entry) == '.':
            return

        if (not self.__p
                and not os.path.islink(entry)
                and (not os.path.exists(entry)
                    or not os.access(entry, os.R_OK))):
            OUT.warn('Cannot access file ' + entry + ' to add it as'
                     ' installation content. This should not happen!')
            return

        allowed_types = {
            'file'    : [ 'file', self.file_md5,  self.file_null ],
            'hardlink': [ 'file', self.file_md5,  self.file_null ],
            'dir'     : [  'dir', self.file_zero, self.file_null ],
            'sym'     : [  'sym', self.file_zero, self.file_link ],
            }

        if not dsttype in allowed_types.keys():
            OUT.die('Oops, webapp-config bug. "dsttype" is ' + dsttype)

        # Generate handler for file attributes
        a = allowed_types[dsttype]

        # For absolute entries the path must match the entry
        if not relative:
            path = entry

        OUT.debug('Adding entry', 7)

        # report if pretending
        if self.__p:

            OUT.info('    pretending to add: ' +
                     ' '.join([dsttype,
                               str(int(relative)),
                               ctype,
                               '"' + path + '"']))
        else:

            # Only the path is enclosed in quotes, NOT the link targets
            self.__content[entry] = [ a[0],
                                      str(int(relative)),
                                      ctype,
                                      '"' + path + '"',
                                      self.file_time(entry),
                                      a[1](real_path),
                                      a[2](entry)]

            if self.__v:
                msg = path
                if msg[0] == "/":
                    msg = self.__root + msg
                    msg = self.__re.sub('/', msg)
                OUT.notice('>>> ' + a[0] + ' ' * (4 - len(a[0])) + ' ('  \
                           + ctype + ') ' + msg)


    def file_zero(self, filename):
        ''' Just return a zero value.'''
        return '0'

    def file_null(self, filename):
        ''' Just return an empty value.'''
        return ''

    def file_md5(self, filename):
        ''' Return the md5 hash for the file content.'''
        return str(md5.md5(open(filename).read()).hexdigest())

    def file_time(self, filename):
        ''' Return the last modification time.'''
        if os.path.islink(filename):
            return str(os.lstat(filename)[8])
        else:
            return str(os.stat(filename)[8])

    def file_link(self, filename):
        ''' Return the path of the link target.'''
        return os.path.realpath(filename)

    def get_sorted_files(self):
        ''' Get a list of files. This is returned as a list sorted according
        to length, so that files lower in the hierarchy can be removed
        first.'''
        installed = self.__content.keys()
        return sorted(installed, key=lambda x: (-len(x), x))

    def get_directories(self):
        ''' Get only the directories as a sorted list.'''
        return [i
                for i in self.get_sorted_files()
                if self.__content[i][0] == 'dir']

    def get_files(self):
        ''' Get only files as a sorted list.'''
        return [i
                for i in self.get_sorted_files()
                if self.__content[i][0] in ['sym', 'file']]


    def get_canremove(self, entry):
        '''
        Determines if an entry can be removed.

        Returns a string if the entry may not be removed. The
        string will describe the reason why the entry should
        not be removed.

        In case the entry can be removed nothing will be
        returned.

        >>> import os.path
        >>> here = os.path.dirname(os.path.realpath(__file__))

        Trying to remove the contents:

        >>> a = Contents(here + '/tests/testfiles/contents/app/',
        ...              package = 'test', version = '1.0')
        >>> a.read()
        >>> a.ignore += ['.svn']
        >>> for i in a.get_directories():
        ...     a.get_canremove(i)
        '!dir test7'
        '!empty dir1'

        >>> for i in a.get_files():
        ...     a.get_canremove(i)
        '!time test2'
        '!time test4'
        '!found test6'
        '!sym dir3'
        '!file dir4'

        # Disabled 
        #'!target test3'

        '''

        OUT.debug('Checking if the file can be removed', 6)

        # Path not found.
        # Cannot remove -> return False
        if not os.path.exists(entry) and not os.path.islink(entry):

            OUT.debug('Did not find the file.', 7)

            return '!found ' + self.epath(entry)

        entry_type = self.etype(entry)

        if entry_type == 'sym':
            # Should be a link but is not.
            if not os.path.islink(entry):
                return '!sym ' + self.epath(entry)

            # Expected link location does not match with
            # current target.
            # this results in leaving broken symlinks behind
            # if self.file_link(entry) != self.etarget(entry):
            #     return '!target ' + self.epath(entry)

        if entry_type == 'file':

            # Expected file, path is not a file
            if not os.path.isfile(entry):
                return '!file ' + self.epath(entry)

            # This is config protected. Do not remove!
            #if self.eowner(entry)[0:6] == 'config':
            #    return '!cfgpro ' + self.epath(entry)

            # Modification time does not match. Refuse to remove.
            if self.file_time(entry) != self.etime(entry):
                return '!time ' + self.epath(entry)

            # Content has different hash. Do not remove.
            if self.file_md5(entry) != self.emd5(entry):
                return '!sum ' + self.epath(entry)

        if entry_type == 'dir':

            # Expected directory, path is not a directory.
            if not os.path.isdir(entry):
                return '!dir ' + self.epath(entry)

            # the rules are simple
            #
            # if the directory is empty, it can go
            # if the directory is not empty, it cannot go

            # get a directory listing

            entry_list = os.listdir(entry)

            # Support for ignoring file. Currently only needed
            # to enable doctests in the subversion repository
            if self.ignore:
                entry_list = [i for i in  entry_list
                              if not i in self.ignore]

            OUT.debug('Remaining files', 7)

            # Directory not empty
            # Cannot remove -> return False
            if entry_list:
                return '!empty ' + self.epath(entry)

        # All checks passed? Remove!

    def entry(self, entry):
        ''' Return a complete entry.'''
        if entry in self.__content.keys():
            return ' '.join(self.__content[entry])
        else:
            raise Exception('Unknown file "' + entry + '"')

    def etype(self, entry):
        '''
        Returns the entry type.
        '''
        if entry in self.__content.keys():
            return self.__content[entry][0]
        else:
            raise Exception('Unknown file "' + entry + '"')

    def erelative(self, entry):
        '''
        Returns if the entry is relative or not.
        '''
        if entry in self.__content.keys():
            return bool(int(self.__content[entry][1]))
        else:
            raise Exception('Unknown file "' + entry + '"')

    def eowner(self, entry):
        '''
        Returns the owner of the entry.
        '''
        if entry in self.__content.keys():
            return self.__content[entry][2]
        else:
            raise Exception('Unknown file "' + entry + '"')

    def epath(self, entry):
        '''
        Returns the (possibly relative) path of the entry.
        '''
        if entry in self.__content.keys():
            msg = self.__content[entry][3]
            if msg[0] == "/":
                msg = self.__root + msg
                msg = self.__re.sub('/', msg)
            return msg
        else:
            raise Exception('Unknown file "' + entry + '"')

    def etime(self, entry):
        '''
        Returns the recorded modification time of the entry.
        '''
        if entry in self.__content.keys():
            return self.__content[entry][4]
        else:
            raise Exception('Unknown file "' + entry + '"')

    def emd5(self, entry):
        '''
        Returns the recorded md5 hash of the entry.
        '''
        if entry in self.__content.keys():
            return self.__content[entry][5]
        else:
            raise Exception('Unknown file "' + entry + '"')

    def etarget(self, entry):
        '''
        Returns the recorded target of the link.
        '''
        if entry in self.__content.keys():
            return self.__content[entry][6]
        else:
            raise Exception('Unknown file "' + entry + '"')

if __name__ == '__main__':
    import doctest, sys
    doctest.testmod(sys.modules[__name__])
