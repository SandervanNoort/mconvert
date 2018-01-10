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
ORIG = "text/lilypond-midi", "text/lilypond"
DEST = "audio/midi"
CONVERT = "ly_midi"


def ly_midi(orig, dest, *_args, **_kwargs):
    """Convert lilypond to pdf"""

    cmd = "lilypond --output={destbase} {orig}".format(
        orig=orig,
        destbase=os.path.splitext(dest)[0])
    try:
        logger.debug("Running: {0}".format(cmd))
        output = subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as error:
        logger.error(error)
        logger.error(tools.to_unicode(error.output))
        return None
    output = tools.to_unicode(output)

    cache = tools.Cache()
    if cache(re.search(r"MIDI output to `(.*)'", output, re.MULTILINE)):
        return os.path.join(os.path.dirname(dest), cache.output.group(1))
    else:
        logger.error("{0}".format(output))
        return None
