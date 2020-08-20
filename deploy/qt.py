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

def export_licenses(export_folder, thirdpartylibs_json, src_dir, build_dir):
    '''Exporting the licenses of the used 3rd-party libraries to
    the :export_folder: folder

    :param export_folder: folder where to put the license files in,
    :param thirdpartylibs_json: '.json' file containing the attributes of
                                the Qt 3rd-party libraies. It can be generated
                                with 'qtchooser -run-tool=qtattributionsscanner
                                -qt=5 --output-format "json"
                                -o 3rdpartylibs.json /path/to/Qt5/sources' (Qt5
                                with the 'qtattributionsscanner' tool must be
                                installed or built, obviously),
    :param src_dir: Qt source directory,
    :param build_dir: Qt build directory (need because 'Makefile's are analysed
                      to find out what 3rd-party libs are used in the Qt build)
    '''

    print('Exporting the licenses of the used 3rd-party libraries...')

    conf = ThirdpartylibsJSON()
    conf.load(thirdpartylibs_json)
    conf.fix_paths(src_dir)

    build_src_subdir = build_dir / 'src'
    libs = {License(lib_data, src_dir) for lib_data in conf.data}
    makefiles = list(build_src_subdir.rglob('Makefile'))
    if not utils.is_linux():
        makefiles.extend(list(build_src_subdir.rglob('Makefile.Release')))
    if not makefiles:
        msg = ('Cannot find Makefiles in the build directory. '
               'Exporting the licenses has been cancelled')
        print(msg)

    for mf in makefiles:
        with open(mf, 'r') as f:
            text = f.read()

            temp_libs = libs.copy()
            for lib in temp_libs:
                for sig in lib.signatures():
                    if sig in text:
                        new_lf_folder = export_folder / lib.id()
                        lib.export_license_file(new_lf_folder)
                        libs.remove(lib)
                        break


class ThirdpartylibsJSON(utils.JSON):
    '''Represent '.json' file containing the attributes of the Qt 3rd-party
    libraries used
    '''

    def fix_paths(self, src_dir):
        '''Change the 'LicenseFile' and 'Path' attributes to the correct
        ones (e.g. the 'Path' attribute equals to '/home/jack/1/qt_source/lib'
        and :src_dir: is '/home/alex/qt_source', then the new 'Path' will be
        '/home/alex/qt_source/lib'; it works only if the source folders -
        'qt_source' - have the same name)

        :param src_dir: Qt source directory,
        :raise ValueError: the source directories in :src_dir: and in
                           the 'Path', 'LicenseFile' attributes do not match
        '''

        for lib in self.data:
            for path_attr in ['LicenseFile', 'Path']:
                lib[path_attr] = self._change_path_prefix(
                    lib[path_attr], src_dir
                )

    @staticmethod
    def _change_path_prefix(path, new_path_prefix):
        if not path:
            return ''

        prefix = pathlib.Path(new_path_prefix)
        path_parts = pathlib.Path(path).parts
        try:
            common_folder_pos = path_parts.index(prefix.parts[-1])
        except ValueError:
            msg = ('Cannot fix the paths automatically because the Qt source '
                   "folders' names do not match. You have to fix the paths "
                   'manually')
            raise ValueError(msg)
        return str(prefix.joinpath(*path_parts[common_folder_pos+1:]))


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


class License:
    '''Represent 3rd-party library license

    :param lib_data: dictionary with 3rd-party library attributes (from
                     '3rdpartylibs.json' file),
    :param src_dir: Qt source directory
    '''

    def __init__(self, lib_data, src_dir):
        self._data = lib_data
        self._src_dir = src_dir

    def signatures(self):
        '''Return the paths to the library files relative to the 'src'
        subdirectory of Qt source directory (:self.src_dir:) and used
        to find out if the lib was built in the current Qt build.
        E.g. Qt source path - '/Qt/source',
        lib file path - '/Qt/source/src/corelib/io/qurltlds_p.h',
        then 'corelib/io/qurltlds_p.h' will be returned. If the lib is
        not a file, for example, '3rdparty/pcre2/' will be returned
        (with a trailing slash)
        '''

        lib_path = pathlib.Path(self._data['Path'])
        src_subdir = self._src_dir / 'src'

        lib_filenames = self._data['Files'].split(' ')
        if not lib_filenames:
            lib_filenames = ['']
        return [self._relative_to(lib_path / name, src_subdir)
                for name in lib_filenames]

    @staticmethod
    def _relative_to(path, prefix):
        rel_path = path.relative_to(prefix)
        # If the relative path has a suffix, the library is a file...
        if rel_path.suffix:
            return str(rel_path)
        # ...if not, it's a directory. For example, we have 2 libs: 'harfbuzz'
        # and 'harfbuzz-ng'. If we do not add '/' at the end, we'll get
        # a mismatch cause 'harfbuzz' is a substring of 'harfbuzz-ng'
        separator = '\\' if sys.platform.startswith('win32') else '/'
        return str(rel_path) + separator

    def license_file(self):
        '''Return the path to the license file'''

        return self._data['LicenseFile']

    def export_license_file(self, export_folder):
        '''Copy the license file into :export_folder:

        :param export_folder: folder to copy the license file into
        '''

        if not export_folder.exists():
            export_folder.mkdir(parents=True)

        lf_path = self.license_file()
        if lf_path:
            lf_name = pathlib.Path(lf_path).name
            new_lf_path = export_folder / lf_name
            shutil.copyfile(lf_path, new_lf_path)
        else:
            # If no license file in the attributes, it's 'Public Domain'
            self._public_domain(export_folder)

    def _public_domain(self, export_folder):
        lf_path = export_folder / 'Public Domain'
        with open(lf_path, 'w') as f:
            f.write(self._data['Copyright'])

    def id(self):
        '''Return the library identificator (unique)'''

        return self._data['Id']

    def __eq__(self, l):
        if not isinstance(l, License):
            return NotImplemented
        return self.id() == l.id()

    def __hash__(self):
        return hash(self.id())


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
