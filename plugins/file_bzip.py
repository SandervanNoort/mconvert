#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""bzip a file"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import bz2
import os
import logging

ORIG = ":"
DEST = "application/bzip2", "application/bzip"
CONVERT = "file_bzip"
PRIORITY = -1
MULTI = False
ADD_EXTENSION = True

logger = logging.getLogger(__name__)


def file_bzip(orig, dest, **_kwargs):
    """Unpack zip"""
    if os.path.isdir(orig):
        logger.error("Not possible to bzip2 directory {0}".format(orig))
        return
    bz2obj = bz2.BZ2File(dest, "wb")
    with open(orig, "rb") as fobj:
        bz2obj.write(fobj.read())
    bz2obj.close()
    return dest
