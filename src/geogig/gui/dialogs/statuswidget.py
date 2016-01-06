from PyQt4 import QtGui, QtCore
from geogigpy import geogig
from geogigpy.geogigexception import GeoGigException, GeoGigConflictException
from geogig.gui.dialogs.conflictdialog import ConflictDialog
from geogig.tools.layertracking import updateTrackedLayers
from geogig.tools.utils import nameFromRepoPath, userFromRepoPath, ownerFromRepoPath
import os
from geogig import config
from qgis.gui import *


def icon(f):
    return QtGui.QIcon(os.path.join(os.path.dirname(__file__),
                            os.pardir, os.pardir, "ui", "resources", f))

pushIcon = icon("push.png")
pullIcon = icon("pull.png")
syncIcon = icon("sync-repo.png")
conflictIcon = icon("conflicts-found.png")

class StatusWidget(QtGui.QWidget):

    repoChanged = QtCore.pyqtSignal()
    repoUploaded = QtCore.pyqtSignal()

    def __init__(self, parent = None):
        super(StatusWidget, self).__init__(parent)
        self.repo = None
        self.layout = QtGui.QHBoxLayout()
        self.layout.setMargin(0)
        self.label = QtGui.QLabel()
        self.layout.addWidget(self.label)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.layout.addItem(spacerItem)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icon/sync-repo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setLayout(self.layout)
        self.label.linkActivated.connect(self.linkClicked)
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

    def syncRepo(self):
        self.repo.uploadRepo()
        self.repoUploaded.emit()
        self.updateLabelText()

    def pull(self):
        try:
            self.repo.repo().pull(geogig.ORIGIN)
            return True
        except GeoGigConflictException:
            QtGui.QMessageBox.warning(self, conflictIcon, 'Edit Conflicts',
                    "Some of your edits conflict with recent edits in geogig.\n\n"
                    + "OPTION A - MERGE:\n\n1. Solve your conflicts then\n\n2. Sync your merged version with geogig.\n\n",
                     + "OPTION B - UNDO: Revert the sync operation to have only your original local edits\n",
                    QtGui.QMessageBox.Ok)
            return False;
        except GeoGigException, e:
            if "FileNotFound" in unicode(e):
                raise GeoGigException("Remote repository does not exist.")
            else:
                raise e

    def push(self):
        try:
            self.repo.repo().push(geogig.ORIGIN)
        except GeoGigException, e:
            if "FileNotFound" in unicode(e):
                raise GeoGigException("Remote repository does not exist.")
            else:
                raise e

    def sync(self):
        if self.pull():
            updateTrackedLayers(self.repo.repo())
            self.push()
            config.iface.messageBar().pushMessage("Repositories have been successfully synchronized.",
                                                  level = QgsMessageBar.INFO, duration = 4)
            return True
        else:
            return False


    def updateRepository(self, repo):
        self.repo = repo
        self.updateLabelText()

    def updateLabelText(self):
        if self.repo is None:
            self.label.setText('<font color="#5f6b77">Select a repository to work with.</b></font>')
        else:
            conflicts = len(self.repo.repo().conflicts())
            if conflicts:
                self.label.setText('<font color="red"> There are %i conflicted features. </font> &nbsp; '
                    '<a style="text-decoration: none; font-weight: bold; color:#3498db" href="solve">Solve conflicts</a> &nbsp;  '
                    '<a style="text-decoration: none; font-weight: bold; color:#3498db" href="abort">Revert edits</a>'
                    % conflicts)
            else:
                self.label.setText("")



