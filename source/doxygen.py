# configure.pyz Copyright (C) 2014 N. Subiron Montoro
#
# This program comes with ABSOLUTELY NO WARRANTY. This is free software, and you
# are welcome to redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.

"""Generate a Doxyfile from a template"""


import util


def generate(settings):
    template_filename = settings.get('doxygen').get('doxyfile_template', None)
    template_filename = settings.expand_variables(template_filename)
    if template_filename is not None:
        with open(template_filename, 'r') as fd:
            template = fd.read()
        if not template:
            util.critical_error('%s seems to be empty', template_filename)
    else:
        template = util.get_resource('defaults/Doxyfile')
    doxyfile = settings.expand_variables(template)

    with open(settings.expand_variables('$builddir/Doxyfile'), 'w+') as fd:
        fd.write(doxyfile)
