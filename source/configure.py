#!/usr/bin/env python

# configure.pyz Copyright (C) 2014 N. Subiron Montoro
#
# This program comes with ABSOLUTELY NO WARRANTY. This is free software, and you
# are welcome to redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.

"""Generate intermediate build files and projects"""

import __builtin__

import argparse
import glob
import json
import logging
import os
import re
import sys

import util
from util import STRING_TYPES
from util import critical_error
from util import print_out


class Settings(object):
    __DATA = None
    __VARIABLES_EXTENDED = None

    @staticmethod
    def load(filepath):
        Settings.__DATA = {'variables': {}}
        Settings.__DATA.update(util.load_yaml(filepath))
        Settings.__VARIABLES_EXTENDED = dict(Settings.__DATA['variables'])
        root = os.path.abspath('.').replace('\\', '/')
        Settings.__VARIABLES_EXTENDED.update({
            'rootpath': root,
            'rootdir': root,
            'cflags': Settings.get('compiler').get('cflags', ''),
            'lflags': Settings.get('compiler').get('lflags', '')
        })

    @staticmethod
    def get(key):
        if key not in Settings.__DATA:
            if key in Settings.__DATA['variables']:
                return Settings.__DATA['variables'][key]
            critical_error('Key "%s" not found on settings file', key)
        return Settings.__DATA[key]

    @staticmethod
    def expand_variables(obj):
        if isinstance(obj, STRING_TYPES):
            for key, value in Settings.__VARIABLES_EXTENDED.items():
                obj = re.sub(r'(\$\{?%s\}?)' % key, value, obj)
            return obj
        elif isinstance(obj, list):
            return [Settings.expand_variables(x) for x in obj]
        elif isinstance(obj, dict):
            return dict((k, Settings.expand_variables(v)) for k, v in obj.items())
        elif obj is None:
            return obj
        else:
            critical_error('Invalid object %s', type(obj))


class Path(object):
    """Static methods to handle paths"""

    @staticmethod
    def clean(path):
        path = os.path.normpath(path).replace('\\', '/')
        return path[1:] if path.startswith('/') else path

    @staticmethod
    def join(*args):
        return Path.clean(os.path.join(*args))

    @staticmethod
    def target_name(path):
        if not path:
            return Settings.get('root_target_name')
        return Path.clean(path).replace('/', '_')

    @staticmethod
    def expand_patterns(patterns, prefix):
        files = []
        for pattern in patterns:
            files.extend(glob.glob(pattern))
        return [Path.join(prefix, x) for x in files if os.path.isfile(x)]


class Target(object):
    """Build target from source directory tree"""

    def __init__(self, path, files, data=None):
        self.path = path
        self.raw = dict(Settings.get('targets')['defaults'])
        self.raw['target_name'] = Path.target_name(path)
        if data is not None:
            self.raw.update(data)
        self._expand(files)
        if self.raw['type'] != 'executable':
            self.raw['target_name'] += '.a'

    def __getitem__(self, key):
        return self.raw[key]

    def _expand(self, files):
        for key in ['sources', 'headers', 'embedded_data']:
            self.raw[key] = Path.expand_patterns(self.raw[key], self.path)

        def used(x): return x in self.raw['sources'] or x in self.raw['headers'] or x in self.raw['embedded_data']
        files = [Path.join(self.path, x) for x in files]
        self.raw['unused'] = [x for x in files if not used(x)]


class Configuration(object):
    """Compiler configuration in settings file"""

    def __init__(self, data):
        if 'name' not in data:
            critical_error('Missing name of configuration in settings file')
        self.name = data['name']
        self.cflags = Compiler.get_compiler_flags(data)
        self.lflags = Compiler.get_linker_flags(data)

        def getdir(key): return data.get(key, '$buildir/%s_%s' % (key, self.name))
        self.bin = getdir('bin')
        self.lib = getdir('lib')
        self.obj = getdir('obj')


class Compiler(object):
    """Compiler settings in settings files"""

    def __init__(self, settings):
        raw = settings.get('configurations')
        self._configurations = [Configuration(x) for x in raw]
        cdata = settings.get('compiler')
        self._variables = {'cxx': cdata['cxx']}
        self._variables['cflags'] = Compiler.get_compiler_flags(cdata)
        self._variables['lflags'] = Compiler.get_linker_flags(cdata)

    def get_configurations(self):
        return self._configurations

    def get_global_variables(self):
        return self._variables

    @staticmethod
    def get_compiler_flags(data):
        cflags = data.get('cflags', '').split()
        cflags += ['-I' + x for x in data.get('includes', [])]
        cflags += ['-D' + x for x in data.get('defines', [])]
        return ' '.join(cflags)

    @staticmethod
    def get_linker_flags(data):
        return ' '.join(data.get('lflags', '').split())


class HelpGatherer(object):
    def __init__(self, argparser):
        self.command_help = {}
        self.callback = argparser.add_argument
        argparser.add_argument = self.add_argument

    def add_argument(self, *args, **kwargs):
        if 'help' in kwargs:
            self.command_help[args[0]] = util.upper_first(kwargs['help']) + '.'
        self.callback(*args, **kwargs)


