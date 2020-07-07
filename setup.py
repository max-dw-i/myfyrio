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
'''

from pathlib import Path
from xml.etree import ElementTree

from setuptools import find_packages, setup

from myfyrio import resources


def version():
    tree = ElementTree.parse(resources.UI.ABOUT.abs_path) # pylint: disable=no-member
    root = tree.getroot()
    for w in root.iter('widget'):
        if w.get('name') == 'versionLbl':
            return w.findtext('./property/string').split(' ')[-1]

    raise ValueError("Cannot extract the programme's version")

readme_file = Path(__file__).parent / 'README.md'
with open(readme_file, 'r') as f:
    long_description = f.read()

URL = 'https://github.com/oratosquilla-oratoria/myfyrio/'

setup(
    name='Myfyrio',
    version=version(),
    author='Maxim Shpak',
    author_email='maxim.shpak@posteo.uk',
    description='Find similar (duplicate) images',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=URL,
    packages=find_packages(exclude=['tests', 'deployment', 'deployment.*']),
    py_modules=['main'],
    package_data={
        'myfyrio.static.images': ['*.png', 'LICENSE'],
        'myfyrio.static.ui': ['*.ui', 'LICENSE'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Natural Language :: English',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Multimedia :: Graphics :: Viewers',
    ],
    keywords='image, picture, photo, identical, similar, duplicate',
    python_requires='>=3.6, <4',
    install_requires=['PyQt5>=5.8.1.1', 'pybktree==1.1'],
    extras_require={
        'dev': ['mypy'],
    },
    entry_points={
        'console_scripts': [
            'myfyrio=main:main',
        ],
    },
    project_urls={
        'Bug Reports': URL + 'issues/',
        'Source': URL,
    },
)
