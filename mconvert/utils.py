#!/usr/bin/env python3
# -*-coding: utf-8-*-

"""Utils"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import re
import six
import os
import logging

from . import tools

logger = logging.getLogger(__name__)


def get_match(orig):
    """Function which determines if ftypes match the orig ftypes"""
    regex = [re.compile(forig[1:]) if forig.startswith(":") else
             forig
             for forig in tools.get_iter(orig)]

    def match(ftypes, regex=regex):
        """One of the ftypes matches"""
        for ftype in tools.get_iter(ftypes):
            for reg in regex:
                if isinstance(reg, six.string_types):
                    if reg == ftype:
                        return ftype
                else:
                    if reg.search(ftype):
                        return ftype
        return False
    return match


def get_available(fname):
    """Return available fname, append "_<counter>" if necesarry"""
    counter = 2
    dirname = os.path.dirname(fname)
    filebase, ext = os.path.splitext(os.path.basename(fname))

    # solve cases like a.tar.gz
    filebase2, ext2 = os.path.splitext(filebase)
    if ext2 != "":
        filebase = filebase2
        ext = ext2 + ext

    orig_fname = fname
    while os.path.exists(fname):
        fname = os.path.join(dirname, filebase + "_{0}".format(counter) + ext)
        counter += 1

    if orig_fname != fname:
        logger.info("{0} exists, renamed to {1}".format(orig_fname, fname))

    return fname


def splitext2(fname, multi=False, is_file=False):
    """Split a filename in dirname, filebase and ext"""
    fname = os.path.realpath(fname)
    dirname = os.path.dirname(fname)
    basename = os.path.basename(fname)
    splits = basename.split(".")
    filebase = splits[0]
    extensions = ["." + ext2 for ext2 in splits[1:]]
    if not extensions and not is_file:
        dirname = os.path.join(dirname, filebase)
        filebase = ""
    return dirname, filebase, extensions if multi else "".join(extensions)
