#!/usr/bin/env python
# -*-coding: utf-8-*-

"""Scan TeX file (is it latex?)"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)


import sys  # pylint: disable=W0611
import re
import subprocess
import logging
import pipes

from mconvert import tools

FTYPES = "video/mp4", "audio/m4a"
SCAN = "ftype_mp4"
logger = logging.getLogger(__name__)
ENCODINGS = {
    "aac": ("audio/aac"),
    "flac": ("audio/flac"),
    "mp3": ("audio/mpeg"),
    "vorbis": ("audio/ogg"),
    "wmav2": ("audio/ms-wma"),
    "mp1": ("audio/mp1"),
    "mp2": ("audio/mp2"),
    }


def ftype_mp4(fname, file_options):
    """File type for mp4 files
            is it video or audio"""

    cache = tools.Cache()
    cmd = "ffprobe {0}".format(pipes.quote(fname))
    try:
        output = subprocess.check_output(
            cmd, shell=True,
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as error:
        logger.error(error)
        logger.error(tools.to_unicode(error))
        return
    output = tools.to_unicode(output)

    streams = set()
    video = False
    for line in output.split("\n"):
        if cache(re.search(
                r".*Stream #0.\d+.*: (.*?): ([a-zA-Z0-9]*).*", line)):
            stype, encoding = cache.output.groups()
            if stype == "Video":
                video = True
                break
            if encoding not in ENCODINGS:
                logger.error("Unknown encoding: {0}".format(encoding))
                streams.add(encoding)
            else:
                streams.add(ENCODINGS[encoding])
    if video and not streams:
        return {file_options["mime_type"]}
    else:
        if video:
            print("TODO: has video, but also audio")
        return streams
