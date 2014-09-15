#!/usr/bin/env python
"""Generate intermediate build files and projects"""

import argparse
import fnmatch
import json
import logging
import os
import re
import sys

def print_out(message, prefix=os.path.basename(__file__)):
    print('%s: %s' % (prefix, message))

def critical_error(message, *args):
    logging.critical(message, *args)
    sys.exit(1)

def remove_comments(string):
    """Remove C comments from string. See http://stackoverflow.com/a/18381470"""
    pattern = r'(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)'
    regex = re.compile(pattern, re.MULTILINE|re.DOTALL)
    replacer = lambda match: match.group(1) if match.group(2) is None else ''
    return regex.sub(replacer, string)

def upper_first(string):
    return string[0].upper() + string[1:] if string else ''

def load_json(filepath):
    with open(filepath, 'r') as datafile:
      try:
        return json.loads(remove_comments(datafile.read()))
      except Exception as exception:
        critical_error('Error parsing file %s\n%s', filepath, exception)

def mkdir_p(path):
    if not os.path.isdir(path):
      os.makedirs(path)

def walk(root):
    """Wrapper around os.walk"""
    exclude_dirs = ['.git', '.hg', '.svn']
    for path, dirs, files in os.walk(root):
      dirs[:] = [d for d in dirs if not d in exclude_dirs]
      yield path, files

class Settings(object):
    __DATA = None

    @staticmethod
    def load(filepath):
        Settings.__DATA = {'variables': {}}
        Settings.__DATA.update(load_json(filepath))

    @staticmethod
    def get(key):
        if key not in Settings.__DATA:
          if key in Settings.__DATA['variables']:
            return Settings.__DATA['variables'][key]
          critical_error('Key "%s" not found on settings file', key)
        return Settings.__DATA[key]

    @staticmethod
    def expand_variables(string):
        for key, value in Settings.get('variables').items():
          string = re.sub(r'(\$\{?%s\}?)' % key, value, string)
        return string


class Path(object):
    """Static methods to handle paths"""

    @staticmethod
    def clean(path):
        path = path.replace('\\', '/')
        return path[1:] if path.startswith('/') else path

    @staticmethod
    def join(*args):
        return Path.clean(os.path.join(*args))

    @staticmethod
    def target_name(path):
        path = Path.clean(path)
        return Settings.get('rootlib') if not path else path.replace('/', '_')

    @staticmethod
    def expand_patterns(patterns, path, files):
        regex = re.compile('|'.join(fnmatch.translate(p) for p in patterns))
        return [Path.join(path, x) for x in files if regex.match(x) is not None]


class Target(object):
    """Build target from source directory tree"""

    def __init__(self, path, files, data=None):
        self.path = path
        self.raw = dict(Settings.get('target_defaults'))
        self.raw['target_name'] = Path.target_name(path)
        if data is not None:
          self.raw.update(data)
        self._expand(files)
        if self.raw['type'] != 'executable':
          self.raw['target_name'] += '.a'

    def __getitem__(self, key):
        return self.raw[key]

    def _expand(self, files):
        for key in ['sources', 'headers', 'unused']:
          self.raw[key] = Path.expand_patterns(self.raw[key], self.path, files)
        used = lambda x: x in self.raw['sources'] or x in self.raw['headers']
        self.raw['unused'] = [x for x in self.raw['unused'] if not used(x)]


class Configuration(object):
    """Compiler configuration in settings file"""

    def __init__(self, data):
        if 'name' not in data:
          critical_error('Missing name of configuration in settings file')
        self.name = data['name']
        self.cflags = Compiler.get_compiler_flags(data)
        self.lflags = Compiler.get_linker_flags(data)
        getdir = lambda key: data.get(key, '$buildir/%s_%s' % (key, self.name))
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
        cflags = list(data.get('cflags', []))
        cflags += ['-I' + x for x in data.get('includes', [])]
        cflags += ['-D' + x for x in data.get('defines', [])]
        return ' '.join(cflags)

    @staticmethod
    def get_linker_flags(data):
        return ' '.join(data.get('lflags', []))


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        self.command_help = {}
        super(ArgumentParser, self).__init__(*args, **kwargs)

    def add_argument(self, *args, **kwargs):
        if 'help' in kwargs:
          self.command_help[args[0]] = upper_first(kwargs['help']) + '.'
        super(ArgumentParser, self).add_argument(*args, **kwargs)


def iterate_targets(root):
    """Iterate over the targets generated based on root directory tree"""
    root = os.path.abspath(root)
    logging.info('sourcedir=%s', root)
    rules_filename = Settings.get('rules_filename')
    for path, files in walk(root):
      relpath = Path.clean(path.replace(root, ''))
      logging.info('Parsing folder: $sourcedir/%s', relpath)
      if not files:
        logging.debug('No files found')
      elif rules_filename in files:
        gypfilepath = os.path.join(path, rules_filename)
        gypdata = load_json(gypfilepath)
        for gyp_target in gypdata.get('targets', []):
          if 'target_name' in gyp_target:
            yield Target(relpath, files, gyp_target)
          else:
            logging.warning(
                'Missing target_name in %s, target ignored',
                gypfilepath)
      else:
        yield Target(relpath, files)

def main():
    argparser = ArgumentParser(description=__doc__)
    argparser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='print debug information')
    argparser.add_argument(
        '-f',
        metavar='SETTINGS_FILE',
        dest='settings_file',
        default=os.path.join(os.path.dirname(__file__), 'settings.json'),
        help='input settings')
    argparser.add_argument(
        '--targets',
        action='store_true',
        help='generate targets.json file')
    argparser.add_argument(
        '--ninja',
        action='store_true',
        help='generate build.ninja file')
    argparser.add_argument(
        '--sublime',
        action='store_true',
        help='generate Sublime Text project file')
    argparser.add_argument(
        '--codeblocks',
        action='store_true',
        help='generate CodeBlocks project files (experimental)')
    args = argparser.parse_args()

    action_count = sum([args.targets, args.ninja, args.sublime, args.codeblocks])

    if action_count == 0:
      print_out('%s: Nothing to be done.' % os.path.basename(__file__))
      return

    loglevel = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(format='%(levelname)s: %(message)s', level=loglevel)

    builtin_open = __builtins__.open
    def open_hook(*args, **kwargs):
        logging.debug('Open file: %s', args[0])
        try:
          return builtin_open(*args, **kwargs)
        except Exception as exception:
          critical_error(exception)
    __builtins__.open = open_hook

    Settings.load(args.settings_file)

    if args.targets or args.sublime or args.codeblocks:
      mkdir_p(Settings.get('projectsdir'))

    targets = [x for x in iterate_targets(Settings.get('sourcedir'))]
    logging.info('%i targets found', len(targets))

    if args.targets:
      print_out(argparser.command_help['--targets'])
      data = {'targets': [x.raw for x in targets]}
      targets_file = os.path.join(Settings.get('projectsdir'), 'targets.json')
      with open(targets_file, 'w+') as out:
        out.write(json.dumps(data, indent=2))
      if action_count == 1:
        return

    compiler = Compiler(Settings)

    if args.ninja or args.sublime:
      print_out(argparser.command_help['--ninja'])
      import ninja
      variables = Settings.get('variables')
      build_targets = ninja.generate(targets, variables, compiler, '.')

      if args.sublime:
        print_out(argparser.command_help['--sublime'])
        import sublime
        sublime.generate(build_targets, Settings)

    if args.codeblocks:
      print_out(argparser.command_help['--codeblocks'])
      import codeblocks
      codeblocks.generate(targets, Settings, compiler)


if __name__ == '__main__':

    main()
