#!/usr/bin/env python
# -*-coding: utf-8-*-

"""Scan lilypond filetype"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)


import sys  # pylint: disable=W0611
import io


FTYPES = "text/lilypond"
SCAN = "ftype_ly"


def ftype_ly(fname, _file_options):
    """File type for sql files"""

    ftype = None
    score = False
    midi = False
    with io.open(fname, "r") as fobj:
        for line in fobj:
            if r"\layout" in line:
                score = True
            if r"\midi" in line:
                midi = True
    if score and midi:
        ftype = "text/lilypond"
    elif score:
        ftype = "text/lilypond-score"
    elif midi:
        ftype = "text/lilypond-midi"
    else:
        sys.exit("Cannot parse lilypond: {0}".format(fname))

    return {ftype}
