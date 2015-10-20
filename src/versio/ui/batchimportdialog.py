# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'batchimportdialog.ui'
#
# Created: Tue Aug 19 13:53:19 2014
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

class Ui_BatchImportDialog(object):
    def setupUi(self, BatchImportDialog):
        BatchImportDialog.setObjectName(_fromUtf8("BatchImportDialog"))
        BatchImportDialog.resize(553, 601)
        self.verticalLayout_3 = QtGui.QVBoxLayout(BatchImportDialog)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.layersGroup = QtGui.QGroupBox(BatchImportDialog)
        self.layersGroup.setObjectName(_fromUtf8("layersGroup"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.layersGroup)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        spacerItem = QtGui.QSpacerItem(1, 1, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.addLayersButton = QtGui.QPushButton(self.layersGroup)
        self.addLayersButton.setObjectName(_fromUtf8("addLayersButton"))
        self.horizontalLayout_2.addWidget(self.addLayersButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.layersList = QtGui.QListWidget(self.layersGroup)
        self.layersList.setDragEnabled(True)
        self.layersList.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.layersList.setDefaultDropAction(QtCore.Qt.IgnoreAction)
        self.layersList.setAlternatingRowColors(True)
        self.layersList.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.layersList.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.layersList.setObjectName(_fromUtf8("layersList"))
        self.verticalLayout_2.addWidget(self.layersList)
        self.label = QtGui.QLabel(self.layersGroup)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout_2.addWidget(self.label)
        self.commitTextBox = QtGui.QPlainTextEdit(self.layersGroup)
        self.commitTextBox.setMaximumSize(QtCore.QSize(16777215, 100))
        self.commitTextBox.setObjectName(_fromUtf8("commitTextBox"))
        self.verticalLayout_2.addWidget(self.commitTextBox)
        self.verticalLayout_3.addWidget(self.layersGroup)
        self.optionsGroup = QtGui.QGroupBox(BatchImportDialog)
        self.optionsGroup.setObjectName(_fromUtf8("optionsGroup"))
        self.verticalLayout = QtGui.QVBoxLayout(self.optionsGroup)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label_16 = QtGui.QLabel(self.optionsGroup)
        self.label_16.setObjectName(_fromUtf8("label_16"))
        self.horizontalLayout.addWidget(self.label_16)
        self.featureIdBox = QtGui.QLineEdit(self.optionsGroup)
        self.featureIdBox.setText(_fromUtf8(""))
        self.featureIdBox.setObjectName(_fromUtf8("featureIdBox"))
        self.horizontalLayout.addWidget(self.featureIdBox)
        self.fidFieldsButton = QtGui.QToolButton(self.optionsGroup)
        self.fidFieldsButton.setObjectName(_fromUtf8("fidFieldsButton"))
        self.horizontalLayout.addWidget(self.fidFieldsButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_26 = QtGui.QHBoxLayout()
        self.horizontalLayout_26.setObjectName(_fromUtf8("horizontalLayout_26"))
        self.label_35 = QtGui.QLabel(self.optionsGroup)
        self.label_35.setObjectName(_fromUtf8("label_35"))
        self.horizontalLayout_26.addWidget(self.label_35)
        self.destTreeBox = QtGui.QLineEdit(self.optionsGroup)
        self.destTreeBox.setPlaceholderText(_fromUtf8(""))
        self.destTreeBox.setObjectName(_fromUtf8("destTreeBox"))
        self.horizontalLayout_26.addWidget(self.destTreeBox)
        self.verticalLayout.addLayout(self.horizontalLayout_26)
        self.verticalLayout_3.addWidget(self.optionsGroup)
        self.buttonBox = QtGui.QDialogButtonBox(BatchImportDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout_3.addWidget(self.buttonBox)

        self.retranslateUi(BatchImportDialog)
        QtCore.QMetaObject.connectSlotsByName(BatchImportDialog)

    def retranslateUi(self, BatchImportDialog):
        BatchImportDialog.setWindowTitle(_translate("BatchImportDialog", "Batch import", None))
        self.layersGroup.setTitle(_translate("BatchImportDialog", "Layers/files", None))
        self.addLayersButton.setText(_translate("BatchImportDialog", "Add...", None))
        self.label.setText(_translate("BatchImportDialog", "Version description pattern ( %f=filename, %d=destination layer):", None))
        self.commitTextBox.setPlainText(_translate("BatchImportDialog", "Updated layer %d with file %f", None))
        self.optionsGroup.setTitle(_translate("BatchImportDialog", "Options", None))
        self.label_16.setText(_translate("BatchImportDialog", "Feature ID definition:", None))
        self.featureIdBox.setPlaceholderText(_translate("BatchImportDialog", "[leave blank to create ID automatically]", None))
        self.fidFieldsButton.setText(_translate("BatchImportDialog", "...", None))
        self.label_35.setText(_translate("BatchImportDialog", "Layer name:", None))

