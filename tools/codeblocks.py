import logging
import os
import platform

import xml.dom.minidom as minidom
import xml.etree.cElementTree as ElementTree

from configure import Path, Settings

EXECUTABLE_EXT = '.exe' if platform.system().lower() == 'windows' else ''

def rpath(path, start=Settings.get('projectsdir')):
    return Path.clean(os.path.relpath(Settings.expand_variables(path), start))

def join_path(*args):
    return rpath(os.path.join(*args))

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
          subelement('Add', compiler, {'option': option})

    def add_linker(self, options, libraries):
        linker = subelement('Linker', self.root)
        for library in libraries:
          subelement('Add', linker, {'library': library})
        for option in options:
          subelement('Add', linker, {'option': option})


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


def create_library(target, cflags, configurations):
    title = target['target_name']
    project = CodeBlocksProject(title, compiler=COMPILER)
    for config in configurations:
      build_target = project.add_target(title + ' - ' + config.name)
      outlib = join_path(config.lib, title)
      output = {'output': outlib}
      output['prefix_auto'] = '0'
      output['extension_auto'] = '1'
      build_target.add_option(output)
      build_target.add_option({'working_dir': ''})
      build_target.add_option({'object_output': rpath(config.obj)})
      build_target.add_option({'type': '2'})
      build_target.add_option({'compiler': COMPILER})
      build_target.add_option({'createDefFile': '1'})
      build_target.add_compiler([cflags, config.cflags])
    for item in ['builddir', 'source']:
      project.add_variable(item, rpath(Settings.get(item)))
    for filename in target['sources'] + target['headers']:
      project.add_file(join_path(Settings.get('source'), filename))
    return project

def create_executable(target, cflags, lflags, configurations):
    title = target['target_name']
    project = CodeBlocksProject(title, compiler=COMPILER)
    for config in configurations:
      build_target = project.add_target(title + ' - ' + config.name)
      outbin = join_path(config.bin, title) + EXECUTABLE_EXT
      output = {'output': outbin}
      output['prefix_auto'] = '0'
      output['extension_auto'] = '1'
      build_target.add_option(output)
      build_target.add_option({'working_dir': rpath(config.bin)})
      build_target.add_option({'object_output': rpath(config.obj)})
      build_target.add_option({'type': '1'})
      build_target.add_option({'compiler': COMPILER})
      build_target.add_compiler([cflags, config.cflags])
      libs = [join_path(config.lib, x) for x in target['dependencies']]
      build_target.add_linker([lflags, config.lflags], libs)
    for item in ['builddir', 'source']:
      project.add_variable(item, rpath(Settings.get(item)))
    for filename in target['sources'] + target['headers']:
      project.add_file(join_path(Settings.get('source'), filename))
    return project

def generate(targets, compiler):
    global COMPILER
    COMPILER = Settings.get('codeblocks_compiler_name')
    projectsdir = Settings.get('projectsdir')
    workspace = CodeBlocksWorkspace('all')
    configurations = compiler.get_configurations()
    cvars = compiler.get_global_variables()
    cflags = cvars['cflags']
    lflags = cvars['lflags']
    for target in targets:
      target_type = target['type']
      if target_type == 'executable':
        project = create_executable(target, cflags, lflags, configurations)
      elif target_type == 'static_library':
        project = create_library(target, cflags, configurations)
      else:
        logging.warning('Target ignored: type "%s" not implemented', target_type)
        continue
      workspace.add_project(project.basename)
      with open(os.path.join(projectsdir, project.basename), 'w+') as out:
        out.write(project.tostring())
    with open(os.path.join(projectsdir, workspace.basename), 'w+') as out:
      out.write(workspace.tostring())
