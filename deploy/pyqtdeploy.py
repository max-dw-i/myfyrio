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

import pathlib
import shutil
import sys

project_dir = pathlib.Path(__file__).parents[1].absolute()
sys.path.append(str(project_dir))

from deploy import qt # pylint:disable=wrong-import-position
from deploy import utils # pylint:disable=wrong-import-position


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
    cmd = f'pyqtdeploy-sysroot {options} {sysroot_json}'
    utils.run(cmd)

def _temp_sysroot_json(sysroot_json, sysroot_dir):
    '''Make a new 'sysroot.json' file and put it in the sysroot folder.
    This file also contain PyQt disabled features that are generated
    based on the Qt disabled features

    :param sysroot_json: path to the default 'sysroot.json',
    :param sysroot_dir: sysroot folder (where to put the new 'sysroot.json'),
    :return: path to the new 'sysroot.json'
    '''

    temp_sysroot_json_path = sysroot_dir / 'sysroot.json'

    conf = utils.SysrootJSON(sysroot_json)
    conf.load()
    conf.generate_pyqt_disabled_features()
    conf.save(temp_sysroot_json_path)

    return temp_sysroot_json_path

def check_build_dependencies():
    '''Check that all the necessary dependencies are installed. If not,
    raise an exception with the packages not installed

    :raise RuntimeError: if there is any not installed package
    '''

    print('Checking build dependencies...')

    qt_xcb_deps = [
        'libfontconfig1-dev',
        'libfreetype6-dev',
        'libx11-dev',
        'libxext-dev',
        'libxfixes-dev',
        'libxi-dev',
        'libxrender-dev',
        'libxcb1-dev',
        'libx11-xcb-dev',
        'libxcb-glx0-dev',
        'libxkbcommon-x11-dev',
        'libxkbcommon-dev',
    ]

    #system_xcb_deps = [
    #    'libxcb-keysyms1-dev',
    #    'libxcb-image0-dev',
    #    'libxcb-shm0-dev',
    #    'libxcb-icccm4-dev',
    #    'libxcb-sync0-dev',
    #    'libxcb-xfixes0-dev',
    #    'libxcb-shape0-dev',
    #    'libxcb-randr0-dev',
    #    'libxcb-render-util0-dev',
    #]
    pkgs = utils.apt_installed(qt_xcb_deps)
    not_installed = '\n'.join(
        [f'{name} is missing' for name, installed in pkgs if not installed]
    )
    if not_installed:
        raise RuntimeError(f'\n{not_installed}')

def _check_load_library():
    msg = ("'pyqtdeploy' needs 'loadlibrary.c' to be in the Python source "
           "(Python-x.x.x/Modules/expat/loadlibrary.c). New Python versions "
           "do not have this file. Check it. If there is no such a file "
           "then go to 'pyqtdeploy/metadata/python_metadata.py' and remove "
           "any mention of it")
    print(msg)

    input('Press any key to continue...')

def check_pdy(pdy_file):
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

    options = f'--sysroot {sysroot_dir} --build-dir {build_dir}'
    cmd = f'pyqtdeploy-build {options} {pdy_file}'
    utils.run(cmd)

    qmake = sysroot_dir / 'host' / 'bin' / 'qmake'
    utils.run(str(qmake), cwd=str(build_dir))

    make_cmd = 'nmake' if sys.platform.startswith('win') else 'make'
    utils.run(make_cmd, cwd=str(build_dir))

def bundle_myfyrio(dist_dir, myfyrio_build_dir, sysroot_dir):
    '''Put all the necessary files (icon, licenses, '.desktop' file, app
    itself) into :dist_dir: and make an archive containing all the files

    :param dist_dir: folder to put the files into,
    :param myfyrio_build_dir: folder where the built executable file is,
    :param sysroot_dir: path to the sysroot folder
    '''

    print('Bundling Myfyrio...')

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()

    myfyrio_path = myfyrio_build_dir / 'Myfyrio'
    new_myfyrio_path = dist_dir / 'Myfyrio'
    shutil.copyfile(myfyrio_path, new_myfyrio_path)

    project_folder = pathlib.Path(__file__).parents[1]
    icon_path = project_folder / 'myfyrio' / 'static' / 'images' / 'icon.png'
    new_icon_path = dist_dir / 'icon.png'
    shutil.copyfile(icon_path, new_icon_path)

    deploy_dir = project_folder / 'deploy'
    desktop_path = deploy_dir / 'static' / 'Myfyrio.desktop'
    new_desktop_path = dist_dir / 'Myfyrio.desktop'
    shutil.copyfile(desktop_path, new_desktop_path)

    licenses_path = deploy_dir / 'static' / 'LICENSES'
    new_licenses_path = dist_dir / 'LICENSES'
    shutil.copytree(licenses_path, new_licenses_path)

    export_folder = new_licenses_path / 'Qt5' / '3rdparty'
    thirdpartylibs_json = deploy_dir / '3rdpartylibs.json'
    qt_src_dir = sysroot_dir / 'build' / 'qtbase-everywhere-src-5.14.2'
    # 'pyqtdeploy' do not use shadow build so 'qt_src_dir'
    # and 'qt_build_dir' are the same
    qt.export_licenses(export_folder, thirdpartylibs_json, qt_src_dir,
                       qt_src_dir)

    shutil.make_archive(new_myfyrio_path, 'gztar', root_dir=dist_dir)


if __name__ == '__main__':
    src_dir = project_dir / 'build-src'
    sysroot_json = project_dir / 'deploy' / 'sysroot.json'
    sysroot_dir = project_dir / 'sysroot'
    pdy_file = project_dir / 'deploy' / 'myfyrio.pdy'

    _check_load_library() # Temporary till pyqtdeploy bug is fixed
    check_pdy(pdy_file)
    check_build_dependencies()

    build_sysroot(src_dir, sysroot_json, sysroot_dir, clean=False)

    myfyrio_build_dir = project_dir / 'build'
    build_myfyrio(sysroot_dir, pdy_file, myfyrio_build_dir)

    dist_dir = project_dir / 'dist'
    bundle_myfyrio(dist_dir, myfyrio_build_dir, sysroot_dir)
