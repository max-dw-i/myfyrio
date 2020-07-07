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

Module that lets you build the application using "setuptools"
'''

import pathlib
import shutil

from deployment import utils

setup_file = pathlib.Path(__file__).parents[1] / 'setup.py'


def source():
    '''Make "Source Distribution"

    :raise ImportWarning: 'setuptools' is not installed
    '''

    _check_package_installed('setuptools')

    cmd = f'python {setup_file} sdist'
    utils.run(cmd)

def wheel():
    '''Make "Pure Python Wheel"

    :raise ImportWarning: 'setuptools' or/and 'wheel' are not installed
    '''

    _check_package_installed('setuptools')
    _check_package_installed('wheel')

    cmd = f'python {setup_file} bdist_wheel'
    utils.run(cmd)

def _check_package_installed(package):
    if not utils.installed(package):
        err_msg = (f'Package "{package}" is not installed: '
                   f'"pip install {package}"')
        raise ImportWarning(err_msg)

def clear():
    '''Clear the temporary directories used for building the application'''

    parent_dir = setup_file.parent
    programme_name = utils.name()
    egg_dir = parent_dir / f'{programme_name}.egg-info'
    build_dir = parent_dir / 'build'

    for d in [egg_dir, build_dir]:
        if d.exists():
            shutil.rmtree(d)
