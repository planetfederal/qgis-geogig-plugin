# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'createversiorepodialog.ui'
#
# Created: Wed Jun 11 10:23:06 2014
#      by: PyQt4 UI code generator 4.11
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

class Ui_CreateVersioRepoDialog(object):
    def setupUi(self, CreateVersioRepoDialog):
        CreateVersioRepoDialog.setObjectName(_fromUtf8("CreateVersioRepoDialog"))
        CreateVersioRepoDialog.resize(400, 279)
        self.verticalLayout = QtGui.QVBoxLayout(CreateVersioRepoDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(CreateVersioRepoDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.titleBox = QtGui.QLineEdit(CreateVersioRepoDialog)
        self.titleBox.setObjectName(_fromUtf8("titleBox"))
        self.verticalLayout.addWidget(self.titleBox)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label_3 = QtGui.QLabel(CreateVersioRepoDialog)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.horizontalLayout.addWidget(self.label_3)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.nameWarningLabel = QtGui.QLabel(CreateVersioRepoDialog)
        self.nameWarningLabel.setStyleSheet(_fromUtf8("color: rgb(255, 0, 0);"))
        self.nameWarningLabel.setObjectName(_fromUtf8("nameWarningLabel"))
        self.horizontalLayout.addWidget(self.nameWarningLabel)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.labelUrl = QtGui.QLabel(CreateVersioRepoDialog)
        font = QtGui.QFont()
        font.setItalic(True)
        self.labelUrl.setFont(font)
        self.labelUrl.setObjectName(_fromUtf8("labelUrl"))
        self.horizontalLayout_3.addWidget(self.labelUrl)
        self.nameBox = QtGui.QLineEdit(CreateVersioRepoDialog)
        self.nameBox.setObjectName(_fromUtf8("nameBox"))
        self.horizontalLayout_3.addWidget(self.nameBox)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.label_2 = QtGui.QLabel(CreateVersioRepoDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.descriptionBox = QtGui.QTextEdit(CreateVersioRepoDialog)
        self.descriptionBox.setObjectName(_fromUtf8("descriptionBox"))
        self.verticalLayout.addWidget(self.descriptionBox)
        self.buttonBox = QtGui.QDialogButtonBox(CreateVersioRepoDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(CreateVersioRepoDialog)
        QtCore.QMetaObject.connectSlotsByName(CreateVersioRepoDialog)

    def retranslateUi(self, CreateVersioRepoDialog):
        CreateVersioRepoDialog.setWindowTitle(_translate("CreateVersioRepoDialog", "Create Versio Repository", None))
        self.label.setText(_translate("CreateVersioRepoDialog", "Title", None))
        self.label_3.setText(_translate("CreateVersioRepoDialog", "URL name", None))
        self.nameWarningLabel.setText(_translate("CreateVersioRepoDialog", "URL name can only contain ASCII characters and numbers", None))
        self.labelUrl.setText(_translate("CreateVersioRepoDialog", "http://versio.com/", None))
        self.label_2.setText(_translate("CreateVersioRepoDialog", "Description", None))

