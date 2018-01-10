#!/usr/bin/env python
# -*-coding: utf-8-*-

# Copyright 2004-2012 Sander van Noort <Sander.van.Noort@gmail.com>
# Licensed under GPLv3 (see LICENSE.txt)

"""Convert between figure types"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import subprocess
import os
import logging
import re
import io
import configobj

from mconvert import tools

ORIG = "text/tex-latex"
DEST = "application/pdf", "application/dvi"
CONVERT = "tex_pdf"
PARAMS = "get_params"
logger = logging.getLogger(__name__)
ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__)))


def tex_pdf(orig, dest, **kwargs):
    """Convert tex to pdf"""
    settings = configobj.ConfigObj(os.path.join(ROOT, "latex.ini"))
    options = kwargs.get("tree").cmd_options.get("options", [])
    ftypes = kwargs.get("tree").items[kwargs.get("step")]["ftypes"]
    latex_cmd = "pdflatex" if "application/pdf" in ftypes else "latex"

    mkdirs(orig, dest)
    dest_tex = mktex(orig, dest, options)
    return latex(orig, dest_tex, latex_cmd, settings)


def latex(orig, dest_tex, latex_cmd, settings, run_bibtex=True):
    """Run (and rerun) latex command"""
    cmd = (
        "{latex} -halt-on-error -interaction=nonstopmode" +
        " -output-directory={dirname} {tex}").format(
            latex=latex_cmd,
            tex=dest_tex,
            dirname=os.path.dirname(dest_tex))
    # -aux-directory=/tmp/thesis
    try:
        output = subprocess.check_output(
            cmd,
            cwd=os.path.dirname(os.path.realpath(orig)),
            shell=True)
    except subprocess.CalledProcessError as error:
        output = error.output
    output = tools.to_unicode(output)
    messages, extra, errors = debug_output(output, settings, dest_tex)

    if "fname" in extra and not errors:
        if run_bibtex and "bibtex" in extra:
            bibtex(extra["bibtex"], orig, dest_tex)
            return latex(orig, dest_tex, latex_cmd, settings, run_bibtex=False)

        if "rerun" in extra:
            return latex(orig, dest_tex, latex_cmd, settings, run_bibtex)

    for fname, page, debug, message in messages:
        if errors and debug != "error":
            continue
        getattr(logger, debug)(
            "{fname}, page={page}\n{msg}\n".format(
                fname=fname,
                page=page,
                msg=re.sub("\n\n\n+", "\n\n", message).strip()))

    return (extra["fname"] if not errors and "fname" in extra else
            None)


def get_params(orig):
    """Get params for this specific latex file"""

    cache = tools.Cache()
    options = []
    params = []
    with open(orig, "r") as fobj:
        for line in fobj:
            if cache(re.match("(%)?.*% +option: *(.*?) *$", line)):
                comment = cache.output.group(1)
                option = cache.output.group(2)
                if option not in options:
                    params.append([option, "", comment is None])
                    options.append(option)
    return params


def extract(msg, fname, settings, dest_tex):
    """Extract info dict from raw latex output"""
    cache = tools.Cache()

    if cache(re.search(r"Output written on (.*) \((\d+) page.*", msg)):
        yield "fname", cache.output.group(1)
        yield "pages", int(cache.output.group(2))
        msg = (msg[0:cache.output.start()] +
               msg[cache.output.end():])

    while cache(re.search("No file (.*.bbl).*", msg)):
        yield "bibtex", cache.output.group(1)
        msg = (msg[0:cache.output.start()] +
               msg[cache.output.end():])

    while (cache(re.search(r"No file .*\.(nav|aux).*", msg)) or
           cache(re.search(r"Label\(s\) may have changed.*", msg)) or
           cache(re.search(r"Rerun to get citations correct\.", msg))):
        yield "rerun", True
        msg = (msg[0:cache.output.start()] +
               msg[cache.output.end():])

    for regex, debug in settings.items():
        while cache(re.search(regex, msg)):
            index = cache.output.lastindex if cache.output.lastindex else 0
            yield (
                debug,
                cache.output.group(index))
            msg = (msg[0:cache.output.start(index)] +
                   msg[cache.output.end(index):])

    if msg.strip() != "":
        yield (
            # main level
            "debug" if fname == "" else
            # (local) style files
            "debug" if fname.endswith("sty") else
            # local latex file
            "warning" if os.path.commonprefix([dest_tex, fname]) != "/" else
            # package/style file
            "debug",
            msg)


def get_fname(fnames, dest_tex):
    """Return filename"""
    if len(fnames) == 0:
        return ""
    fname = fnames[-1]
    if fname == dest_tex:
        return os.path.basename(fname)
    else:
        return fname


def parse_output(output):
    """Parse the latex output"""
    cache = tools.Cache()
    msg = ""
    # quote = False
    pos = 0
    line = ""
    vals = []
    start = "\000"
    for char in output + "\000":
        if pos == 79 and char == "\n":
            pos = 0
            continue

        if char == "\n":
            pos = 0
            line = ""
        else:
            pos += 1
            line += char
        if (line.startswith("   ") or
                line.startswith("l.") or
                line.startswith("\\")):
            msg += char
            continue

#         if char == "`":
#             quote = True
#         elif char == "'":
#             quote = False
#
#         if quote:
#             msg += char
#             continue

        if char in ["(", ")", "[", "]", "\000"]:
            key = None
            if (start == "(" and
                    cache(re.match(r"([\/\.].*?)([\n ]|$)(.*)",
                                   msg, re.DOTALL))):
                key = cache.output.group(1)
                msg = cache.output.group(2) + cache.output.group(3)
            elif (start == "[" and
                  cache(re.match(r"(\d+)(.*)", msg))):
                key = int(cache.output.group(1))
                msg = cache.output.group(2)
#             elif start == "\000":
#                 key = "START"
#             if key is None and start in ("(", "["):
#                 vals[-1]["msg"] += vals[-1]["end"] + msg
#                 vals[-1]["end"] = char
#             else:
            vals.append(
                {"start": start, "key": key, "msg": msg, "end": char})
            start = char
            msg = ""
        else:
            msg += char

    change = True
    while change:
        change = False
        for index, values in enumerate(vals):
            if (
                    (values["start"] == "(" and values["end"] == ")" and
                     values["key"] is None) or
                    (values["start"] == "[" and values["end"] == "]" and
                     values["key"] is None)):
                vals[index - 1]["msg"] += (
                    values["start"] + values["msg"] + values["end"] +
                    vals[index + 1]["msg"])
                vals[index - 1]["end"] = vals[index + 1]["end"]
                del vals[index]
                del vals[index]
                change = True
                break

    return vals


def debug_output(output, regex, dest_tex):
    """Parse output"""
    with io.open("/tmp/latex_output.txt", "w") as fobj:
        fobj.write(output)

    vals = parse_output(output)
    messages = []
    extra = {}

    fnames = []
    page = 0
    errors = False
    for values in vals:
        if values["start"] == "[":
            page = values["key"]
        elif values["start"] == "]":
            # end page
            pass
        elif values["start"] == "(":
            fnames.append(values["key"])
        elif values["start"] == ")":
            fnames.pop(-1)
        if not values["msg"].strip():
            continue
        fname = get_fname(fnames, dest_tex)
        for debug, message in extract(
                values["msg"], fname, regex, dest_tex):
            if debug in ["fname", "pages", "rerun"]:
                extra[debug] = message
            elif debug == "bibtex":
                extra.setdefault("bibtex", []).append(message)
            else:
                messages.append([fname, page, debug, message])
            if debug == "error":
                errors = True
    return messages, extra, errors


def bibtex(fnames, orig, dest_tex):
    """Run bibtex over files with missing references"""
    for fname in fnames:
        auxname = os.path.join(
            os.path.dirname(dest_tex),
            os.path.splitext(fname)[0] + ".aux")
        auxdir = os.path.dirname(fname)
        cmd = "openout_any=a TEXMFOUTPUT={0} bibtex {1}".format(
            os.path.normpath(os.path.join(os.path.dirname(dest_tex), auxdir)),
            auxname)
        try:
            output = subprocess.check_output(
                cmd,
                cwd=os.path.dirname(orig),
                shell=True)
        except subprocess.CalledProcessError as error:
            output = error.output
        output = tools.to_unicode(output)
        if "error messages" in output:
            print(output)


def mkdirs(orig, dest):
    """Create directory structure to write *.aux files"""
    main = os.path.dirname(os.path.realpath(orig))
    for dirpath, dirnames, _filenames in os.walk(main):
        for dirname in dirnames:
            reldir = os.path.relpath(os.path.join(dirpath, dirname), main)
            newdir = os.path.join(os.path.dirname(dest), reldir)
            if not os.path.exists(newdir):
                os.makedirs(newdir)


def mktex(orig, dest, options):
    """Write the latex doc based on the options"""
    orig_obj = io.open(orig, "r")
    cache = tools.Cache()
    dest_tex = os.path.join(
        os.path.dirname(dest),
        os.path.splitext(os.path.basename(dest))[0] + ".tex")
    dest_tex_obj = io.open(dest_tex, "w")
    for line in orig_obj:
        if cache(re.match("(%)? *(.*) +% +option: (.*)$", line)):
            _comment, cmd, option = cache.output.groups()
            if option.strip() in options:
                dest_tex_obj.write(
                    "{0} % option: {1}\n".format(cmd, option))
        else:
            dest_tex_obj.write(line)
    orig_obj.close()
    dest_tex_obj.close()
    return dest_tex
