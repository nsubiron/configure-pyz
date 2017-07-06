# configure.pyz Copyright (C) 2014 N. Subiron Montoro
#
# This program comes with ABSOLUTELY NO WARRANTY. This is free software, and you
# are welcome to redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.

import json
import logging
import os
import pkgutil
import re
import sys


from contextlib import contextmanager

try:

    import yaml

except ImportError:

    print('CRITICAL: requires PyYaml')
    sys.exit(2)


if sys.version_info[0] != 2:
    STRING_TYPES = (str,)
else:
    STRING_TYPES = (str, unicode)


def program_name():
    return 'configure.pyz'


def get_default_settings_file():
    return 'configure.yaml'


def print_out(message, prefix=program_name()):
    print('%s: %s' % (prefix, message))


def critical_error(message, *args):
    logging.critical(message, *args)
    sys.exit(1)


@contextmanager
def pushd(directory):
    """Context manager to temporally change working directory."""
    cwd = os.getcwd()
    try:
        os.chdir(directory)
        yield
    finally:
        os.chdir(cwd)


def get_resource(filename):
    return pkgutil.get_data('__main__', filename).decode('utf-8')


def remove_comments(string):
    """Remove C comments from string. See http://stackoverflow.com/a/18381470"""
    pattern = r'(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)'
    regex = re.compile(pattern, re.MULTILINE|re.DOTALL)
    replacer = lambda match: match.group(1) if match.group(2) is None else ''
    return regex.sub(replacer, string)


def load_json(filepath):
    with open(filepath, 'r') as datafile:
        try:
            return json.loads(remove_comments(datafile.read()))
        except Exception as exception:
            critical_error('Error parsing file %s\n%s', filepath, exception)


def load_yaml(filepath):
    with open(filepath, 'r') as datafile:
        try:
            return yaml.load(datafile)
        except Exception as exception:
            critical_error('Error parsing file %s\n%s', filepath, exception)


def load_yaml_or_json(filepath):
    with open(filepath, 'r') as datafile:
        try:
            ext = os.path.splitext(filepath)[1]
            if any(ext == x for x in ['.yaml', '.yml']):
                return yaml.load(datafile)
            else: # assume it may be a json file with c comments.
                return yaml.load(remove_comments(datafile.read()).replace('\t', '  '))
        except Exception as exception:
            critical_error('Error parsing file %s\n%s', filepath, exception)


def upper_first(string):
    return string[0].upper() + string[1:] if string else ''


def mkdir_p(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def walk(root):
    """Wrapper around os.walk"""
    exclude_dirs = ['.git', '.hg', '.svn']
    for path, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        yield path, files


def which(program):
    # http://stackoverflow.com/a/377028
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None
