#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Command line iap"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import subprocess
import logging

from mconvert import tools

ORIG = "application/sql-postgresql-dump"
DEST = "application/sql-postgresql"
CONVERT = "zpsql_psql"

logger = logging.getLogger(__name__)


def zpsql_psql(orig, dest, **_kwargs):
    """Convert condensed psql to txt psql"""
    try:
        subprocess.check_call(
            "pg_restore {0} > {1}".format(orig, dest),
            shell=True)
    except subprocess.CalledProcessError as error:
        logger.error(error)
        logger.error(tools.to_unicode(error.output))
        return None
    return dest
