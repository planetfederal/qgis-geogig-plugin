# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'createlocalversiorepodialog.ui'
#
# Created: Fri Jan 30 16:31:00 2015
#      by: PyQt4 UI code generator 4.11.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_CreateLocalVersioRepoDialog(object):
    def setupUi(self, CreateLocalVersioRepoDialog):
        CreateLocalVersioRepoDialog.setObjectName(_fromUtf8("CreateLocalVersioRepoDialog"))
        CreateLocalVersioRepoDialog.resize(400, 142)
        self.verticalLayout = QtGui.QVBoxLayout(CreateLocalVersioRepoDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(CreateLocalVersioRepoDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.titleBox = QtGui.QLineEdit(CreateLocalVersioRepoDialog)
        self.titleBox.setObjectName(_fromUtf8("titleBox"))
        self.verticalLayout.addWidget(self.titleBox)
        self.label_3 = QtGui.QLabel(CreateLocalVersioRepoDialog)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.verticalLayout.addWidget(self.label_3)
        self.usernameBox = QtGui.QLineEdit(CreateLocalVersioRepoDialog)
        self.usernameBox.setObjectName(_fromUtf8("usernameBox"))
        self.verticalLayout.addWidget(self.usernameBox)
        self.buttonBox = QtGui.QDialogButtonBox(CreateLocalVersioRepoDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(CreateLocalVersioRepoDialog)
        QtCore.QMetaObject.connectSlotsByName(CreateLocalVersioRepoDialog)

    def retranslateUi(self, CreateLocalVersioRepoDialog):
        CreateLocalVersioRepoDialog.setWindowTitle(_translate("CreateLocalVersioRepoDialog", "Create Versio Repository", None))
        self.label.setText(_translate("CreateLocalVersioRepoDialog", "Title", None))
        self.label_3.setText(_translate("CreateLocalVersioRepoDialog", "User name", None))

