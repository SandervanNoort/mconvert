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

ORIG = "application/rar"
DEST = None
CONVERT = "unrar"
PRIORITY = 1

rarfile.PATH_SEP = os.path.sep


def unrar(orig, dest, *_args, **_kwargs):
    """Unpack zip"""
    rarobj = rarfile.RarFile(orig, "r")
    members = rarobj.infolist()
    if dest is None:
        return [(str(index),
                 os.path.normpath(member.filename),
                 None if not member.isdir() else {"inode/directory"})
                for index, member in enumerate(members)]

    member = members[int(os.path.basename(dest))]
    rarobj.extract(member, path=os.path.dirname(dest))
    fullname = os.path.join(os.path.dirname(dest), member.filename)
    newname = os.path.join(os.path.dirname(dest),
                           os.path.basename(fullname))
    dirname = os.path.normpath(os.path.dirname(member.filename))
    if dirname != ".":
        os.rename(fullname, newname)
    if dirname != ".":
        return dirname, newname
    else:
        return newname
