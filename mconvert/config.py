#!/usr/bin/env python3
# -*-coding: utf-8-*-

"""configuration for mconvert"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import os
import sys  # pylint: disable=W0611
import logging
import configobj
import magic
import collections
import re
import imp
import six
import pipes
import subprocess

from . import tools
from . import utils


logger = logging.getLogger(__name__)
logging.getLogger(__name__).addHandler(logging.NullHandler())


MIMEFILES = [
    "/etc/mime.types",
    "/etc/httpd/mime.types",                    # Mac OS X
    "/etc/httpd/conf/mime.types",               # Apache
    "/etc/apache/mime.types",                   # Apache 1
    "/etc/apache2/mime.types",                  # Apache 2
    "/usr/local/etc/httpd/conf/mime.types",
    "/usr/local/lib/netscape/mime.types",
    "/usr/local/etc/httpd/conf/mime.types",     # Apache 1.2
    "/usr/local/etc/mime.types",                # Apache 1.3
    ]
OPTIONS = ["MULTI", "PARAMS", "PRIORITY", "ADD_EXTENSION", "ENCODING"]
ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_DIR = os.path.join(ROOT, "config")
SPEC_DIR = os.path.join(ROOT, "config")
PLUGIN_DIR = os.path.join(ROOT, "plugins")

# variables which are dynamically filled
SETTINGS = {}
PLUGINS = {}
MAGIC_DICT = None
MIMETYPE_DICT = None
EXTENSION_DICT = None


def init(module):
    """Initialize settings/plugins"""
    logger.debug("Initializing mconvert config""")
    module.SETTINGS = get_settings()
    module.PLUGINS = get_plugins()
    module.MAGIC_DICT = get_magic()
    module.EXTENSION_DICT, module.MIMETYPE_DICT = get_mimetypes()


def get_settings():
    """Fill the settings database"""
    settings = configobj.ConfigObj(
        os.path.join(CONFIG_DIR, "settings.ini"),
        configspec=os.path.join(SPEC_DIR, "settings.spec"))
    tools.cobj_check(settings)
    for values in settings["mime_fix"].values():
        for i in range(len(values)):
            values[i] = re.compile(values[i]) if values[i] != "" else None
    return settings


def get_plugins():
    """Fill the plugins"""
    cache = tools.Cache()
    plugins = {}
    if not os.path.exists(PLUGIN_DIR):
        logger.error("Plugin dir {0} does not exist".format(PLUGIN_DIR))
        return plugins
    for fname in os.listdir(PLUGIN_DIR):
        fullname = os.path.join(PLUGIN_DIR, fname)
        if cache(re.match(r".+\.py$", fname)):
            add_python(fullname, plugins)
        elif cache(re.match("^(.*)_(.*).ini$", fname)):
            add_ini(fullname, plugins)
    return plugins


def add_python(fullname, plugins):
    """Add python plugin"""
    fname = os.path.basename(fullname)
    try:
        mod = imp.load_source(fname[:-3], fullname)
    except Exception as error:  # (general exception) pylint: disable=W0703
        logger.error("Cannot load plugin {0}".format(fname))
        logger.debug("{0}".format(error))
        return

    if (hasattr(mod, "ORIG") and hasattr(mod, "DEST") and
            hasattr(mod, "CONVERT") and
            hasattr(mod, mod.CONVERT)):
        plugins[fname] = {
            "convert": getattr(mod, mod.CONVERT),
            "match": utils.get_match(mod.ORIG),
            "forig": tools.get_iter(mod.ORIG, True),
            "fdest": tools.get_iter(mod.DEST, True)}
        for option in OPTIONS:
            if not hasattr(mod, option):
                continue
            value = getattr(mod, option)
            plugins[fname][option.lower()] = (
                getattr(mod, value)
                if (isinstance(value, six.string_types) and
                    hasattr(mod, value)) else
                value)
        if hasattr(mod, "FAST") and hasattr(mod, mod.FAST):
            plugins[fname]["fast"] = getattr(mod, mod.FAST)
    elif (hasattr(mod, "FTYPES") and hasattr(mod, "SCAN") and
          hasattr(mod, mod.SCAN)):
        plugins[fname] = {
            "scan": getattr(mod, mod.SCAN),
            "match": utils.get_match(mod.FTYPES)}
    else:
        logger.debug("{0} has no plugin variables".format(fname))
        return


