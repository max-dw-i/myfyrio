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

Module that implements different functions used in build process
'''

import importlib.util
import json
import os
import pathlib
import subprocess
from xml.etree import ElementTree


def name():
    '''Return the programme's name'''

    return _widget_text('nameLbl')

def version():
    '''Return the programme's version'''

    return _widget_text('versionLbl').split(' ')[-1]

def _widget_text(widget_name):
    project_root = pathlib.Path(__file__).parents[1]
    about_ui = project_root / 'myfyrio' / 'static' / 'ui' / 'aboutwindow.ui'

    tree = ElementTree.parse(about_ui)
    root = tree.getroot()
    for w in root.iter('widget'):
        if w.get('name') == widget_name:
            return w.findtext('./property/string')

    raise ValueError(f'Cannot find the "{widget_name}" widget')

def pip_installed(package):
    '''Check if :package: is installed by the 'pip' package manager

    :param package: name of the package to check,
    :return: True - :package: is installed, False - otherwise
    '''

    # If the package name has dashes ('-'), replace with dots ('.')
    spec = importlib.util.find_spec(package)
    installed = False
    if spec is not None:
        installed = True

    return installed

def apt_installed(packages):
    '''Check if :packages: are installed by the 'apt' package manager

    :param packages: Iterable[str], names of the packages to check,
    :return: List[Tuple[str, bool]],
             list of tuples (Package Name, Installed or not)
    '''

    installed = run('apt list --installed', stdout=False)
    return [(pkg, pkg in installed) for pkg in packages]

def run(cmd, cwd=None, stdout=True):
    '''Run a command in the shell

    :param cmd: command to run,
    :param cwd: set the current working directory (optional, default - None),
    :param stdout: True - print to stdout,
                   False - intercept the command output for
                   analysing (optional, default - True),
    :return: command output if :stdout: is False, an empty string if :stdout:
             is True
    '''

    result = subprocess.run(cmd, shell=True, check=True, cwd=cwd,
                            stdout=None if stdout else subprocess.PIPE)
    output = result.stdout
    if output is None:
        return ''
    return output.decode('utf-8')

def ccache_wrapper(cmd):
    '''Precede the :cmd: command with a command adding the 'ccache' path
    with the compiler symlinks to :PATH: so 'ccache' can be used

    :cmd: command to run,
    :return: e.g. 'export PATH=/usr/lib/ccache:rest_of_PATH && make'
    '''

    CCACHE_PATH = '/usr/lib/ccache'
    PATH = os.environ['PATH']
    new_PATH = f'{CCACHE_PATH}:{PATH}'
    return f'export PATH={new_PATH} && {cmd}'


class ConfigJSON:
    '''Represent '.json' file'''

    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None

    def load(self):
        with open(self.file_path, 'r') as f:
            data = f.read()
            self.data = json.loads(data)

    def save(self, file_path):
        data = json.dumps(self.data)
        with open(file_path, 'w') as f:
            f.write(data)


class SysrootJSON(ConfigJSON):
    '''Parse and load 'sysroot.json' containing build settings'''

    @staticmethod
    def _uncomment(data):
        qt5 = data['qt5']
        for k in ['configure_options', 'disabled_features']:
            qt5[k] = [v for v in qt5[k] if not v.startswith('#')]

    def load(self):
        super().load()
        self._uncomment(self.data)

    def qt_options(self):
        '''Return Qt configuration options as a string.
        E.g. '-static -no-opengl -ccache'
        '''

        options = self.data['qt5']['configure_options']
        return ' '.join(options)

    def qt_disabled_features(self):
        '''Return Qt disabled features as a string.
        E.g. '-no-feature-colornames -no-feature-fontdialog'
        '''
        features = self.data['qt5']['disabled_features']
        return ' '.join(['-no-feature-' + f for f in features])

    def generate_pyqt_disabled_features(self):
        '''Use the Qt disabled features to generate PyQt disabled features and
        assign them to the corresponding json object
        '''

        features = self.data['qt5']['disabled_features']
        features = ['PyQt_' + f.replace('-', '_') for f in features]

        options = self.data['qt5']['configure_options']
        if '-no-opengl' in options:
            features.append('PyQt_desktop_opengl')
            features.append('PyQt_opengl')

        self.data['pyqt5']['disabled_features'] = features
