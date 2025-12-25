#!/usr/bin/env python

import sys
import setuptools

# this affects the names of all the directories we do stuff with
sys.path.insert(0, './')
from WebappConfig.version import WCVERSION

def get_version():
      return WCVERSION

setuptools.setup(
      name          = 'webapp-config',
      version       = get_version(),
)
