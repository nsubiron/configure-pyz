#!/usr/bin/env python

"""run all the test cases"""

import argparse
import fnmatch
import logging
import os
import re
import subprocess
import sys

from contextlib import contextmanager


class Logger(object):
    def __init__(self, file_stream):
        self.file_stream = file_stream
        self.current_test = 'null'

    def error(self, text):
        text = '%s: %s' % (self.current_test, text)
        self._write('ERROR: %s' % text)
        logging.error(text)

    def info(self, text):
        self._write('INFO: %s' % text)
        logging.info(text)

    def log_new_test(self, filename, folder):
        folder = os.path.basename(os.path.normpath(folder))
        filename = os.path.splitext(filename)[0]
        self.current_test = '.'.join([folder, filename])
        text = '%s: running' % self.current_test
        self.info(text)

    def success(self):
        self.info('%s: success' % self.current_test)

    def print_command_output(self, output, display_on_screen=False):
        self._write(output)
        if display_on_screen:
            print('\033[30;1m%s\033[0m' % output)

    def _write(self, text):
        self.file_stream.write(text + '\n')


@contextmanager
def pushd(directory):
    """Context manager to temporally change working directory."""
    cwd = os.getcwd()
    try:
        os.chdir(directory)
        yield
    finally:
        os.chdir(cwd)


def run_test(filename, directory, environmet):
    filename = './' + filename
    with pushd(directory):
        return subprocess.check_output(
            filename,
            env=environmet,
            stderr=subprocess.STDOUT).decode('utf-8')


def source_walk(root, file_pattern):
    root = os.path.abspath(root)
    regex = re.compile(fnmatch.translate(file_pattern))
    for path, _, files in os.walk(root):
        files[:] = [f for f in files if regex.match(f) is not None]
        for filename in files:
            yield filename, path


def do_the_test():
    argparser = argparse.ArgumentParser(description=__doc__)
    argparser.add_argument(
        '--script',
        metavar='FILENAME',
        dest='script_filename',
        default='*.sh',
        help='filename of the script to run on each subfolder (can have wild cards)')
    argparser.add_argument(
        '--log-file',
        metavar='FILEPATH',
        dest='log_file',
        default='./test.log',
        help='log file path')
    argparser.add_argument(
        'configure_pyz_path',
        help='path to the configure.pyz to test')
    argparser.add_argument(
        'testdir',
        help='directory containing test cases')
    args = argparser.parse_args()

    loglevel = logging.DEBUG
    logging.basicConfig(format='%(levelname)s: %(message)s', level=loglevel)

    if not os.path.isdir(args.testdir):
        logging.critical('"%s" is not a directory', args.testdir)
        return

    with open(args.log_file, 'w+') as file_stream:
        logger = Logger(file_stream)

        environmet = dict(os.environ)
        environmet['CONFIGURE_PYZ'] = os.path.abspath(args.configure_pyz_path)
        for filename, path in source_walk(args.testdir, args.script_filename):
            try:
                logger.log_new_test(filename, path)
                output = run_test(filename, path, environmet)
                logger.print_command_output(output)
                logger.success()
            except subprocess.CalledProcessError as exception:
                logger.print_command_output(exception.output, display_on_screen=True)
                logger.error(exception)
                sys.exit(1)
            except Exception as exception:
                logger.error(exception)
                sys.exit(2)

        logger.info("every test terminated successfully")


if __name__ == '__main__':

    do_the_test()
