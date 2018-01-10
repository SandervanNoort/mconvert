#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""gzip a file"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import gzip
import os
import logging

ORIG = ":"
DEST = "application/gzip"
CONVERT = "file_gzip"
PRIORITY = -1
MULTI = False
ADD_EXTENSION = True

logger = logging.getLogger(__name__)


def file_gzip(orig, dest, **_kwargs):
    """Unpack zip"""
    if os.path.isdir(orig):
        logger.error("Not possible to gzip directory {0}".format(orig))
        return
    gzipobj = gzip.GzipFile(dest, "wb")
    with open(orig, "rb") as fobj:
        gzipobj.write(fobj.read())
    gzipobj.close()
    return dest
