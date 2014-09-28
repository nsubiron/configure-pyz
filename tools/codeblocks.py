import logging
import os
import platform

import xml.dom.minidom as minidom
import xml.etree.cElementTree as ElementTree

from configure import Path

EXECUTABLE_EXT = '.exe' if platform.system().lower() == 'windows' else ''

class CodeBlocks(object):
    """Helper class"""

    def __init__(self, settings, compiler):
        self._settings = settings
        self.compiler_name = settings.get('codeblocks_compiler_name')
        self.projectsdir = settings.get('projectsdir')
        self.configurations = compiler.get_configurations()
        cvars = compiler.get_global_variables()
        self.cflags = cvars['cflags']
        self.lflags = cvars['lflags']

    def makepath(self, *args):
        path = self._settings.expand_variables(os.path.join(*args))
        return Path.clean(os.path.relpath(path, self.projectsdir))


def subelement(name, parent, dictionary={}):
    subelm = ElementTree.SubElement(parent, name)
    for key, value in dictionary.items():
      subelm.set(key, value)
    return subelm

class XmlFile(object):
    def __init__(self, rootname, basename):
        self.basename = basename
        self.root = ElementTree.Element(rootname)

    def tostring(self):
        xmlstring = ElementTree.tostring(self.root)
        return minidom.parseString(xmlstring).toprettyxml(indent='  ')


class CodeBlocksWorkspace(XmlFile):
    def __init__(self, title):
        XmlFile.__init__(self, 'CodeBlocks_workspace_file', title + '.workspace')
        self.workspace = subelement('Workspace', self.root, {'title': title})

    def add_project(self, filename):
        subelement('Project', self.workspace, {'filename': filename})


class BuildTarget(object):
    def __init__(self, parent, title):
        self.root = subelement('Target', parent, {'title': title})

    def add_option(self, dictionary):
        subelement('Option', self.root, dictionary)

    def add_compiler(self, options):
        compiler = subelement('Compiler', self.root)
        for option in options:
          if option and not option.isspace():
            subelement('Add', compiler, {'option': option.strip()})

    def add_linker(self, options, libraries):
        linker = subelement('Linker', self.root)
        for library in libraries:
          if library and not library.isspace():
            subelement('Add', linker, {'library': library.strip()})
        for option in options:
          if option and not option.isspace():
            subelement('Add', linker, {'option': option.strip()})


class CodeBlocksProject(XmlFile):
    def __init__(self, title, compiler):
        XmlFile.__init__(self, 'CodeBlocks_project_file', title + '.cbp')
        subelement('FileVersion', self.root, {'major': '1', 'minor': '6'})
        self.project = subelement('Project', self.root)
        subelement('Option', self.project, {'title': title})
        subelement('Option', self.project, {'compiler': compiler})
        subelement('Option', self.project, {'execution_dir': '..'})
        self.build = subelement('Build', self.project)
        self.environment = subelement('Environment', self.build)

    def add_target(self, title):
        return BuildTarget(self.build, title)

    def add_variable(self, name, value):
        subelement('Variable', self.environment, {'name': name, 'value': value})

    def add_file(self, filename):
        subelement('Unit', self.project, {'filename': filename})


def create_base_project(target, codeblocks):
    project = CodeBlocksProject(target['target_name'], codeblocks.compiler_name)
    for name in ['builddir', 'sourcedir']:
      project.add_variable(name, codeblocks.makepath('$' + name))
    for filename in target['sources'] + target['headers']:
      project.add_file(codeblocks.makepath('$sourcedir', filename))
    return project

def create_library(target, compiler, codeblocks):
    project = create_base_project(target, codeblocks)
    title = target['target_name']
    for config in codeblocks.configurations:
      build_target = project.add_target(title + ' - ' + config.name)
      outlib = codeblocks.makepath(config.lib, title)
      output = {'output': outlib}
      output['prefix_auto'] = '0'
      output['extension_auto'] = '1'
      build_target.add_option(output)
      build_target.add_option({'working_dir': ''})
      build_target.add_option({'object_output': codeblocks.makepath(config.obj)})
      build_target.add_option({'type': '2'})
      build_target.add_option({'compiler': codeblocks.compiler_name})
      build_target.add_option({'createDefFile': '1'})
      cflags = compiler.get_compiler_flags(target.raw)
      build_target.add_compiler([codeblocks.cflags, config.cflags, cflags])
    return project

def create_executable(target, compiler, codeblocks):
    project = create_base_project(target, codeblocks)
    title = target['target_name']
    for config in codeblocks.configurations:
      build_target = project.add_target(title + ' - ' + config.name)
      outbin = codeblocks.makepath(config.bin, title) + EXECUTABLE_EXT
      output = {'output': outbin}
      output['prefix_auto'] = '0'
      output['extension_auto'] = '1'
      build_target.add_option(output)
      build_target.add_option({'working_dir': codeblocks.makepath(config.bin)})
      build_target.add_option({'object_output': codeblocks.makepath(config.obj)})
      build_target.add_option({'type': '1'})
      build_target.add_option({'compiler': codeblocks.compiler_name})
      cflags = compiler.get_compiler_flags(target.raw)
      build_target.add_compiler([codeblocks.cflags, config.cflags, cflags])
      cleanlib = lambda x: x[2:] if x.startswith('-l') else codeblocks.makepath(config.lib, x)
      libs = [cleanlib(x) for x in target['dependencies']]
      lflags = compiler.get_linker_flags(target.raw)
      build_target.add_linker([codeblocks.lflags, config.lflags, lflags], libs)
    return project

def generate(targets, settings, compiler):
    codeblocks = CodeBlocks(settings, compiler)
    workspace = CodeBlocksWorkspace('all')
    for target in targets:
      if not target['headers'] and not target['sources']:
        continue
      target_type = target['type']
      if target_type == 'executable':
        project = create_executable(target, compiler, codeblocks)
      elif target_type == 'static_library':
        project = create_library(target, compiler, codeblocks)
      else:
        logging.warning('Target ignored: type "%s" not implemented', target_type)
        continue
      workspace.add_project(project.basename)
      with open(os.path.join(codeblocks.projectsdir, project.basename), 'w+') as out:
        out.write(project.tostring())
    with open(os.path.join(codeblocks.projectsdir, workspace.basename), 'w+') as out:
      out.write(workspace.tostring())
