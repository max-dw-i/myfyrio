'''Copyright 2019 Maxim Shpak <maxim.shpak@posteo.uk>

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

Graphical user interface'''

import logging
import pathlib

from PyQt5.QtCore import QFileInfo, Qt, QThreadPool, pyqtSlot
from PyQt5.QtGui import QBrush, QColor, QFontMetrics, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QListWidgetItem, QMainWindow,
    QMessageBox, QVBoxLayout, QWidget)
from PyQt5.uic import loadUi

from doppelganger import processing

UI = str(pathlib.Path('doppelganger') / 'gui.ui')
IMAGE_ERROR = str(pathlib.Path('doppelganger') / 'resources' / 'image_error.png')
SIZE = 200
SELECTED_BACKGROUND_COLOR = '#d3d3d3'

gui_logger = logging.getLogger('main.gui')

class InfoLabelWidget(QLabel):
    '''Abstract Label class'''

    def __init__(self, text):
        super().__init__()
        self.setAlignment(Qt.AlignHCenter)
        self.setText(self._word_wrap(text))

    def _word_wrap(self, text):
        '''QLabel wraps words only at word-breaks but we need
        it to happen at any letter

        :param text: str, any text,
        :return: str, wrapped text
        '''

        fontMetrics = QFontMetrics(self.font())
        wrapped_text = ''
        line = ''

        for c in text:
            # We have 4 margins 9px each (I guess) so we take 40
            if fontMetrics.size(Qt.TextSingleLine, line + c).width() > SIZE - 40:
                wrapped_text += line + '\n'
                line = c
            else:
                line += c
        wrapped_text += line

        return wrapped_text


class SimilarityLabel(InfoLabelWidget):
    '''Label class to show info about images similarity'''


class ImageSizeLabel(InfoLabelWidget):
    '''Label class to show info about the image size'''


class ImagePathLabel(InfoLabelWidget):
    '''TextEdit class to show the path to an image'''

    def __init__(self, text):
        super().__init__(QFileInfo(text).canonicalFilePath())

class ImageInfoWidget(QWidget):
    '''Label class to show info about an image (its similarity
    rate, size and path)'''

    def __init__(self, path, difference, dimensions, filesize):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignBottom)

        widgets = (
            SimilarityLabel(str(difference)),
            ImageSizeLabel(self._get_image_size(dimensions, filesize)),
            ImagePathLabel(path)
        )
        for widget in widgets:
            layout.addWidget(widget)
        self.setLayout(layout)

    @staticmethod
    def _get_image_size(dimensions, filesize):
        '''Return info about image dimensions and file size

        :param dimensions: tuple, (width: int, height: int),
        :param filesize: float, file size in bytes, kilobytes or megabytes,
                                rounded to the first decimal place,
        :returns: str, string with format '{width}x{height}, {file_size} {units}'
        '''

        width, height = dimensions[0], dimensions[1]
        units = 'KB'

        return f'{width}x{height}, {filesize} {units}'


class ThumbnailWidget(QLabel):
    '''Label class to render image thumbnail'''

    def __init__(self, thumbnail):
        super().__init__()
        self.setAlignment(Qt.AlignHCenter)
        self.pixmap = self._QByteArray_to_QPixmap(thumbnail)
        self.setPixmap(self.pixmap)

    @staticmethod
    def _QByteArray_to_QPixmap(thumbnail):
        '''Converts a QByteArray image to QPixmap

        :param thumbnails: <class QByteArray>, an image,
        :returns: corresponding <class QPixmap> object or,
                  if something's wrong - <class QPixmap>
                  object with 'error image'
        '''

        # Pixmap can read BMP, GIF, JPG, JPEG, PNG, PBM, PGM, PPM, XBM, XPM
        if thumbnail is None:
            return QPixmap(IMAGE_ERROR).scaled(SIZE, SIZE)

        pixmap = QPixmap()
        pixmap.loadFromData(thumbnail)

        if pixmap.isNull():
            gui_logger.error('Something happened while converting QByteArray into QPixmap')
            return QPixmap(IMAGE_ERROR).scaled(SIZE, SIZE)

        return pixmap

    def mark(self):
        '''Mark a thumbnail as selected'''

        marked = self.pixmap.copy()
        width, height = marked.width(), marked.height()

        painter = QPainter(marked)
        brush = QBrush(QColor(0, 0, 0, 128))
        painter.setBrush(brush)
        painter.drawRect(0, 0, width, height)
        painter.end()
        self.setPixmap(marked)

    def unmark(self):
        '''Mark a thumbnail as not selected'''

        self.setPixmap(self.pixmap)


