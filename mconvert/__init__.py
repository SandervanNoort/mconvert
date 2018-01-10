#!/usr/bin/env python3
# -*-coding: utf-8-*-

"""base class of mconvert"""

from __future__ import (division, absolute_import, unicode_literals,
                        print_function)

from .convert import convert_fname, Tree
from . import config, mime
from .mime import get_all_extensions, get_all_ftypes

convert = convert_fname

AUTHOR = "Sander van Noort"
EMAIL = "Sander.van.Noort@gmail.com"
VERSION = "0.1"
DESCRIPTION = """Convert between different file types"""
