#!/usr/bin/python

"""Generate Sublime Text project file"""

import json
import os

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

def main(stdin, debug=None):
    targets = [line[:line.find(':')] for line in stdin]
    generator = SublimeProject()
    working_dir = os.path.abspath('.')
    generator.add_path(working_dir, ['build'])
    if debug is not None:
      dflag = ' DEBUG=' + debug
      main_target = debug
      gdb_command = 'gdb --interpreter=mi ./bin/' + debug
      generator.add_settings('sublimegdb_workingdir', working_dir)
      generator.add_settings('sublimegdb_commandline', gdb_command)
    else:
      main_target = targets[0] if len(targets) == 1 else None
      dflag = ''
    binary_path = os.path.join(working_dir, 'bin')
    make_all = BuildSystem('make - All', 'make%s build' % dflag, working_dir)
    make_all.add_variant('Clean', 'make clean')
    make_all.add_variant('Projects', 'make%s projects' % dflag)
    make_all.add_variant('Documentation', 'make doxygen')
    ninja_all = BuildSystem('ninja - All', 'ninja', working_dir)
    ninja_all.add_variant('Clean', 'ninja -t clean')
    if main_target is not None:
      run_command = os.path.join(binary_path, main_target)
      make_all.add_variant('Run', 'make%s build && %s' % (dflag, run_command))
      ninja_all.add_variant('Run', 'ninja && %s' % run_command)
    generator.add_build_system(make_all)
    generator.add_build_system(ninja_all)
    for target in targets:
      build_target = BuildSystem(
          'ninja - %s' % target,
          'ninja %s' % target,
          working_dir)
      binary = os.path.join(binary_path, target)
      build_target.add_variant('Run', 'ninja %s && %s' % (target, binary))
      generator.add_build_system(build_target)
    print(generator.to_string())

if __name__ == '__main__':

    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    dflag_help = 'Add settings for SublimeGDB for the given target'
    parser.add_argument('--debug', '-d', metavar='target', help=dflag_help)
    args = parser.parse_args()

    main(sys.stdin, args.debug)
