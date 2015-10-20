# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'diffviewerdialog.ui'
#
# Created: Tue Jan 27 09:07:53 2015
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

class Ui_DiffViewerDialog(object):
    def setupUi(self, DiffViewerDialog):
        DiffViewerDialog.setObjectName(_fromUtf8("DiffViewerDialog"))
        DiffViewerDialog.resize(957, 712)
        DiffViewerDialog.setStyleSheet(_fromUtf8("#DiffViewer3 {\n"
"   background-color: #eeeeee;\n"
"\n"
"}"))
        self.verticalLayout_5 = QtGui.QVBoxLayout(DiffViewerDialog)
        self.verticalLayout_5.setObjectName(_fromUtf8("verticalLayout_5"))
        self.groupBox = QtGui.QGroupBox(DiffViewerDialog)
        self.groupBox.setMaximumSize(QtCore.QSize(16777215, 100))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.groupBox)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout_2.addWidget(self.label_2)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.commit1Widget = QtGui.QWidget(self.groupBox)
        self.commit1Widget.setObjectName(_fromUtf8("commit1Widget"))
        self.horizontalLayout_4.addWidget(self.commit1Widget)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_8 = QtGui.QVBoxLayout()
        self.verticalLayout_8.setSpacing(0)
        self.verticalLayout_8.setObjectName(_fromUtf8("verticalLayout_8"))
        spacerItem1 = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.verticalLayout_8.addItem(spacerItem1)
        self.horizontalLayout.addLayout(self.verticalLayout_8)
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.label_4 = QtGui.QLabel(self.groupBox)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.horizontalLayout_5.addWidget(self.label_4)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem2)
        self.verticalLayout_2.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        self.commit2Widget = QtGui.QWidget(self.groupBox)
        self.commit2Widget.setObjectName(_fromUtf8("commit2Widget"))
        self.horizontalLayout_6.addWidget(self.commit2Widget)
        self.verticalLayout_2.addLayout(self.horizontalLayout_6)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_5.addWidget(self.groupBox)
        self.groupBox_2 = QtGui.QGroupBox(DiffViewerDialog)
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.label = QtGui.QLabel(self.groupBox_2)
        self.label.setMinimumSize(QtCore.QSize(0, 0))
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout_3.addWidget(self.label)
        self.layerCombo = QtGui.QComboBox(self.groupBox_2)
        self.layerCombo.setMinimumSize(QtCore.QSize(300, 0))
        self.layerCombo.setObjectName(_fromUtf8("layerCombo"))
        self.horizontalLayout_3.addWidget(self.layerCombo)
        spacerItem3 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem3)
        self.verticalLayout_3.addLayout(self.horizontalLayout_3)
        self.attributesTable = QtGui.QTableView(self.groupBox_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.attributesTable.sizePolicy().hasHeightForWidth())
        self.attributesTable.setSizePolicy(sizePolicy)
        self.attributesTable.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.attributesTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.attributesTable.setObjectName(_fromUtf8("attributesTable"))
        self.attributesTable.horizontalHeader().setMinimumSectionSize(200)
        self.attributesTable.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout_3.addWidget(self.attributesTable)
        self.splitter_2 = QtGui.QSplitter(self.groupBox_2)
        self.splitter_2.setOrientation(QtCore.Qt.Horizontal)
        self.splitter_2.setObjectName(_fromUtf8("splitter_2"))
        self.splitter = QtGui.QSplitter(self.splitter_2)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.mapWidget = QtGui.QWidget(self.splitter)
        self.mapWidget.setObjectName(_fromUtf8("mapWidget"))
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.mapWidget)
        self.verticalLayout_4.setMargin(0)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.horizontalLayout_12 = QtGui.QHBoxLayout()
        self.horizontalLayout_12.setObjectName(_fromUtf8("horizontalLayout_12"))
        spacerItem4 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_12.addItem(spacerItem4)
        self.baseLayerCheck = QtGui.QCheckBox(self.mapWidget)
        self.baseLayerCheck.setObjectName(_fromUtf8("baseLayerCheck"))
        self.horizontalLayout_12.addWidget(self.baseLayerCheck)
        self.compareLayerCheck = QtGui.QCheckBox(self.mapWidget)
        self.compareLayerCheck.setObjectName(_fromUtf8("compareLayerCheck"))
        self.horizontalLayout_12.addWidget(self.compareLayerCheck)
        self.zoomToExtentButton = QtGui.QToolButton(self.mapWidget)
        self.zoomToExtentButton.setText(_fromUtf8(""))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icon/zoom-extent.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.zoomToExtentButton.setIcon(icon)
        self.zoomToExtentButton.setIconSize(QtCore.QSize(24, 24))
        self.zoomToExtentButton.setObjectName(_fromUtf8("zoomToExtentButton"))
        self.horizontalLayout_12.addWidget(self.zoomToExtentButton)
        self.verticalLayout_4.addLayout(self.horizontalLayout_12)
        self.mapContainer = QtGui.QWidget(self.mapWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mapContainer.sizePolicy().hasHeightForWidth())
        self.mapContainer.setSizePolicy(sizePolicy)
        self.mapContainer.setObjectName(_fromUtf8("mapContainer"))
        self.verticalLayout_4.addWidget(self.mapContainer)
        self.verticalLayout_3.addWidget(self.splitter_2)
        self.verticalLayout_5.addWidget(self.groupBox_2)

        self.retranslateUi(DiffViewerDialog)
        QtCore.QMetaObject.connectSlotsByName(DiffViewerDialog)

    def retranslateUi(self, DiffViewerDialog):
        DiffViewerDialog.setWindowTitle(_translate("DiffViewerDialog", "Comparison View", None))
        self.groupBox.setTitle(_translate("DiffViewerDialog", "Commits to Compare", None))
        self.label_2.setText(_translate("DiffViewerDialog", "Base", None))
        self.label_4.setText(_translate("DiffViewerDialog", "Compare", None))
        self.groupBox_2.setTitle(_translate("DiffViewerDialog", "Changes [select features in table to highlight them in map canvas]", None))
        self.label.setText(_translate("DiffViewerDialog", "Layer         ", None))
        self.baseLayerCheck.setText(_translate("DiffViewerDialog", "Base layer", None))
        self.compareLayerCheck.setText(_translate("DiffViewerDialog", "Compare layer", None))

import geogigclient_resources_rc
