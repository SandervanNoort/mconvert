#!/usr/bin/env python3
# -*-coding: utf-8-*-

"""Display some debug info"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import collections
import os
import pprint

from . import mime


def get_tree(tree, full=False):
    """Show tree structure"""
    if full:
        actives = set(range(len(tree.items)))
    else:
        actives = set(tree.finals[0])
        for step in set(actives):
            actives.update(tree.items[step]["_parents"])
    grid = grid_childs(tree, {}, 0, actives=actives)
    grid_names = {}
    col_width = collections.defaultdict(int)
    max_row = 0
    max_col = 0
    for (row, col), step in grid.items():
        grid_names[(row, col)] = get_name(tree, step, full)
        col_width[col] = max(col_width[col], len(grid_names[(row, col)]))
        max_row = max(max_row, row)
        max_col = max(max_col, col)

    outputs = []

    for row in range(max_row + 1):
        output = ""
        for col in range(max_col + 1):
            output += (
                "" if col == 0 else
                " => " if (row, col) in grid_names else
                "    ")
            output += (
                "{{0:<{0}}}".format(col_width[col]).format(
                    grid_names[row, col]) if (row, col) in grid_names else
                " " * col_width[col])
        outputs.append(output)
    return "\n".join(outputs)


def grid_childs(tree, grid, step, row=0, col=0, actives=None):
    """Add step and its children to the grid"""
    # (too many arguments) pylint: disable=R0913

    if actives is not None and step not in actives:
        return grid
    rows = [row1 for row1, col1 in grid.keys() if col1 >= col]
    row = max(row, 0 if not rows else max(rows) + 1)
    grid[(row, col)] = step

    for child in sorted(tree.items[step].get("_childs", [])):
        grid = grid_childs(
            tree, grid, child, row, col + 1, actives=actives)
    return grid


def get_name(tree, step, full=True):
    """Show the filename or filetype of a certain step"""
    props = tree.items[step]
    name = os.path.basename(
        props["name"] if "name" in props else
        props["fullname"] if (
            props.get("fullname") is not None and
            0 in props["parents"]) else
        props["fname"] if "fname" in props else
        props["index"] if "index" in props else
        "")
    ftype = mime.get_name(props.get("ftypes"), full)

    name = (ftype if name == "" else
            "{0} [{1}]".format(ftype, name))
    if len(props.get("parents", [])) > 1:
        name += " (*{0})".format(step)
    elif full:
        name += " ({0})".format(step)
    return name


def get_items(tree):
    """Show all items"""
    output = ""
    for step, props in enumerate(tree.items):
        output += "{0}: ".format(step)
        output += pprint.pformat(
            {key: elem for key, elem in props.items()
             if not key.startswith("_")},
            indent=3)
        output += "\n"
    return output
