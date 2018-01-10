#!/usr/bin/env python
# -*-coding: utf-8-*-

"""Scan TeX file (is it latex?)"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)


import sys  # pylint: disable=W0611
import re
import io


FTYPES = "text/tex"
SCAN = "ftype_tex"


def ftype_tex(fname, _file_options):
    """File type for sql files"""

    with io.open(fname, "r") as fobj:
        for line_no, line in enumerate(fobj):
            if re.search("documentclass", line, re.IGNORECASE):
                return "text/tex-latex"
            if line_no == 100:
                break
    return "text/tex-snippet"
