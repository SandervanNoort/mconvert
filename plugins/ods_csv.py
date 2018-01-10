#!/usr/bin/env python
# -*-coding: utf-8-*-

"""Convert libreoffice spreadsheet to csv"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

import sys  # pylint: disable=W0611
import zipfile
import os
import io
import bs4

from mconvert import tools

ORIG = "application/vnd.oasis.opendocument.spreadsheet"
DEST = "text/csv"
CONVERT = "ods_csv"


def get_value(elem):
    """Convert to int/float if possible"""
    if elem.get("calcext:value-type") == "string":
        value = elem.text
    elif elem.get("calcext:value-type") == "date":
        value = elem.get("office:date-value")
    elif "table:formula" in elem.attrs:
        value = elem.get("office:value")
    elif elem.get("calcext:value-type") == "float":
        value = elem.get("office:value")
    elif elem.text != "":
        print("ERROR", elem)
        sys.exit()
    else:
        value = None

    if value is None:
        return None
    if value.isnumeric():
        return int(value)
    try:
        return float(value)
    except ValueError:
        return value


def ods_xml(orig, dest):
    """Extract xml from ods file"""
    zipobj = zipfile.ZipFile(orig)
    with io.open(dest, "wb") as xmlobj:
        xmlobj.write(zipobj.read("content.xml"))
    zipobj.close()
    return dest


def ods_csv(orig, dest, **_kwargs):
    """Convert ODS to csv"""

    # extract content from odf file
    dest_xml = os.path.join(
        os.path.dirname(dest),
        os.path.splitext(os.path.basename(dest))[0] + ".xml")
    ods_xml(orig, dest_xml)

    # convert content to csv
    csvobj = tools.csvopen(dest, "w")
    writer = tools.uwriter(csvobj)

    xmlobj = io.open(dest_xml, "r")
    soup = bs4.BeautifulSoup(xmlobj, "xml")

    for table in soup.findAll("table"):
        empty_rows = 0
        for row in table.findAll("table-row"):
            values = []
            for elem in row.findAll("table-cell"):
                value = get_value(elem)
                if "table:number-columns-repeated" in elem.attrs:
                    values.extend(
                        int(elem.get("table:number-columns-repeated")) *
                        [value])
                else:
                    values.append(value)
            while values and values[-1] in [None, ""]:
                values.pop()
            if values == []:
                empty_rows += 1
            else:
                for _ in range(empty_rows):
                    writer.writerow([])
                writer.writerow(values)
                empty_rows = 0

        # only first sheet
        break
    csvobj.close()
    xmlobj.close()

    return dest
