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

Module that lets you build the application using 'setuptools'
'''

import pathlib
import shutil
import sys

project_dir = pathlib.Path(__file__).parents[3].resolve()
sys.path.append(str(project_dir))

# pylint:disable=wrong-import-position
from deploy import utils
from myfyrio import metadata as md


def source(setup_file):
    '''Make "Source Distribution"

    :param setup_file: path to the 'setup.py' file,
    :raise ImportWarning: 'setuptools' is not installed
    '''

    print('Source Distribution...')

    _check_package_installed('setuptools')

    cmd = f'python {setup_file} sdist'
    utils.run(cmd)

def wheel(setup_file):
    '''Make "Pure Python Wheel"

    :param setup_file: path to the 'setup.py' file,
    :raise ImportWarning: 'setuptools' or/and 'wheel' are not installed
    '''

    print('Pure Python Wheel...')

    _check_package_installed('setuptools')
    _check_package_installed('wheel')

    cmd = f'python {setup_file} bdist_wheel'
    utils.run(cmd)

def _check_package_installed(package):
    if not utils.pip_installed(package):
        err_msg = (f'Package "{package}" is not installed: '
                   f'"pip install {package}"')
        raise ImportWarning(err_msg)

def clear(setup_file):
    '''Clear the temporary directories used for building the application

    :param setup_file: path to the 'setup.py' file
    '''

    print('Clearing temporary directories...')

    parent_dir = setup_file.parent
    egg_dir = parent_dir / f'{md.NAME.lower()}.egg-info'
    build_dir = parent_dir / 'build'

    for d in [egg_dir, build_dir]:
        if d.exists():
            shutil.rmtree(d)


if __name__ == '__main__':

    setup_file = project_dir / 'setup.py'

    source(setup_file)
    wheel(setup_file)
    clear(setup_file)
