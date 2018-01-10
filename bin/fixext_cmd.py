#!/usr/bin/env python3
# -*-coding: utf-8-*-

"""Fix the extension of a file"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import argparse
import os
import six.moves

import mconvert.mime


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("fnames", nargs="+")
    cmd_options = parser.parse_args()

    for fname in cmd_options.fnames:
        ftypes = mconvert.mime.get_all_ftypes(fname)
        extensions = mconvert.mime.get_all_extensions(ftypes)
        filebase, ext = os.path.splitext(fname)
        if not extensions or ext in extensions:
            continue
        newname = filebase + extensions[0]
        print(fname, "=>", newname)
        rename = six.moves.input("Rename: ")
        if rename.lower().startswith("y"):
            os.rename(fname, newname)
