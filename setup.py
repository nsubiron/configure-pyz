#!/usr/bin/env python

"""zip source directory tree"""

import argparse
import fnmatch
import logging
import os
import re
import zipfile

def source_walk(root):
    root = os.path.abspath(root)
    regex = re.compile(fnmatch.translate('*.py[co]'))
    for path, _, files in os.walk(root):
      files[:] = [f for f in files if regex.match(f) is None]
      for filename in files:
        fullpath = os.path.join(path, filename)
        yield fullpath, os.path.relpath(fullpath, root)

def setup():
    argparser = argparse.ArgumentParser(description=__doc__)
    argparser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='print debug information')
    argparser.add_argument(
        '-o',
        metavar='zipfile',
        dest='output',
        help='output file name')
    argparser.add_argument(
        'source',
        help='source directory')
    args = argparser.parse_args()

    loglevel = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(format='%(levelname)s: %(message)s', level=loglevel)

    if not os.path.isdir(args.source):
      logging.critical('"%s" is not a directory', args.source)
      return

    if args.output is None:
      args.output = args.source + '.zip'

    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as fzip:
      for path, relpath in source_walk(args.source):
        fzip.write(path, relpath)


if __name__ == '__main__':

    setup()
