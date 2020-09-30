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

# pylint:disable=wrong-import-position
from deploy import utils
from deploy.packaging import bundle
from myfyrio import metadata as md
from myfyrio import resources


def make_zst(dest_dir):
    '''Make a '.zst' package

    :param dest_dir: path to the directory that contains the 'release'
                     directory with the programme's files and where to
                     put the package at
    '''

    print("Making '.zst' package...")

    dest_dir = pathlib.Path(dest_dir)
    release_dir = dest_dir / 'release'
    if not release_dir.exists():
        raise RuntimeError('Package cannot be made if app is not built yet')

    exe_name = md.NAME.lower()
    version = md.VERSION
    pkg_name = f'{exe_name}-{version}'
    pkg_dir = dest_dir / pkg_name
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)

    shutil.copytree(release_dir, pkg_dir)
    bundle.generate_desktop(release_dir, '/usr/bin', '', True)
    generate_PKGBUILD(pkg_dir)

    utils.run('makepkg', cwd=pkg_dir)

    zst_file_name = f'{exe_name}-{version}-1-x86_64.pkg.tar.xz'
    shutil.copyfile(pkg_dir / zst_file_name, dest_dir / zst_file_name)

    shutil.rmtree(pkg_dir)

    print('Done.')


def generate_PKGBUILD(pkg_root_dir):
    '''Generate the 'PKGBUILD' file and put it into :pkg_root_dir:

    :param pkg_root_dir: package root directory
    '''

    icon_name = pathlib.Path(resources.Image.ICON.value).name # pylint:disable=no-member

    fields = [
        f'# Maintainer: {md.AUTHOR} <{md.AUTHOR_EMAIL}>',
        f'pkgname={md.NAME.lower()}',
        f'pkgver={md.VERSION}',
        'pkgrel=1',
        f'pkgdesc="{md.DESCRIPTION}"',
        "arch=('x86_64')",
        f'url="{md.URL_ABOUT}"',
        "license=('GPL3')",
        ("depends=('freetype2' 'fontconfig' 'libx11' 'libxkbcommon-x11'"
         " 'hicolor-icon-theme')"),
        'source=()',
        '',
        'package() {',
        '    cd ..',
        '',
        '    exe_dir=$pkgdir/usr/bin',
        '    mkdir -p $exe_dir',
        '    cp -fa $pkgname $exe_dir',
        '',
        '    desktop_file_dir=$pkgdir/usr/share/applications',
        '    mkdir -p $desktop_file_dir',
        '    cp -fa $pkgname.desktop $desktop_file_dir',
        '',
        '    icon_dir=$pkgdir/usr/share/icons/hicolor/512x512/apps',
        '    mkdir -p $icon_dir',
        f'    cp -fa {icon_name} $icon_dir',
        '',
        '    doc_dir=$pkgdir/usr/share/doc/$pkgname',
        '    mkdir -p $doc_dir',
        '    cp -rfa 3RD-PARTY-LICENSE $doc_dir/3RD-PARTY-LICENSE',
        '    cp -fa LICENSE $doc_dir',
        '    cp -fa COPYRIGHT $doc_dir',
        '}'
    ]

    PKGBUILD_file = pathlib.Path(pkg_root_dir) / 'PKGBUILD'
    utils.save_file('\n'.join(fields), PKGBUILD_file, 0o644)


def check_package(pkg_dir):
    '''Run the 'namcap' command to check the package for sanity

    :param pkg_dir: directory containing the built package
    '''

    print('Checking the package...')

    pkg_name = f'{md.NAME.lower()}-{md.VERSION}-1-x86_64.pkg.tar.xz'
    cmd = f'namcap {pkg_name}'
    utils.run(cmd, cwd=pkg_dir)

    print('Done.')


if __name__ == '__main__':

    dist_dir = project_dir / 'dist'

    make_zst(dist_dir)
    check_package(dist_dir)
