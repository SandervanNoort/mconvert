#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Convert between figure types"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import time
import zipfile
import os
import subprocess
import logging

from mconvert import tools

ORIG = "application/zip"
DEST = None
CONVERT = "unzip"
FAST = "unzip_fast"
PRIORITY = 1

logger = logging.getLogger(__name__)


def unzip_fast(orig, dest, *_args, **kwargs):
    """Unzip immediately"""
    overwrite = kwargs.get("tree").cmd_options.get("overwrite", False)
    cmd = "unzip {options} {orig} -d {dest}".format(
        orig=orig,
        dest=dest,
        options="-o" if overwrite else "")
    try:
        logger.debug("Call: {0}".format(cmd))
        subprocess.check_call(cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as error:
        logger.error(error)
        logger.error(tools.to_unicode(error.output))
        return False
    return True


def unzip(orig, dest, *_args, **_kwargs):
    """Unpack zip"""
    zipobj = zipfile.ZipFile(orig, "r")
    members = zipobj.infolist()
    if dest is None:
        return [
            (str(index),
             os.path.normpath(member.filename),
             {"inode/directory"} if member.filename.endswith("/") else None)
            for index, member in enumerate(members)]
    member = members[int(os.path.basename(dest))]
    fname = os.path.normpath(member.filename)
    if fname == ".":
        return None

    zipobj.extract(member, path=os.path.dirname(dest))
    fullname = os.path.join(os.path.dirname(dest), fname)

    # zip does not automatically change mtime (tar does)
    mtime = time.mktime(member.date_time + (0, 0, 0))
    os.utime(fullname, (mtime, mtime))

    newname = os.path.join(os.path.dirname(dest),
                           os.path.basename(fname))
    dirname = os.path.dirname(fname)
    if dirname != "":
        os.rename(fullname, newname)
    if dirname != "":
        return dirname, newname
    else:
        return newname
