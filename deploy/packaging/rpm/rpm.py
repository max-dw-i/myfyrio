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

Module that lets us make a '.rpm' package
'''

# https://rpm-packaging-guide.github.io/

import pathlib
import shutil
import sys

project_dir = pathlib.Path(__file__).parents[3].resolve()
sys.path.append(str(project_dir))

from deploy import utils # pylint:disable=wrong-import-position


def make_rpm(dist_dir):
    '''Make a '.rpm' package

    :param dist_dir: path to the 'dist' directory (contains the 'release'
                     directory with the built app files)
    '''

    print("Making '.rpm' package...")

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

    appfiles_dir = pkg_dir.joinpath('usr', 'share', name)
    shutil.copytree(release_dir, appfiles_dir)

    desktopfile_dir = pkg_dir.joinpath('usr', 'share', 'applications')
    desktopfile_dir.mkdir()
    desktopfile_name = name + '.desktop'
    shutil.move(str(appfiles_dir / desktopfile_name), desktopfile_dir)
    _update_spec(desktopfile_dir / desktopfile_name, _update_desktop_field)

    shutil.make_archive(dist_dir / f'v{version}', 'gztar',
                        root_dir=dist_dir, base_dir=pkg_name)
    shutil.rmtree(pkg_dir)

    SOURCES_dir = pkg_dir / 'SOURCES'
    SOURCES_dir.mkdir(parents=True)
    shutil.move(str(dist_dir / f'v{version}.tar.gz'), SOURCES_dir)

    rpmscripts_dir = project_dir.joinpath('deploy', 'packaging', 'rpm')
    SPECS_dir = pkg_dir / 'SPECS'
    SPECS_dir.mkdir()
    new_specfile = SPECS_dir / f'{name}.spec'
    shutil.copyfile(rpmscripts_dir / f'{name}.spec', new_specfile)
    _update_spec(new_specfile, _update_spec_field)

    make_pkg_cmd = (f'rpmbuild {new_specfile} -bb '
                    f'--define "_topdir {pkg_dir}" '
                    f'--define "_rpmdir {dist_dir}"')
    utils.run(make_pkg_cmd, cwd=dist_dir)

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
    '''Update a field in the 'control' file

    :param line: line to update
    '''

    parts = line.split(': ')
    if len(parts) == 1:
        return line

    field_name = parts[0]

    if line.startswith('Name'):
        field_val = utils.name().lower()
    elif line.startswith('Version'):
        field_val = utils.version()
    else:
        field_val = parts[1].rstrip()

    return f'{field_name}: {field_val}\n'


def check_package(dist_dir):
    '''Run the 'rpmlint' command to check the package for sanity

    :param dist_dir: path to the 'dist' directory (contains the 'release'
                     directory with the built app files)
    '''

    print('Checking the package...')

    ARCH = 'x86_64'
    name = utils.name().lower()
    version = utils.version()
    pkg_name = f'{name}-{version}-1.{ARCH}.rpm'
    pkg_dir = dist_dir / ARCH

    cmd = f'rpmlint {pkg_name}'
    utils.run(cmd, cwd=pkg_dir)

    print('Done.')


if __name__ == '__main__':

    dist_dir = project_dir / 'dist'

    make_rpm(dist_dir)
    check_package(dist_dir)
