#!/usr/bin/env python3
# -*-coding: utf-8-*-

"""Get mimetype of a file"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import six
import re
import os
import logging

from . import utils
from . import config
from . import tools

logger = logging.getLogger(__name__)
DEFAULT = "UNKNOWN/UNKNOWN"


def get_all_extensions(ftypes):
    """Return all possible extensions for filetype"""
    extensions = tools.SetList()
    for ftype in tools.get_iter(ftypes):
        if ftype.startswith("."):
            extensions.append(ftype)
        elif ftype in config.EXTENSION_DICT:
            extensions.extend(config.EXTENSION_DICT[ftype])
    return extensions


def get_extension(ftypes):
    """Return one extension for ftype"""

    extensions = get_all_extensions(ftypes)
    if extensions:
        if len(extensions) > 1:
            logger.info("{ftypes} has multiple extensions: {ext}".format(
                ftypes=", ".join(ftypes),
                ext=", ".join(extensions)))
        return extensions[0]
    else:
        return None


def get_all_ftypes(fname, checkfile=True, is_ext=False):
    """Get all ftypes for filename"""

    ftypes_name = None
    if is_ext:
        if re.match(r"[^/\.]+/[^/\.]+$", fname):
            return {fname}
        elif re.match(r"[^/\.]+$", fname):
            ext = "." + fname
        elif re.match(r"\.[^/\.]+$", fname):
            ext = fname
        else:
            logger.info("Unknown extension {0}".format(fname))
            ftypes_name = {DEFAULT}
    else:
        extensions = utils.splitext2(fname, True)[2]
        if extensions:
            ext = extensions[-1]
        else:
            ftypes_name = {"text/plain"}

    if ftypes_name is None:
        if ext in config.MIMETYPE_DICT:
            ftypes_name = config.MIMETYPE_DICT[ext]
        else:
            logger.info("Unknown extension {ext} for {fname}".format(
                ext=ext, fname=fname))
            ftypes_name = {DEFAULT}

    if os.path.exists(fname) and checkfile:
        ftype_magic, file_options = get_ftype_magic(fname)
        ftypes_scan = scan(ftypes_name, ftype_magic, file_options)
        ftypes = (
            merge_ftypes(ftypes_name, ftype_magic, file_options)
            if ftypes_scan is None else
            set(tools.get_iter(ftypes_scan)))
    else:
        ftypes = ftypes_name

    return ftypes


def scan(ftypes_name, ftype_magic, file_options):
    """Plugin scan"""
    ftypes_scan = None
    all_ftypes = ftypes_name.union(
        [file_options["mime_raw"], ftype_magic])
    for poptions in config.PLUGINS.values():
        if "scan" not in poptions:
            continue
        match = poptions["match"](all_ftypes)
        if not match:
            continue
        ftypes_scan = poptions["scan"](file_options["fname"], file_options)
        if ftypes_scan is not None:
            break
    return ftypes_scan


def get_ftype(fname, checkfile=True):
    """Return one extension for ftype"""

    ftypes = get_all_ftypes(fname, checkfile)
    if ftypes:
        if len(ftypes) > 1:
            logger.info("{fname} has multiple ftypes: {ftypes}".format(
                ftypes=", ".join(ftypes),
                fname=fname))
        return ftypes[0]
    else:
        return None


def get_ftype_magic(fname):
    """Get the file type of an existing input file"""

    file_options = {
        "fname": fname,
        "mime_raw": config.MAGIC_DICT["raw"].file(fname),
        "mime_type": config.MAGIC_DICT["type"].file(fname)}
    ftype = file_options["mime_type"]
    cache = tools.Cache()
    if cache(re.match("(.*)/x-(.*)", ftype)):
        ftype = "{0}/{1}".format(*cache.output.groups())


    for new_ftype, (mime_type, mime_raw) in \
            config.SETTINGS["mime_fix"].items():
        if (
                (mime_raw is None or
                 mime_raw.match(file_options["mime_raw"])) and
                (mime_type is None or mime_type.match(ftype))):
            ftype = new_ftype
    return ftype, file_options


def merge_ftypes(ftypes_name, ftype_magic, file_options):
    """There is a difference between ftypes by name and magic"""

    if ftype_magic == "inode/directory":
        return {ftype_magic}

    merged = set()
    for ftype_name in ftypes_name:
        if ftype_magic == ftype_name:
            merged.add(ftype_name)
        elif ftype_name in config.SETTINGS["mime_magic"]:
            type_exp, raw_exp = (
                (config.SETTINGS["mime_magic"][ftype_name], None)
                if isinstance(config.SETTINGS["mime_magic"][ftype_name],
                              six.string_types) else
                config.SETTINGS["mime_magic"][ftype_name])
            if (type_exp == ftype_magic and
                    (raw_exp is None or
                     re.search(raw_exp, file_options["mime_raw"]))):
                merged.add(ftype_name)
        elif "/" in ftype_name:
            ftype_name_base = ftype_name.split("/")[0]
            ftype_magic_base = ftype_magic.split("/")[0]
            if config.SETTINGS["mime_magic"].get(ftype_name_base) == \
                    ftype_magic_base:
                merged.add(ftype_name)

    if merged:
        return merged
    else:
        logger.debug(
            ("{fname}\n" +
             "  ftype by name: {ftypes}\n" +
             "  ftype by contents: {mime_type} / {mime_raw}").format(
                 fname=file_options["fname"],
                 mime_type=file_options["mime_type"],
                 mime_raw=file_options["mime_raw"],
                 ftypes=",".join(ftypes_name)))
        return {ftype_magic}


def get_name(ftypes, full=True):
    """Get a short name for the ftypes"""

    if full:
        return ",".join([get_short(ftype) for ftype in ftypes])
    else:
        ftype = sorted(list(ftypes), key=len)[0] if ftypes else ""
        return get_short(ftype)


def get_short(ftype):
    """Get a short name for the ftypes"""
    for orig, short in config.SETTINGS["short"].items():
        ftype = ftype.replace(orig, short)
    return ftype
