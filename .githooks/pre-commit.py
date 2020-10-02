#!/usr/bin/env python

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

import pathlib
import sys
from xml.etree import ElementTree

# __file__ is symlink from ./.git/hook so the index == 2 (not 1)
project_dir = pathlib.Path(__file__).parents[2].resolve()
sys.path.append(str(project_dir))

# pylint:disable=wrong-import-position
from myfyrio import metadata as md
from myfyrio import resources


def ui_field_text(ui_file, w_name):
    tree = ElementTree.parse(ui_file)
    root = tree.getroot()
    for w in root.iter('widget'):
        if w.get('name') == w_name:
            return w.findtext('./property/string')
    raise ValueError('Cannot find the widget in the file')

main_ui = pathlib.Path(resources.UI.MAIN.get()) # pylint: disable=no-member
about_ui = pathlib.Path(resources.UI.ABOUT.get()) # pylint: disable=no-member
main_name = main_ui.name
about_name = about_ui.name
md_name = pathlib.Path(md.__file__).name

msg = ''

app_name = md.NAME

if app_name != ui_field_text(main_ui, 'MainWindow'):
    raise ValueError(f"Names in '{main_name}' and '{md_name}' don't match")

if app_name != ui_field_text(about_ui, 'nameLbl'):
    raise ValueError(f"Names in '{about_name}' and '{md_name}' don't match")

if md.VERSION != ui_field_text(about_ui, 'versionLbl').split(' ')[-1]:
    raise ValueError(f"Versions in '{about_name}' and '{md_name}' don't match")

copyright_label = ui_field_text(about_ui, 'copyrightLbl')

if md.AUTHOR not in copyright_label:
    raise ValueError(f"Author name in '{about_name}' may be wrong")

if md.AUTHOR_EMAIL not in copyright_label:
    raise ValueError(f"Author email in '{about_name}' may be wrong")
