"""Generate Sublime Text project file"""

import json
import os

from configure import Path
from configure import critical_error

class BuildSystem(object):
    def __init__(self, name, shell_cmd, working_dir):
        self.data = {'name': name, 'shell_cmd': shell_cmd}
        self.data['working_dir'] = working_dir
        self.data['file_regex'] = '^(..[^:]*):([0-9]+):?([0-9]+)?:? (.*)$'
        self.data['variants'] = []

    def add_variant(self, name, shell_cmd):
        self.data['variants'].append({'name': name, 'shell_cmd': shell_cmd})


class SublimeProject(object):
    def __init__(self):
        self._data = {'folders': [], 'build_systems': [], 'settings': {}}

    def add_path(self, path, folder_exclude_patterns=None):
        folder = {'path': path}
        if folder_exclude_patterns is not None:
          folder['folder_exclude_patterns'] = folder_exclude_patterns
        self._data['folders'].append(folder)

    def add_settings(self, key, value):
        self._data['settings'][key] = value

    def add_build_system(self, build_system):
        self._data['build_systems'].append(build_system.data)

    def to_string(self):
        return json.dumps(self._data, indent=2)


def get_bin(config_name, settings):
    for item in settings.get('configurations'):
      if item['name'] == config_name:
        return settings.expand_variables(item['bin'])
    critical_error('Configuration "%s" not found', config_name)

def generate(build_targets, settings):
    output_dir = settings.get('projectsdir')
    relpath = Path.clean(os.path.relpath(os.getcwd(), output_dir))
    project = SublimeProject()
    project.add_path(relpath, [settings.get('builddir')])

    working_dir = Path.join('${project_path}', relpath)

    make_all = BuildSystem('make - All', 'make build', working_dir)
    make_all.add_variant('All', 'make all')
    make_all.add_variant('Clean', 'make clean')
    make_all.add_variant('Project', 'make sublime')
    make_all.add_variant('Doxygen', 'make doxygen')
    ninja_all = BuildSystem('ninja - All', 'ninja', working_dir)
    ninja_all.add_variant('Clean', 'ninja -t clean')
    ninja_all.add_variant('Doxygen', 'ninja doxygen')
    project.add_build_system(make_all)
    project.add_build_system(ninja_all)

    for target in build_targets:
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
      project.add_build_system(build_target)

    extension = '.sublime-project'
    filename = os.path.join(output_dir, settings.get('project_name') + extension)
    with open(filename, 'w+') as out:
      out.write(project.to_string())
