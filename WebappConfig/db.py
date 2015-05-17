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
''' This module provides handlers for the web application database as
well as the database of virtual installs.  '''

# ========================================================================
# Dependencies
# ------------------------------------------------------------------------

import time, os, os.path, re

import WebappConfig.wrapper as wrapper

from WebappConfig.debug       import OUT
from WebappConfig.permissions import PermissionMap


# ========================================================================
# Reduced base class
# ------------------------------------------------------------------------

class AppHierarchy:
    '''
    This base class provides a few common classes shared between the db
    handler for /var/db/webapps and /usr/share/webapps.

    Doctests can be found in the derived classes.
    '''


    def __init__(self,
                 fs_root,
                 root,
                 category   = '',
                 package    = '',
                 version    = '',
                 dbfile     = 'installs'):

        self.__r        = fs_root
        self.root       = self.__r + root
        self.root       = re.compile('/+').sub('/', self.root)

        if not os.path.isdir(self.root):
            OUT.die('"' + self.root + '" specifies no directory! webapp'
                    '-config needs a valid directory to store/retrieve in'
                    'formation. Please correct your settings.')

        self.category   = category
        self.pn         = package
        self.pvr        = version
        self.dbfile     = dbfile

    def package_name(self):
        ''' Returns the package name in case the database has been initialized
        with a specific name and version.'''
        if self.category:
            return self.category + '/' + self.pn + '-' + self.pvr
        else:
            return self.pn + '-' + self.pvr

    def set_category(self, cat):
        ''' Set category name.'''
        self.category = cat

    def set_package(self, package):
        ''' Set the package name.'''
        self.pn = package

    def set_version(self, version):
        ''' Set the package version.'''
        self.pvr = version

    def approot(self):
        ''' Return the root directory of the package.'''
        if self.pn:
            result = self.root + '/' + self.category + '/' + self.pn
            return re.compile('/+').sub('/', result)

    def appdir(self):
        ''' Return specific package directory (name + version).'''
        if self.pvr and self.approot():
            result = self.approot() + '/' + self.pvr
            return re.compile('/+').sub('/', result)

    def appdb(self):
        ''' Return the complete path to the db file.'''
        if self.appdir():
            result = self.appdir() + '/' + self.dbfile
            return re.compile('/+').sub('/', result)

    def list_locations(self):
        ''' List all available db files.'''

        OUT.debug('Retrieving hierarchy locations', 6)

        dbpath = self.appdb()

        if dbpath and os.path.isfile(dbpath):
            return {dbpath : [ self.category, self.pn, self.pvr]}

        if dbpath and not os.path.isfile(dbpath):
            OUT.debug('Package "' + self.package_name()
                      + '" not listed in the hierarchy (file "'
                      + dbpath + ' is missing)!', 8)
            return {}

        locations = {}
        packages  = []

        if self.pn:
            packages.append(os.path.join(self.root, self.pn))
            if self.category:
                packages.append(os.path.join(self.root, self.category, self.pn))
        else:
            packages.extend(os.path.join(self.root, m) for m in os.listdir(self.root))
            for i in packages:
                if os.path.isdir(i):
                    packages.extend(os.path.join(i,m) for m in os.listdir(i))

        for i in packages:

            OUT.debug('Checking package', 8)

            if os.path.isdir(i):

                OUT.debug('Checking version', 8)

                versions = os.listdir(i)

                for j in versions:
                    appdir = os.path.join(i,j)
                    location = os.path.join( appdir, self.dbfile)
                    if (os.path.isdir(appdir) and
                        os.path.isfile(location)):
                            pn = os.path.basename(i)
                            cat = os.path.basename(os.path.split(i)[0])
                            if cat == "webapps":
                                cat = ""
                            locations[location] = [ cat, pn, j ]

        return locations

# ========================================================================
# Handler for /var/db/webapps
# ------------------------------------------------------------------------

