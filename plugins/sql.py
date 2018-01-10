#!/usr/bin/env python
# -*-coding: utf-8-*-

"""Scan sql file (mysql, postgresql, zipped sql"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)


import sys  # pylint: disable=W0611
import re
import io


FTYPES = ":sql"
SCAN = "ftype_sql"


def ftype_sql(fname, file_options):
    """File type for sql files"""

    if file_options["mime_raw"].startswith("PostgreSQL custom database dump"):
        return {"application/sql-postgresql-dump"}
    elif file_options["mime_type"] != "text/plain":
        return None

    ftype = None
    with io.open(fname, "r") as fobj:
        for line_no, line in enumerate(fobj):
            if re.search("PostgreSQL database dump", line, re.IGNORECASE):
                ftype = "application/sql-postgresql"
            elif re.search("`.*`", line):
                ftype = "application/sql-mysql"
#             if re.search("mysql", line, re.IGNORECASE):
#                 ftype = "application/sql-mysql"

            if line_no == 100 or ftype is not None:
                break
    if ftype is None:
        sys.exit("Cannot determine sql type for {0}".format(fname))
    else:
        return {ftype}
