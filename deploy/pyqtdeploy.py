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

project_dir = pathlib.Path(__file__).parents[1].resolve()
sys.path.append(str(project_dir))

# pylint:disable=wrong-import-position
from deploy import qt, utils
from myfyrio import metadata as md


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

    conf = SysrootJSON()
    conf.load(sysroot_json)
    conf.generate_pyqt_disabled_features()
    cw_sysroot_json = sysroot_dir / 'sysroot.json'
    conf.save(cw_sysroot_json)

    options = (
        f'--sysroot {sysroot_dir} '
        f'--source-dir {src_dir} '
        '--no-clean '
        '--verbose'
    )
    build_sysroot_cmd = f'pyqtdeploy-sysroot {options} {cw_sysroot_json}'
    qt_src = sysroot_dir.joinpath('build', 'qtbase-everywhere-src-5.14.2')
    qt.run(build_sysroot_cmd, qt_src)


def check_load_library_reminder():
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

    name = md.NAME.lower()

    pdy_file = project_dir.joinpath('deploy', f'{name}.pdy')
    check_load_library_reminder() # Temporary till pyqtdeploy bug is fixed
    check_pdy_reminder(pdy_file)
    qt.check_build_dependencies()

    src_dir = project_dir / 'build-src'
    sysroot_json = project_dir.joinpath('deploy', 'sysroot.json')
    sysroot_dir = project_dir / 'sysroot'

    build_sysroot(src_dir, sysroot_json, sysroot_dir, clean=False)

    build_dir = project_dir / 'build'
    build_myfyrio(sysroot_dir, pdy_file, build_dir)
