# configure.pyz Copyright (C) 2014 N. Subiron Montoro
#
# This program comes with ABSOLUTELY NO WARRANTY. This is free software, and you
# are welcome to redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.

"""Generate Sublime Text project file"""

import json
import os
import re

from configure import Path

import util
from util import critical_error


class BuildSystem(object):
    def __init__(self, name, shell_cmd, working_dir):
        self.data = {'name': name, 'shell_cmd': shell_cmd}
        self.data['working_dir'] = working_dir
        self.data['file_regex'] = '^(..[^:]*):([0-9]+):?([0-9]+)?:? (.*)$'
        self.data['variants'] = []

    def add_variant(self, name, shell_cmd):
        self.data['variants'].append({'name': name, 'shell_cmd': shell_cmd})


def get_bin(config_name, settings):
    for item in settings.get('configurations'):
        if item['name'] == config_name:
            return settings.expand_variables(item['bin'])
    critical_error('Configuration "%s" not found', config_name)


def generate(ninja_targets, settings):
    project_name = settings.get('project_name')
    working_dir = '$rootdir'

    make_all = BuildSystem('make - ' + project_name, 'make build', working_dir)
    make_all.add_variant('All', 'make all')
    make_all.add_variant('Clean', 'make clean')
    make_all.add_variant('Sublime Text Project', 'make sublime')
    make_all.add_variant('Doxygen Documentation', 'make doxygen')
    ninja_all = BuildSystem('ninja - ' + project_name, 'ninja', working_dir)
    ninja_all.add_variant('All', 'ninja all')
    ninja_all.add_variant('Clean', 'ninja -t clean')
    ninja_all.add_variant('Doxygen Documentation', 'ninja doxygen')

    build_systems = [make_all.data, ninja_all.data]

    for target in ninja_targets.build_targets:
        build_target = BuildSystem(
            target.config + ' - ' + target.name,
            'ninja %s' % target.phony_name,
            working_dir)
        bindir = get_bin(target.config, settings)
        binary = Path.join(working_dir, bindir, target.name)
        build_target.add_variant(
            'Run',
            'ninja %s && %s' % (target.phony_name, binary))
        build_target.add_variant(
            'Clean',
            'ninja -t clean %s' % target.phony_name)
        build_systems.append(build_target.data)

    sublime_settings = settings.get('sublime')

    template_filename = settings.expand_variables(sublime_settings.get('project_template', None))
    if template_filename is not None:
        with open(template_filename, 'r') as fd:
            template = fd.read()
        if not template:
            critical_error('%s seems to be empty', template_filename)
    else:
        template = util.get_resource('defaults/tmpl.sublime-project')

    project = re.sub(
        r'(\$build_systems)',
        json.dumps(build_systems, indent=4, separators=(',', ': ')),
        template)
    project = settings.expand_variables(project)

    filename = settings.expand_variables('$projectsdir/$project_name.sublime-project')
    util.mkdir_p(os.path.dirname(filename))
    with open(filename, 'w+') as out:
        out.write(project)
