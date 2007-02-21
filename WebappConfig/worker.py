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
''' This module provides the classes for actually adding or removing
files of a virtual install location.  '''

__version__ = "$Id: worker.py 245 2006-01-13 16:57:29Z wrobel $"

# ========================================================================
# Dependencies
# ------------------------------------------------------------------------

import sys, os, os.path, shutil, stat, re

from WebappConfig.debug    import OUT
import WebappConfig.wrapper as wrapper

# ========================================================================
# Helper functions
# ------------------------------------------------------------------------

def all(boolean):
    ''' Replacement for reduce() '''
    for i in boolean:
        if not i:
            return False
    return True

# ========================================================================
# Worker class
# ------------------------------------------------------------------------

class WebappRemove:
    '''
    This is the handler for removal of web applications from their virtual
    install locations.

    For removal of files a content handler is sufficient:

    >>> OUT.color_off()
    >>> import os.path
    >>> here = os.path.dirname(os.path.realpath(__file__))
    >>> from WebappConfig.content import Contents
    >>> a = Contents(here + '/tests/testfiles/contents/app2',
    ...              package = 'test', version = '1.0', pretend = True)
    >>> a.read()
    >>> b = WebappRemove(a, True, True)

    # Pretend to remove files:

    # b.remove_files() #doctest: +ELLIPSIS

    # Deleted the test since this will almost certainly fail because
    # of the modification time.

    Deleted test for removal of directories. They are always reported as 'not
    empty' in case I am working in the subversion repository.
    '''

    def __init__(self,
                 content,
                 verbose,
                 pretend):

        self.__content = content
        self.__v       = verbose
        self.__p       = pretend

    def remove_dirs(self):
        '''
        It is time to remove the dirs that we installed originally.
        '''

        OUT.debug('Trying to remove directories', 6)

        success = [self.remove(i) for i in self.__content.get_directories()]

        # Tell the caller if anything was left behind

        return all(success)

    def remove_files(self):
        '''
        It is time to remove the files that we installed originally.
        '''

        OUT.debug('Trying to remove files', 6)

        success = [self.remove(i) for i in self.__content.get_files()]

        # Tell the caller if anything was left behind

        return all(success)

    def remove(self, entry):
        '''
        Decide whether to delete something - and then go ahead and do so

        Just like portage, we only remove files that have not changed
        from when we installed them.  If the timestamp or checksum is
        different, we leave the file in place.

        Inputs

          entry    - file/dir/sym to remove
        '''

        OUT.debug('Trying to remove file', 6)

        # okay, deal with the file | directory | symlink

        removeable = self.__content.get_canremove(entry)

        if not removeable:

            # Remove directory or file.

            # Report if we are only pretending
            if self.__p:
                OUT.info('    pretending to remove: ' + entry)

            # try to remove the entry
            try:
                entry_type = self.__content.etype(entry)
                if self.__content.etype(entry) == 'dir':
                    # its a directory -> rmdir
                    if not self.__p:
                        os.rmdir(entry)
                else:
                    # its a file -> unlink
                    if not self.__p:
                        os.unlink(entry)
            except:
                # Report if there is a problem
                OUT.notice('!!!      '
                           + self.__content.epath(entry))
                return

            if self.__v and not self.__p:
                # Report successful deletion

                OUT.notice('<<< ' + entry_type + ' '
                           * (5 - len(entry_type))
                           + self.__content.epath(entry))

            self.__content.delete(entry)

            return True

        else:

            OUT.notice(removeable)

            return False


