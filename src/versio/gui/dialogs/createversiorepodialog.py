from PyQt4 import QtGui
from qgis.core import *
from versio.ui.createversiorepodialog import Ui_CreateVersioRepoDialog
from geogigpy.geogigexception import GeoGigConflictException
from geogigpy import geogig
import re

class CreateVersioRepoDialog(QtGui.QDialog):
    def __init__(self, name = None):
        QtGui.QDialog.__init__(self)
        self.ui = Ui_CreateVersioRepoDialog()
        self.ui.setupUi(self)
        self.ui.nameBox.textChanged.connect(self.nameChanged)
        self.ui.titleBox.textChanged.connect(self.titleChanged)
        self.ui.nameWarningLabel.setVisible(False)
        self.ui.buttonBox.accepted.connect(self.okPressed)
        self.ui.buttonBox.rejected.connect(self.cancelPressed)

        self.name = None
        self.title = None
        self.description = None

        if name is not None:
            self.ui.titleBox.setText(name)

        self.ui.labelUrl.setText("[versio_endpoint]")
        self.resize(400, 300)

    def okPressed(self):
        name = self.ui.nameBox.text().strip()
        if not re.match("^[A-Za-z0-9_-]*$", name) or name == "":
            self.ui.nameBox.setStyleSheet("QLineEdit{background: yellow}")
            return
        self.name = name
        self.title = self.ui.titleBox.text().strip()
        self.description = self.ui.descriptionBox.toPlainText()
        self.close()

    def cancelPressed(self):
        self.name = None
        self.title = None
        self.description = None
        self.close()

    def titleChanged(self):
        title = self.ui.titleBox.text().lower()
        validChars = 'abcdefghijklmnopqrstuvwxyz1234567890'
        name = ''.join(c for c in title if c in validChars)
        self.ui.nameBox.setText(name)

    def nameChanged(self):
        self.ui.nameBox.setStyleSheet("QLineEdit{background: white}")
        name = self.ui.nameBox.text()
        self.ui.nameWarningLabel.setVisible(not re.match("^[A-Za-z0-9_-]*$", name))
