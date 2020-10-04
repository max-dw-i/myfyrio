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

Module that lets us make a '.msi' package (installer)
'''

# https://github.com/oleg-shilo/wixsharp/wiki/Building-MSI-%E2%80%93-Step-by-step-tutorial

import pathlib
import shutil
import sys

project_dir = pathlib.Path(__file__).parents[3].resolve()
sys.path.append(str(project_dir))

# pylint:disable=wrong-import-position
from deploy import utils
from myfyrio import metadata as md
from myfyrio import resources


def make_msi(dest_dir, wix_dir):
    '''Make a '.msi' package (installer)

    :param dest_dir: path to the directory that contains the 'release'
                     directory with the programme's files and where to
                     put the package at,
    :param wix_dir: path to the 'Wix#' directory
    '''

    print("Making '.msi' package...")

    dest_dir = pathlib.Path(dest_dir)
    release_dir = dist_dir / 'release'
    if not release_dir.exists():
        raise RuntimeError('Package cannot be made if app is not built yet')

    exe_name = md.NAME.lower()
    version = md.VERSION
    pkg_dir = dest_dir / f'{exe_name}-{md.VERSION}'
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    pkg_dir.mkdir()

    files_dir = pkg_dir / 'Files'
    files_dir.mkdir()

    _copy_exe(release_dir, files_dir)
    _copy_licenses(release_dir, files_dir)
    _copy_wix(wix_dir, pkg_dir)
    _copy_setup(pkg_dir)

    cmd = f'{set_env_vars(wix_dir)} && cscs.exe setup.cs'
    utils.run(cmd, cwd=pkg_dir)

    shutil.copyfile(pkg_dir / f'{md.NAME}.msi',
                    dist_dir / f'{exe_name}-{version}-x64.msi')

    shutil.rmtree(pkg_dir)

    print('Done.')


def _copy_exe(src_dir, pkg_files_dir):
    exe_name = f'{md.NAME.lower()}.exe'
    shutil.copyfile(src_dir / exe_name, pkg_files_dir / exe_name)


def _copy_licenses(src_dir, pkg_files_dir):
    LICENSE = resources.License.LICENSE.value # pylint:disable=no-member
    LICENSE_name = pathlib.Path(LICENSE).name
    shutil.copy(src_dir / LICENSE_name, pkg_files_dir / LICENSE_name)

    COPYRIGHT = resources.License.COPYRIGHT.value # pylint:disable=no-member
    COPYRIGHT_name = pathlib.Path(COPYRIGHT).name
    shutil.copy(src_dir / COPYRIGHT_name, pkg_files_dir / COPYRIGHT_name)

    shutil.copytree(src_dir / '3RD-PARTY-LICENSE',
                    pkg_files_dir / '3RD-PARTY-LICENSE')


def _copy_wix(wix_dir, temp_pkg_dir):
    shutil.copyfile(wix_dir / 'cscs.exe', temp_pkg_dir / 'cscs.exe')
    shutil.copyfile(wix_dir / 'WixSharp.dll', temp_pkg_dir / 'WixSharp.dll')


def _copy_setup(temp_pkg_dir):
    setup_file = project_dir.joinpath('deploy', 'packaging', 'msi', 'setup.cs')
    working_setup_file = temp_pkg_dir / 'setup.cs'
    shutil.copyfile(setup_file, working_setup_file)


def set_env_vars(wix_dir):
    '''Return the command that sets the 'WIXSHARP_WIXDIR' environment variable

    :param wix_dir: path to the 'Wix#' directory
    '''

    wix_bin_path = wix_dir.joinpath('Wix_bin', 'bin')
    return f'set WIXSHARP_WIXDIR={wix_bin_path}'


if __name__ == '__main__':

    dist_dir = project_dir / 'dist'
    wix_dir = pathlib.Path(r'C:\WixSharp')

    make_msi(dist_dir, wix_dir)
