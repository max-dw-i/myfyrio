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

import os
import pathlib
import shutil
import sys
import textwrap

project_dir = pathlib.Path(__file__).parents[3].resolve()
sys.path.append(str(project_dir))

# pylint:disable=wrong-import-position
from deploy import utils
from deploy.packaging import bundle
from myfyrio import metadata as md
from myfyrio import resources


def make_deb(dest_dir):
    '''Make a '.deb' package

    :param dest_dir: path to the directory that contains the 'release'
                     directory with the programme's files and where to
                     put the package at
    '''

    print("Making '.deb' package...")

    dest_dir = pathlib.Path(dest_dir)
    release_dir = dest_dir / 'release'
    if not release_dir.exists():
        raise RuntimeError('Package cannot be made if app is not built yet')

    exe_name = md.NAME.lower()
    pkg_name = f'{exe_name}_{md.VERSION}-1_{architecture()}'
    pkg_dir = dest_dir / pkg_name
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    pkg_dir.mkdir()

    pkg_exe, installed_exe_dir = _copy_exe(release_dir, pkg_dir)
    _copy_licenses(release_dir, pkg_dir)
    _copy_icon(release_dir, pkg_dir)
    _generate_desktop_file(pkg_dir, installed_exe_dir)
    generate_control(pkg_dir, pkg_exe)

    make_pkg_cmd = f'fakeroot dpkg-deb --build {pkg_name}'
    # If dpkg-deb is fresh enough, use the command below
    #make_pkg_cmd = f'dpkg-deb --build --root-owner-group {pkg_name}'
    utils.run(make_pkg_cmd, cwd=dest_dir)

    shutil.rmtree(pkg_dir)

    print('Done.')


def _copy_exe(src_dir, temp_pkg_dir):
    exe_name = md.NAME.lower()
    installed_exe_dir = pathlib.Path('usr/bin')
    pkg_exe_dir = temp_pkg_dir / installed_exe_dir
    pkg_exe = pkg_exe_dir / exe_name

    pkg_exe_dir.mkdir(parents=True)
    shutil.copyfile(src_dir / exe_name, pkg_exe)

    # Executable bit is not kept when copy :(
    os.chmod(pkg_exe, os.stat(pkg_exe).st_mode | 0o111)

    return pkg_exe, pathlib.Path('/') / installed_exe_dir


def _copy_licenses(src_dir, temp_pkg_dir):
    exe_name = md.NAME.lower()
    doc_dir = pathlib.Path(f'usr/share/doc/{exe_name}')
    pkg_doc_dir = temp_pkg_dir / doc_dir

    pkg_doc_dir.mkdir(parents=True)
    shutil.copyfile(src_dir / 'LICENSE', pkg_doc_dir / 'LICENSE')
    shutil.copyfile(src_dir / 'COPYRIGHT', pkg_doc_dir / 'COPYRIGHT')
    shutil.copytree(src_dir / '3RD-PARTY-LICENSE',
                    pkg_doc_dir / '3RD-PARTY-LICENSE')


def _copy_icon(src_dir, temp_pkg_dir):
    icon_name = pathlib.Path(resources.Image.ICON.value).name # pylint:disable=no-member
    icon_dir = pathlib.Path(f'usr/share/icons/hicolor/512x512/apps')
    pkg_icon_dir = temp_pkg_dir / icon_dir

    pkg_icon_dir.mkdir(parents=True)
    shutil.copyfile(src_dir / icon_name, pkg_icon_dir / icon_name)


def _generate_desktop_file(temp_pkg_dir, installed_exe_dir):
    desktop_dir = temp_pkg_dir.joinpath('usr', 'share', 'applications')
    desktop_dir.mkdir()
    bundle.generate_desktop(desktop_dir, installed_exe_dir, '', True)


def generate_control(pkg_root_dir, executable):
    '''Generate the 'control' file and put it into ':pkg_root_dir:/DEBIAN'

    :param pkg_root_dir: package root directory,
    :param executable: path to the executable file
    '''

    fields = [
        f'Package: {md.NAME.lower()}',
        f'Version: {md.VERSION}-1',
        'Section: utils',
        f'Depends: {dependencies(executable)}',
        'Priority: optional',
        f'Architecture: {architecture()}',
        f'Maintainer: {md.AUTHOR} <{md.AUTHOR_EMAIL}>',
        f'Homepage: {md.URL_ABOUT}',
        f'Description: {md.DESCRIPTION}\n{extended_description()}',
        '' # 'control' need an empty line at the end of the file
    ]

    DEBIAN_dir = pathlib.Path(pkg_root_dir) / 'DEBIAN'
    DEBIAN_dir.mkdir()
    utils.save_file('\n'.join(fields), DEBIAN_dir / 'control', 0o644)


def extended_description():
    """'Control' needs that a space precedes any line in the extended
    description, also wrap the text so each line is 80 symbols long max

    :return: extended description
    """

    fixed_lines = []
    for line in md.long_description().split('\n'):
        if not line: # empty line
            fixed_lines.append(' .')
            continue

        if line.startswith('- '): # unordered list
            line_prefix = '  '
        else:
            line_prefix = ' '

        for wrapped_line in textwrap.wrap(line, 79):
            fixed_lines.append(f'{line_prefix}{wrapped_line}')

    return '\n'.join(fixed_lines)


def architecture():
    '''Return the system architecture (in dpkg's terms)'''

    cmd = 'dpkg --print-architecture'
    output = utils.run(cmd, stdout=False)
    return output.rstrip()


def dependencies(executable):
    '''Return the external dependencies of the executable (in dpkg's terms)

    :param executable: path to the executable file
    '''

    cwd = project_dir / 'dist'

    # The command need 'debian/control' to work, for some reason
    debian_dir = cwd / 'debian'
    debian_dir.mkdir()
    with open(debian_dir / 'control', 'x'): pass # pylint:disable=multiple-statements

    cmd = f'dpkg-shlibdeps -O {executable}'
    output = utils.run(cmd, cwd=cwd, stdout=False)

    shutil.rmtree(debian_dir)

    return output.split('Depends=')[-1].rstrip()


def check_package(pkg_dir):
    '''Run the 'lintian' command to check the package for sanity

    :param pkg_dir: directory containing the built package
    '''

    print('Checking the package...')

    pkg_name = f'{md.NAME.lower()}_{md.VERSION}-1_{architecture()}.deb'
    cmd = f'lintian {pkg_name}'
    utils.run(cmd, cwd=pkg_dir)

    print('Done.')


if __name__ == '__main__':

    dist_dir = project_dir / 'dist'

    make_deb(dist_dir)
    check_package(dist_dir)
