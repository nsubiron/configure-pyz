import os
import xml.dom.minidom as minidom
import xml.etree.cElementTree as ElementTree

# @todo Workaround, to be changed.
import configure as util

# @todo Default compiler ??
COMPILER = 'cygwin_g_compiler'

CFLAGS = '-Wall -std=c++11 -ggdb -D_DEBUG'
LFLAGS = '-Wall -rdynamic -pthread'

GYP = 'rules.gyp'

SRC = 'source'
BIN = 'bin'
LIB = 'lib'
OBJ = 'obj'

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

    def add_compiler(self, cflags):
        compiler = subelement('Compiler', self.root)
        subelement('Add', compiler, {'option': cflags})

    def add_linker(self, lflags, libraries):
        linker = subelement('Linker', self.root)
        for library in libraries:
          subelement('Add', linker, {'library': library})
        subelement('Add', linker, {'option': lflags})


class CodeBlocksProject(XmlFile):
    def __init__(self, title, compiler, execution_dir):
        XmlFile.__init__(self, 'CodeBlocks_project_file', title + '.cbp')
        subelement('FileVersion', self.root, {'major': '1', 'minor': '6'})
        self.project = subelement('Project', self.root)
        subelement('Option', self.project, {'title': title})
        subelement('Option', self.project, {'compiler': compiler})
        subelement('Option', self.project, {'execution_dir': execution_dir})
        self.build = subelement('Build', self.project)

    def add_target(self, title):
        return BuildTarget(self.build, title)

    def add_file(self, filename):
        subelement('Unit', self.project, {'filename': filename})


def create_library(root, path, files, builddir):
    title = util.basename_from_path(path.replace(root, ''))
    project = CodeBlocksProject(title, compiler=COMPILER, execution_dir=root)
    build_target = project.add_target(title)
    output = {'output': os.path.join(builddir, LIB, title)}
    output['prefix_auto'] = '0'
    output['extension_auto'] = '1'
    build_target.add_option(output)
    build_target.add_option({'working_dir': root})
    build_target.add_option({'object_output': os.path.join(builddir, OBJ)})
    build_target.add_option({'type': '2'})
    build_target.add_option({'compiler': COMPILER})
    build_target.add_option({'createDefFile': '1'})
    build_target.add_compiler(CFLAGS + ' -I ' + root)
    for filename in files:
      project.add_file(os.path.join(path, filename))
    return project

def create_executable(root, path, files, builddir):
    files.remove(GYP)
    title = util.basename_from_path(path.replace(root, ''))
    project = CodeBlocksProject(title, compiler=COMPILER, execution_dir=root)
    gypfile_path = os.path.join(path, GYP)
    for target, dependencies in util.get_targets(gypfile_path):
      build_target = project.add_target(target)
      output = {'output': os.path.join(builddir, BIN, target)}
      output['prefix_auto'] = '0'
      output['extension_auto'] = '1'
      build_target.add_option(output)
      build_target.add_option({'working_dir': root})
      build_target.add_option({'object_output': os.path.join(builddir, OBJ)})
      build_target.add_option({'type': '1'})
      build_target.add_option({'compiler': COMPILER})
      build_target.add_compiler(CFLAGS + ' -I ' + root)
      libraries = [os.path.join(builddir, LIB, x) for x in dependencies]
      build_target.add_linker(LFLAGS, libraries)
    for filename in files:
      project.add_file(os.path.join(path, filename))
    return project

def main():
    root = os.path.abspath('.')
    builddir = os.path.join(root, 'build', 'codeblocks')
    workspace = CodeBlocksWorkspace('all')
    source = os.path.join(root, SRC)
    for path, _, files in util.walk(source, ['*.cpp', '*.cc', '*.h', GYP]):
      if files:
        if GYP in files:
          project = create_executable(source, path, files, builddir)
        else:
          project = create_library(source, path, files, builddir)
        workspace.add_project(project.basename)
        with open(os.path.join(root, 'projects', project.basename), 'w+') as out:
          out.write(project.tostring())
    with open(os.path.join(root, 'projects', workspace.basename), 'w+') as out:
      out.write(workspace.tostring())

if __name__ == '__main__':

    main()
