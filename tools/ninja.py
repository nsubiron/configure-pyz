"""Generate build.ninja file"""

import logging
import os
import platform

from collections import namedtuple

import ninja_syntax

OUTPUT_FILE = 'build.ninja'

RULES_FILEPATH = os.path.join(os.path.dirname(__file__), 'rules.ninja')

EXECUTABLE_EXT = '.exe' if platform.system().lower() == 'windows' else ''

BuildTarget = namedtuple('BuildTarget', 'config, name, phony_name')

class Ninja(object):
    def __init__(self, out):
        self._writer = ninja_syntax.Writer(out)
        self._writer.comment('Automatic generated file, do not modify.')
        self._writer.newline()
        self._writer.include(os.path.relpath(RULES_FILEPATH))
        self._current_config = None
        self._targets = {}

    def add_variables(self, dictionary):
        self._writer.newline()
        for key, value in dictionary.items():
          self._writer.variable(key, value)

    def open_configuration(self, name, bin, lib, obj):
        self._writer.newline()
        self._writer.comment(name)
        self.add_variables({'bin': bin, 'lib': lib, 'obj': obj})
        self._current_config = name
        self._targets[name] = []

    def add_static_library(self, target, cflags=None):
        self._writer.newline()
        objects = [self._add_object_file(x, cflags) for x in target['sources']]
        out = '$lib/' + target['target_name']
        self._writer.build(out, 'ar', objects)

    def add_executable(self, target, cflags=None, lflags=None):
        self._writer.newline()
        target_name = target['target_name']
        deps = [self._add_object_file(x, cflags) for x in target['sources']]
        deps += ['$lib/' + x for x in target['dependencies']]
        out = '$bin/' + target_name + EXECUTABLE_EXT
        variables = {'lflags': '$lflags ' + lflags} if lflags else None
        self._writer.build(out, 'link', deps, variables=variables)
        phony_name = target_name + '_' + self._current_config
        self._writer.build(phony_name, 'phony', out)
        self._targets[self._current_config].append(phony_name)
        return BuildTarget(self._current_config, target_name, phony_name)

    def add_build_targets(self):
        self._writer.newline()
        self._writer.comment('other targets')
        self._writer.newline()
        for name, targets in self._targets.items():
          self._writer.build(name, 'phony', targets)
        self._writer.newline()
        self._writer.build('$builddir/Doxyfile', 'sed', '$doxyfile')
        self._writer.build('doxygen', 'doxygen', '$builddir/Doxyfile')
        self._writer.newline()
        self._writer.build('all', 'phony', self._targets.keys())
        self._writer.default(self._targets.keys()[0])

    def _add_object_file(self, source, cflags=None):
        out = '$obj/%s.o' % os.path.splitext(source)[0]
        variables = {'cflags': '$cflags ' + cflags} if cflags else None
        self._writer.build(out, 'cxx', '$source/' + source, variables=variables)
        return out


def generate(targets, variables, compiler, output_dir):
    build_targets = []
    with open(os.path.join(output_dir, OUTPUT_FILE), 'w+') as out:
      ninja = Ninja(out)
      ninja.add_variables(variables)
      ninja.add_variables(compiler.get_global_variables())
      for config in compiler.get_configurations():
        ninja.open_configuration(config.name, config.bin, config.lib, config.obj)
        for target in targets:
          if not target['sources']:
            logging.warning('Target ignored: no sources found')
          target_type = target['type']
          if target_type == 'executable':
            btarget = ninja.add_executable(target, config.cflags, config.lflags)
            build_targets.append(btarget)
          elif target_type == 'static_library':
            ninja.add_static_library(target, config.cflags)
          else:
            logging.warning('Target ignored: type "%s" not implemented', target_type)
      ninja.add_build_targets()
    return build_targets
