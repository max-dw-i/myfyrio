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

Module that lets us build 'Myfyrio' using 'pyqtdeploy'
'''

import os
import pathlib
import shutil
import sys

project_dir = pathlib.Path(__file__).parents[1].resolve()
sys.path.append(str(project_dir))

from deploy import qt, qt3rdparty, utils # pylint:disable=wrong-import-position


def build_sysroot(src_dir, sysroot_json, sysroot_dir, clean=True):
    '''Build sysroot folder

    :param src_dir: folder containing source archives (Qt, PyQt, SIP, Python),
    :param sysroot_json: path to the config file (sysroot.json),
    :param sysroot_dir: directory where the sysroot will be located,
    :param clean: True - remove the sysroot folder if it exists,
                  False - otherwise (optional, default - True)
    '''

    if sysroot_dir.exists() and not clean:
        return

    print('Building SYSROOT...')

    if sysroot_dir.exists():
        shutil.rmtree(sysroot_dir)

    sysroot_dir.mkdir()

    sysroot_json = _temp_sysroot_json(sysroot_json, sysroot_dir)

    options = (
        f'--sysroot {sysroot_dir} '
        f'--source-dir {src_dir} '
        '--no-clean '
        '--verbose'
    )
    build_sysroot_cmd = f'pyqtdeploy-sysroot {options} {sysroot_json}'
    qt_src = sysroot_dir.joinpath('build', 'qtbase-everywhere-src-5.14.2')
    qt.run(build_sysroot_cmd, qt_src)


def _temp_sysroot_json(template_sysroot_json, sysroot_dir):
    '''Make a new 'sysroot.json' file and put it in the sysroot folder.
    This file also contain PyQt disabled features that are generated
    based on the Qt disabled features

    :param template_sysroot_json: path to the default 'sysroot.json',
    :param sysroot_dir: sysroot folder (where to put the new 'sysroot.json'),
    :return: path to the new 'sysroot.json'
    '''

    working_sysroot_json = sysroot_dir / 'sysroot.json'

    conf = SysrootJSON()
    conf.load(template_sysroot_json)
    conf.generate_pyqt_disabled_features()
    conf.save(working_sysroot_json)

    return working_sysroot_json


def _check_load_library_reminder():
    msg = ("'pyqtdeploy' needs 'loadlibrary.c' to be in the Python source "
           "(Python-x.x.x/Modules/expat/loadlibrary.c). New Python versions "
           "do not have this file. Check it. If there is no such a file "
           "then go to 'pyqtdeploy/metadata/python_metadata.py' and remove "
           "any mention of it")
    print(msg)

    input('Press any key to continue...')


def check_pdy_reminder(pdy_file):
    '''Remind about checking the paths in the :pdy_file:

    :param pdy_file: '.pdy' file to check
    '''

    msg = (f"Check the paths in '{pdy_file}' (main script, "
           "application package directory, packages directory, etc.)")
    print(msg)

    input('Press any key to continue...')


def build_myfyrio(sysroot_dir, pdy_file, build_dir):
    '''Build the programme

    :param sysroot_dir: path to the sysroot folder,
    :param pdy_file: path to the project '.pdy' file,
    :param build_dir: myfyrio build directory
    '''

    print('Building Myfyrio...')

    qt_src = sysroot_dir.joinpath('build', 'qtbase-everywhere-src-5.14.2')

    options = f'--sysroot {sysroot_dir} --build-dir {build_dir}'
    build_project_cmd = f'pyqtdeploy-build {options} {pdy_file}'
    qt.run(build_project_cmd, qt_src)

    qmake_cmd = sysroot_dir.joinpath('qt', 'bin', 'qmake')
    qt.run(str(qmake_cmd), qt_src, cwd=build_dir)

    make_cmd = 'make' if utils.is_linux() else 'nmake'
    qt.run(make_cmd, qt_src, cwd=build_dir)


def bundle_myfyrio(dist_dir, myfyrio_build_dir, sysroot_dir):
    '''Put all the necessary files (icon, licenses, '.desktop' file, app
    itself) into :dist_dir: and make an archive containing all the files

    :param dist_dir: folder to put the files into,
    :param myfyrio_build_dir: folder where the built executable file is,
    :param sysroot_dir: path to the sysroot folder
    '''

    print('Bundling Myfyrio...')

    release_dir = dist_dir / 'release'
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    release_dir.mkdir(parents=True)

    _copy_exe(release_dir, myfyrio_build_dir)
    _copy_licenses(release_dir, sysroot_dir)
    if utils.is_linux():
        _copy_icon(release_dir)
        _copy_desktop_file(release_dir)

    _set_permissions(release_dir)

    _archiving(release_dir, dist_dir)


def _copy_exe(dest_dir, myfyrio_build_dir):
    exe_file = 'Myfyrio'
    myfyrio_path = myfyrio_build_dir / exe_file
    if not utils.is_linux():
        exe_file += '.exe'
        myfyrio_path = myfyrio_build_dir.joinpath('release', exe_file)
    new_myfyrio_path = dest_dir / exe_file
    shutil.copyfile(myfyrio_path, new_myfyrio_path)

    mode = os.stat(new_myfyrio_path).st_mode
    os.chmod(new_myfyrio_path, mode | 0o111) # make executable


def _copy_icon(dest_dir):
    icon_path = project_dir.joinpath('myfyrio', 'static', 'images', 'icon.png')
    new_icon_path = dest_dir / 'icon.png'
    shutil.copyfile(icon_path, new_icon_path)


def _copy_desktop_file(dest_dir):
    deploy_dir = project_dir / 'deploy'
    desktop_path = deploy_dir.joinpath('static', 'myfyrio.desktop')
    new_desktop_path = dest_dir / 'myfyrio.desktop'
    shutil.copyfile(desktop_path, new_desktop_path)


def _copy_licenses(dest_dir, sysroot_dir):
    # Copy the prepared earlier LICENSEs
    deploy_dir = project_dir / 'deploy'
    licenses_path = deploy_dir.joinpath('static', 'LICENSES')
    new_licenses_path = dest_dir / 'LICENSES'
    shutil.copytree(licenses_path, new_licenses_path)
    if not utils.is_linux():
        libffi_license = new_licenses_path / 'libffi'
        shutil.rmtree(libffi_license)

    # Export Qt 3rd-party LICENSEs
    QT = 'qtbase-everywhere-src-5.14.2'
    export_folder = new_licenses_path.joinpath('Qt5', '3rdparty')
    thirdpartylibs_json = deploy_dir / '3rdpartylibs.json'
    qt_build_dir = sysroot_dir.joinpath('build', QT)

    json = utils.JSON()
    json.load(thirdpartylibs_json)
    thirdparty_libs = json.data

    prev_src_dir = ('/media/ntfs/Maxim/Sources/myfyrio/build-src/' + QT)
    qt3rdparty.fix_3rdpartylib_paths(
        thirdparty_libs, prev_src_dir, qt_build_dir
    )

    qt_src_dir = project_dir.joinpath('build-src', QT)
    if not qt_src_dir.exists():
        archive = qt_src_dir.parent / (QT + '.tar.gz')
        shutil.unpack_archive(archive, qt_src_dir)

    qt3rdparty.export_used_licenses(
        export_folder, thirdparty_libs, qt_build_dir, qt_src_dir
    )


def _set_permissions(release_dir):
    for path in release_dir.rglob('*'):
        if path.is_dir() or path.name == 'Myfyrio':
            os.chmod(path, 0o755)
        else:
            os.chmod(path, 0o644)


def _archiving(dir_to_arch, dest_dir):
    app_name = utils.name()
    app_version = utils.version()
    platform = 'linux64' if utils.is_linux() else 'win64'
    arch_name = dest_dir / f'{app_name}-{app_version}-{platform}'
    arch_format = 'gztar' if utils.is_linux() else 'zip'
    shutil.make_archive(arch_name, arch_format, root_dir=dir_to_arch)


class SysrootJSON(utils.BetterJSON):
    '''Represent 'sysroot.json' containing build settings'''

    def generate_pyqt_disabled_features(self):
        '''Use the Qt disabled features to generate PyQt disabled features and
        assign them to the corresponding 'json' object
        '''

        qt5 = self.data['qt5']
        features = ['PyQt_' + feature.replace('-', '_')
                    for feature in qt5['disabled_features']]

        if '-no-opengl' in qt5['configure_options']:
            features.append('PyQt_desktop_opengl')
            features.append('PyQt_opengl')

        self.data['pyqt5']['disabled_features'] = features


if __name__ == '__main__':
    pdy_file = project_dir.joinpath('deploy', 'myfyrio.pdy')
    _check_load_library_reminder() # Temporary till pyqtdeploy bug is fixed
    check_pdy_reminder(pdy_file)
    qt.check_build_dependencies()

    src_dir = project_dir / 'build-src'
    sysroot_json = project_dir.joinpath('deploy', 'sysroot.json')
    sysroot_dir = project_dir / 'sysroot'

    build_sysroot(src_dir, sysroot_json, sysroot_dir, clean=False)

    myfyrio_build_dir = project_dir / 'build'
    build_myfyrio(sysroot_dir, pdy_file, myfyrio_build_dir)

    dist_dir = project_dir / 'dist'
    bundle_myfyrio(dist_dir, myfyrio_build_dir, sysroot_dir)
