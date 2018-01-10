#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Build lilypond files"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import io
import logging

logger = logging.getLogger(__name__)


ORIG = "text/lilypond"
DEST = "text/lilypond"
CONVERT = "ly_ly"


def ly_ly(orig, dest, *_args, **_kwargs):
    """Convert lilypond to lilypond with nice indentation"""

    tab = 0
    with io.open(orig, "r") as fobj_in, io.open(dest, "w") as fobj_out:
        for line in fobj_in:
            line = line.strip()
            if line == "":
                continue
            fobj_out.write(tab * "   " + line + "\n")
            prev_tab = tab
            tab += (line.count("{") + line.count("<<") -
                    line.count("}") - line.count(">>"))
            if tab == 0 and prev_tab != 0:
                fobj_out.write("\n")
    return dest
