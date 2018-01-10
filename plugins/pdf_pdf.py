#!/usr/bin/env python
# -*-coding: utf-8-*-

"""Convert multiple pdf to one pdf"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

# http://askubuntu.com/questions/32048/renumber-pages-of-a-pdf

import sys  # pylint: disable=W0611
import os
import subprocess
import io
import logging
import PyPDF2

from mconvert import tools


ORIG = "application/pdf"
DEST = "application/pdf"
PARAMS = [
    ("q=screen", "low-quality", False),
    ("q=ebook", "medium-quality", False),
    ("q=prepress", "high-quality", False),
    ("bw", "black / white", False)]

CONVERT = "pdf_pdf"
MULTI = True


logger = logging.getLogger(__name__)


def pdf_pdf(orig, dest, **kwargs):
    """Combine the fnames into output"""

    if isinstance(orig, list):
        pdfmarks = os.path.join(os.path.dirname(dest), "pdfmarks")
        with io.open(pdfmarks, "w") as fobj:
            fobj.write("""[ /Title (Merged)
                    /DOCINFO pdfmark
                [/_objdef {pl} /type /dict /OBJ pdfmark
                [{pl} <</Nums [\n""")
            page = 1
            for orig_elem in tools.get_iter(orig):
                pdfobj = PyPDF2.PdfFileReader(orig_elem)
                filebase = os.path.splitext(os.path.basename(orig_elem))[0]
                for subpage in range(pdfobj.getNumPages()):
                    fobj.write("{page:d} << /P ({name} {subpage}) >>\n".format(
                        page=page, name=filebase,
                        subpage=(" [{0}]".format(subpage + 1)
                                 if subpage > 0 else "")))
                    page += 1
            fobj.write("{0:d} << >>\n".format(page))
            fobj.write("""]>> /PUT pdfmark
                [{Catalog} <</PageLabels {pl}>> /PUT pdfmark\n""")

    else:
        pdfmarks = ""

    options = kwargs.get("tree").cmd_options["options"]
    # -dDOPDFMARKS
    import shlex
    cmd = (
        "gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite {bw} {size}" +
        " -sOUTPUTFILE={output} {orig} {pdfmarks}").format(
            output=shlex.quote(dest),
            orig=" ".join([
                shlex.quote(fname)
                for fname in tools.get_iter(orig)
            ]),
            pdfmarks=pdfmarks,
            bw=("-sColorConversionStrategy=Gray" +
                " -dProcessColorModel=/DeviceGray" if "bw" in options else ""),
            size=("-dPDFSETTINGS=/screen" if "q=screen" in options else
                  "-dPDFSETTINGS=/ebook" if "q=ebook" in options else
                  "-dPDFSETTINGS=/prepress" if "q=prepress" in options else
                  ""))
    logger.info(cmd)
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as error:
        logger.error(error)
        logger.error(tools.to_unicode(error.output))
        return None
    return dest
