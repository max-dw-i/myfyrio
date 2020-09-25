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

Module that lets us make a '.deb' package
'''

# https://www.internalpointers.com/post/build-binary-deb-package-practical-guide
# https://medium.com/swlh/introduction-to-debian-maintainer-script-flow-charts-6f76423b80d9

import pathlib
import shutil
import sys

project_dir = pathlib.Path(__file__).parents[3].resolve()
sys.path.append(str(project_dir))

from deploy import utils # pylint:disable=wrong-import-position


def make_deb(dist_dir):
    '''Make a '.deb' package

    :param dist_dir: path to the 'dist' directory (contains the 'release'
                     directory with the built app files)
    '''

    print("Making '.deb' package...")

    release_dir = dist_dir / 'release'
    if not release_dir.exists():
        raise RuntimeError('Package cannot be made if app is not built yet')

    name = utils.name().lower()
    version = utils.version()
    arch = _architecture()
    pkg_name = f'{name}_{version}-1_{arch}'
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
    _update_config_file(desktopfile_dir / desktopfile_name,
                        _update_desktop_field)

    debscripts_dir = project_dir.joinpath('deploy', 'packaging', 'deb')
    DEBIAN_dir = pkg_dir / 'DEBIAN'
    shutil.copytree(debscripts_dir, DEBIAN_dir)
    DEBIAN_dir.joinpath('deb.py').unlink()
    _update_config_file(DEBIAN_dir / 'control', _update_control_field,
                        appfiles_dir / name.capitalize())

    make_pkg_cmd = f'fakeroot dpkg-deb --build {pkg_name}'
    # If dpkg-deb is fresh enough, use the command below
    #make_pkg_cmd = f'dpkg-deb --build --root-owner-group {pkg_name}'
    utils.run(make_pkg_cmd, cwd=dist_dir)

    shutil.rmtree(pkg_dir)

    print('Done.')


def _architecture():
    '''Return the system architecture (in dpkg's terms)'''

    cmd = 'dpkg --print-architecture'
    output = utils.run(cmd, stdout=False)
    return output.rstrip()


def _dependencies(executable):
    '''Return the external dependencies of the executable

    :param executable: path to the executable file
    '''

    print('Finding external dependencies...')

    cwd = project_dir / 'dist'

    # The command need 'debian/control' to work, for some reason
    debian_dir = cwd.joinpath('debian')
    debian_dir.mkdir()
    with open(debian_dir / 'control', 'x'): pass # pylint:disable=multiple-statements

    cmd = f'dpkg-shlibdeps -O {executable}'
    output = utils.run(cmd, cwd=cwd, stdout=False)

    shutil.rmtree(debian_dir)

    return output.split('Depends=')[-1].rstrip()


def _update_config_file(file, update_func, *args, **kwargs):
    '''Update fields in a config file

    :param file: file to update,
    :param update_func: function used to update :file:
    '''

    with open(file, 'r+') as f:
        modified_text = [update_func(line, *args, **kwargs) for line in f]
        f.seek(0)
        f.write(''.join(modified_text))


def _update_desktop_field(line):
    '''Update a field in the '.desktop' file

    :param line: line to update
    '''

    if line.startswith('Exec'):
        return line[:-1] + ' -u\n'
    return line


def _update_control_field(line, executable):
    '''Update a field in the 'control' file

    :param line: line to update,
    :param executable: path to the executable file
    '''

    parts = line.split(': ')
    field_name = parts[0]

    if line.startswith('Package'):
        field_val = utils.name()
    elif line.startswith('Version'):
        field_val = utils.version()+'-1'
    elif line.startswith('Architecture'):
        field_val = _architecture()
    elif line.startswith('Depends'):
        field_val = _dependencies(executable)
    else:
        field_val = parts[1].rstrip()

    return f'{field_name}: {field_val}\n'


def check_package(dist_dir):
    '''Run the 'lintian' command to check the package for sanity

    :param dist_dir: path to the 'dist' directory (contains the 'release'
                     directory with the built app files)
    '''

    print('Checking the package...')

    ARCH = 'amd64'
    name = utils.name().lower()
    version = utils.version()
    pkg_name = f'{name}_{version}-1_{ARCH}.deb'

    cmd = f'lintian {pkg_name}'
    utils.run(cmd, cwd=dist_dir)

    print('Done.')


if __name__ == '__main__':

    dist_dir = project_dir / 'dist'

    make_deb(dist_dir)
    check_package(dist_dir)
