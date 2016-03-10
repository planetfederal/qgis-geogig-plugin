# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from PyQt4 import QtGui, QtCore
from geogigpy import geogig
from geogigpy.geogigexception import GeoGigException, GeoGigConflictException
from geogig.gui.dialogs.conflictdialog import ConflictDialog
from geogig.tools.layertracking import updateTrackedLayers
from geogig.tools.utils import nameFromRepoPath, userFromRepoPath, ownerFromRepoPath
import os
from geogig import config
from qgis.gui import *

class StatusWidget(QtGui.QLabel):

    repoChanged = QtCore.pyqtSignal()

    def __init__(self, parent = None):
        super(StatusWidget, self).__init__(parent)
        self.repo = None
        self.linkActivated.connect(self.linkClicked)
        self.updateLabelText()

    def linkClicked(self, url):
        if url == "abort":
            self.repo.repo().abort()
            self.updateLabelText()
        elif url == "solve":
            dlg = ConflictDialog(self, self.repo.repo())
            dlg.exec_()
            if dlg.solved:
                self.repo.repo().addandcommit(self.repo.repo().mergemessage())
                self.repoChanged.emit()
                self.updateLabelText()


    def updateRepository(self, repo):
        self.repo = repo
        self.updateLabelText()

    def updateLabelText(self):
        if self.repo is None:
            self.setText('<font color="#5f6b77">Select a repository to work with.</b></font>')
        else:
            conflicts = len(self.repo.repo().conflicts())
            if conflicts:
                self.setText('<font color="red"> There are %i conflicted features. </font> &nbsp; '
                    '<a style="text-decoration: none; font-weight: bold; color:#3498db" href="solve">Solve conflicts</a> &nbsp;  '
                    '<a style="text-decoration: none; font-weight: bold; color:#3498db" href="abort">Abort merge</a>'
                    % conflicts)
            else:
                self.setText("The current branch is <b>%s</b>" % self.repo.repo().head)



