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

Module that lets you build Qt
'''

import os
import pathlib
import shutil
import sys

project_dir = pathlib.Path(__file__).parents[1].resolve()
sys.path.append(str(project_dir))

from deploy import utils # pylint:disable=wrong-import-position


def build(src_dir, build_dir, install_dir, options='', disabled_features='',
          clean=True):
    '''Build Qt5

    :param src_dir: folder with Qt5 source,
    :param build_dir: path to the build directory,
    :param install_dir: installation directory,
    :param options: Qt5 build options (optional),
    :param disabled_features: Qt5 disabled features with '-no-feature' prefix
                              (optional),
    :param clean: True - remove the existing :build_dir:, False - not
                  (optional, default - True)
    '''

    print('Building Qt...')

    if build_dir.exists():
        if clean:
            shutil.rmtree(build_dir)
            build_dir.mkdir()
        else:
            config_file = build_dir / 'config.cache'
            if config_file.exists():
                config_file.unlink()
    else:
        build_dir.mkdir()

    configure_path = src_dir / 'configure'
    configure_cmd = (f'{configure_path} {options} {disabled_features} '
                     f'-prefix {install_dir}')
    run(configure_cmd, src_dir, cwd=build_dir)

    make_cmd = 'make' if utils.is_linux() else 'nmake'
    run(make_cmd, src_dir, cwd=build_dir)

    print('Installing Qt...')

    if install_dir.exists():
        shutil.rmtree(install_dir)
    install_dir.mkdir()

    install_cmd = f'{make_cmd} install'
    run(install_cmd, src_dir, cwd=build_dir)

def run(cmd, src_dir, cwd=None):
    '''Run a command in the shell

    :param cmd: command to run,
    :param src_dir: folder with Qt5 source (to set environment variables in
                    Windows),
    :param cwd: set the current working directory (optional, default - None)
    '''

    if not utils.is_linux():
        set_vars_cmd = set_vars_msvc_cmd(src_dir)
        cmd = f'{set_vars_cmd} && {cmd}'

    utils.run(cmd, cwd=cwd)

def set_vars_msvc_cmd(src_dir):
    '''Return the command setting MSVC environment variables

    :param src_dir: folder with Qt5 source
    '''

    env_vars_bat = (r"C:\Program Files (x86)\Microsoft Visual Studio\2017"
                    r"\Community\VC\Auxiliary\Build\vcvarsall.bat")
    if not pathlib.Path(env_vars_bat).exists():
        raise RuntimeError('Microsoft Visual Studio is not installed')

    env_vars_bat = project_dir / 'deploy' / 'setvarsmsvc.bat'
    return f'CALL "{env_vars_bat}" {src_dir}'

def check_build_dependencies():
    '''Check that all the necessary dependencies are installed'''

    # https://doc.qt.io/qt-5/windows-requirements.html
    # https://doc.qt.io/qt-5/linux-requirements.html

    print('Checking build dependencies...')

    if utils.is_linux():
        deps = [
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
            'libxkbcommon-dev'
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
        check_func = utils.apt_installed
        msg = 'is not installed'
    else:
        deps = [
            'Perl64', # ActivePerl
            'Python'
        ]
        path = os.environ['PATH']
        check_func = lambda names: [(n, n in path) for n in names]
        msg = "is not installed or installed but not in 'PATH'"

    all_installed = True
    for name, installed in check_func(deps):
        if not installed:
            all_installed = False
            print(f'{name} {msg}')

    if not all_installed:
        input("Some dependencies are missing. If you are sure that "
              "everything is fine, press any key to continue...")


class QtJSON(utils.BetterJSON):
    '''Represent 'sysroot.json' with a couple of useful Qt plugin methods'''

    def qt_options(self):
        '''Return Qt configuration options as a string.
        E.g. '-static -no-opengl -ccache'
        '''

        return ' '.join(self.data['qt5']['configure_options'])

    def qt_disabled_features(self):
        '''Return Qt disabled features as a string.
        E.g. '-no-feature-colornames -no-feature-fontdialog'
        '''

        return ' '.join(['-no-feature-' + feature
                         for feature in self.data['qt5']['disabled_features']])


if __name__ == '__main__':
    check_build_dependencies()

    sysroot = project_dir / 'sysroot'
    if not sysroot.exists():
        sysroot.mkdir()

    sysroot_json = project_dir.joinpath('deploy', 'sysroot.json')
    conf = QtJSON()
    conf.load(sysroot_json)
    options = conf.qt_options()
    disabled_features = conf.qt_disabled_features()

    src_dir = project_dir.joinpath('build-src', 'qtbase-everywhere-src-5.14.2')
    build_dir = sysroot / 'build-qt'
    install_dir = sysroot / 'Qt'
    build(src_dir, build_dir, install_dir, clean=False, options=options,
          disabled_features=disabled_features)