class DuplicateCandidateWidget(QWidget):
    '''Widget class to render a duplicate candidate image and
    all the info about it (its similarity rate, size and path)
    '''

    def __init__(self, image):
        super().__init__()
        self.image = image
        self.selected = False
        self.imageLabel, self.imageInfo = self._widgets()
        self._setWidgetEvents()

        self.setFixedWidth(SIZE)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        for widget in (self.imageLabel, self.imageInfo):
            layout.addWidget(widget)
        self.setLayout(layout)

    def _widgets(self):
        '''Returns ThumbnailWidget and ImageInfoWidget objects
        which are parts of a DuplicateCandidateWidget object

        :returns: tuple, (<class ThumbnailWidget> obj,
                          <class ImageInfoWidget> obj)
        '''

        imageLabel = ThumbnailWidget(self.image.thumbnail)

        try:
            dimensions = self.image.get_dimensions()
        except OSError as e:
            gui_logger.error(e)
            dimensions = (0, 0)

        try:
            filesize = self.image.get_filesize()
        except OSError as e:
            gui_logger.error(e)
            filesize = 0

        imageInfo = ImageInfoWidget(self.image.path, self.image.difference,
                                    dimensions, filesize)

        return imageLabel, imageInfo

    def _setWidgetEvents(self):
        '''Link events and functions called on the events'''

        self.mouseReleaseEvent = self._mouseRelease

    def _mouseRelease(self, event):
        '''Function called on mouse release event'''

        window = self.window()

        if self.selected:
            self.selected = False
            self.imageLabel.unmark()
            window._switch_buttons()
        else:
            self.selected = True
            self.imageLabel.mark()
            window._switch_buttons()

    def delete(self):
        '''Delete an image from disk and its DuplicateCandidateWidget
        instance

        :raise OSError: if something went wrong while removing images
        '''

        try:
            self.image.delete_image()
        except OSError as e:
            msgBox = QMessageBox(
                QMessageBox.Warning,
                'Removing image',
                f'Error occured while removing image {self.image.path}'
            )
            msgBox.exec()

            raise OSError(e)
        else:
            self.deleteLater()

    def move(self, dst):
        '''Move an image to a new location and delete its DuplicateCandidateWidget
        instance

        :param dst: str, a new location, eg. /new/location,
        :raise OSError: if something went wrong while removing images
        '''

        try:
            self.image.move_image(dst)
        except OSError as e:
            msgBox = QMessageBox(
                QMessageBox.Warning,
                'Moving image',
                f'Error occured while moving image {self.image.path}'
            )
            msgBox.exec()

            raise OSError(e)
        else:
            self.deleteLater()


class ImageGroupWidget(QWidget):
    '''Widget class to keep similar images together'''

    def __init__(self, image_group):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        for image in image_group:
            thumbnail = DuplicateCandidateWidget(image)
            layout.addWidget(thumbnail)
        self.setLayout(layout)

    def getSelectedWidgets(self):
        '''Return list of the selected DuplicateCandidateWidget instances'''

        widgets = self.findChildren(
            DuplicateCandidateWidget,
            options=Qt.FindDirectChildrenOnly
        )
        return [widget for widget in widgets if widget.selected]

    def __len__(self):
        return len(self.findChildren(DuplicateCandidateWidget,
                                     options=Qt.FindDirectChildrenOnly))


