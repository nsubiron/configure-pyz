import json

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
        self._data = {'folders': [], 'build_systems': []}

    def add_path(self, path):
        self._data['folders'].append({'path': path})

    def add_build_system(self, build_system):
        self._data['build_systems'].append(build_system.data)

    def to_string(self):
        return json.dumps(self._data, indent=2)

def main(stdin):
    targets = [line[:line.find(':')] for line in stdin]
    generator = SublimeProject()
    generator.add_path('./..')
    working_dir = '${project_path}/..'
    binary_path = working_dir + '/bin'
    make_all = BuildSystem('make - All', 'make build', working_dir)
    make_all.add_variant('Clean', 'make clean')
    make_all.add_variant('Projects', 'make projects')
    if len(targets) == 1:
      make_all.add_variant('Run', 'make all && %s/%s' % (binary_path, targets[0]))
    generator.add_build_system(make_all)
    for target in targets:
      build_target = BuildSystem(
          'ninja - %s' % target,
          'ninja %s' % target,
          working_dir)
      binary = binary_path + '/' + target
      build_target.add_variant('Run', 'ninja %s && %s' % (target, binary))
      generator.add_build_system(build_target)
    print(generator.to_string())

if __name__ == '__main__':

  import sys

  main(sys.stdin)
