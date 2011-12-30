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
webapp-config needs a permission handling that allows to combine original
file permission settings with values supplied by the user.
'''

__version__ = "$Id: permissions.py 129 2005-11-06 12:46:31Z wrobel $"

# ========================================================================
# Dependencies
# ------------------------------------------------------------------------

import re, types, grp, pwd

# ========================================================================
# Permission Helper
# ------------------------------------------------------------------------

# Mask

ALL     = 7
READ    = 4
WRITE   = 2
EXECUTE = 1

# Shifting

USER    = 6
GROUP   = 3
OTHER   = 0

class PermissionMap:
    ''' Permission Helper class that is initialized with a permission
    mask. Subsequently the class can be used to combine this mask
    with file permissions to generate a merged target value. '''

    # Describes valid permission masks

    valid = re.compile('^([ugoa]{1,4})([+-=])([rwx]{0,3})$')

    def __call__(self, permissions):
        ''' "permissions" represents the last 9 bits of the permission
        map as a normal integer (a value between 0 and 512).

        Test the simple case:

        >>> a = PermissionMap('0777')
        >>> a(0644)
        511
        >>> a(0000)
        511
        >>> a = PermissionMap('o+x')
        >>> a(0000)
        1
        >>> a = PermissionMap('ugo+rwx')
        >>> a(0000)
        511
        >>> a = PermissionMap('u=rwx,g=x,o=w')
        >>> a(0644)
        458
        >>> a = PermissionMap('u-rw,g=x,o+x')
        >>> a(0644)
        13
        >>> a = PermissionMap('u-rwx,g-rwx,o-x')
        >>> a(0751)
        0
        >>> a = PermissionMap('u=rw,g=r,o=')
        >>> a(0000)
        416
        '''

        # Check if the permissions are absolute

        if self.__absolute:
            return self.__permissions
        else:

            for i in self.__permissions:

                # Permission mask. More complex

                entity   = self.valid.match(i).group(1)
                operator = self.valid.match(i).group(2)
                perm     = self.valid.match(i).group(3)

                # Generate the permission bits

                perm_bit = 0

                for i in perm:
                    if i == 'r':
                        perm_bit |= READ
                    if i == 'w':
                        perm_bit |= WRITE
                    if i == 'x':
                        perm_bit |= EXECUTE

                for i in entity:
                    if i == 'u':
                        shift = [ USER  ]
                    if i == 'g':
                        shift = [ GROUP ]
                    if i == 'o':
                        shift = [ OTHER ]
                    if i == 'a':
                        shift = [ USER, GROUP, OTHER ]

                    for j in shift:
                        if operator == '=':
                            permissions &= ~(ALL << j)
                        if operator == '-':
                            permissions &= ~(perm_bit << j)
                        if operator == '+' or operator == '=':
                            permissions |= (perm_bit << j)

        return permissions

    def __init__(self, permissions):
        '''Check that the given permission map evaluates to something
        useful.

        "permissions" must be a string. It can either specify
        absolute permissions as an octal number or it uses the
        syntax for the unix chmod command (only
        [ugoa]{1,4}[+-=][rxw]{1,3} as a comma-seperated list).

        Check a few values:
        >>> a = PermissionMap('0777')

        >>> a = PermissionMap('0788')
        Traceback (most recent call last):
        ...
        Exception: Invalid permission string "0788"

        >>> a = PermissionMap('u+r, go-wx')

        >>> a = PermissionMap('u=+r,go-wx')
        Traceback (most recent call last):
        ...
        Exception: Invalid permission string "u=+r,go-wx"

        >>> a = PermissionMap('u=rw,g=r,o=')
        '''

        self.__permissions = 0

        # Simple case: absolute octal permission

        if re.compile('[0-7]{4}').match(permissions):
            self.__absolute    = True
            self.__permissions = eval(permissions)

        else:
            # Split on commas first

            splitted_permissions = [ x.strip()
                                     for x in permissions.split(',') ]

            # Now analyze each part for correct structure

            for i in splitted_permissions:
                if not self.valid.match(i):
                    raise Exception('Invalid permission string "'
                                    + permissions + '"')

            self.__permissions = splitted_permissions
            self.__absolute    = False

def get_group(group):
    '''
    Specify a group id either as integer, as string that can
    be transformed into an integer or a string that matches
    a group name.

    >>> get_group(0)
    0
    >>> get_group('0')
    0
    >>> get_group('root')
    0
    >>> get_group('does_not_exist')
    Traceback (most recent call last):
    ...
    KeyError: 'The given group "does_not_exist" does not exist!'
    '''

    gid = -1
    ngroup = -1

    # Can we transform the value to an integer?
    if type(group) != types.IntType:
        try:
            ngroup = int(group)
        except ValueError:
            ngroup = -1
    else:
        # The value is an integer
        ngroup = group

    # Value was specified as integer or was transformed
    if ngroup != -1:
        try:
            # Try to match the integer to a group id
            gid = grp.getgrgid(ngroup)[2]
        except KeyError:
            pass

    if gid == -1:
        # No success yet. Try to match to the group name
        try:
            gid = grp.getgrnam(str(group))[2]
        except KeyError:
            raise KeyError('The given group "' + str(group)
                           + '" does not exist!')

    return gid

def get_user(user):
    '''
    Specify a user id either as integer, as string that can
    be transformed into an integer or a string that matches
    a user name.

    >>> get_user(0)
    0
    >>> get_user('0')
    0
    >>> get_user('root')
    0
    >>> get_user('does_not_exist')
    Traceback (most recent call last):
    ...
    KeyError: 'The given user "does_not_exist" does not exist!'
    '''
    uid = -1
    nuser = -1

    # Can we transform the value to an integer?
    if type(user) != types.IntType:
        try:
            nuser = int(user)
        except ValueError:
            nuser = -1
    else:
        # The value is an integer
        nuser = user

    # Value was specified as integer or was transformed
    if nuser != -1:
        try:
            # Try to match the integer to a user id
            uid = pwd.getpwuid(nuser)[2]
        except KeyError:
            pass

    if uid == -1:
        # No success yet. Try to match to the user name
        try:
            uid = pwd.getpwnam(str(user))[2]
        except KeyError:
            raise KeyError('The given user "' + str(user)
                           + '" does not exist!')
    return uid

if __name__ == '__main__':
    import doctest, sys
    doctest.testmod(sys.modules[__name__])
