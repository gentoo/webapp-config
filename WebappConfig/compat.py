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

import  hashlib

def create_md5(filename):
<<<<<<< HEAD
    if hex(sys.hexversion) >= '0x3020000':
        filename = open(filename).read()
        encoded_file = filename.encode('utf8')
        return str(hashlib.md5(encoded_file).hexdigest())
    else:
        return str(hashlib.md5(open(filename).read()).hexdigest())
=======
    with open(filename, 'rb') as f:
        return str(hashlib.md5(f.read()).hexdigest())
>>>>>>> 04e9a55... WebappConfig/compat.py: Revamps create_md5() function.

