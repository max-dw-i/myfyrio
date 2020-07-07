'''MIT License

Copyright (c) 2020 Maxim Shpak <maxim.shpak@posteo.uk>

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom
the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.

-------------------------------------------------------------------------------

Module that implements different functions used in build process
'''

import importlib.util
import subprocess
import sys
from xml.etree import ElementTree

from myfyrio import resources


def name():
    '''Return the programme's name'''

    return _text('nameLbl')

def version():
    '''Return the programme's version'''

    return _text('versionLbl').split(' ')[-1]

def _text(widget_name):
    tree = ElementTree.parse(resources.UI.ABOUT.abs_path) # pylint: disable=no-member
    root = tree.getroot()
    for w in root.iter('widget'):
        if w.get('name') == widget_name:
            return w.findtext('./property/string')

    raise ValueError(f'Cannot find the "{widget_name}" widget')

def installed(package):
    '''Check if :package: is installed

    :param package: name of the package to check,
    :return: True - :package: is installed, False - otherwise
    '''

    # If the package name has dashes ('-'), replace with dots ('.')
    spec = importlib.util.find_spec(package)
    installed = False
    if spec is not None:
        installed = True

    return installed

def run(cmd, cwd=None):
    '''Run a command in the shell

    :param cmd: command to run,
    :param cwd: set the current working directory (optional)
    '''

    try:
        subprocess.call(cmd, shell=True, cwd=cwd)
    except OSError as e:
        print("OSError:", e, file=sys.stderr)
        sys.exit(1)