class MainForm(QMainWindow):
    '''Main GUI class'''

    def __init__(self):
        super().__init__()
        loadUi(UI, self)
        self.scrollAreaLayout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self._setWidgetEvents()
        self.signals = processing.Signals()
        self.threadpool = QThreadPool()

        self.sensitivity = 5

        self._show_menubar()

    def _setWidgetEvents(self):
        '''Link events and functions called on the events'''

        self.addFolderBtn.clicked.connect(self.addFolderBtn_click)
        self.delFolderBtn.clicked.connect(self.delFolderBtn_click)

        self.startBtn.clicked.connect(self.startBtn_click)
        self.stopBtn.clicked.connect(self.stopBtn_click)
        self.moveBtn.clicked.connect(self.moveBtn_click)
        self.deleteBtn.clicked.connect(self.deleteBtn_click)

        self.highRb.clicked.connect(self.highRb_click)
        self.mediumRb.clicked.connect(self.mediumRb_click)
        self.lowRb.clicked.connect(self.lowRb_click)

    def _show_menubar(self):
        fileMenu = self.menubar.addMenu('File')
        #fileMenu.addAction(self.addFolderAct)
        #fileMenu.addSeparator(self.exitAct)

        editMenu = self.menubar.addMenu('Edit')

        viewMenu = self.menubar.addMenu('View')
        #viewMenu.addAction(self.showDifference)

        optionsMenu = self.menubar.addMenu('Options')
        #optionsMenu.addAction(self.showHiddenFolders)
        #optionsMenu.addAction(self.includeSubfolders)
        #optionsMenu.addAction(self.betweenFoldersOnly)
        #optionsMenu.addAction(self.confirmToClose)

        helpMenu = self.menubar.addMenu('Help')
        #helpMenu.addAction(self.help)
        #helpMenu.addAction(self.homePage)
        #helpMenu.addAction(self.About)

    def _openFolderNameDialog(self):
        '''Open file dialog and return the folder full path'''

        folder_path = QFileDialog.getExistingDirectory(
            self,
            'Open Folder',
            '',
            QFileDialog.ShowDirsOnly
        )
        return folder_path

    def _clear_form_before_start(self):
        '''Clear the form from the previous duplicate images
        found and labels before doing another search
        '''

        group_widgets = self.scrollAreaWidget.findChildren(
            ImageGroupWidget,
            options=Qt.FindDirectChildrenOnly
        )
        for group_widget in group_widgets:
            group_widget.deleteLater()

        for label in ['thumbnails', 'image_groups', 'remaining_images',
                      'found_in_cache', 'loaded_images', 'duplicates']:
            self._update_label_info(label, str(0))

        self.progressBar.setValue(0)

    def _get_user_folders(self):
        '''Get all the folders a user added to the 'pathListWidget'

        :returns: set of str, the folders the user wants to
                  process
        '''

        return {self.pathListWidget.item(i).data(Qt.DisplayRole)
                for i in range(self.pathListWidget.count())}

    def _render_image_groups(self, image_groups):
        '''Add ImageGroupWidget to scrollArea

        :param image_groups: list, [<class Image> obj, ...]
        '''

        for group in image_groups:
            self.scrollAreaLayout.addWidget(ImageGroupWidget(group))

        if not image_groups:
            msg_box = QMessageBox(
                QMessageBox.Information,
                'No duplicate images found',
                'No duplicate images have been found in the selected folders'
            )
            msg_box.exec()

    def _update_label_info(self, label, text):
        '''Update a label's info

        :param label: str, one of ('thumbnails', 'image_groups',
                                   'remaining_images', 'found_in_cache',
                                   'loaded_images', 'duplicates'),
        :param text: str, text to add to a label
        '''

        labels = {'thumbnails': self.thumbnailsLabel,
                  'image_groups': self.dupGroupLabel,
                  'remaining_images': self.remainingPicLabel,
                  'found_in_cache': self.foundInCacheLabel,
                  'loaded_images': self.loadedPicLabel,
                  'duplicates': self.duplicatesLabel}

        label_to_change = labels[label]
        label_text = label_to_change.text().split(' ')
        label_text[-1] = text
        label_to_change.setText(' '.join(label_text))

    def has_selected_widgets(self):
        '''Checks if there are selected DuplicateCandidateWidget in the form

        :returns: bool, True if there are any
        '''

        group_widgets = self.scrollAreaWidget.findChildren(
            ImageGroupWidget,
            options=Qt.FindDirectChildrenOnly
        )
        for group_widget in group_widgets:
            selected_widgets = group_widget.getSelectedWidgets()
            if selected_widgets:
                return True
        return False

    def _call_on_selected_widgets(self, func, *args, **kwargs):
        '''Call a function on selected widgets

        :param func: function to call
        '''

        group_widgets = self.scrollAreaWidget.findChildren(
            ImageGroupWidget,
            options=Qt.FindDirectChildrenOnly
        )
        for group_widget in group_widgets:
            selected_widgets = group_widget.getSelectedWidgets()
            for selected_widget in selected_widgets:
                try:
                    func(selected_widget, *args, **kwargs)
                except OSError as e:
                    gui_logger.error(e)
                else:
                    selected_widget.selected = False
            # If we select all (or except one) the images in a group,
            if len(group_widget) - len(selected_widgets) <= 1:
                # and all the selected images were processed correctly (so
                # there are no selected images anymore), delete the whole group
                if not group_widget.getSelectedWidgets():
                    group_widget.deleteLater()

    def _delete_images(self):
        '''Delete selected images and DuplicateCandidateWidget widgets'''

        self._call_on_selected_widgets(DuplicateCandidateWidget.delete)
        self._switch_buttons()

    def _move_images(self):
        '''Move selected images and delete selected DuplicateCandidateWidget widgets'''

        new_dst = self._openFolderNameDialog()
        if new_dst:
            self._call_on_selected_widgets(DuplicateCandidateWidget.move, new_dst)
            self._switch_buttons()

    def _image_processing_finished(self):
        '''Called when image processing is finished'''

        self.progressBar.setValue(100)
        self.startBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)

    def _start_processing(self, folders):
        '''Set up image processing and run it'''

        img_proc = processing.ImageProcessing(self, folders, self.sensitivity)

        img_proc.signals.update_info.connect(self._update_label_info)
        img_proc.signals.update_progressbar.connect(self.progressBar.setValue)
        img_proc.signals.result.connect(self._render_image_groups)
        img_proc.signals.finished.connect(self._image_processing_finished)

        worker = processing.Worker(img_proc.run)
        self.threadpool.start(worker)

    def _switch_buttons(self):
        if self.has_selected_widgets():
            self.moveBtn.setEnabled(True)
            self.deleteBtn.setEnabled(True)
        else:
            self.moveBtn.setEnabled(False)
            self.deleteBtn.setEnabled(False)

    @pyqtSlot()
    def highRb_click(self):
        '''Function called on 'High' radio button click event'''

        self.sensitivity = 5

    @pyqtSlot()
    def mediumRb_click(self):
        '''Function called on 'Medium' radio button click event'''

        self.sensitivity = 10

    @pyqtSlot()
    def lowRb_click(self):
        '''Function called on 'Low' radio button click event'''

        self.sensitivity = 20

    @pyqtSlot()
    def addFolderBtn_click(self):
        '''Function called on 'Add Path' button click event'''

        folder_path = self._openFolderNameDialog()
        if folder_path:
            folder_path_item = QListWidgetItem()
            folder_path_item.setData(Qt.DisplayRole, folder_path)
            self.pathListWidget.addItem(folder_path_item)
            self.delFolderBtn.setEnabled(True)
            self.startBtn.setEnabled(True)

    @pyqtSlot()
    def delFolderBtn_click(self):
        '''Function called on 'Delete Path' button click event'''

        item_list = self.pathListWidget.selectedItems()
        for item in item_list:
            self.pathListWidget.takeItem(self.pathListWidget.row(item))

        if not self.pathListWidget.count():
            self.delFolderBtn.setEnabled(False)
            self.startBtn.setEnabled(False)

    @pyqtSlot()
    def startBtn_click(self):
        '''Function called on 'Start' button click event'''

        self._clear_form_before_start()
        self.stopBtn.setEnabled(True)
        self.startBtn.setEnabled(False)

        folders = self._get_user_folders()
        self._start_processing(folders)

    @pyqtSlot()
    def stopBtn_click(self):
        '''Function called on 'Stop' button click event'''

        self.signals.interrupt.emit()

        msgBox = QMessageBox(QMessageBox.Information, 'Interruption request',
                             'The image processing has been stopped')
        msgBox.exec()

        self.stopBtn.setEnabled(False)

    @pyqtSlot()
    def moveBtn_click(self):
        '''Function called on 'Move' button click event'''

        self._move_images()

    @pyqtSlot()
    def deleteBtn_click(self):
        '''Function called on 'Delete' button click event'''

        confirm = QMessageBox.question(
            self,
            'Deletion confirmation',
            'Do you really want to remove the selected images?',
            QMessageBox.Yes|QMessageBox.Cancel
        )

        if confirm == QMessageBox.Yes:
            self._delete_images()
