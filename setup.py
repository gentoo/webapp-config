#!/usr/bin/env python

import sys

from distutils.core import setup

# this affects the names of all the directories we do stuff with
sys.path.insert(0, './')
from WebappConfig.version import WCVERSION


setup(name          = 'webapp-config',
      version       = WCVERSION,
      description   = 'Python script for managing the deployment of web-based applications',
      author        = 'Stuart Herbert, Renat Lumpau, Gunnar Wrobel',
      author_email  = 'stuart@gentoo.org',
      url           = 'http://svn.gnqs.org/projects/vhost-tools',
      packages      = ['WebappConfig'],
      scripts       = ['sbin/webapp-config', 'sbin/webapp-cleaner'],
      license       = 'GPL',
      )
