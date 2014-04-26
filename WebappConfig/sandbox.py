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
Sandbox operations
'''

# ========================================================================
# Dependencies
# ------------------------------------------------------------------------

import os, os.path, sys

# stolen from portage
try:
    import resource
    max_fd_limit = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
except ImportError:
    max_fd_limit = 256
if os.path.isdir("/proc/%i/fd" % os.getpid()):
    def get_open_fds():
        return (int(fd) for fd in os.listdir("/proc/%i/fd" % os.getpid()) if fd.isdigit())
else:
    def get_open_fds():
        return list(range(max_fd_limit))


class Sandbox:
    '''
    Basic class for handling sandbox stuff
    '''

    def __init__(self, config):

        self.config     = config
        self.__write    = ['g_installdir',
                           'g_htdocsdir',
                           'g_cgibindir',
                           'vhost_root']
        self.__syswrite = ':/dev/tty:/dev/pts:/dev/null:/tmp'

        self.sandbox_binary = '/usr/bin/sandbox'

        self.env      = {'SANDBOX_WRITE' : self.get_write() }

    def get_write(self):
        '''Return write paths.'''
        return ':'.join ( map ( self.get_config, self.__write ) ) \
                + self.__syswrite

    def get_config(self, option):
        ''' Return a config option.'''
        return self.config.config.get('USER', option)

    # stolen from portage
    def spawn(self, mycommand, full_env):
        """
        Spawns a given command.

        @param mycommand: the command to execute
        @type mycommand: String or List (Popen style list)
        @param full_env: A dict of Key=Value pairs for env variables
        @type full_env: Dictionary
        """

        # Default to propagating our stdin, stdout and stderr.
        fd_pipes = {0:0, 1:1, 2:2}

        # mypids will hold the pids of all processes created.
        mypids = []

        command = []
        command.append(self.sandbox_binary)
        command.append(mycommand)

        # merge full_env (w-c variables) with env (write path)
        self.env.update(full_env)
        for a in list(self.env.keys()):
            if not self.env[a]:
                self.env[a] = ''

        pid = os.fork()

        if not pid:
            try:
                self._exec(command, self.env, fd_pipes)
            except Exception as e:
                # We need to catch _any_ exception so that it doesn't
                # propagate out of this function and cause exiting
                # with anything other than os._exit()
                sys.stderr.write("%s:\n   %s\n" % (e, " ".join(command)))
                sys.stderr.flush()
                os._exit(1)

        # Add the pid to our list
        mypids.append(pid)

        # Clean up processes
        while mypids:

            # Pull the last reader in the pipe chain. If all processes
            # in the pipe are well behaved, it will die when the process
            # it is reading from dies.
            pid = mypids.pop(0)

            # and wait for it.
            retval = os.waitpid(pid, 0)[1]

            if retval:
                # If it failed, kill off anything else that
                # isn't dead yet.
                for pid in mypids:
                    if os.waitpid(pid, os.WNOHANG) == (0,0):
                        os.kill(pid, signal.SIGTERM)
                        os.waitpid(pid, 0)

                # If it got a signal, return the signal that was sent.
                if (retval & 0xff):
                    return ((retval & 0xff) << 8)

                # Otherwise, return its exit code.
                return (retval >> 8)

        # Everything succeeded
        return 0

    # stolen from portage
    def _exec(self, binary, env, fd_pipes):

        """
        Execute a given binary with options in a sandbox

        @param binary: Name of program to execute
        @type binary: String
        @param env: Key,Value mapping for Environmental Variables
        @type env: Dictionary
        @param fd_pipes: Mapping pipes to destination; { 0:0, 1:1, 2:2 }
        @type fd_pipes: Dictionary
        @rtype: None
        @returns: Never returns (calls os.execve)
        """

        # Set up the command's pipes.
        my_fds = {}
        # To protect from cases where direct assignment could
        # clobber needed fds ({1:2, 2:1}) we first dupe the fds
        # into unused fds.
        for fd in fd_pipes:
            my_fds[fd] = os.dup(fd_pipes[fd])
        # Then assign them to what they should be.
        for fd in my_fds:
            os.dup2(my_fds[fd], fd)
        # Then close _all_ fds that haven't been explictly
        # requested to be kept open.
        for fd in get_open_fds():
            if fd not in my_fds:
                try:
                    os.close(fd)
                except OSError:
                    pass

        # And switch to the new process.
        os.execve(binary[0], binary, env)
