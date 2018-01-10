#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Convert between figure types"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import re
import sys  # pylint: disable=W0611
import io
from mconvert import tools

ORIG = "text/csv"
DEST = "text/tex-latex"
CONVERT = "csv_tex"


def csv_tex(orig, dest, *_args, **_kwargs):
    """Convert csv to tex"""

    csvobj = tools.csvopen(orig, "r")
    texobj = io.open(dest, "w")

    tools.start_pos(csvobj)
    reader = tools.ureader(csvobj)
    tabular = get_tabular(reader)

    full = True
    if full:
        texobj.write("\\documentclass{article}\n" +
                     "\\usepackage{booktabs}\n" +
                     "\\usepackage{fullpage}\n" +
                     "\\usepackage{times}\n" +
                     "\\begin{document}\n" +
                     "\\pagestyle{empty}\n")

    texobj.write("\\begin{{tabular}}{{{0}}}\n".format(tabular))
    texobj.write("\\toprule\n")

    tools.start_pos(csvobj)
    headers = next(reader)
    texobj.write(get_texline(headers, header=True))

    texobj.write("\\midrule\n")
    for row in reader:
        texobj.write(get_texline(row))
    texobj.write("\\bottomrule\n")
    texobj.write("\\end{tabular}\n")

    if full:
        texobj.write("\\end{document}\n")

    csvobj.close()
    texobj.close()

    return dest


def texify(text):
    """Texify a string"""

    if "$" not in text:
        text = re.sub(">=", r"$\\geq$", text)
#     else:
#         text = re.sub(">=", r"\geq", text)

    text = re.sub("([<>])", "${\\1}$", text)
    text = re.sub("%", "\\%", text)
    if "$" not in text:
        text = re.sub("-", "--", text)
    return text


def get_tabular(reader):
    """Get the col_types for a csv file"""

    headers = next(reader)
    col_types = {}
    for index in range(len(headers)):
        col_types[index] = set([])

    for row in reader:
        for index, value in enumerate(row):
            if (re.match(r"\\textbf{[-\d\.]+}", value) or
                    re.match(r"[-\d\.\,]+[MK]*", value)):
                col_types[index].add("number")
            elif value != "":
                col_types[index].add("text")
    tabular = ""
    for index, types in tools.sort_iter(col_types):
        if len(types) == 1 and "number" in types:
            tabular += "r"
        elif index == 0:
            tabular += "l"
        elif re.match("answer", headers[index], re.IGNORECASE):
            tabular += "l"
        else:
            tabular += "c"
    return tabular


def get_texline(line, header=False):
    """From a csv-list of values, make a texline"""

    def text_header(text):
        """headers"""
        return r"\textsc{{{0}}}".format(texify(text))

    def text_cell(text):
        """Normal cell"""
        return texify(text)

    if len(line) == 0:
        return ""

    value = line[0]
    multi = 1
    values = []
    for elem in line[1:] + [None]:
        if elem == "MULTI":
            multi += 1
        else:
            if multi == 1:
                values.append(text_header(value) if header else
                              text_cell(value))
            else:
                values.append(
                    r"\multicolumn{{{multi}}}{{l}}{{{value}}}".format(
                        multi=multi,
                        value=(text_header(value) if header else
                               text_cell(value))))
            value = elem
            multi = 1
    return " & ".join(values) + " \\\\ \n"
