#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Convert lilypond midi and pdf"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import subprocess
import logging
import os
import re

from mconvert import tools

logger = logging.getLogger(__name__)
ORIG = "text/lilypond-score", "text/lilypond"
DEST = "application/postscript"
CONVERT = "ly_pdf"


def ly_pdf(orig, dest, *_args, **_kwargs):
    """Convert lilypond to pdf"""

    cmd = "lilypond --ps --output={destbase} {orig}".format(
        orig=orig,
        destbase=os.path.splitext(dest)[0])
    try:
        logger.debug("Running: {0}".format(cmd))
        output = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, shell=True)
        output = tools.to_unicode(output)
    except subprocess.CalledProcessError as error:
        logger.error(error)
        logger.error(tools.to_unicode(error.output))
        return None

    cache = tools.Cache()
    if cache(re.search("Layout output to `(.*)'", output, re.MULTILINE)):
        return os.path.join(os.path.dirname(dest), cache.output.group(1))
    else:
        logger.error("ERROR: {0}".format(output))
        return None