def iterate_targets(root):
    """Iterate over the targets generated based on root directory tree"""
    root = os.path.abspath(root)
    logging.info('sourcedir=%s', root)
    target_rules_filename = Settings.get('targets')['filename']
    for path, files in util.walk(root):
        with util.pushd(os.path.join(root, path)):
            relpath = Path.clean(path.replace(root, ''))
            logging.info('Parsing folder: $sourcedir/%s', relpath)
            if not files:
                logging.debug('No files found')
            elif target_rules_filename in files:
                target_rules_filepath = os.path.join(path, target_rules_filename)
                target_rules = util.load_yaml_or_json(target_rules_filepath)
                for gyp_target in target_rules.get('targets', []):
                    yield Target(relpath, files, gyp_target)
            else:
                yield Target(relpath, files)


def main():
    argparser = argparse.ArgumentParser(description=__doc__)
    argparser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s ' + util.get_resource('version.txt'))
    argparser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='print debug information')
    argparser.add_argument(
        '--targets',
        action='store_true',
        help='write out targets (for debugging purposes)')
    argparser.add_argument(
        '--hello-world',
        action='store_true',
        dest='init_hello_world',
        help='initialize this folder with a "hello world" project')
    settings_file_group = argparser.add_argument_group('configuration file')
    default_settings = util.get_default_settings_file()
    settings_file_group.add_argument(
        '-f',
        metavar='FILE',
        dest='settings_file',
        default=default_settings,
        help='path to an existing config file, defaults to %s' % default_settings)
    settings_file_group.add_argument(
        '-g',
        action='store_true',
        dest='init_settings_file',
        help='generate a default %s file' % default_settings)
    generators_group = argparser.add_argument_group('generators')
    help_gatherer = HelpGatherer(generators_group)
    generators_group.add_argument(
        '--embed',
        action='store_true',
        help='embed resources (experimental)')
    generators_group.add_argument(
        '--ninja',
        action='store_true',
        help='generate build.ninja')
    generators_group.add_argument(
        '--makefile',
        action='store_true',
        help='generate Makefile')
    generators_group.add_argument(
        '--doxyfile',
        action='store_true',
        help='generate doxygen\'s Doxyfile')
    generators_group.add_argument(
        '--sublime',
        action='store_true',
        help='generate Sublime Text project')
    generators_group.add_argument(
        '--codeblocks',
        action='store_true',
        help='generate CodeBlocks projects (experimental)')
    args = argparser.parse_args()

    loglevel = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(format='%(levelname)s: %(message)s', level=loglevel)

    try:
        builtin_open = __builtin__.open

        def open_hook(*args, **kwargs):
            logging.debug('Open file: %s', args[0])
            try:
                return builtin_open(*args, **kwargs)
            except Exception as exception:
                critical_error(exception)
        __builtin__.open = open_hook
    except Exception as exception:
        critical_error('Hook to "open" failed: %s', exception)

    if args.init_settings_file or args.init_hello_world:
        print_out('Generate %s.' % args.settings_file)
        import init
        init.init_settings_file(args.settings_file)
    if args.init_hello_world:
        print_out('Generate "Hello World" code.')
        init.init_hello_world()
        args.makefile = True

    if args.settings_file is None:
        print_out('Missing settings.')
        argparser.print_usage()
        return

    actions = ['targets', 'embed', 'ninja', 'makefile', 'doxyfile', 'sublime', 'codeblocks']
    action_count = sum(getattr(args, x) for x in actions)

    if action_count == 0:
        print_out('Nothing to be done.')
        argparser.print_usage()
        return

    Settings.load(args.settings_file)

    targets = [x for x in iterate_targets(Settings.get('sourcedir'))]
    logging.info('%i targets found', len(targets))

    if args.targets:
        data = {'targets': [x.raw for x in targets]}
        targets_file = os.path.join(Settings.get('builddir'), 'targets.json')
        util.mkdir_p(os.path.dirname(targets_file))
        with open(targets_file, 'w+') as out:
            out.write(json.dumps(data, indent=2))
        print_out('Targets saved to %s.' % targets_file)
        if action_count == 1:
            return

    if args.embed:
        print_out(help_gatherer.command_help['--embed'])
        import embedder
        embedder.embed(targets, Settings.get('sourcedir'))
        print_out("Targets may have changed, re-run configure.pyz to update.")
        return

    compiler = Compiler(Settings)

    if args.doxyfile:
        print_out(help_gatherer.command_help['--doxyfile'])
        import doxygen
        doxygen.generate(Settings)

    if args.ninja or args.makefile or args.sublime:
        print_out(help_gatherer.command_help['--ninja'])
        import ninja
        ninja_targets = ninja.generate(targets, Settings, compiler, '.')

        if args.makefile:
            print_out(help_gatherer.command_help['--makefile'])
            import makefile
            this = Path.clean(os.path.relpath(sys.argv[0]))
            command_call = [this, '-f', args.settings_file]
            makefile.generate(command_call, ninja_targets, actions, Settings, '.')

        if args.sublime:
            print_out(help_gatherer.command_help['--sublime'])
            import sublime
            sublime.generate(ninja_targets, Settings)

    if args.codeblocks:
        print_out(help_gatherer.command_help['--codeblocks'])
        import codeblocks
        codeblocks.generate(targets, Settings, compiler)


if __name__ == '__main__':

    main()
