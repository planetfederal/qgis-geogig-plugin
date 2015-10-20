from PyQt4 import QtGui
from versio.ui.createlocalversiorepodialog import Ui_CreateLocalVersioRepoDialog
import re

class CreateLocalVersioRepoDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.ui = Ui_CreateLocalVersioRepoDialog()
        self.ui.setupUi(self)

        self.ui.buttonBox.accepted.connect(self.okPressed)
        self.ui.buttonBox.rejected.connect(self.cancelPressed)

        self.username = None
        self.title = None


    def okPressed(self):
        self.ui.usernameBox.setStyleSheet("QLineEdit{background: white}")
        self.ui.titleBox.setStyleSheet("QLineEdit{background: white}")
        title = self.ui.titleBox.text().strip()
        if title == "":
            self.ui.titleBox.setStyleSheet("QLineEdit{background: yellow}")
            return
        username = self.ui.usernameBox.text().strip()
        if not re.match("^[A-Za-z0-9_-]*$", username) or username == "":
            self.ui.nameBox.setStyleSheet("QLineEdit{background: yellow}")
            return
        self.title = title
        self.username = username
        self.close()

    def cancelPressed(self):
        self.username = None
        self.title = None
        self.close()

