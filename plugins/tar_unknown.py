#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Convert between figure types"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import tarfile
import os

ORIG = "application/tar"
DEST = None
CONVERT = "untar"
PRIORITY = 1


def untar(orig, dest, *_args, **_kwargs):
    """Unpack zip"""
    tarobj = tarfile.TarFile(orig, "r")
    members = tarobj.getmembers()
    if dest is None:
        return [(str(index),
                 os.path.normpath(member.name),
                 None if member.isfile() else {"inode/directory"})
                for index, member in enumerate(members)
                if member.name != "."]
    member = members[int(os.path.basename(dest))]
    fname = os.path.normpath(member.name)

    tarobj.extract(member, path=os.path.dirname(dest))
    fullname = os.path.join(os.path.dirname(dest), fname)
    newname = os.path.join(os.path.dirname(dest),
                           os.path.basename(fname))
    dirname = os.path.dirname(fname)
    if dirname != "":
        os.rename(fullname, newname)
    if dirname != "":
        return dirname, newname
    else:
        return newname
