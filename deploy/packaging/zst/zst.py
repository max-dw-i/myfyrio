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

Module that lets us make a '.zst' package (Arch Linux Build System)
'''

# https://wiki.archlinux.org/index.php/Creating_Packages

import pathlib
import shutil
import sys

project_dir = pathlib.Path(__file__).parents[3].resolve()
sys.path.append(str(project_dir))

from deploy import utils # pylint:disable=wrong-import-position


def make_zst(dist_dir):
    '''Make a '.zst' package

    :param dist_dir: path to the 'dist' directory (contains the 'release'
                     directory with the built app files)
    '''

    print("Making '.zst' package...")

    release_dir = dist_dir / 'release'
    if not release_dir.exists():
        raise RuntimeError('Package cannot be made if app is not built yet')

    name = utils.name().lower()
    version = utils.version()
    pkg_name = f'{name}-{version}'
    pkg_dir = dist_dir / pkg_name
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)

    shutil.copytree(release_dir, pkg_dir)
    _update_spec(pkg_dir / f'{name}.desktop', _update_desktop_field)

    zstscripts_dir = project_dir.joinpath('deploy', 'packaging', 'zst')
    shutil.copyfile(zstscripts_dir / f'{name}.install',
                    pkg_dir / f'{name}.install')
    new_specfile = pkg_dir / 'PKGBUILD'
    shutil.copyfile(zstscripts_dir / 'PKGBUILD', new_specfile)
    _update_spec(new_specfile, _update_spec_field)

    utils.run('makepkg', cwd=pkg_dir)

    zst_file_name = f'{name}-{version}-1-x86_64.pkg.tar.xz'
    shutil.copyfile(pkg_dir / zst_file_name, dist_dir / zst_file_name)

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


def _update_desktop_field(line):
    '''Update a field in the '.desktop' file

    :param line: line to update
    '''

    if line.startswith('Exec'):
        return line[:-1] + ' -u\n'
    return line


def _update_spec_field(line):
    '''Update a field in the 'PKGBUILD' file

    :param line: line to update
    '''

    if line.startswith('pkgname'):
        new_val = utils.name().lower()
    elif line.startswith('pkgver'):
        new_val = utils.version()
    else:
        return line

    parts = line.split('=')
    parts[-1] = f'{new_val}\n'
    return '='.join(parts)


def check_package(dist_dir):
    '''Run the 'namcap' command to check the package for sanity

    :param dist_dir: path to the 'dist' directory (contains the 'release'
                     directory with the built app files)
    '''

    print('Checking the package...')

    ARCH = 'x86_64'
    name = utils.name().lower()
    version = utils.version()
    pkg_name = f'{name}-{version}-1-{ARCH}.pkg.tar.xz'

    cmd = f'namcap {pkg_name}'
    utils.run(cmd, cwd=dist_dir)

    print('Done.')


if __name__ == '__main__':

    dist_dir = project_dir / 'dist'

    make_zst(dist_dir)
    check_package(dist_dir)
