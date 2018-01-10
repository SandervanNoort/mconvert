#!/usr/bin/env python
# -*-coding: utf-8-*-

"""Convert json to topojson"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

# http://askubuntu.com/questions/32048/renumber-pages-of-a-pdf

import sys  # pylint: disable=W0611
import subprocess
import logging


ORIG = "application/qgis"
DEST = "text/topojson"
PARAMS = [("q=1", "100%", False)]

CONVERT = "json_topojson"
MULTI = False


logger = logging.getLogger(__name__)


def json_topojson(orig, dest, **kwargs):
    """Combine the fnames into output"""

    options = kwargs.get("tree").cmd_options["options"]
    cmd = "topojson -o {dest} {options} -- {orig}".format(
        orig=orig, dest=dest, options=" ".join(options))
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as error:
        logger.error(error)
        return

    return dest
