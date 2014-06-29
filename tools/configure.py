import fnmatch
import json
import logging
import os
import re

import ninja_syntax

NINJA_CONFIG = 'tools/config.ninja'

SOURCES = ['*.cpp']

EXEGYP_FILENAME = 'rules.gyp'

ROOTLIB_BASENAME = 'root'

def clean_path(path):
    path = path.replace('\\', '/')
    return path[1:] if path.startswith('/') else path

def join_path(*args):
    return clean_path(os.path.join(*args))

def basename_from_path(path):
    path = clean_path(path)
    return ROOTLIB_BASENAME if not path else path.replace('/', '_')

def regex_callable(patterns):
    """Return a callable object that returns True if matches any regular
    expression in patterns"""
    if patterns is None:
      return lambda x: False
    if isinstance(patterns, str):
      patterns = [patterns]
    regex = re.compile(r'|'.join(fnmatch.translate(p) for p in patterns))
    return lambda x: regex.match(x) is not None

def walk(root, file_includes=['*'], file_excludes=None, dir_excludes=['.git', '.svn']):
    """Convenient wrap around os.walk. Patterns are checked on base names, not
    on full path names."""
    fincl = regex_callable(file_includes)
    fexcl = regex_callable(file_excludes)
    dexcl = regex_callable(dir_excludes)
    for path, dirs, files in os.walk(os.path.abspath(root)):
      dirs[:] = [d for d in dirs if not dexcl(d)]
      files[:] = [f for f in files if fincl(f) and not fexcl(f)]
      yield path, dirs, files

def get_targets(gypfile_path):
    logging.info('Parsing rules %s', gypfile_path)
    with open(gypfile_path, 'r') as gypfile:
      data = json.load(gypfile)
      for target in data.get('targets', []):
        yield target.get('target_name'), target.get('dependencies', [])

def add_objects(ninja, relpath, files):
    objfiles = []
    for filename in files:
      basename, _ = os.path.splitext(filename)
      objfile = join_path('$obj', relpath, basename + '.o')
      ninja.build(objfile, 'cxx', join_path('$source', relpath, filename))
      objfiles.append(objfile)
    return objfiles

def recursive_parse(root):
    with open('build.ninja', 'w+') as out:
      ninja = ninja_syntax.Writer(out)
      ninja.include(NINJA_CONFIG)
      for path, _, files in walk(root, SOURCES + [EXEGYP_FILENAME]):
        logging.info('Parsing folder %s', path)
        if files:
          ninja.newline()
          relpath = clean_path(path.replace(root, ''))
          if EXEGYP_FILENAME in files:
            # Add executables.
            files.remove(EXEGYP_FILENAME)
            objfiles = add_objects(ninja, relpath, files)
            gypfile_path = join_path(path, EXEGYP_FILENAME)
            for target, dependencies in get_targets(gypfile_path):
              if target is None:
                target = basename_from_path(relpath)
              infiles = objfiles + ['$lib/' + x for x in dependencies]
              ninja.build(join_path('$bin', target), 'link', infiles)
              ninja.build(target, 'phony', join_path('$bin', target))
          else:
            # Add a library.
            objfiles = add_objects(ninja, relpath, files)
            if objfiles:
              lib = join_path('$lib', basename_from_path(relpath) + '.a')
              ninja.build(lib, 'ar', objfiles)

if __name__ == '__main__':

    import sys

    recursive_parse(os.path.abspath(sys.argv[1]))
