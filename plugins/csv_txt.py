#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Convert between figure types"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import io
import collections
from mconvert import tools

ORIG = "text/csv"
DEST = "text/plain"
CONVERT = "csv_txt"


def csv_txt(orig, new, **_kwargs):
    """Pretty print a csv file"""

    txtobj = io.open(new, "w")
    csvobj = tools.csvopen(orig, "r")
    tools.start_pos(csvobj)
    reader = tools.ureader(csvobj)
    max_size = collections.defaultdict(int)
    for row in reader:
        for col, val in enumerate(row):
            max_size[col] = max(max_size[col], len(val))
    line_format = "  ".join([
        "{{{0}:<{1}}}".format(col, size)
        for col, size in max_size.items()])
    for _counter in range(tools.start_pos(csvobj, get_counter=True)):
        line = next(csvobj)
        if isinstance(line, bytes):
            line = line.decode("utf8")
        txtobj.write(line)
    for row in reader:
        if len(row) == 0:
            continue
        txtobj.write(line_format.format(*row) + "\n")
    csvobj.close()

    txtobj.close()
    return new