def add_ini(fullname, plugins):
    """Add ini plugin"""
    fname = os.path.basename(fullname)
    try:
        ini = configobj.ConfigObj(fullname)
    except configobj.ConfigObjError:
        logger.error("Cannot parse plugin {0}".format(fname))
        return
    if not("ORIG" in ini and "DEST" in ini and "CONVERT" in ini):
        logger.error("No ORIG/DEST/CONVERT in {0}".format(fname))
        return

    if ini["DEST"] == "None":
        ini["DEST"] = None

    def func(orig, dest, ini=ini, **_kwargs):
        """Create function based on command"""
        cmd = ini["CONVERT"].format(
            orig=pipes.quote(orig),
            dest=pipes.quote(dest))
        try:
            logger.debug("Running: {0}".format(cmd))
            subprocess.check_output(
                cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as inst:
            logger.error("Calling {0}".format(cmd))
            logger.error("{0}".format(inst.output))
            return None
        return dest
    plugins[fname] = {
        "convert": func,
        "match": utils.get_match(ini["ORIG"]),
        "fdest": tools.get_iter(ini["DEST"], True),
        "forig": tools.get_iter(ini["DEST"], True)}
    for option in OPTIONS:
        if option in ini:
            value = ini[option]
            plugins[fname][option.lower()] = (
                int(value) if value.isdigit() else
                value)


def get_magic():
    """Load the magic databases"""
    magic_dict = {
        "raw": magic.open(magic.MAGIC_RAW),
        "type": magic.open(magic.MAGIC_MIME_TYPE)}
    for value in magic_dict.values():
        value.load()
    return magic_dict


def get_mimetypes():
    """Parsing mimefiles"""
    cache = tools.Cache()
    extension_dict = collections.defaultdict(tools.SetList)
    mimetype_dict = collections.defaultdict(set)
    import itertools
    for mimetype, ext in itertools.chain(
            add_mimefiles(), add_mailcap(), add_globs(), add_mime_settings()):
        if cache(re.search("(.*)/x-(.*)", mimetype)):
            mimetype = "{0}/{1}".format(*cache.output.groups())
        if "/" not in mimetype:
            continue
        if ext != "" and not ext.startswith("."):
            ext = "." + ext
        extension_dict[mimetype].append(ext)
        mimetype_dict[ext].add(mimetype)

    return extension_dict, mimetype_dict


def add_mime_settings():
    """Add mimetypes from settings"""
    for mimetype, extensions in SETTINGS["mimetypes"].items():
        for ext in tools.get_iter(extensions):
            yield mimetype, ext


def add_mimefiles():
    """Add mimetypes from mimefiles"""
    for fname in MIMEFILES:
        try:
            with open(fname, "r") as fobj:
                for line in fobj:
                    line = line.strip()
                    words = line.split()
                    if len(words) < 2 or words[0].startswith("#"):
                        continue
                    mimetype, all_extensions = words[0], words[1:]
                    for ext in all_extensions:
                        yield mimetype, ext
        except EnvironmentError:
            pass


def add_mailcap():
    """Add from mailcap"""
    cache = tools.Cache()
    try:
        with open("/etc/mailcap", "r") as fobj:
            for line in fobj:
                line = line.strip()
                if line.startswith("#"):
                    continue
                values = line.split(";")
                mimetype = values[0]
                for value in values:
                    if cache(re.search("nametemplate=%s.(.*)", value)):
                        yield mimetype, cache.output.group(1)
    except EnvironmentError:
        pass


def add_globs():
    """Add from globs"""
    try:
        with open("/usr/share/mime/globs", "r") as fobj:
            for line in fobj:
                line = line.strip()
                if line.startswith("#") or ":" not in line:
                    continue
                mimetype, glob = line.split(":")
                if not re.match(r"\*\..*", glob):
                    continue
                yield mimetype, glob[1:]
    except EnvironmentError:
        pass


tools.Delayed(__name__, init)
