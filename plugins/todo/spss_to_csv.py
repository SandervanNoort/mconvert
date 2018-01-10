#!/usr/bin/env python
# -*-coding: utf-8-*-

"""Convert spss to csv"""

import rpy
import math
import datetime
import csv
import sys
import os

SPSS_DATE0 = datetime.datetime(1582, 10, 14, 0, 0)
MIN_SECS = (datetime.datetime(1900, 1, 1, 0, 0) - SPSS_DATE0).total_seconds()
MAX_SECS = (datetime.datetime(2050, 1, 1, 0, 0) - SPSS_DATE0).total_seconds()


def to_dates(values, key):
    """Convert values to dates if possible"""
    vals = [val for val in values if val is not None]
    if min(vals) > MIN_SECS and max(vals) < MAX_SECS:
        print "Assuming {0} is a date".format(key)
        values = [SPSS_DATE0 + datetime.timedelta(seconds=val)
                  if val is not None else None
                  for val in values]
        times = sum(set([
            val.second + val.minute
             for val in values
             if val is not None]))
        if times == 0:
            values = [val.date() if val is not None else None
                      for val in values]
        return values
    else:
        return values


def spss_to_csv(spss_name, csv_name=None):
    """Convert spss file to csv file"""

    if csv_name is None:
        basename = os.path.splitext(spss_name)[0]
        csv_name = basename + ".csv"

    rpy.r("library(foreign)")
    data = rpy.r("read.spss('{0}')".format(spss_name))
    keys = data.keys()

    for key, values in data.items():
        types = set([type(val) for val in values])
        if len(types) != 1:
            sys.exit("ERROR: multiple types for {0}: {1}".format(key, types))
        first = values[0]

        if isinstance(first, float):
            values = [None if math.isnan(val) else val for val in values]

        if isinstance(first, float):
            values = to_dates(values, key)

        elif isinstance(first, float):
            values = [int(val) if val is not None and val.is_integer() else val
                      for val in values]
        data[key] = values

    row = 0
    with open(csv_name, "w") as fobj:
        writer = csv.writer(fobj)
        writer.writerow(keys)
        while True:
            try:
                line = [data[key][row] for key in keys]
                writer.writerow(line)
            except IndexError:
                break
            row += 1

if __name__ == "__main__":
    if len(sys.argv) <= 1:
        sys.exit("Supply arguments for spss filenames to convert")
    for fname in sys.argv[1:]:
        spss_to_csv(fname)
