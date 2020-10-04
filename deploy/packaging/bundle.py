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

Module that implements functions helping bundle the programme
'''

import os
import pathlib
import shutil
import sys

project_dir = pathlib.Path(__file__).parents[2].resolve()
sys.path.append(str(project_dir))

# pylint:disable=wrong-import-position
from deploy import qt3rdparty, utils
from myfyrio import metadata as md
from myfyrio import resources


def bundle(build_dir, dest_dir):
    '''Bundle the programme: copy all the necessary file into
    ':dest_dir:/release' and make an archive with the data in :dest_dir:

    :param build_dir: directory with the built executable,
    :param dest_dir: directory to put the archive into
    '''

    print('Bundling Myfyrio...')

    dest_dir = pathlib.Path(dest_dir)
    release_dir = dest_dir / 'release'

    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True)

    copy_exe(build_dir, release_dir, strip=True)

    sysroot_dir = project_dir / 'sysroot'
    copy_licenses(release_dir, sysroot_dir)

    if utils.is_linux():
        copy_icon(release_dir)
        generate_desktop(release_dir, '', '', user_mode=True)

    pack(dest_dir, release_dir)


def copy_exe(src_dir, dest_dir, strip=False):
    '''Copy the executable from :src_dir: into :dest_dir: and set its mod
    to 755. Also the symbols can be stripped

    :param src_dir: directory where the executable is located,
    :param dest_dir: directory to put the executable into,
    :param strip: True - strip the executable (optional)
    '''

    exe_name = md.NAME.lower()
    if not utils.is_linux():
        exe_name += '.exe'
        src_dir = pathlib.Path(src_dir) / 'release'
    new_exe = pathlib.Path(dest_dir) / exe_name
    shutil.copyfile(src_dir / exe_name, new_exe)

    if strip and utils.is_linux():
        utils.strip_exe(new_exe)

    os.chmod(new_exe, 0o755)


def copy_licenses(dest_dir, sysroot_dir):
    '''Copy the licenses of the used libraries into :dest_dir: and set the
    file's mods to 644, the directories' mods to 755

    :param dest_dir: directory to put the licenses into,
    :param sysroot_dir: path to the built sysroot directory
    '''

    dest_dir = pathlib.Path(dest_dir)
    thirdparty_dir = dest_dir / '3RD-PARTY-LICENSE'
    qt_thirdparty_dir = thirdparty_dir.joinpath('Qt5', '3rdparty')

    _copy_app_license(dest_dir)
    _copy_thirdparty_licenses(thirdparty_dir)
    _export_qt_thirdparty_licenses(qt_thirdparty_dir, sysroot_dir)


def _copy_app_license(dest_dir):
    LICENSE = resources.License.LICENSE.get() # pylint:disable=no-member
    LICENSE_copy = dest_dir / pathlib.Path(LICENSE).name
    shutil.copyfile(LICENSE, LICENSE_copy)
    os.chmod(LICENSE_copy, 0o644)

    COPYRIGHT = resources.License.COPYRIGHT.get() # pylint:disable=no-member
    COPYRIGHT_copy = dest_dir / pathlib.Path(COPYRIGHT).name
    shutil.copyfile(COPYRIGHT, COPYRIGHT_copy)
    os.chmod(COPYRIGHT_copy, 0o644)


def _copy_thirdparty_licenses(dest_dir):
    # Copy the prepared earlier the '3RD-PARTY-LICENSE' licenses
    deploy_dir = project_dir / 'deploy'
    shutil.copytree(deploy_dir / '3RD-PARTY-LICENSE', dest_dir)
    if not utils.is_linux():
        libffi_license = dest_dir / 'libffi'
        shutil.rmtree(libffi_license)

    _set_license_dir_permissions(dest_dir)


def _export_qt_thirdparty_licenses(dest_dir, sysroot_dir):
    QT = 'qtbase-everywhere-src-5.14.2'
    deploy_dir = project_dir / 'deploy'
    thirdpartylibs_json = deploy_dir / '3rdpartylibs.json'
    qt_build_dir = pathlib.Path(sysroot_dir).joinpath('build', QT)

    json = utils.JSON()
    json.load(thirdpartylibs_json)
    thirdparty_libs = json.data

    prev_qt_src_dir = '/media/ntfs/Maxim/Sources/myfyrio/build-src/' + QT
    qt3rdparty.fix_3rdpartylib_paths(
        thirdparty_libs, prev_qt_src_dir, qt_build_dir
    )

    qt_src_dir = project_dir.joinpath('build-src', QT)
    if not qt_src_dir.exists():
        archive = qt_src_dir.parent / f'{QT}.tar.gz'
        shutil.unpack_archive(archive, qt_src_dir)

    qt3rdparty.export_used_licenses(
        dest_dir, thirdparty_libs, qt_build_dir, qt_src_dir
    )

    _set_license_dir_permissions(dest_dir)


def _set_license_dir_permissions(license_dir):
    os.chmod(license_dir, 0o755)
    for file in license_dir.rglob('*'):
        if file.is_dir():
            os.chmod(file, 0o755)
        else:
            os.chmod(file, 0o644)


def copy_icon(dest_dir):
    '''Copy the programme's icon into :dest_dir: and set its mod to 644

    :param dest_dir: directory to put the licenses into
    '''

    icon_name = pathlib.Path(resources.Image.ICON.value).name # pylint:disable=no-member
    icon = project_dir.joinpath(md.NAME.lower(), 'static', 'images', icon_name)
    new_icon = pathlib.Path(dest_dir) / icon_name
    shutil.copyfile(icon, new_icon)

    os.chmod(new_icon, 0o644)


def generate_desktop(dest_dir, exe_dir, icon_dir, user_mode=False):
    '''Generate a '.desktop' file, put it into :dest_dir: and set its mod
    to 644

    :param dest_dir: directory to put the desktop file into,
    :param exe_dir: directory with the installed executable,
    :param icon_dir: directory with the installed icon,
    :param user_mode: True - add the '-u' argument to the 'Exec' field
    '''

    name = md.NAME
    lowercase_name = name.lower()
    exe = pathlib.Path(exe_dir) / lowercase_name
    icon_name = pathlib.Path(resources.Image.ICON.value).name # pylint:disable=no-member
    icon = pathlib.Path(icon_dir) / icon_name
    user_mode_arg = ' -u' if user_mode else ''

    fields = [
        '[Desktop Entry]',
        'Type=Application',
        'Version=1.0',
        f'Name={name}',
        f'Comment={md.DESCRIPTION}',
        f'Exec={exe}{user_mode_arg}',
        f'Icon={icon}',
        'Terminal=false',
        'Categories=Utility;'
    ]

    desktop_file = pathlib.Path(dest_dir) / f'{lowercase_name}.desktop'
    utils.save_file('\n'.join(fields), desktop_file, 0o644)


def pack(dest_dir, dir_to_arch):
    '''Pack the data in :dir_to_arch: and put the result archive
    into :dest_dir:

    :param dest_dir: directory to put the result archive into,
    :param dir_to_arch: directory to pack
    '''

    if utils.is_linux():
        platform = 'linux64'
        arch_format = 'gztar'
    else:
        platform = 'win64'
        arch_format = 'zip'

    arch_name = f'{md.NAME.lower()}-{md.VERSION}-{platform}'
    arch = pathlib.Path(dest_dir) / arch_name
    shutil.make_archive(arch, arch_format, root_dir=dir_to_arch)


if __name__ == '__main__':

    bundle(project_dir / 'build', project_dir / 'dist')
