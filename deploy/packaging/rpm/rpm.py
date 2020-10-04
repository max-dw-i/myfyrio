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
import textwrap

project_dir = pathlib.Path(__file__).parents[3].resolve()
sys.path.append(str(project_dir))

# pylint:disable=wrong-import-position
from deploy import utils
from deploy.packaging import bundle
from myfyrio import metadata as md
from myfyrio import resources


def make_rpm(dest_dir):
    '''Make a '.rpm' package

    :param dist_dir: path to the directory that contains the 'release'
                     directory with the programme's files and where to
                     put the package at
    '''

    print("Making '.rpm' package...")

    dest_dir = pathlib.Path(dest_dir)
    release_dir = dest_dir / 'release'
    if not release_dir.exists():
        raise RuntimeError('Package cannot be made if app is not built yet')

    pkg_name = f'{md.NAME.lower()}-{md.VERSION}'
    pkg_dir = dest_dir / pkg_name
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    pkg_dir.mkdir()

    pkg_BUILD_dir = pkg_dir / 'BUILD'
    _, installed_exe_dir = _copy_exe(release_dir, pkg_BUILD_dir)
    _copy_licenses(release_dir, pkg_BUILD_dir)
    _copy_icon(release_dir, pkg_BUILD_dir)
    _generate_desktop_file(pkg_BUILD_dir, installed_exe_dir)
    spec_file = generate_spec(pkg_dir)

    make_pkg_cmd = (f'rpmbuild {spec_file} -bb '
                    f'--define "_topdir {pkg_dir}" '
                    f'--define "_rpmdir {dest_dir}"')
    utils.run(make_pkg_cmd, cwd=dest_dir)

    shutil.rmtree(pkg_dir)

    print('Done.')


def _copy_exe(src_dir, temp_pkg_dir):
    exe_name = md.NAME.lower()
    installed_exe_dir = pathlib.Path('usr/bin')
    pkg_exe_dir = temp_pkg_dir / installed_exe_dir
    pkg_exe = pkg_exe_dir / exe_name

    pkg_exe_dir.mkdir(parents=True)
    shutil.copy(src_dir / exe_name, pkg_exe)

    return pkg_exe, pathlib.Path('/') / installed_exe_dir


def _copy_licenses(src_dir, temp_pkg_dir):
    exe_name = md.NAME.lower()
    doc_dir = pathlib.Path(f'usr/share/doc/{exe_name}')
    pkg_doc_dir = temp_pkg_dir / doc_dir
    pkg_doc_dir.mkdir(parents=True)

    LICENSE = resources.License.LICENSE.value # pylint:disable=no-member
    LICENSE_name = pathlib.Path(LICENSE).name
    shutil.copy(src_dir / LICENSE_name, pkg_doc_dir / LICENSE_name)

    COPYRIGHT = resources.License.COPYRIGHT.value # pylint:disable=no-member
    COPYRIGHT_name = pathlib.Path(COPYRIGHT).name
    shutil.copy(src_dir / COPYRIGHT_name, pkg_doc_dir / COPYRIGHT_name)

    shutil.copytree(src_dir / '3RD-PARTY-LICENSE',
                    pkg_doc_dir / '3RD-PARTY-LICENSE')


def _copy_icon(src_dir, temp_pkg_dir):
    icon_name = pathlib.Path(resources.Image.ICON.value).name # pylint:disable=no-member
    icon_dir = pathlib.Path(f'usr/share/icons/hicolor/512x512/apps')
    pkg_icon_dir = temp_pkg_dir / icon_dir

    pkg_icon_dir.mkdir(parents=True)
    shutil.copy(src_dir / icon_name, pkg_icon_dir / icon_name)


def _generate_desktop_file(temp_pkg_dir, installed_exe_dir):
    desktop_dir = temp_pkg_dir.joinpath('usr', 'share', 'applications')
    desktop_dir.mkdir()
    bundle.generate_desktop(desktop_dir, installed_exe_dir, '', True)


def generate_spec(pkg_root_dir):
    '''Generate the '.spec' file and put it into ':pkg_root_dir:/SPECS'

    :param pkg_root_dir: package root directory,
    :return: path to the '.spec' file
    '''

    name = md.NAME.lower()

    fields = [
        f'Name: {name}',
        f'Version: {md.VERSION}',
        'Release: 1',
        f'Summary: {md.DESCRIPTION}',
        'License: GPLv3',
        f'Packager: {md.AUTHOR} <{md.AUTHOR_EMAIL}>',
        f'URL: {md.URL_ABOUT}',
        r'Source0: %{url}archive/v%{version}.tar.gz',
        '',
        r'%define _build_id_links none',
        '',
        r'%description',
        f'{extended_description()}',
        '',
        r'%build',
        '',
        r'%install',
        r'cp -rfa . %{buildroot}',
        '',
        r'%files',
        r'%{_bindir}/*',
        r'%{_datadir}/applications/*',
        r'%{_datadir}/doc/%{name}/*',
        r'%{_datadir}/icons/hicolor/512x512/*'
    ]

    SPECS_dir = pathlib.Path(pkg_root_dir) / 'SPECS'
    SPECS_dir.mkdir()
    spec_file = SPECS_dir / f'{name}.spec'
    utils.save_file('\n'.join(fields), spec_file, 0o644)

    return spec_file


def extended_description():
    """Wrap the text so each line is 80 symbols long max

    :return: extended description
    """

    fixed_lines = []
    for line in md.long_description().split('\n'):
        if not line: # empty line
            fixed_lines.append('')
            continue

        for wrapped_line in textwrap.wrap(line, 79):
            fixed_lines.append(wrapped_line)

    return '\n'.join(fixed_lines)


def check_package(pkg_dir):
    '''Run the 'rpmlint' command to check the package for sanity

    :param pkg_dir: directory containing the built package
    '''

    print('Checking the package...')

    pkg_name = f'{md.NAME.lower()}-{md.VERSION}-1.x86_64.rpm'
    cmd = f'rpmlint {pkg_name}'
    utils.run(cmd, cwd=pkg_dir)

    print('Done.')


if __name__ == '__main__':

    dist_dir = project_dir / 'dist'
    built_pkg_dir = dist_dir / 'x86_64'

    make_rpm(dist_dir)
    check_package(built_pkg_dir)
