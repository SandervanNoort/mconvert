#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Convert between figure types"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import rarfile
import os

from mconvert import tools

ORIG = ":file"
DEST = "application/rar"
CONVERT = "file_rar"
MULTI = True


def get_available(arc, all_arcs):
    """Return available name, adding "_<number>.ext" if already there"""

    counter = 2
    dirname = os.path.dirname(arc)
    filebase, ext = os.path.splitext(os.path.basename(arc))
    while arc in all_arcs:
        arc = os.path.join(dirname, filebase + "_{0}".format(counter) + ext)
        counter += 1
    all_arcs.add(arc)
    return arc


def file_rar(orig, dest, **_kwargs):
    """Unpack zip"""
    rarobj = rarfile.RarFile(dest, "w")
    all_arcs = set()
    for fname in tools.get_iter(orig):
        arc = get_available(os.path.basename(fname), all_arcs)
        rarobj.write(fname, arcname=arc)
    rarobj.close()
    return dest
