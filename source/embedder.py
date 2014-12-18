"""Embed files into C code"""

import filecmp
import os
import shutil
import subprocess
import tempfile

def _embed(inputfile):
    command = ['xxd', '-i', inputfile]
    # Ugly workaround.
    data = [x for x in subprocess.check_output(command).decode('utf-8').split('\n')]
    return '\n'.join(data[1:-3])

def _get_variable_name(filepath):
    return filepath.replace('.', '_').replace('/', '_').lower()

class EmbeddedDataFile(object):
    def __init__(self, cppout, hout):
        self.cppout = cppout
        self.hout = hout

    def add_data(self, name, data):
        cppformat = 'unsigned char %s[] = {\n%s\n};\n'
        self.cppout.write(cppformat % (name, data))
        hformat = 'extern unsigned char %s[];\n'
        self.hout.write(hformat % name)

def _mv_temp_file(tempf, dst):
    tempf.close()
    if not os.path.isfile(dst) or not filecmp.cmp(tempf.name, dst):
      shutil.move(tempf.name, dst)
    else:
      os.remove(tempf.name)

def _embed_target(target, sourcedir):
    cppfile_path = os.path.join(sourcedir, target.path, 'EmbeddedData.cpp')
    hfile_path = os.path.join(sourcedir, target.path, 'EmbeddedData.h')
    with tempfile.NamedTemporaryFile(delete=False) as cppfile:
      with tempfile.NamedTemporaryFile(delete=False) as hfile:
        writer = EmbeddedDataFile(cppfile, hfile)
        for item in target["embedded_data"]:
          data = _embed(os.path.join(sourcedir, item))
          writer.add_data(_get_variable_name(item), data)
        _mv_temp_file(cppfile, cppfile_path)
        _mv_temp_file(hfile, hfile_path)

def embed(targets, sourcedir):
    for target in targets:
      if target["embedded_data"]:
        _embed_target(target, sourcedir)
