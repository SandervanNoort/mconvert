#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Convert between figure types"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import bz2
import os
import logging
import io

ORIG = "application/bzip2", "application/bzip"
DEST = None
CONVERT = "bunzip2"
PRIORITY = 0.5
logger = logging.getLogger(__name__)


def bunzip2(orig, dest, *_args, **_kwargs):
    """Unpack zip"""
    fname, ext = os.path.splitext(orig)
    if dest is None:
        if ext.lower() not in (".bz", ".bz2"):
            logger.debug("Gzip file {0} not ending with .gz".format(orig))
        return [("0", os.path.basename(fname), None)]
    dirname = os.path.dirname(dest)
    bz2obj = bz2.BZ2File(orig, "r")
    fullname = os.path.join(dirname, os.path.basename(fname))
    with io.open(fullname, "wb") as fobj:
        fobj.write(bz2obj.read())
    return fullname
