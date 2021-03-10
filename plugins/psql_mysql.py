#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Command line iap"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import io
import re
import sys  # pylint: disable=W0611
import logging

from mconvert import tools

ORIG = "application/sql-postgresql"
DEST = "application/sql-mysql"
CONVERT = "psql_mysql"

MAX_ROWS = 100
logger = logging.getLogger(__name__)


def psql_mysql(orig, dest, **_kwargs):
    """Convert based on fobj"""

    tools.create_dir(dest, is_dir=False, remove=True)
    mysql = io.open(dest, "w")
    psql = io.open(orig, "r")

    cache = tools.Cache()
    for line in psql:
        line = strip(line)
        if cache(re.match(r"CREATE TABLE (.*) \(", line)):
            # table_rename
            table = cache.output.group(1)
            table_def(mysql, table, line, psql)
        elif line == "" or line.startswith("--"):
            pass
        elif (re.match("ALTER TABLE .*", line) or
              re.match("CREATE SEQUENCE .*", line) or
              re.match("DROP SEQUENCE .*", line) or
              re.match("DROP TABLE .*", line) or
              re.match("ALTER SEQUENCE .*", line) or
              re.match("SELECT .*", line) or
              re.match("SET .*", line)):
            while not line.endswith(";"):
                line = next(psql)
                line = strip(line)

        elif cache(re.match(r"COPY (.*) \((.*)\) FROM stdin;", line)):
            # table_rename
            table = cache.output.group(1)
            data_def(mysql, table, cache.output.group(2), psql)
        else:
            logger.error("Unknown line: {0}".format(repr(line)))
    mysql.close()
    return dest


def get_coldef(coldef):
    """convert column def from psql to mysql"""
    cache = tools.Cache()
    if coldef.endswith(","):
        coldef = coldef[:-1]

    if cache(re.match(r"character varying\((\d+)\)", coldef)):
        return "VARCHAR({0})".format(cache.output.group(1))
    elif re.match("timestamp with time zone", coldef):
        return "TEXT"
    elif re.match("unknown", coldef):
        return "TEXT"
    else:
        return coldef


def get_colname(colname):
    """convert column name from psql to mysql"""
    cache = tools.Cache()
    if cache(re.match("\"(.*)\"", colname)):
        return cache.output.group(1)
    else:
        return colname


def get_val(val):
    """convert psql value to mysql value"""
    if val == "f":
        return "0"
    elif val == "t":
        return "1"
    elif val == "\\N":
        return "NULL"
    else:
        return "'{0}'".format(val)


def table_def(mysql, table, line, psql):
    """Convert table definition"""

    cache = tools.Cache()
    mysql.write("DROP TABLE IF EXISTS `{0}`;\n".format(table))
    mysql.write("CREATE TABLE `{0}` (\n".format(table))
    columns = []
    for line in psql:
        line = strip(line)
        if line == ");":
            mysql.write(",\n".join(columns) + "\n);\n")
            break
        elif re.match("CONSTRAINT.*", line):
            pass
        elif cache(re.match("(.+?) (.*)$", line)):
            columns.append("  {0} {1}".format(
                get_colname(cache.output.group(1)),
                get_coldef(cache.output.group(2))))
        else:
            sys.exit("Unknown column definition " + repr(line))


def data_def(mysql, table, columns, psql):
    """Convert data"""

    row = 0
    for line in psql:
        line = strip(line)
        if line == "\\.":
            mysql.write(";\n")
            return

        if row == 0:
            mysql.write("INSERT INTO `{table}` ({columns}) VALUES ".format(
                table=table,
                columns=",".join([get_colname(colname)
                                  for colname in re.split(", *", columns)])))
        else:
            mysql.write(", ")
        mysql.write("({0})".format(
            ",".join([get_val(val)
                      for val in re.split("\t", line)])))
        row += 1
        if row == MAX_ROWS:
            mysql.write(";\n")
            row = 0


def strip(line):
    """Strip a line and convert to utf8 if necesary"""
    if isinstance(line, bytes):
        line = line.decode("utf8")
    return line.strip()
