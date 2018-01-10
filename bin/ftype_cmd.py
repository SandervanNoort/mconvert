#!/usr/bin/env python3
# -*-coding: utf-8-*-

"""Return ftype of a file"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import argparse

import mconvert.mime


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("fnames", nargs="+")
    cmd_options = parser.parse_args()

    for fname in cmd_options.fnames:
        print("{fname}: {ftypes}".format(
            fname=fname,
            ftypes=", ".join(mconvert.mime.get_all_ftypes(fname))))
