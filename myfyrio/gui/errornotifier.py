'''Copyright 2019-2020 Maxim Shpak <maxim.shpak@posteo.uk>

This file is part of Myfyrio.

Myfyrio is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Myfyrio is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Myfyrio. If not, see <https://www.gnu.org/licenses/>.

-------------------------------------------------------------------------------

Module implementing error notifications
'''

from typing import List

from PyQt5 import QtWidgets

from myfyrio import resources


def errorMessage(err_msgs: List[str]) -> None:
    '''Create QMessageBox (the "Warning" type) with the error message
    and show it to the user. If more than one error happened, show
    the general error message. If no errors happened, do nothing

    :param err_msgs: list with the messages of the happened errors
    '''

    log_file_name = resources.Log.ERROR.value # pylint: disable=no-member
    SEE_LOGS_MSG = f'For more details, see the "{log_file_name}" file'

    if err_msgs:
        if len(err_msgs) == 1:
            err_msg = err_msgs[0]
        else:
            err_msg = ('Some errors happened during the work '
                       'of the programme')

        err_msg = f'{err_msg}. {SEE_LOGS_MSG}'
        msg_box = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Warning, 'Error', err_msg
        )
        msg_box.exec()
