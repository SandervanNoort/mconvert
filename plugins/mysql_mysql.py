#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Command line iap"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import io
import sys  # pylint: disable=W0611
import re


ORIG = "application/sql-mysql"
DEST = "application/sql-mysql"
CONVERT = "mysql_mysql"
MULTI = True


def rename(old_name):
    """Rename table name"""
    if old_name == b"pollster_results_weekly":
        return b"survey_nb15"
    if old_name == b"pollster_results_intake":
        return b"intake_nb15"
    print("unknown", old_name)
    sys.exit()


def mysql_mysql(orig, dest, **kwargs):
    """Convert CSV file to mysql"""

    options = kwargs.get("tree").cmd_options.get("options", [])
    rename_tbl = None
    for option in options:
        if isinstance(option, tuple) and option[0] == "rename_tbl":
            rename_tbl = option[1]
            break

    mysql = io.open(dest, "wb")
    for orig_fname in orig if isinstance(orig, list) else [orig]:
        with io.open(orig_fname, "rb") as fobj:
            content = fobj.read()
            if rename_tbl:
                for tbl in re.findall(b"CREATE TABLE `(.*)`", content):
                    new_tbl = rename_tbl(tbl)
                    content = re.sub(
                        b"`" + tbl + b"`",
                        b"`" + new_tbl + b"`",
                        content)
            mysql.write(content)
    mysql.close()
    return dest
