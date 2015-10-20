# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'syncDialog.ui'
#
# Created: Tue Sep 09 08:25:57 2014
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

class Ui_SyncDialog(object):
    def setupUi(self, SyncDialog):
        SyncDialog.setObjectName(_fromUtf8("SyncDialog"))
        SyncDialog.resize(470, 410)
        SyncDialog.setMinimumSize(QtCore.QSize(0, 410))
        SyncDialog.setMaximumSize(QtCore.QSize(16777215, 410))
        SyncDialog.setStyleSheet(_fromUtf8("#SyncDialog {\n"
"  background-color: #eeeeee;\n"
"}"))
        self.verticalLayout = QtGui.QVBoxLayout(SyncDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.label_5 = QtGui.QLabel(SyncDialog)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.horizontalLayout_3.addWidget(self.label_5)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.comboBox = QtGui.QComboBox(SyncDialog)
        self.comboBox.setObjectName(_fromUtf8("comboBox"))
        self.horizontalLayout_4.addWidget(self.comboBox)
        self.manageRemotesButton = QtGui.QToolButton(SyncDialog)
        self.manageRemotesButton.setObjectName(_fromUtf8("manageRemotesButton"))
        self.horizontalLayout_4.addWidget(self.manageRemotesButton)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.syncAllCheckBox = QtGui.QCheckBox(SyncDialog)
        self.syncAllCheckBox.setObjectName(_fromUtf8("syncAllCheckBox"))
        self.verticalLayout.addWidget(self.syncAllCheckBox)
        spacerItem1 = QtGui.QSpacerItem(20, 25, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        spacerItem2 = QtGui.QSpacerItem(10, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.pushButton = QtGui.QPushButton(SyncDialog)
        self.pushButton.setMinimumSize(QtCore.QSize(110, 60))
        self.pushButton.setMaximumSize(QtCore.QSize(120, 16777215))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icon/push-repo.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pushButton.setIcon(icon)
        self.pushButton.setIconSize(QtCore.QSize(32, 32))
        self.pushButton.setAutoDefault(False)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.horizontalLayout_2.addWidget(self.pushButton)
        spacerItem3 = QtGui.QSpacerItem(40, 2, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)
        self.label_2 = QtGui.QLabel(SyncDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.label_2.setFont(font)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout_2.addWidget(self.label_2)
        spacerItem4 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem4)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        spacerItem5 = QtGui.QSpacerItem(20, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem5)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem6 = QtGui.QSpacerItem(10, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem6)
        self.pullButton = QtGui.QPushButton(SyncDialog)
        self.pullButton.setMinimumSize(QtCore.QSize(110, 60))
        self.pullButton.setMaximumSize(QtCore.QSize(120, 16777215))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/icon/pull-repo.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pullButton.setIcon(icon1)
        self.pullButton.setIconSize(QtCore.QSize(32, 32))
        self.pullButton.setAutoDefault(False)
        self.pullButton.setObjectName(_fromUtf8("pullButton"))
        self.horizontalLayout.addWidget(self.pullButton)
        spacerItem7 = QtGui.QSpacerItem(40, 2, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem7)
        self.pullLabel = QtGui.QLabel(SyncDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pullLabel.sizePolicy().hasHeightForWidth())
        self.pullLabel.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(13)
        self.pullLabel.setFont(font)
        self.pullLabel.setStyleSheet(_fromUtf8("#pullLabel {\n"
"    line-height: 180%;\n"
"}"))
        self.pullLabel.setWordWrap(False)
        self.pullLabel.setObjectName(_fromUtf8("pullLabel"))
        self.horizontalLayout.addWidget(self.pullLabel)
        spacerItem8 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem8)
        self.verticalLayout.addLayout(self.horizontalLayout)
        spacerItem9 = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.MinimumExpanding)
        self.verticalLayout.addItem(spacerItem9)
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setObjectName(_fromUtf8("horizontalLayout_6"))
        spacerItem10 = QtGui.QSpacerItem(40, 0, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_6.addItem(spacerItem10)
        self.closeButton = QtGui.QPushButton(SyncDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.closeButton.sizePolicy().hasHeightForWidth())
        self.closeButton.setSizePolicy(sizePolicy)
        self.closeButton.setMinimumSize(QtCore.QSize(0, 0))
        self.closeButton.setStyleSheet(_fromUtf8(""))
        self.closeButton.setIconSize(QtCore.QSize(16, 16))
        self.closeButton.setObjectName(_fromUtf8("closeButton"))
        self.horizontalLayout_6.addWidget(self.closeButton)
        self.syncButton = QtGui.QPushButton(SyncDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.syncButton.sizePolicy().hasHeightForWidth())
        self.syncButton.setSizePolicy(sizePolicy)
        self.syncButton.setMinimumSize(QtCore.QSize(132, 28))
        self.syncButton.setStyleSheet(_fromUtf8("QPushButton#syncButton {\n"
"    min-width: 10em;\n"
"    min-height: 2em;\n"
"}"))
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8(":/icon/sync-repo.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.syncButton.setIcon(icon2)
        self.syncButton.setIconSize(QtCore.QSize(24, 24))
        self.syncButton.setAutoDefault(False)
        self.syncButton.setDefault(True)
        self.syncButton.setObjectName(_fromUtf8("syncButton"))
        self.horizontalLayout_6.addWidget(self.syncButton)
        self.verticalLayout.addLayout(self.horizontalLayout_6)

        self.retranslateUi(SyncDialog)
        QtCore.QMetaObject.connectSlotsByName(SyncDialog)

    def retranslateUi(self, SyncDialog):
        SyncDialog.setWindowTitle(_translate("SyncDialog", "Sync a Repo", None))
        self.label_5.setText(_translate("SyncDialog", "Sync with Remote:", None))
        self.manageRemotesButton.setText(_translate("SyncDialog", "Manage remotes", None))
        self.syncAllCheckBox.setText(_translate("SyncDialog", "Push all branches (not just current branch)", None))
        self.pushButton.setText(_translate("SyncDialog", "Push", None))
        self.label_2.setText(_translate("SyncDialog", "Push your changes to the Remote.", None))
        self.pullButton.setText(_translate("SyncDialog", "Pull", None))
        self.pullLabel.setText(_translate("SyncDialog", "Pull updates from the Remote.", None))
        self.closeButton.setText(_translate("SyncDialog", "Close", None))
        self.syncButton.setToolTip(_translate("SyncDialog", "Push and Pull from the Remote ", None))
        self.syncButton.setText(_translate("SyncDialog", "Sync: Pull and Push", None))

import geogigclient_resources_rc
