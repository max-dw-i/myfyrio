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

Module implementing logging
'''

import logging
import logging.handlers as handlers
import sys

from doppelganger import resources


class Logger:
    '''Class implementing setting and getting the programme's logger'''

    NAME = 'main'
    MAX_FILE_SIZE = 1024**2 # Bytes
    FILES_TOTAL = 2

    @classmethod
    def setLogger(cls) -> None:
        '''Set the programme's logger. The logger has level 'WARNING',
        rotates log files (2 files 2 MegaBytes each at most). Message format is
        'time - logger name - message level - messsage'
        '''

        logger = logging.getLogger(cls.NAME)
        logger.setLevel(logging.WARNING)

        FORMAT = '{asctime} - {name} - {levelname} - {message}'
        formatter = logging.Formatter(fmt=FORMAT, style='{')

        logfile = resources.Log.ERROR.abs_path # pylint: disable=no-member
        rh = handlers.RotatingFileHandler(logfile, maxBytes=cls.MAX_FILE_SIZE,
                                          backupCount=cls.FILES_TOTAL-1)
        rh.setFormatter(formatter)
        logger.addHandler(rh)

        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    @classmethod
    def getLogger(cls, suffix: str) -> logging.Logger:
        '''Get the programme's logger with name 'NAME + . + :suffix:'
        (e.g. 'main.processing' if :suffix: == 'processing').

        :param suffix:  suffix of the logger name,
        :return:        "Logger" object
        '''

        logger_name = '.'.join([cls.NAME, suffix])
        return logging.getLogger(logger_name)
