'''Copyright 2019-2020 Maxim Shpak <maxim.shpak@posteo.uk>

This file is part of Doppelgänger.

Doppelgänger is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Doppelgänger is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Doppelgänger. If not, see <https://www.gnu.org/licenses/>.

-------------------------------------------------------------------------------

Module implementing error notifications
'''

from typing import List

from PyQt5.QtWidgets import QMessageBox

from doppelganger.resources import Log


class ErrorNotifier:
    '''Collect all the errors happened during work of the programme
    and show them to the user as QMessageBox
    '''

    def __init__(self) -> None:
        self._errors: List[str] = []

    def addError(self, err: str) -> None:
        '''Add a new error message to the "ErrorNotifier" object'''

        self._errors.append(err)

    def reset(self) -> None:
        '''Clear all the previously added error messages'''

        self._errors = []

    def errorMessage(self) -> None:
        '''Create QMessageBox (the "Warning" type) with the error message
        and show it to the user. If more than one error have happened, show
        the general error message. If no errors have happened, do nothing
        '''

        log_file_name = Log.ERROR.value # pylint: disable=no-member
        SEE_LOGS_MSG = f'For more details, see the "{log_file_name}" file'

        if self._errors:
            if len(self._errors) == 1:
                err_msg = self._errors[0]
            else:
                err_msg = ('Some errors have happened during the work '
                           'of the programme')

            err_msg = f'{err_msg}. {SEE_LOGS_MSG}'
            msg_box = QMessageBox(QMessageBox.Warning, 'Error', err_msg)
            msg_box.exec()
