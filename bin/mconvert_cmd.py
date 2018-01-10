#!/usr/bin/env python3
# -*-coding: utf-8-*-

"""Convert between file types"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import argparse
import logging
import os

import mconvert
from mconvert import tools


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "orig", nargs="+",
        help="Orig files to be converted")
    parser.add_argument(
        "new",
        help="Desination files of conversion")
    parser.add_argument(
        "-d", "--debug", nargs="?", const="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="debug level on the command line")
#     parser.add_argument(
#         "-r", "--recursive", nargs="?", choices=[0, 1], type=int, default=1,
#         help="recusively unpack files (f.e. zip files inside zipfiles)")
    parser.add_argument(
        "-dry", action="store_true", default=False,
        help="do not actually convert")
    parser.add_argument("-o", "--options", nargs="+", default=list())
    parser.add_argument("-ow", "--overwrite",
                        action="store_true", default=False)
    parser.add_argument("-f", "--ftypes", nargs="+", default=list())
    parser.add_argument("-m", "--multi", nargs="+", default=list())
    parser.add_argument(
        "-u", "--unpack", action="store_true", default=False,
        help="unpack zip-file to confirm filetypes")
    parser.add_argument("-s", "--same", action="store_true", default=False)
    cmd_options = parser.parse_args()

    rootlogger = logging.getLogger("")
    rootlogger.setLevel(logging.DEBUG)
    rootlogger.addHandler(tools.get_output_handler(
        "warning" if cmd_options.debug is None else cmd_options.debug))
    rootlogger.addHandler(tools.get_debug_handler(
        os.path.join(os.path.expanduser("~"), ".mconvert.log")))

    logger = logging.getLogger(__name__)

    tree = mconvert.Tree(
        cmd_options.orig,
        cmd_options.new,
        same=cmd_options.same,
        unpack=cmd_options.unpack,
        ftypes=cmd_options.ftypes,
        dry=cmd_options.dry,
        options=cmd_options.options,
        multi=cmd_options.multi,
        overwrite=cmd_options.overwrite)
    tree.build()
    converted, not_converted = tree.save_all()
    if converted:
        print("Created: {0}".format(", ".join(converted)))
    if not_converted:
        print("Not converted: {0}".format(", ".join(not_converted)))
