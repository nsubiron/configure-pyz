"""Embed files into C code"""

import binascii
import filecmp
import os
import shutil
import tempfile
import textwrap

def _embed(inputfile, chunksize=2, width=80, indent=2):
    with open(inputfile, 'rb') as fd:
      hexdata = binascii.hexlify(fd.read())
    chunks = ['0x' + hexdata[i:(i+chunksize)] for i in range(0, len(hexdata), chunksize)]
    ind = ' ' * indent
    return ind + ('\n'+ind).join(textwrap.wrap(', '.join(chunks), width-indent)), len(chunks)

def _get_variable_name(filepath):
    return filepath.replace('.', '_').replace('/', '_').lower()

class EmbeddedDataFile(object):
    def __init__(self, cppout, hout):
        self.cppout = cppout
        self.hout = hout

    def add_data(self, name, data, length):
        cppformat = 'unsigned char %s[] = {\n%s\n};\n'
        cppformat += 'unsigned int %s_len = %iu;\n'
        self.cppout.write(cppformat % (name, data, name, length))
        hformat = 'extern unsigned char %s[];\n'
        hformat += 'extern unsigned int %s_len;\n'
        self.hout.write(hformat % (name, name))

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
          data, length = _embed(os.path.join(sourcedir, item))
          writer.add_data(_get_variable_name(item), data, length)
        _mv_temp_file(cppfile, cppfile_path)
        _mv_temp_file(hfile, hfile_path)

def embed(targets, sourcedir):
    for target in targets:
      if target["embedded_data"]:
        _embed_target(target, sourcedir)
