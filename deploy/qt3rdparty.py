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

Copy of 'licenses.py' from 'qt-3rdparty-licenses' without the '__main__' part
'''


import os
import pathlib
import shutil
import sys


def export_used_licenses(export_folder, thirdparty_libs, build_dir,
                         src_dir=None):
    '''Exporting the licenses of the used Qt 3rd-party libraries to
    the :export_folder: folder

    :param export_folder:   directory where to put the license files in,
    :param thirdparty_libs: list containing the Qt 3rd-party libraries with its
                            attributes (List[Dict[Attribute, Value]]),
    :param build_dir:       Qt build directory (need because 'Makefile's are
                            analysed to find out what 3rd-party libraries are
                            used in the Qt build),
    :param src_dir:         separate and clean Qt source directory (optional,
                            if a 'non-shadow build' is used, need to exclude
                            any premade 'Makefile's from the analysis; if a
                            'shadow built' is used, there'll not be any in
                            the build directory)
    '''

    print('Exporting the licenses of the used Qt 3rd-party libraries...')

    export_folder = pathlib.Path(export_folder)

    libs = libraries_factory(thirdparty_libs)

    for mf_path in Makefile.search(build_dir, src_dir=src_dir):
        mf = Makefile(mf_path)
        for lib in libs.copy():
            if lib.used(mf):
                new_license_dir = export_folder / lib.id()
                lib.export_license_file(new_license_dir)
                lib.export_copyright_file(new_license_dir)
                libs.remove(lib)


def libraries_factory(thirdparty_libs):
    '''Return a set of 'library' objects based on the attributes from
    :thirdparty_libs:

    :param thirdparty_libs: list containing the Qt 3rd-party libraries with its
                            attributes (List[Dict[Attribute, Value]]),
    :return: Set[Union[Library, WebgradientsLib]]
    '''

    libs = set()
    for lib_attrs in thirdparty_libs:
        id = lib_attrs['Id'] # pylint:disable=redefined-builtin
        if id == 'webgradients':
            lib = WebgradientsLib(lib_attrs)
        else:
            lib = Library(lib_attrs)

        libs.add(lib)
    return libs


def fix_3rdpartylib_paths(thirdparty_libs, prev_src_dir, src_dir):
    '''Change the 'LicenseFile' and 'Path' attributes so they point to the
    correct libraries in :src_dir: (e.g. the 'Path' attribute is
    '/home/jack/prev_qt_source/lib', :src_dir: is '/home/alex/new_qt_source'
    and :prev_src_dir: is '/home/jack/prev_qt_source', then the new 'Path' will
    be '/home/alex/new_qt_source/lib'. It can be useful if we want to
    generate the file with 3rd-party library attributes once and then use
    it in different places

    :param thirdparty_libs: list containing the Qt 3rd-party libraries with its
                            attributes (List[Dict[Attribute, Value]]),
    :param prev_src_folder: previous Qt source folder
                            (e.g. 'prev_qt_source'),
    :param src_dir:         Qt source directory
                            (e.g. '/home/alex/new_qt_source')
    '''

    src_dir = pathlib.Path(src_dir)
    prev_src_dir = pathlib.Path(prev_src_dir)

    for lib in thirdparty_libs:
        for path_attr in ['LicenseFile', 'Path']:
            path = lib[path_attr]
            if not path:
                continue

            path_parts = pathlib.Path(path).parts
            prev_src_folder_pos = path_parts.index(prev_src_dir.name)
            same_parts = path_parts[prev_src_folder_pos+1:]
            lib[path_attr] = str(src_dir.joinpath(*same_parts))


class Library:
    '''Represent a 3rd-party library used by Qt

    :param lib_data: dictionary with 3rd-party library attributes (from
                     '3rdpartylibs.json' file)
    '''

    def __init__(self, lib_data):
        self._data = lib_data
        self._signatures = []

    def used(self, makefile):
        '''Return True if any of the library files is found in :makefile:,
        False - otherwise

        :param makefile: Makefile object
        '''

        for sig in self.signatures:
            if makefile.has_path(sig):
                return True
        return False

    @property
    def signatures(self):
        '''Return the library file paths that used to find out if the lib is
        used in a Qt build. If the lib does not have information about
        the library files but only directory, the path to the directory will
        be returned, for example, '.../3rdparty/pcre2/' (with a trailing slash)
        '''

        sigs = self._signatures
        if sigs:
            return sigs

        lib_path, lib_filenames = pathlib.Path(self.path()), self.files()
        if lib_filenames: # e.g. 'linuxperf'
            lib_filepaths = [str(lib_path / name) for name in lib_filenames]
        elif lib_path.suffix: # e.g. 'grayraster'
            lib_filepaths = [lib_path]
        else: # e.g. 'angle'
            suffixes = (
                '.h', '.hh',
                '.c', '.cpp', '.cc',
                '.jar', # 'gradle', NEED TO BE TESTED (ANDROID)
                '.S', # 'pixman', NEED TO BE TESTED (ARM NEON)
                '.ttf' # fonts for WASM, NEED TO BE TESTED
            )
            lib_filepaths = [filepath for filepath in lib_path.rglob('*')
                             if filepath.suffix in suffixes]

        self._signatures = lib_filepaths
        return lib_filepaths

    def files(self):
        '''Return the library files (from the "Files" attribute). If there is
        none, an empty list is returned
        '''

        files = self._data['Files']
        if not files:
            return []
        return [name.rstrip(',') for name in files.split(' ')]

    def path(self):
        '''Return the library path (from the "Path" attribute)'''

        return self._data['Path']

    def license_file(self):
        '''Return the path to the license file (from the "LicenseFile"
        attribute)
        '''

        return self._data['LicenseFile']

    def copyright(self):
        '''Return the library copyright information'''

        return self._data['Copyright']

    def export_license_file(self, export_folder):
        '''Copy the license file into :export_folder:

        :param export_folder: folder to copy the license file into
        '''

        if not export_folder.exists():
            export_folder.mkdir(parents=True)

        license_file_path = self.license_file()
        if license_file_path:
            name = pathlib.Path(license_file_path).name
            new_path = export_folder / name
            shutil.copyfile(license_file_path, new_path)
        else:
            # If no license file in the attributes, it's 'Public Domain'
            self._public_domain(export_folder)

    def _public_domain(self, export_folder):
        license_file_path = export_folder / 'Public Domain'
        with open(license_file_path, 'w') as f:
            f.write(self._data['Copyright'])

    def export_copyright_file(self, export_folder):
        '''Copy the copyright file into :export_folder:

        :param export_folder: folder to copy the copyright file into
        '''

        if not export_folder.exists():
            export_folder.mkdir(parents=True)

        copyright_file = export_folder / 'COPYRIGHT'
        with open(copyright_file, 'w') as f:
            copyright_info = self.copyright()
            f.write(copyright_info)

    def id(self):
        '''Return the library identificator (unique, from the "Id"
        attribute)
        '''

        return self._data['Id']

    def __eq__(self, l):
        if not isinstance(l, Library):
            return NotImplemented
        return self.id() == l.id()

    def __hash__(self):
        return hash(self.id())


class WebgradientsLib(Library):
    '''Represent the 'webgradients' 3rd-party library'''

    @property
    def signatures(self):
        '''Return the 'webgradients.binaryjson' path'''

        file_path = super().signatures[0]
        parts = file_path.split('.')
        # Not '.css' but premade '.binaryjson' is used in compilation
        parts[-1] = 'binaryjson'
        return ['.'.join(parts)]


class Makefile:
    '''Represent a Makefile used in a Qt build process

    :param file_path: path to the Makefile
    '''

    def __init__(self, file_path):
        self.file_path = pathlib.Path(file_path)

        with open(file_path, 'r') as f:
            self._data = f.read()

    def has_path(self, path):
        '''Check if the Makefile uses :path: in the Qt build process

        :param path: path to some file,
        :return: True - the path has been found, False - otherwise
        '''

        separators = {' ', '\n', '\t'}
        data = self._data
        search_area_start = data.find('####### Compile')
        if search_area_start == -1:
            return False

        search_area_end = data.find('####### Install')

        # Makefiles generated by qmake do not use implicit rules, wildcards (as
        # far as I know, only explicit rules) so it must be sufficient just to
        # search for library files

        path = pathlib.Path(path)
        name = str(path.name)
        i = data.find(name, search_area_start, search_area_end)
        while i != -1:
            start, end = i, i

            while data[start] not in separators:
                start -= 1

            while data[end] not in separators:
                end += 1

            contender = self._sanitise(data[start+1:end])
            if contender == str(path):
                return True

            i = data.find(name, end+1, search_area_end)

        return False

    def _sanitise(self, s):
        if s[-1] == ':':
            return ''

        for prefix in ('-I', '$(INSTALL_ROOT)'):
            if s.startswith(prefix):
                s = s[len(prefix):]

        cwd = pathlib.Path.cwd()
        os.chdir(self.file_path.parent)
        path = pathlib.Path(s).resolve()
        os.chdir(cwd)
        return str(path)

    @staticmethod
    def search(build_dir, src_dir=None):
        '''Search 'Makefiles' in a Qt build directory

        :param build_dir:   Qt build directory,
        :param src_dir:     separate and clean Qt source directory (optional,
                            if need to exclude any premade 'Makefile's),
        :return:            list with the paths of the found 'Makefile's
        '''

        makefile_name = 'Makefile' # Linux, gcc

        # Exclude the premade 'Makefile's
        exclude_mfs = []
        if src_dir is not None:
            src_dir = pathlib.Path(src_dir)
            for mf_path in src_dir.rglob(makefile_name):
                path_tail = str(mf_path.relative_to(src_dir))
                exclude_mfs.append(path_tail)

        exclude_mfs = tuple(exclude_mfs)

        if sys.platform.startswith('win'):
            makefile_name = 'Makefile*Release' # Win, msvc

        build_dir = pathlib.Path(build_dir)
        makefiles = [mf_path for mf_path in build_dir.rglob(makefile_name)
                     if not str(mf_path).endswith(exclude_mfs)]
        return makefiles
