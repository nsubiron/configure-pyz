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


def get_compiler():
    for compiler in SUPPORTED_COMPILERS:
        if util.which(compiler) is not None:
            return compiler
    return SUPPORTED_COMPILERS[0]


def initialize():
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

    with open(util.get_default_settings_file(), 'w+') as  fd:
        fd.write(template)
