"""Generate Makefile"""

import textwrap
import os

from configure import critical_error

HEADER_COMMENT = 'File automatically generated by configure.py, do not modify'

class Writer(object):
    """Makefile writer. Only comments are wrapped."""

    def __init__(self, output, width=80):
        self.output = output
        self.width = width

    def newline(self):
        self.output.write('\n')

    def comment(self, text):
        for line in textwrap.wrap(text, self.width - 2):
            self.output.write('# ' + line + '\n')

    def variable(self, key, value, indent=0):
        if value is None:
            return
        if isinstance(value, list):
            value = ' '.join(filter(None, value))  # Filter out empty strings.
        self._line('%s = %s' % (key, value), indent)

    def default(self, targets):
        self.rule('default', targets)

    def phony(self, targets):
        self.rule('.PHONY', targets)

    def rule(self, name, dependencies=None, commands=None):
        line = [name + ':']
        if dependencies is not None:
          line += dependencies
        self._line(' '.join(line))
        if commands is not None:
          for command in commands:
            self._command(command)

    def _command(self, command):
        self._line('@' + command, indent=1)

    def _line(self, text, indent=0):
        self.output.write('\t' * indent + text + '\n')


def remove_actions(actions_to_remove, container):
    for action in actions_to_remove:
      if action not in container:
        critical_error('Action "%s" missing!', action)
      container.remove(action)

def generate(command_call, ninja_targets, actions, settings, output_dir):
    remove_actions(['ninja', 'makefile'], actions)
    filepath = os.path.join(output_dir, settings.get('makefile_filename'))
    with open(filepath, 'w+') as out:
      makefile = Writer(out)
      makefile.comment(HEADER_COMMENT)
      makefile.newline()
      makefile.variable('CONFIG', ['python'] + command_call + ['$(FLAGS)'])
      makefile.newline()
      makefile.default(['build'])
      makefile.newline()
      makefile.phony(['configure'] + actions)
      makefile.newline()
      makefile.rule('configure', commands=['$(CONFIG) --ninja --makefile'])
      makefile.newline()
      makefile.rule('build', ['configure'], ['ninja'])
      makefile.newline()
      makefile.rule('clean', commands=['ninja -t clean'])
      for action in actions:
        makefile.newline()
        commands = ['$(CONFIG) --' + action]
        makefile.rule(action, commands=commands)
      for target in ninja_targets.global_targets:
        makefile.newline()
        commands = ['ninja ' + target.phony_name]
        makefile.rule(target.phony_name, ['configure'], commands)
