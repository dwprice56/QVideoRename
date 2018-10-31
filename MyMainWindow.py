#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright (C) 2017 David Price
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# import datetime, os, os.path, pathlib, subprocess, sys, tempfile, xml.dom, xml.dom.minidom as minidom

import os
import re
import sys

sys.path.insert(0, '../Helpers')

from PyQt5.QtGui import QValidator
from PyQt5.QtCore import (
    QSettings
    )

from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTableWidgetItem
    )

from mainwindowui import Ui_MainWindow

from PyQt5Validators import (
    WidgetValidatorList,
    QLineEdit_FolderExists_Validator,
    QLineEdit_NotBlank_Validator
    )

from AppInit import __TESTING_DO_NOT_SAVE_SESSION__

class MyMainWindow(QMainWindow, Ui_MainWindow):

    TABLE_FILES_FOLDER_COLUMN       = 0
    TABLE_FILES_ORIGINAL_FILE_NAME_COLUMN = 1
    TABLE_FILES_NEW_FIOLE_NAME_COLUMN     = 2

    def __init__(self, parent=None):
        super().__init__(parent)

        self.reYear = re.compile(r"\((1|2)\d{3}\)")

        self.setupUi(self)

        self.widgetValidators = WidgetValidatorList()

        self.comboBox_OldText.currentTextChanged.connect(self.updateFilesTable)
        self.lineEdit_OldText = self.comboBox_OldText.lineEdit()
        self.lineEdit_OldText.setClearButtonEnabled(True)
        self.lineEdit_OldText.setPlaceholderText('Enter the text to be replaced in the file name')
        validator = QLineEdit_NotBlank_Validator(self.lineEdit_OldText,
            message = 'The Old Text field may not be blank.')
        validator.setFlags(validator.FLAG_CLEAR_HIGHLIGHT_BEFORE_VALIDATING | validator.FLAG_HIGHLIGHT_WIDGETS_WITH_ERRORS)
        self.widgetValidators.append(validator)

        self.comboBox_NewText.currentTextChanged.connect(self.updateFilesTable)
        self.lineEdit_NewText = self.comboBox_NewText.lineEdit()
        self.lineEdit_NewText.setClearButtonEnabled(True)
        self.lineEdit_NewText.setPlaceholderText('Enter the replacement text for the file name')

        self.toolButton_Text_Refresh.clicked.connect(self.updateFilesTable)

        self.comboBox_RootFolder.currentTextChanged.connect(self.updateRootFolder)
        self.lineEdit_RootFolder = self.comboBox_RootFolder.lineEdit()
        self.lineEdit_RootFolder.setClearButtonEnabled(True)
        self.lineEdit_RootFolder.setPlaceholderText('The folder containing the files to be renamed')
        validator = QLineEdit_FolderExists_Validator(self.lineEdit_RootFolder,
            message = 'The Root Folder field does not contain a valid folder name.')
        validator.setFlags(validator.FLAG_CLEAR_HIGHLIGHT_BEFORE_VALIDATING | validator.FLAG_HIGHLIGHT_WIDGETS_WITH_ERRORS)
        self.widgetValidators.append(validator)

        self.pushButton_RootFolder_Browse.clicked.connect(self.rootFolder_Browse)
        self.toolButton_RootFolder_Refresh.clicked.connect(self.rootFolder_Refresh)

        self.tableWidget_Files.setHorizontalHeaderLabels(('Folder', 'Original File Name', 'New File Name'))
        self.tableWidget_Files.resizeColumnsToContents()

        self.pushButton_MakeItSo.clicked.connect(self.makeItSo)
        self.pushButtoFiles_Clear.clicked.connect(self.filesClear)

        self.actionQuit.triggered.connect(QApplication.instance().quit)

        # Help menu actions
        # ======================================================================
        self.actionAbout.triggered.connect(self.onAction_About)
        self.actionAbout_Qt.triggered.connect(QApplication.aboutQt)

    def closeEvent(self, event):
        """ Save the window geometry and state before closing.
        """
        settings = QSettings()

        settings.setValue('geometry', self.saveGeometry())
        settings.setValue('windowState', self.saveState())

        event.accept()

    def updateFilesTable(self, text=None):
        """ Update the files table whenever something changed.
        """
        # if (text is not None):
        #     print ('(updateFilesTable) Parameter text =', text)
        #
        # print ('(updateFilesTable) OldText =', self.comboBox_OldText.currentText())
        # print ('(updateFilesTable) NewText =', self.comboBox_NewText.currentText())

        self.UpdateNewNames()
        self.tableWidget_Files.resizeColumnsToContents()

    def updateRootFolder(self, text=None):
        """ Update the files table whenever something changed.
        """
        # if (text is not None):
        #     print ('(updateRootFolder) Parameter text =', text)

        rootFolder = self.comboBox_RootFolder.currentText()
        # print ('(updateRootFolder) RootFolder =', rootFolder)

        if (os.path.exists(rootFolder)):
            self.NewTextFromRootFolderYear()
            self.AddFilesToTable()

    def rootFolder_Browse(self):
        """ Browse for the root folder.
        """
        rootFolder = QFileDialog.getExistingDirectory(self,
            'Select Root Folder', self.comboBox_RootFolder.currentText())
        if (not rootFolder):
            return

        self.comboBox_RootFolder.setCurrentText(rootFolder)
        # self.lineEdit_RootFolder.validator().clearHighlight()

        self.NewTextFromRootFolderYear()
        self.AddFilesToTable()

    def rootFolder_Refresh(self):
        """ Refresh for the root folder.
        """
        # self.lineEdit_RootFolder.validator().clearHighlight()

        self.NewTextFromRootFolderYear()
        self.AddFilesToTable()

    def makeItSo(self):
        """ Change the file names.
        """
        if (not self.validate()):
            QMessageBox.critical(QApplication.instance().mainWindow, 'Form Validation Error',
                'One or more fields have an error.  Please correct the error(s) and try again.')
            return

        rowCount = self.tableWidget_Files.rowCount()
        oldText = self.comboBox_OldText.currentText()
        newText = self.comboBox_NewText.currentText()

        if (rowCount < 1 or oldText == ''):
            return

        for rowIndex in range(rowCount):
            folder = self.tableWidget_Files.item(rowIndex, 0).text()
            oldFilename = self.tableWidget_Files.item(rowIndex, 1).text()
            newFilename = self.tableWidget_Files.item(rowIndex, 2).text()

            if (newFilename == ''):
                continue

            oldFullFilename = os.path.join(folder, oldFilename)
            newFullFilename = os.path.join(folder, newFilename)

            os.rename(oldFullFilename, newFullFilename)
            print (oldFullFilename, newFullFilename)

        self.UpdateComboBoxList(self.comboBox_OldText)
        self.UpdateComboBoxList(self.comboBox_NewText)
        self.UpdateComboBoxList(self.comboBox_RootFolder)

        self.AddFilesToTable()

        print ('BOOM!')

    def filesClear(self):
        """ Clear the files table.
        """
        self.comboBox_OldText.clearEditText()
        self.comboBox_NewText.clearEditText()
        self.comboBox_RootFolder.clearEditText()
        self.tableWidget_Files.setRowCount(0)

    def AddFilesToTable(self):
        """ Add the file names from the folder to the table.
        """
        self.tableWidget_Files.setRowCount(0)
        self.tableWidget_Files.resizeColumnsToContents()

        rootFolder = self.comboBox_RootFolder.currentText()

        if (not os.path.exists(rootFolder)):
            QMessageBox.critical(QApplication.instance().mainWindow, 'Folder Validation Error',
                'The root folder can''t be foud.  Please correct the error and try again.')
            return

        for dirpath, dirnames, filenames in os.walk(rootFolder):
            print ()
            print (dirpath)

            for filename in sorted(filenames, key=lambda s: s.lower()):
                rowIndex = self.tableWidget_Files.rowCount()

                self.tableWidget_Files.insertRow(rowIndex)
                self.tableWidget_Files.setItem(rowIndex, 0, QTableWidgetItem(dirpath))
                self.tableWidget_Files.setItem(rowIndex, 1, QTableWidgetItem(filename))
                self.tableWidget_Files.setItem(rowIndex, 2, QTableWidgetItem(''))

            if (not self.checkBox_Subfolders.isChecked()):
                break

        self.UpdateNewNames()

        self.tableWidget_Files.resizeColumnsToContents()
        self.tableWidget_Files.resizeRowsToContents()

    def NewTextFromRootFolderYear(self):
        """ Extract the year from the folder name (if present) and put it in the
            New Text field.
        """
        if (not (self.checkBox_ExtractYear.isEnabled() and self.checkBox_ExtractYear.isChecked())):
            return

        rootFolder = self.comboBox_RootFolder.currentText()
        if (len(rootFolder) < 6):
            return

        year = rootFolder[-6:]
        if (self.reYear.match(year) is None):
            return

        self.comboBox_NewText.setCurrentText(year)

    def UpdateComboBoxList(self, combobox):
        """ Delete the text from the combo box list, if present.

            Insert the text at the top of the list.
        """
        listText = combobox.currentText()

        index = combobox.findText(listText)
        if (index != -1):
            combobox.removeItem(index)

        combobox.insertItem(0, listText)
        combobox.setCurrentIndex(0)

    def UpdateNewNames(self):
        """Create new file names from the existing file names.
        """
        rowCount = self.tableWidget_Files.rowCount()
        oldText = self.comboBox_OldText.currentText()
        newText = self.comboBox_NewText.currentText()

        if (rowCount < 1 or oldText == ''):
            return

        for rowIndex in range(rowCount):
            filename = self.tableWidget_Files.item(rowIndex, 1).text()
            pos = filename.find(oldText)
            if (pos == -1):
                self.tableWidget_Files.item(rowIndex, 2).setText('')
            else:
                self.tableWidget_Files.item(rowIndex, 2).setText(filename.replace(oldText, newText))

        self.tableWidget_Files.resizeColumnsToContents()

    def onAction_About(self):
        """ Display the about dialog.
        """
        QMessageBox.about(self, 'About QVideoRename', ('Rename Video Files\n'
        'Version 2.0.0\n'
        'Copyright 2018\n'
        'David Price'
        ))

    def validate(self):
        """ Validate the fields on the main window.

            Data must be transfered from widgets to data objects first.
        """

        notValid = False

        try:
            for validator in self.widgetValidators:             # TODO This should be a method in WidgetValidatorList
                notValid |= (not validator.isValid())

        except UserDoNotContinueException:
            return False

        return (not notValid)
