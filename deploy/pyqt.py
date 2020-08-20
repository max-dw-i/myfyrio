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

Module that lets you build PyQt
'''

import pathlib
import shutil
import sys

project_dir = pathlib.Path(__file__).parents[1].resolve()
sys.path.append(str(project_dir))

from deploy import qt, utils # pylint:disable=wrong-import-position


def build(src_dir, build_dir, qmake, build_options=None, install_dir=None):
    '''Build PyQt5

    :param src_dir: folder with the unpacked PyQt5,
    :param build_dir: path to the build directory,
    :param qmake: path to the Qt5 'qmake',
    :param build_options: list with build options,
                          e.g. ['--confirm-license', '--verbose'],
    :param install_dir: installation directory (optional, default - None,
                        if None, it will be installed in the Python
                        'site-packages' directory)
    '''

    # pip install PyQt-builder
    print('Building PyQt...')

    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()

    options = [
        f'--build-dir {build_dir}',
        f'--qmake {qmake}',
    ]

    if build_options is not None:
        options.extend(build_options)

    if install_dir is not None:
        if not install_dir.exists():
            install_dir.mkdir()

        options.append(f'--target-dir {install_dir}')

    options = ' '.join(options)
    cmd = f'sip-install {options}'
    if utils.is_linux():
        add_ccache_cmd = utils.add_ccache_to_PATH_cmd()
        cmd = f'{add_ccache_cmd} && {cmd}'
    qt.run(cmd, src_dir, cwd=src_dir)

def check_build_dependencies():
    '''Check that all the necessary dependencies are installed'''

    if not utils.pip_installed('pyqtbuild'):
        raise RuntimeError('Install PyQt-builder')

def set_project_toml():
    # TODO: add disabled features to toml dynamically
    pass


if __name__ == '__main__':
    check_build_dependencies()

    sysroot = project_dir / 'sysroot'
    if not sysroot.exists():
        sysroot.mkdir()

    src_dir = project_dir.joinpath('build-src', 'PyQt5-5.14.2mod')
    build_dir = sysroot / 'build-pyqt'
    install_dir = sysroot / 'PyQt'
    qt_bin = sysroot.joinpath('Qt', 'bin')
    qmake = qt_bin / ('qmake' if utils.is_linux() else 'qmake.exe')

    options = [
        '--confirm-license',
        '--no-dbus-python',
        '--no-designer-plugin',
        '--no-qml-plugin',
        '--no-tools',
        '--no-docstring',
        '--enable QtCore',
        '--enable QtGui',
        '--enable QtWidgets',
        '--verbose'
    ]

    build(src_dir, build_dir, qmake, build_options=options,
          install_dir=install_dir)
