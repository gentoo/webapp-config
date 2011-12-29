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

# ========================================================================
# Dependencies
# ------------------------------------------------------------------------

import sys, os, os.path, re

from WebappConfig.debug        import OUT
from WebappConfig.worker       import WebappRemove, WebappAdd
from WebappConfig.permissions  import get_group, get_user

from WebappConfig.wrapper      import package_installed

# ========================================================================
# Server classes
# ------------------------------------------------------------------------

class Basic:

    name   = 'Basic Server'
    desc   = 'supports installation on all webservers'
    dep    = ''

    def set_server_user(self):
        self.vhost_server_uid = get_user(0)
        self.vhost_server_gid = get_group(0)

    def __init__(self,
                 directories,
                 permissions,
                 handler,
                 flags,
                 pm):

        if self.dep and not self.supported(pm):
            print self.dep
            OUT.die('Your configuration file sets the server type "' + self.name
                    + '"\nbut the corresponding package does not seem to be '
                    'installed!\nPlease "emerge ' + self.dep + '" or correct '
                    'your settings.')

        try:
            self.set_server_user()
        except KeyError, e:
            OUT.die('The user for the server type "' + self.name
                    + '" does not exist!')

        self.__sourced   = directories['source']
        self.__destd     = directories['destination']
        self.__hostroot  = directories['hostroot']
        self.__vhostroot = directories['vhostroot']

        # + server owned
        permissions['file']['server-owned'][0] = self.vhost_server_uid
        permissions['file']['server-owned'][1] = self.vhost_server_gid
        permissions['dir']['server-owned'][0]  = self.vhost_server_uid
        permissions['dir']['server-owned'][1]  = self.vhost_server_gid
        # and config owned directories have server gid
        permissions['dir']['config-owned'][1]  = self.vhost_server_gid
        # allows server and config owned
        permissions['file']['config-server-owned'][1] = self.vhost_server_gid
        permissions['dir']['config-server-owned'][1]  = self.vhost_server_gid

        self.__perm      = permissions
        self.__handler   = handler
        self.__flags     = flags

        self.__ws        = handler['source']
        self.__content   = handler['content']
        self.__protect   = handler['protect']
        self.__dotconfig = handler['dotconfig']
        self.__ebuild    = handler['ebuild']
        self.__db        = handler['db']

        self.__v         = flags['verbose']
        self.__p         = flags['pretend']

        wd = WebappRemove(self.__content,
                          self.__v,
                          self.__p)

        handler['removal'] = wd

        self.__del       = wd

        # Set by the install function
        self.__add       = None


    def upgrade(self, new_category, new_package, new_version):

        # I have switched the order of upgrades
        # we are now removing the olde app and then installing the new one
        # I am not sure why it was the other way around before
        # and this way seems more intuitive and also has the benefit
        # of working -- rl03

        # first remove the older app

        OUT.info('Removing old version ' + self.__dotconfig.packagename())

        self.clean()

        # now install the new one
        self.__content.set_category(new_category)
        self.__content.set_version(new_version)
        self.__content.set_package(new_package)
        self.__db.set_category(new_category)
        self.__db.set_version(new_version)
        self.__db.set_package(new_package)

        self.install(True)

    def clean(self):

        self.file_behind_flag = False

        OUT.debug('Basic server clean', 7)

        self.file_behind_flag |= self.__del.remove_files()

        self.file_behind_flag |= self.__del.remove_dirs()

        OUT.info('Any files or directories listed above must be removed b'
                 'y hand')

        # okay, let's finish off
        #
        # we don't need the contents file anymore

        self.file_behind_flag |= not self.__content.kill()

        # right - we need to run the hook scripts now
        # if they fail, we don't actually care

        # run the hooks

        self.__ebuild.run_hooks('clean', self)

        # do we need the dotconfig file?
        #
        # if the .webapp file is the only one in the dir, we believe
        # that we can remove it

        self.__dotconfig.kill()

        # is the installation directory empty?

        if not os.listdir(self.__destd) and os.path.isdir(self.__destd):
            if not self.__p:
                os.rmdir(self.__destd)
        else:
            OUT.notice('--- ' + self.__destd)

        # update the list of installs

        self.__db.remove(self.__destd)

        # did we leave anything behind?

        if self.file_behind_flag:
            OUT.warn('Remove whatever is listed above by hand')


    def install(self, upgrade = False):

        self.config_protected_dirs = []

        OUT.debug('Basic server install', 7)

        # The root of the virtual install location needs to exist

        if not os.path.isdir(self.__destd) and not self.__p:

            OUT.debug('Directory missing', 7)

            dir = self.__destd
            dirs = []

            while dir != '/':
                dirs.insert(0, dir)
                dir = os.path.dirname(dir)

            a = self.__perm['dir']['install-owned'][2]('0755')
            OUT.debug('Strange')

            # Create the directories
            for i in dirs:
                if not os.path.isdir(i):
                    os.mkdir(i)
                    os.chmod(i, 
                             self.__perm['dir']['install-owned'][2]('0755'))
                    os.chown(i,
                             self.__perm['dir']['install-owned'][0],
                             self.__perm['dir']['install-owned'][1])

                if self.__v:
                    OUT.info('  Creating installation directory: '
                             + i)

        # Create the handler for installing

        self.__flags['relative'] = True

        wa = WebappAdd(self.__sourced,
                       self.__destd,
                       self.__perm,
                       self.__handler,
                       self.__flags)

        self.__add = wa

        OUT.info('Installing ' + self.__ws.package_name() + '...')

        # we need to create the directories to place our files in
        # and we need to copy in the files

        OUT.info('  Creating required directories', 1)
        OUT.info('  Linking in required files', 1)
        OUT.info('    This can take several minutes for larger apps', 1)

        self.__add.mkdirs()

        self.config_protected_dirs += self.__add.config_protected_dirs

        # Create the second handler for installing the root files

        self.__flags['relative'] = False

        wa = WebappAdd(self.__hostroot,
                       self.__vhostroot,
                       self.__perm,
                       self.__handler,
                       self.__flags)

        self.__add = wa

        self.__add.mkdirs()

        self.config_protected_dirs += self.__add.config_protected_dirs

        OUT.info('  Files and directories installed', 1)

        self.__dotconfig.write(self.__ws.category,
                               self.__ws.pn,
                               self.__ws.pvr,
                               self.__flags['host'],
                               self.__flags['orig'],
                               str(self.__perm['file']['config-owned'][0])
                               + ':' + str(self.__perm['file']['config-owned'][1]),)

        self.__db.add(self.__destd,
                      self.__perm['file']['config-owned'][0],
                      self.__perm['file']['config-owned'][1])

        # run the hooks

        self.__ebuild.run_hooks('install', self)

        # show the post-installation instructions

        if not upgrade:
            self.__ebuild.show_postinst(self)
        else:
            self.__ebuild.show_postupgrade(self)

        # to finish, we need to tell the user if they need to run
        # etc-update or not

        if self.config_protected_dirs:

            # work out whether this directory is part of the
            # CONFIG_PROTECT list or not

            self.__protect.how_to_update(self.config_protected_dirs)

        self.__content.write()

        # and we're done

        OUT.info('Install completed - success', 1)

    def supported(self, pm):
        # I don't think we should be forcing to have a webserver installed -- rl03
        # Maybe, but the test should then be disabled somewhere else.
        # Reverted back to the original version for now -- wrobel
        if self.dep and package_installed(self.dep, pm):
            return True
        return False

class Apache(Basic):

    name   = 'Apache'
    desc   = 'supports installation on Apache 1 & 2'
    dep    = '>=www-servers/apache-1.3'

    def set_server_user(self):
        self.vhost_server_uid = get_user('apache')
        self.vhost_server_gid = get_group('apache')

class Lighttpd(Basic):

    name   = 'Lighttpd'
    desc   = 'supports installation on lighttpd'
    dep    = 'www-servers/lighttpd'

    def set_server_user(self):
        self.vhost_server_uid = get_user('lighttpd')
        self.vhost_server_gid = get_group('lighttpd')

class Cherokee(Basic):

    name   = 'Cherokee'
    desc   = 'supports installation on Cherokee'
    dep    = 'www-servers/cherokee'

    def set_server_user(self):
        self.vhost_server_uid = get_user('cherokee')
        self.vhost_server_gid = get_group('cherokee')

def listservers():

    OUT.notice('\n'.join(['apache',
                          'lighttpd',
                          'cherokee']))
