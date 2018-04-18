# configure.pyz Copyright (C) 2014 N. Subiron Montoro
#
# This program comes with ABSOLUTELY NO WARRANTY. This is free software, and you
# are welcome to redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.

"""Helper to initialize setting files"""


import logging
import os
import re

import util


SUPPORTED_COMPILERS = ['g++', 'clang++']


def critical_error_if_file_exists(path):
    if os.path.isfile(path):
        util.critical_error('"%s" already exists', path)


def get_compiler():
    for compiler in SUPPORTED_COMPILERS:
        if util.which(compiler) is not None:
            return compiler
    return SUPPORTED_COMPILERS[0]


def init_settings_file(filepath):
    critical_error_if_file_exists(filepath)

    if util.which('ninja') is None:
        logging.warning('cannot find ninja')

    varlist = {
        'project_name': os.path.basename(os.getcwd()),
        'sourcedir': 'source',
        'cxx': get_compiler()
    }

    template = util.get_resource('defaults/configure.yaml')

    for key, value in varlist.items():
        template = re.sub(r'(%%%s%%)' % key, value, template)

    with open(filepath, 'w+') as fd:
        fd.write(template)


def init_hello_world():
    targets_filepath = 'source/hello_world/targets.json'
    helloworld_filepath = 'source/hello_world/hello_world.cpp'
    critical_error_if_file_exists(helloworld_filepath)
    critical_error_if_file_exists(targets_filepath)
    util.mkdir_p(os.path.dirname(targets_filepath))

    with open(targets_filepath, 'w+') as fd:
        fd.write(util.get_resource('defaults/targets.json'))
    with open(helloworld_filepath, 'w+') as fd:
        fd.write(util.get_resource('defaults/hello_world.cpp'))