class WebappAdd:
    '''
    This is the class that handles the actual transfer of files from
    the web application source directory to the virtual install location.

    The setup of the class is rather complex since a lot of different
    handlers are needed for the task.

    >>> OUT.color_off()
    >>> import os.path
    >>> here = os.path.dirname(os.path.realpath(__file__))

    The content handler points to the virtual install directory:

    >>> from WebappConfig.content import Contents
    >>> a = Contents(here + '/tests/testfiles/installtest', pretend = True)

    Removal of files will be necessary while upgrading :

    >>> b = WebappRemove(a, True, True)

    The handler for protected files is simple:

    >>> import WebappConfig.protect
    >>> c = WebappConfig.protect.Protection()

    And finally a fully initialized source is needed:

    >>> from WebappConfig.db import WebappSource
    >>> d = WebappSource(here + '/tests/testfiles/share-webapps',
    ...             'installtest', '1.0')
    >>> d.read()
    >>> d.ignore = ['.svn']

    >>> e = WebappAdd('htdocs',
    ...               here + '/tests/testfiles/installtest',
    ...               {'dir'  : {
    ...                          'default-owned': ('root', 'root', '0644'),
    ...                         },
    ...                'file' : {
    ...                          'virtual' : ('root', 'root', '0644'),
    ...                          'server-owned' : ('apache', 'apache', '0660'),
    ...                          'config-owned' : ('nobody', 'nobody', '0600'),
    ...                         }},
    ...               {'content': a,
    ...                'removal': b,
    ...                'protect': c,
    ...                'source' : d},
    ...               {'relative': 1,
    ...                'upgrade':  False,
    ...                'pretend':  True,
    ...                'verbose':  False,
    ...                'linktype': 'soft'})

    Installing a standard file:

    >>> e.mkfile('test1')
    *     pretending to add: sym 1 virtual "test1"
    >>> e.mkfile('test4')
    *     pretending to add: file 1 server-owned "test4"

    This location is already occupied. But since the file is not
    known, it will be deleted:

    >>> e.mkfile('test2') #doctest: +ELLIPSIS
    *     would have removed ".../tests/testfiles/installtest/test2" since it is in the way for the current install. It should not be present in that location!
    *     pretending to add: sym 1 virtual "test2"

    This location is also occupied but it it is a config protected
    file so it may not be removed:

    >>> e.mkfile('test3') #doctest: 
    ^o^ hiding test3
    *     pretending to add: file 1 config-owned "test3"
    
    >>> e.mkdir('dir1') 
    *     pretending to add: dir 1 default-owned "dir1"
    
    >>> e.mkdir('dir2') #doctest: +ELLIPSIS
    *     .../tests/testfiles/installtest/dir2 already exists, but is not a directory - removing
    *     pretending to add: dir 1 default-owned "dir2"

    And finally everything combined:

    >>> e.mkdirs('') #doctest: +ELLIPSIS
    *     Installing from .../tests/testfiles/share-webapps/installtest/1.0/htdocs/
    *     pretending to add: dir 1 default-owned "dir1"
    *     Installing from .../tests/testfiles/share-webapps/installtest/1.0/htdocs/dir1
    *     pretending to add: sym 1 virtual "dir1/webapp_test"
    *     .../tests/testfiles/installtest//dir2 already exists, but is not a directory - removing
    *     pretending to add: dir 1 default-owned "dir2"
    *     Installing from .../tests/testfiles/share-webapps/installtest/1.0/htdocs/dir2
    *     pretending to add: sym 1 virtual "dir2/webapp_test"
    *     pretending to add: sym 1 virtual "test1"
    *     would have removed ".../tests/testfiles/installtest//test2" since it is in the way for the current install. It should not be present in that location!
    *     pretending to add: sym 1 virtual "test2"
    ^o^ hiding /test3
    *     pretending to add: file 1 config-owned "test3"
    *     pretending to add: file 1 server-owned "test4"

    '''

    def __init__(self,
                 source,
                 destination,
                 permissions,
                 handler,
                 flags):

        self.__sourced   = source
        self.__destd     = destination
        self.__perm      = permissions
        self.__ws        = handler['source']
        self.__content   = handler['content']
        self.__remove    = handler['removal']
        self.__protect   = handler['protect']
        self.__link_type = flags['linktype']
        self.__relative  = flags['relative']
        self.__u         = flags['upgrade']
        self.__v         = flags['verbose']
        self.__p         = flags['pretend']

        self.config_protected_dirs = []

    def mkdirs(self, directory = ''):
        '''
        Create a set of directories

        Inputs

        directory   - the directory within the source hierarchy
        '''

        sd = self.__sourced + '/' + directory
        real_dir = re.compile('/+').sub('/',
                self.__ws.appdir()
                + '/' + self.__sourced
                + '/' + directory)

        OUT.debug('Creating directories', 6)

        if not self.__ws.source_exists(sd):

            OUT.warn(self.__ws.package_name()
                     + ' does not install any files from '
                     + real_dir + '; skipping')
            return

        OUT.info('    Installing from ' + real_dir)

        for i in self.__ws.get_source_directories(sd):

            OUT.debug('Handling directory', 7)

            # create directory first
            self.mkdir(directory + '/' + i)

            # then recurse into the directory
            self.mkdirs(directory + '/' + i)

        for i in self.__ws.get_source_files(sd):

            OUT.debug('Handling file', 7)

            # handle the file
            self.mkfile(directory + '/' + i)


    def mkdir(self, directory):
        '''
        Create a directory with the correct ownership and permissions.

        directory   - name of the directory
        '''
        src_dir = self.__sourced + '/' + directory
        dst_dir = self.__destd + '/' + directory

        OUT.debug('Creating directory', 6)

        # some special cases
        #
        # these should be triggered only if we are trying to install
        # a webapp into a directory that already has files and dirs
        # inside it

        if os.path.exists(dst_dir) and not os.path.isdir(dst_dir):
            # something already exists with the same name
            #
            # in theory, this should automatically remove symlinked
            # directories

            OUT.warn('    ' + dst_dir + ' already exists, but is not a di'
                     'rectory - removing')
            if not self.__p:
                os.unlink(dst_dir)

        dirtype = self.__ws.dirtype(src_dir)

        OUT.debug('Checked directory type', 8)

        (user, group, perm) = self.__perm['dir'][dirtype]

        dsttype = 'dir'

        if not os.path.isdir(dst_dir):

            OUT.debug('Creating directory', 8)

            if not self.__p:
                os.makedirs(dst_dir, perm(0755))

                os.chown(dst_dir,
                         user,
                         group)

        self.__content.add(dsttype,
                           dirtype,
                           self.__destd,
                           directory,
                           self.__relative)

    def mkfile(self, filename):
        '''
        This is what we are all about.  No more games - lets take a file
        from the master image of the web-based app, and make it available
        inside the install directory.

        filename    - name of the file

        '''

        OUT.debug('Creating file', 6)

        dst_name  = self.__destd + '/' + filename
        file_type = self.__ws.filetype(self.__sourced + '/' + filename)

        OUT.debug('File type determined', 7)

        # are we overwriting an existing file?

        OUT.debug('Check for existing file', 7)

        if os.path.exists(dst_name):

            OUT.debug('File in the way!', 7)

            my_canremove = True

            # o-oh - we're going to be overwriting something that already
            # exists

            # If we are upgrading, check if the file can be removed
            if self.__u:
                my_canremove = self.__remove.remove(self.__destd, filename)
            # Config protected file definitely cannot be removed
            elif file_type[0:6] == 'config':
                my_canremove = False

            if not my_canremove:
                # not able to remove the file
                #           or
                # file is config-protected

                dst_name = self.__protect.get_protectedname(self.__destd,
                                                            filename)
                OUT.notice('^o^ hiding ' + filename)
                self.config_protected_dirs.append(self.__destd + '/' 
                                                  + os.path.dirname(filename))

                OUT.debug('Hiding config protected file', 7)

            else:

                # it's a file we do not know about - so get rid
                # of it anyway
                #
                # this behaviour here *is* by popular request
                # personally, I'm not comfortable with it -- Stuart

                if not self.__p:
                    if os.path.isdir(dst_name):
                        os.rmdir(dst_name)
                    else:
                        os.unlink(dst_name)
                else:
                    OUT.info('    would have removed "' +  dst_name + '" s'
                             'ince it is in the way for the current instal'
                             'l. It should not be present in that location'
                             '!')


        # if we get here, we can get on with the business of making
        # the file available

        (user, group, perm) = self.__perm['file'][file_type]
        my_contenttype = ''

        src_name = self.__ws.appdir() + '/' + self.__sourced + '/' + filename

        # Fix the paths
        src_name = re.compile('/+').sub('/', src_name)
        dst_name = re.compile('/+').sub('/', dst_name)

        OUT.debug('Creating File', 7)

        # this is our default file type
        #
        # we link in (soft and hard links are supported)
        # if we're allowed to
        #
        # some applications (/me points at PHP scripts)
        # won't run if symlinked in.
        # so we now support copying files in too
        #
        # default behaviour is to hard link (if we can), and
        # to copy if we cannot
        #
        # if the user wants symlinks, then the user has to
        # use the new '--soft' option

        if file_type == 'virtual' or os.path.islink(src_name):

            if self.__link_type == 'soft':
                try:

                    OUT.debug('Trying to softlink', 8)

                    if not self.__p:
                        os.symlink(src_name, dst_name)

                    my_contenttype = 'sym'

                except Exception, e:

                    if self.__v:
                        OUT.warn('Failed to softlink (' + str(e) + ')')

            elif os.path.islink(src_name):
                try:

                    OUT.debug('Trying to copy symlink', 8)

                    if not self.__p:
                        os.symlink(os.readlink(src_name), dst_name)

                    my_contenttype = 'sym'

                except Exception, e:

                    if self.__v:
                        OUT.warn('Failed copy symlink (' + str(e) + ')')

            else:
                try:

                    OUT.debug('Trying to hardlink', 8)

                    if not self.__p:
                        os.link(src_name, dst_name)

                    my_contenttype = 'file'

                except Exception, e:

                    if self.__v:
                        OUT.warn('Failed to hardlink (' + str(e) + ')')

        if not my_contenttype:
            if not self.__p:
                shutil.copy(src_name, dst_name)
            my_contenttype = 'file'


        if not self.__p and not os.path.islink(src_name):

            old_perm =  os.stat(src_name)[stat.ST_MODE] & 511

            os.chown(dst_name,
                     user,
                     group)

            os.chmod(dst_name,
                     perm(old_perm))

        self.__content.add(my_contenttype,
                           file_type,
                           self.__destd,
                           filename,
                           self.__relative)


if __name__ == '__main__':
    import doctest, sys
    doctest.testmod(sys.modules[__name__])
