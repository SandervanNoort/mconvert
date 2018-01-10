#!/usr/bin/env python
# -*-coding: utf-8-*-

"""Extract audio from file"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import subprocess
import sys  # pylint: disable=W0611
import re
import os
import logging

from mconvert import tools

logger = logging.getLogger(__name__)

ENCODINGS = {
    "aac": ("audio/aac", ".mp4"),
    "flac": ("audio/flac", ".flac"),
    "mp3": ("audio/mpeg", ".mp3"),
    "vorbis": ("audio/ogg", ".ogg"),
    "wmav2": ("audio/ms-wma", ".wma"),
    "mp1": ("audio/mpeg", ".mp2"),
    "mp2": ("audio/mpeg", ".mp2"),
    "ac3": ("audio/ac3", ".ac3"),
    }
# "wmv1": ("vid_wmv", "_vid.asf"),
# "mpeg1video": ("vid_mpg", "_vid.mpg"),

ORIG = ":video/"
DEST = None
CONVERT = "video_audio"


def video_audio(orig, dest, *_args, **_kwargs):
    """Extract audio from video file"""

    streams = get_streams(orig)
    if dest is None:
        return [(str(stream), None, {ENCODINGS[encoding][0]})
                for stream, encoding in streams.items()]
    dirname = os.path.dirname(dest)
    stream = int(os.path.basename(dest))
    _mimetype, ext = ENCODINGS[streams[stream]]
    newname = os.path.join(
        dirname,
        os.path.splitext(os.path.basename(orig))[0] + ext)
    tools.create_dir(newname, remove=True)
    cmd = ("ffmpeg -i '{orig}' -vcodec copy -acodec copy -map 0:{stream}" +
           " '{newname}'").format(
               orig=orig, newname=newname, stream=stream)
    # mplayer -dumpaudio -dumpfile $output $input
    # yes n | avidemux2_cli $input --save-raw-audio $output
    logger.debug(cmd)
    try:
        subprocess.check_output(
            cmd, shell=True,
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as error:
        logger.error(error)
        logger.error(tools.to_unicode(error.output))
        return None
#     dest = os.path.join(
#         dirname,
#         os.path.splitext(os.path.basename(orig))[0] +
#         mime.get_extension({encoding}))
#     if newname != dest:
#         os.rename(newname, dest)
    return newname


def get_streams(orig):
    """Get audio stream type"""
    streams = {}
    cmd = "ffprobe '{0}'".format(orig)
    cache = tools.Cache()
    try:
        output = subprocess.check_output(
            cmd, shell=True,
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as error:
        logger.error(error)
        logger.error(tools.to_unicode(error.output))
        return None
    output = tools.to_unicode(output)

    for line in output.split("\n"):
        if cache(re.search(r".*Stream #0.(\d+).*: (.*?): (.+?)[, ].*", line)):
            stream, stype, encoding = cache.output.groups()
            if stype != "Audio":
                continue
            if encoding not in ENCODINGS:
                logger.error("Unknown encoding: {0}".format(encoding))
            else:
                streams[int(stream)] = encoding
    return streams
