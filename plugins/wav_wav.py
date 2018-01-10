#!/usr/bin/env python
# -*-coding: utf-8-*-

"""Convert multiple pdf to one pdf"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

# http://askubuntu.com/questions/32048/renumber-pages-of-a-pdf

import os
import sys  # pylint: disable=W0611
import subprocess
import logging

from mconvert import tools

ORIG = "audio/wav"
DEST = "audio/wav"
CONVERT = "wav_wav"


logger = logging.getLogger(__name__)


def wav_wav(orig, dest, **_kwargs):
    """Combine the fnames into output"""

    # options = kwargs.get("tree").cmd_options.get("options", [])

    # first demux it to 16 bit 48khz
    dest_list = []
    for index, orig_elem in enumerate(tools.get_iter(orig)):
        tmp_dest = os.path.join(
            os.path.dirname(dest),
            "{0}_{1}".format(index, os.path.basename(dest)))
        cmd = "ffmpeg -i {orig} -acodec pcm_s16le -ar 48000 {dest}".format(
            dest=tmp_dest,
            orig=orig_elem)
        logger.debug(cmd)
        try:
            subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            logger.error(error)
            logger.error(tools.to_unicode(error.output))
            continue
        dest_list.append(tmp_dest)

    if len(dest_list) > 1:
        cmd = "sox {orig} {dest}".format(
            orig=" ".join(orig),
            dest=dest)
        logger.debug(cmd)
        try:
            subprocess.check_call(cmd, shell=True)
        except subprocess.CalledProcessError as error:
            logger.error(error)
            logger.error(tools.to_unicode(error.output))
    else:
        os.rename(dest_list[0], dest)
    return dest
