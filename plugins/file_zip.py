#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Convert between figure types"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import zipfile
import os

ORIG = ":"
DEST = "application/zip"
CONVERT = "file_zip"
PRIORITY = -1
MULTI = True


def get_available(arc, all_arcs):
    """Return available name, adding "_<number>.ext" if already there"""

    counter = 2
    dirname = os.path.dirname(arc)
    filebase, ext = os.path.splitext(os.path.basename(arc))
    while arc in all_arcs:
        arc = os.path.join(dirname, filebase + "_{0}".format(counter) + ext)
        counter += 1
    return arc


def file_zip(_orig, dest, **kwargs):
    """Create a zip"""
    zipobj = zipfile.ZipFile(dest, "w")

    tree = kwargs.get("tree")
    parents = tree.items[kwargs.get("step")]["parents"]
    arcnames = [
        os.path.join(
            tree.get_dirname(parent),
            os.path.basename(tree.items[parent]["fullname"]))
        for parent in parents]
    fullnames = [
        tree.items[parent]["fullname"]
        for parent in parents]
    prefix = os.path.commonprefix(arcnames)
    if prefix in arcnames:
        prefix = os.path.dirname(prefix)
    for arcname, fullname in zip(arcnames, fullnames):
        arcname = get_available(
            os.path.relpath(arcname, prefix),
            zipobj.namelist())
        zipobj.write(fullname, arcname=arcname)

    zipobj.close()
    return dest
