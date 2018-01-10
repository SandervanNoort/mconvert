#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Convert between figure types"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import gzip
import os
import logging
import io

ORIG = "application/gzip"
DEST = None
CONVERT = "gunzip"
PRIORITY = 0.5

logger = logging.getLogger(__name__)


def gunzip(orig, dest, *_args, **_kwargs):
    """Unpack zip"""
    fname, ext = os.path.splitext(orig)
    if dest is None:
        return [("0",
                 os.path.basename(fname),
                 None if ext.lower() != ".tgz" else {"application/tar"})]
    dirname = os.path.dirname(dest)
    gzipobj = gzip.GzipFile(orig, "r")
    fullname = os.path.join(dirname, os.path.basename(fname))
    with io.open(fullname, "wb") as fobj:
        fobj.write(gzipobj.read())
    return fullname
