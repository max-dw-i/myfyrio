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

from deploy import utils # pylint:disable=wrong-import-position


def make_msi(dist_dir, wix_dir):
    '''Make a '.msi' package (installer)

    :param dist_dir: path to the 'dist' directory (contains the 'release'
                     directory with the built app files),
    :param wix_dir: path to the 'Wix#' directory
    '''

    print("Making '.msi' package...")

    release_dir = dist_dir / 'release'
    if not release_dir.exists():
        raise RuntimeError('Package cannot be made if app is not built yet')

    name = utils.name().lower()
    version = utils.version()
    pkg_name = f'{name}-{version}'
    pkg_dir = dist_dir / pkg_name
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    pkg_dir.mkdir()

    files_dir = pkg_dir / 'Files'
    files_dir.mkdir()
    shutil.copytree(release_dir / 'LICENSES', files_dir / 'LICENSES')
    exe_file = name.capitalize() + '.exe'
    shutil.copyfile(release_dir / exe_file, files_dir / exe_file)

    cscs_file = wix_dir / 'cscs.exe'
    shutil.copyfile(cscs_file, pkg_dir / 'cscs.exe')
    wixsharpdll_file = wix_dir / 'WixSharp.dll'
    shutil.copyfile(wixsharpdll_file, pkg_dir / 'WixSharp.dll')
    setup_file = project_dir.joinpath('deploy', 'packaging', 'msi', 'setup.cs')
    new_setup_file = pkg_dir / 'setup.cs'
    shutil.copyfile(setup_file, new_setup_file)
    _update_spec(new_setup_file, _update_spec_field)

    set_var_cmd = _set_env_vars(wix_dir)
    make_pkg_cmd = ('cscs.exe setup.cs')
    cmd = f'{set_var_cmd} && {make_pkg_cmd}'
    utils.run(cmd, cwd=pkg_dir)

    msi_file_name = name.capitalize() + '.msi'
    new_msi_file_name = f'{name}-{version}-x64.msi'
    shutil.copyfile(pkg_dir / msi_file_name, dist_dir / new_msi_file_name)

    shutil.rmtree(pkg_dir)

    print('Done.')


def _update_spec(file, update_func):
    '''Update fields in a config file (rpm's '.spec', '.desktop')

    :param file: file to update,
    :param update_func: function used to update :file:
    '''

    with open(file, 'r+') as f:
        modified_text = [update_func(line) for line in f]
        f.seek(0)
        f.write(''.join(modified_text))


def _update_spec_field(line):
    '''Update data in the 'setup.cs' file

    :param line: line to update
    '''

    if line.startswith('//css_ref'):
        new_val = (fr'{wix_dir}\Wix_bin\SDK'
                   r'\Microsoft.Deployment.WindowsInstaller.dll')
    elif 'var name =' in line:
        name = utils.name()
        new_val = f'"{name}"'
    elif 'var version =' in line:
        version = utils.version()
        new_val = f'"{version}"'
    else:
        return line

    parts = line.split(' ')
    parts[-1] = f'{new_val};\n'
    return ' '.join(parts)


def _set_env_vars(wix_dir):
    '''Return the command setting the 'WIXSHARP_WIXDIR' environment variable

    :param wix_dir: path to the 'Wix#' directory
    '''

    wix_bin_path = wix_dir.joinpath('Wix_bin', 'bin')
    return f'set WIXSHARP_WIXDIR={wix_bin_path}'


if __name__ == '__main__':

    dist_dir = project_dir / 'dist'
    wix_dir = pathlib.Path(r'C:\WixSharp')

    make_msi(dist_dir, wix_dir)