class WebappDB(AppHierarchy):
    '''
    The DataBase class handles a file-oriented data base that stores
    information about virtual installs of web applications.
    '''

    def __init__(self,
                 fs_root    = '/',
                 root       = '/var/db/webapps',
                 category   = '',
                 package    = '',
                 version    = '',
                 installs   = 'installs',
                 dir_perm   = PermissionMap('0755'),
                 file_perm  = PermissionMap('0600'),
                 verbose    = False,
                 pretend    = False):

        AppHierarchy.__init__(self,
                              fs_root,
                              root,
                              category,
                              package,
                              version,
                              dbfile = installs)

        self.__dir_perm   = dir_perm
        self.__file_perm  = file_perm
        self.__v          = verbose
        self.__p          = pretend

    def remove(self, installdir):
        '''
        Remove a record from the list of virtual installs.

        installdir - the installation directory
        '''
        if not installdir:
            OUT.die('The installation directory must be specified!')

        dbpath = self.appdb()

        if not dbpath:
            OUT.die('No package specified!')

        if not os.access(dbpath, os.R_OK):
            OUT.warn('Unable to read the install database ' + dbpath)
            return

        # Read db file
        fdb = open(dbpath)
        entries = fdb.readlines()
        fdb.close()

        newentries = []
        found = False

        for i in entries:

            j = i.strip().split(' ')

            if j:

                if len(j) != 4:

                    # Remove invalid entry
                    OUT.warn('Invalid line "' + i.strip() + '" remo'
                             'ved from the database file!')
                elif j[3] != installdir:

                    OUT.debug('Keeping entry', 7)

                    # Keep valid entry
                    newentries.append(i.strip())

                elif j[3] == installdir:

                    # Remove entry, indicate found
                    found = True

        if not found:
            OUT.warn('Installation at "' +  installdir + '" could not be '
                     'found in the database file. Check the entries in "'
                     + dbpath + '"!')

        if not self.__p:
            installs = open(dbpath, 'w')
            installs.write('\n'.join(newentries) + '\n')
            installs.close()
            if not self.has_installs():
                os.unlink(dbpath)
        else:
            OUT.info('Pretended to remove installation ' + installdir)
            OUT.info('Final DB content:\n' + '\n'.join(newentries) + '\n')

    def add(self, installdir, user, group):
        '''
        Add a record to the list of virtual installs.

        installdir - the installation directory
        '''

        if not installdir:
            OUT.die('The installation directory must be specified!')

        if not str(user):
            OUT.die('Please specify a valid user!')

        if not str(group):
            OUT.die('Please specify a valid group!')

        OUT.debug('Adding install record', 6)

        dbpath = self.appdb()

        if not dbpath:
            OUT.die('No package specified!')

        if not self.__p and not os.path.isdir(os.path.dirname(dbpath)):
            os.makedirs(os.path.dirname(dbpath), self.__dir_perm(0o755))

        fd = None

        if not self.__p:
            fd = os.open(dbpath,
                         os.O_WRONLY | os.O_APPEND | os.O_CREAT,
                         self.__file_perm(0o600))

        entry = str(int(time.time())) + ' ' + str(user) + ' ' + str(group)\
            + ' ' + installdir + '\n'

        OUT.debug('New record', 7)

        if not self.__p:
            os.write(fd, (entry).encode('utf-8'))
            os.close(fd)
        else:
            OUT.info('Pretended to append installation ' + installdir)
            OUT.info('Entry:\n' + entry)


    def read_db(self):
        '''
        Returns the db content.
        '''

        files = self.list_locations()

        if not files:
            return {}

        result = {}

        for j in list(files.keys()):

            if files[j][0]:
                p = files[j][0] + '/' + files[j][1] + '-' + files[j][2]
            else:
                p = files[j][1] + '-' + files[j][2]

            add = []

            installs = open(j).readlines()

            for i in installs:
                if len(i.split(' ')) == 4:
                    add.append(i.split(' '))

            if add:
                result[p] = add

        return result

    def prune_database(self, action):
        '''
        Prunes the installs files to ensure no webapp
        is incorrectly listed as installed.
        '''

        loc = self.read_db()
        
        if not loc and self.__v:
            OUT.die('No virtual installs found!')

        files = self.list_locations()
        keys = sorted(loc)

        if action != 'clean':
            OUT.warn('This is a list of all outdated entries that would be removed: ')
        for j in keys:
            for i in loc[j]:
                appdir = i[3].strip()
                # We check to see if the webapp is installed.
                if not os.path.exists(appdir+'/.webapp-'+j):
                    if self.__v:
                       OUT.warn('No .webapp file found in dir: ')
                       OUT.warn(appdir)
                       OUT.warn('Assuming webapp is no longer installed.')
                       OUT.warn('Pruning entry from database.')
                    if action == 'clean':
                        for installs in list(files.keys()):
                            contents = open(installs).readlines()
                            new_entries = ''
                            for entry in contents:
                                # Grab all the other entries but the one that
                                # isn't installed.
                                if not re.search('.* ' + appdir +'\\n', entry):
                                    new_entries += entry
                            f = open(installs, 'w')
                            f.write(new_entries)
                            f.close()
                    else:
                        OUT.warn(appdir)

    def has_installs(self):
        ''' Return True in case there are any virtual install locations 
        listed in the db file '''
        if self.read_db():
            return True
        return False

    def listinstalls(self):
        '''
        Outputs a list of what has been installed so far.
        '''

        loc = self.read_db()

        if not loc and self.__v:
            OUT.die('No virtual installs found!')

        keys = sorted(loc)

        for j in keys:
            # The verbose output is meant to be readable for the user
            if self.__v:
                OUT.info('Installs for ' + '-'.join(j.split('/')), 4)

            for i in loc[j]:
                if self.__v:
                    # The verbose output is meant to be readable for
                    # the user
                    OUT.info('  ' + i[3].strip(), 1)
                else:
                    # This is a simplified form for the webapp.eclass
                    print(i[3].strip())

# ========================================================================
# Handler for /usr/share/webapps
# ------------------------------------------------------------------------

