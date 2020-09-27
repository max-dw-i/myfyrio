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
import subprocess
import sys
from collections import UserDict


def pip_installed(package):
    '''Check if :package: is installed by the 'pip' package manager

    :param package: name of the package to check,
    :return: True - :package: is installed, False - otherwise
    '''

    # If the package name has dashes ('-'), replace with dots ('.')
    package = package.replace('-', '.')
    spec = importlib.util.find_spec(package)
    return spec is not None

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

def save_file(text, file, chmod=None):
    '''Save :text: into :file:. Also set the file permissions

    :param text: text to save into the file,
    :param file: path to the file,
    :param chmod: permissions, e.g. 0o644 (optional)
    '''

    with open(file, 'w') as f:
        f.write(text)

    if chmod is not None:
        os.chmod(file, chmod)

def strip_exe(executable):
    '''Remove symbols from :executable:

    :param executable: executable file to strip
    '''

    cmd = f'strip -s {executable}'
    run(cmd)

def add_ccache_to_PATH_cmd():
    '''Return the command adding the 'ccache' path with the compiler symlinks
    to :PATH: so 'ccache' can be used

    :return: 'export PATH=/usr/lib/ccache:rest_of_PATH'
    '''

    CCACHE_PATH = '/usr/lib/ccache'
    PATH = os.environ['PATH']
    return f'export PATH={CCACHE_PATH}:{PATH}'

def is_linux():
    '''Return True if the platform is 'Linux', otherwise - False'''

    if sys.platform.startswith('linux'):
        return True
    return False


class JSON(UserDict):
    '''Represent '.json' file

    :param file_path: path to the '.json' file
    '''

    def load(self, file_path):
        with open(file_path, 'r') as f:
            self.data = json.load(f) # pylint:disable=attribute-defined-outside-init

    def save(self, file_path):
        with open(file_path, 'w') as f:
            json.dump(self.data, f)


class BetterJSON(JSON):
    '''Represent '.json' file that can have platform specific options
    and 'comment values' if an option is a list. After the file is loaded,
    it's sanitised (without 'comment values' and platform specific options -
    your platform options have been chosen and merged under a not platform
    specific option, e.g. the platform is 'win' and the options are 'option'
    and 'win#option', then the values of these 2 options will be merged under
    a new option 'option')
    '''

    def load(self, file_path):
        super().load(file_path)

        self._group_platform_options()
        self._uncomment() # call AFTER '_group_platform_options'

    def _group_platform_options(self):
        platform = 'linux'
        if sys.platform.startswith('win'):
            platform = 'win'

        data = {plugin: {} for plugin in self.data}
        for plugin, options in self.data.items():
            for option, value in options.items():
                if '#' in option:
                    # platform specific, e.g. 'win|macos#configure_options'
                    option_platforms, option = option.split('#')
                    if platform not in option_platforms:
                        continue

                if option in data[plugin]:
                    if not isinstance(value, list):
                        raise ValueError(f"'{option}' is already provided")
                    data[plugin][option].extend(value)
                else:
                    data[plugin][option] = value

        self.data = data # pylint:disable=attribute-defined-outside-init

    def _uncomment(self):
        for plugin, options in self.data.items():
            for option, value in options.items():
                if isinstance(value, list):
                    self.data[plugin][option] = [el for el in value
                                                 if not el.startswith('#')]
