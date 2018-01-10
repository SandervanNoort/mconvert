#!/usr/bin/env python
# -*-coding: utf-8-*-

"""Convert json to topojson"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

# http://askubuntu.com/questions/32048/renumber-pages-of-a-pdf

import sys  # pylint: disable=W0611
import os
import subprocess
import logging

from mconvert import tools


ORIG = "application/qgis"
DEST = "application/qgis"

CONVERT = "shp_shp"
MULTI = True



logger = logging.getLogger(__name__)


def shp_shp(orig, dest, **kwargs):
    """Combine the fnames into output"""

    dest = os.path.splitext(dest)[0] + ".shp"
    for orig_elem in tools.get_iter(orig):
        cmd = (
            "ogr2ogr -f 'ESRI Shapefile'" +
            " -update -append {dest} {orig}").format(
                orig=orig_elem, dest=dest)
        try:
            subprocess.check_call(cmd, shell=True)
        except subprocess.CalledProcessError as error:
            logger.error(error)
            return

    fulldest = [dest]
    for fname in os.listdir(os.path.dirname(dest)):
        fullname = os.path.join(os.path.dirname(dest), fname)
        if fullname != dest:
            fulldest.append(fullname)
    return fulldest