class WebappSource(AppHierarchy):
    '''
    The WebappSource class handles a web application hierarchy under
    /usr/share/webapps.
    '''

    def __init__(self,
                 fs_root    = '/',
                 root       = '/usr/share/webapps',
                 category   = '',
                 package    = '',
                 version    = '',
                 installed  = 'installed_by_webapp_eclass',
                 pm         = ''):

        AppHierarchy.__init__(self,
                              fs_root,
                              root,
                              category,
                              package,
                              version,
                              dbfile = installed)

        self.__types = None
        self.pm = pm

        # Ignore specific files from the install location
        self.ignore = []

    def read(self,
             config_owned  = 'config-files',
             server_owned  = 'server-owned-files',
             virtual_files = 'virtual',
             default_dirs  = 'default-owned'):
        '''
        Initialize the type cache.
        '''
        import WebappConfig.filetype

        server_files = []
        config_files = []

        if os.access(self.appdir() + '/' + config_owned, os.R_OK):
            flist = open(self.appdir() + '/' + config_owned)
            config_files = flist.readlines()

            OUT.debug('Identified config-protected files.', 7)

            flist.close()

        if os.access(self.appdir() + '/' + server_owned, os.R_OK):
            flist = open(self.appdir() + '/' + server_owned)
            server_files = flist.readlines()

            OUT.debug('Identified server-owned files.', 7)

            flist.close()

        self.__types = WebappConfig.filetype.FileType(config_files,
                                                      server_files,
                                                      virtual_files,
                                                      default_dirs)

    def filetype(self, filename):
        ''' Determine filetype for the given file.'''
        if self.__types:

            OUT.debug('Returning file type', 7)

            return self.__types.filetype(filename)

    def dirtype(self, directory):
        ''' Determine filetype for the given directory.'''
        if self.__types:

            OUT.debug('Returning directory type', 7)

            return self.__types.dirtype(directory)

    def source_exists(self, directory):
        '''
        Checks if the specified source directory exists within the
        application directory.
        '''
        if self.appdir() and os.path.isdir(self.appdir()
                                            + '/' + directory):
            return True
        return False

    def get_source_directories(self, directory):
        '''
        Lists the directories provided by the source directory
        'directory'
        '''
        dirs = []

        if self.source_exists(directory):
            source_dir = self.appdir() + '/' + directory
            dir_entries = os.listdir(source_dir)
            for i in dir_entries:
                if (not os.path.islink(source_dir + '/' + i)
                    and os.path.isdir(source_dir + '/' + i)):
                    dirs.append(i)

        # Support for ignoring entries. Currently only needed
        # to enable doctests in the subversion repository
        if self.ignore:
            dirs = [i for i in  dirs
                    if not i in self.ignore]

        dirs.sort()

        return dirs

    def get_source_files(self, directory):
        '''
        Lists the files provided by the source directory
        'directory'
        '''

        files = []

        if self.source_exists(directory):
            source_dir = self.appdir() + '/' + directory
            dir_entries = os.listdir(source_dir)
            for i in dir_entries:
                if (os.path.isfile(source_dir + '/' + i)
                    or os.path.islink(source_dir + '/' + i)):
                    files.append(i)

        # Support for ignoring files. Currently only needed
        # to enable doctests in the subversion repository
        if self.ignore:
            files = [i for i in  files
                    if not i in self.ignore]

        files.sort()

        return files

    def listunused(self, db):
        '''
        Outputs a list of what has not been installed so far
        '''

        packages = self.list_locations()

        if not packages:
            OUT.die('No packages found!')

        keys = sorted(packages)

        OUT.debug('Check for unused web applications', 7)

        for i in keys:

            db.set_category(packages[i][0])
            db.set_package (packages[i][1])
            db.set_version (packages[i][2])

            if not db.has_installs():
                if packages[i][0]:
                    OUT.notice(packages[i][0] + '/' + packages[i][1] + '-' + packages[i][2])
                else:
                    OUT.notice(packages[i][1] + '-' + packages[i][2])


    def packageavail(self):
        '''
        Check to see whether the given package has been installed or not.

        These checks are carried out by using wrapper.py to facilitate
        distribution independant handling of the task.

        Outputs:
            0       - on success
            1       - package not found
            2       - no package to find
            3       - package isn't webapp-config compatible          '
        '''

        OUT.debug('Verifying package ' + self.package_name(), 6)

        # package_installed() does not handle "/PN" correctly
        package = self.pn

        if self.category:
            package = self.category + '/' + self.pn

        # not using self.package_name() here as we don't need pvr
            return 1

        # unfortunately, just because a package has been installed, it
        # doesn't mean that the package itself is webapp-compatible
        #
        # we need to check that the package has an entry in the
        # application repository

        if not self.appdb():
            return 3
        else:
            return 0

    def reportpackageavail(self):
        '''
        This is a simple wrapper around packageavail() that outputs
        user-friendly error messages if an error occurs

        Cannot test the rest, do not want to die.
        '''

        OUT.info('Do we have ' + self.package_name() + ' available?')

        available = self.packageavail()

        if available == 0:
            OUT.info('  Yes, we do')
        if available == 1:
            OUT.die('  Please emerge ' + self.package_name() + ' first.')
        if available == 3:
            OUT.die('  ' + self.package_name() + ' is not compatible with '
                    'webapp-config.\nIf it should be, report this at '
                    + wrapper.bugs_link)
