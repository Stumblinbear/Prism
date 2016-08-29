# -*- coding: utf-8 -*-
#
# *****************************************************************************
# Copyright (c) 2016 by the authors, see LICENSE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Authors:
#   Trevin Miller <stumblinbear@gmail.com>
#
# ****************************************************************************

import sys

if sys.version_info < (3, 0):
    sys.stdout.write("Unable to start Prism. Python 3.x is required!\n")
    sys.exit(1)

import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import prism.daemon

if __name__ == "__main__":
    daemon = prism.daemon.Daemon()
    sys.exit(daemon.start(sys.argv))
