# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from PyQt4 import QtGui
from geogig.ui.createrepodialog import Ui_CreateRepoDialog

class CreateRepoDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.ui = Ui_CreateLocalVersioRepoDialog()
        self.ui.setupUi(self)

        self.ui.buttonBox.accepted.connect(self.okPressed)
        self.ui.buttonBox.rejected.connect(self.cancelPressed)

        self.title = None


    def okPressed(self):
        self.ui.usernameBox.setStyleSheet("QLineEdit{background: white}")
        self.ui.titleBox.setStyleSheet("QLineEdit{background: white}")
        title = self.ui.titleBox.text().strip()
        if title == "":
            self.ui.titleBox.setStyleSheet("QLineEdit{background: yellow}")
            return
        self.title = title
        self.close()

    def cancelPressed(self):
        self.title = None
        self.close()

