# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import os
import logging
import shutil
from PyQt4 import QtGui, QtCore, uic
from qgis.core import *
from qgis.gui import *
from geogig import config
from geogig.gui.executor import execute
from geogig.tools.exporter import loadRepoExportedLayers, exportFullRepo
from geogig.tools.layertracking import removeTrackedForRepo, isTracked, \
    updateTrackedLayers, getTrackedPathsForRepo
from geogigpy import geogig
from geogigpy.geogigexception import GeoGigException, GeoGigConflictException
from geogig.tools.utils import *
from geogig.gui.dialogs.historyviewer import HistoryViewer
from geogig.gui.dialogs.statuswidget import StatusWidget
from geogig.gui.dialogs.layerfilter import LayersFilterDialog
from geogig.gui.pyqtconnectordecorator import killGateway
from geogig.gui.dialogs.importdialog import ImportDialog
from geogig.tools.layers import getVectorLayers
from geogig.gui.dialogs.batchimportdialog import BatchImportDialog
from geogig.gui.dialogs.syncdialog import SyncDialog
from geogig.tools.repowrapper import *
from geogig.layeractions import setAsTracked, repoWatcher, setAsUntracked
import sys

def icon(f):
    return QtGui.QIcon(os.path.join(os.path.dirname(__file__),
                            os.pardir, os.pardir, "ui", "resources", f))

addIcon = icon("new-repo.png")
resetIcon = icon("reset.png")
refreshIcon = icon("refresh.png")
privateReposIcon = icon("your-repos.png")
sharedReposIcon = icon("shared-repos.png")
repoIcon = icon("repo-downloaded.png")
disabledRepoIcon = QtGui.QIcon(repoIcon.pixmap(16, 16, mode = QtGui.QIcon.Disabled))
searchIcon = icon("search-repos.png")
newBranchIcon = icon("create_branch.png")
deleteIcon = icon("delete.gif")
syncIcon = icon("sync-repo.png")

logger = logging.getLogger("geogigpy")

# Adding so that our UI files can find resources_rc.py
sys.path.append(os.path.dirname(__file__))

pluginPath = os.path.split(os.path.dirname(os.path.dirname(__file__)))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'navigatorDialog.ui'))

class NavigatorDialog(BASE, WIDGET):

    def __init__(self):
        super(NavigatorDialog, self).__init__(None)

        self.currentRepo = None
        self.currentRepoName = None
        self.reposItem = None
        self.setupUi(self)

        self.setAllowedAreas(QtCore.Qt.RightDockWidgetArea | QtCore.Qt.LeftDockWidgetArea)

        self.filterBox.adjustSize()
        tabHeight = self.filterBox.height() + self.filterBox.parent().layout().spacing()
        self.tabWidget.setStyleSheet("QTabWidget::pane {border: 0;} QTabBar::tab { height: %ipx}" % tabHeight);

        self.newRepoButton.clicked.connect(self.newRepo)
        self.openButton.clicked.connect(self.openRepo)
        self.filterBox.textChanged.connect(self.filterRepos)
        self.repoTree.itemClicked.connect(self.treeItemClicked)
        self.filterButton.clicked.connect(self.showFilterPopup)
        self.clearFilterButton.clicked.connect(self.clearFilter)
        self.tabWidget.currentChanged.connect(self.tabChanged)
        self.repoTree.customContextMenuRequested.connect(self.showRepoTreePopupMenu)
        self.repoDescription.setOpenLinks(False)
        self.repoDescription.anchorClicked.connect(self.descriptionLinkClicked)
        self.repoTree.setFocusPolicy(QtCore.Qt.NoFocus)

        with open(resourceFile("repodescription.css")) as f:
            sheet = "".join(f.readlines())
        self.repoDescription.document().setDefaultStyleSheet(sheet)
        self.repoTree.header().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.repoTree.header().setResizeMode(1, QtGui.QHeaderView.ResizeToContents)

        self.statusWidget = StatusWidget()
        layout = QtGui.QVBoxLayout()
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.addWidget(self.statusWidget)
        self.repoWidget.setLayout(layout)

        self.versionsTree = HistoryViewer()
        layout = QtGui.QVBoxLayout()
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.addWidget(self.versionsTree)
        self.versionsWidget.setLayout(layout)

        self.tabWidget.setCornerWidget(self.filterWidget)
        self.clearFilterButton.setEnabled(False)

        self.versionsTree.headChanged.connect(self.statusWidget.updateLabelText)
        self.versionsTree.repoChanged.connect(self.statusWidget.updateLabelText)
        self.statusWidget.repoChanged.connect(self.versionsTree.updateCurrentBranchItem)

        self.lastSelectedRepoItem = None

        def _updateDescription(repo):
            if self.currentRepo is not None and repo.url == self.currentRepo.repo().url:
                self.updateCurrentRepoDescription()
                self.versionsTree.updateCurrentBranchItem()
                self.statusWidget.updateLabelText()
        repoWatcher.repoChanged.connect(_updateDescription)

        self.updateNavigator()

    def updateNavigator(self):
        self.fillTree()
        self.updateCurrentRepo(None, None)

        self.layersFilterDialog = None
        self.repoLayers = []



    def descriptionLinkClicked(self, url):
        url = url.toString()
        if url == "title":
            text, ok = QtGui.QInputDialog.getText(self, 'Title',
                                              'Enter the new repository title:',
                                              text = self.currentRepo.title)
            if ok:
                self.currentRepo.title = text
                self.updateCurrentRepoDescription()
                self.lastSelectedRepoItem.refreshTitle()

    def updateCurrentRepoDescription(self):
        self.repoDescription.setText(self.currentRepo.fullDescription)

    def fillTree(self):
        self.updateCurrentRepo(None, None)
        self.repoTree.clear()
        self.reposItem = None
        repos = execute(localRepos)

        self.reposItem = OrderedParentItem("Local Repositories", 0)
        self.reposItem.setIcon(0, privateReposIcon)
        for repo in repos:
            item = RepoItem(repo)
            self.reposItem.addChild(item)
        if self.reposItem.childCount():
            self.repoTree.addTopLevelItem(self.reposItem)
            self.filterRepos()
            self.reposItem.setExpanded(True)
        self.repoTree.sortItems(0, QtCore.Qt.AscendingOrder)


    def showFilterPopup(self):
        if self.layersFilterDialog is None:
            self.layersFilterDialog = LayersFilterDialog(self.repoLayers, self.filterButton, self)
            self.layersFilterDialog.filterLayersChanged.connect(self.filterLayersChanged)
            self.layersFilterDialog.filterTextChanged.connect(self.filterTextChanged)
        self.layersFilterDialog.setFilterLayers(self.versionsTree.filterLayers)
        self.layersFilterDialog.setFilterText(self.versionsTree.filterText)
        self.layersFilterDialog.show()

    def clearFilter(self):
        self.versionsTree.filterLayers = None
        self.versionsTree.filterText = ""
        self.clearFilterButton.setEnabled(False)

    def tabChanged(self, i):
        self.filterWidget.setVisible(i != 0)

    def filterLayersChanged(self):
        enabled = self.layersFilterDialog.filterText.strip() != "" or self.versionsTree.filterLayers is not None
        self.clearFilterButton.setEnabled(enabled)
        self.versionsTree.filterLayers = self.layersFilterDialog.filterLayers

    def filterTextChanged(self):
        enabled = self.layersFilterDialog.filterText.strip() != "" or self.versionsTree.filterLayers is not None
        self.clearFilterButton.setEnabled(enabled)
        self.versionsTree.filterText = self.layersFilterDialog.filterText

    def showHistoryTab(self):
        self.historyTabButton.setAutoRaise(False)
        self.descriptionTabButton.setAutoRaise(True)
        self.versionsWidget.setVisible(True)
        self.repoDescription.setVisible(False)
        self.filterWidget.setVisible(True)
        self.filterButton.setEnabled(len(self.repoLayers) != 0)

    def showDescriptionTab(self):
        self.historyTabButton.setAutoRaise(True)
        self.descriptionTabButton.setAutoRaise(False)
        self.versionsWidget.setVisible(False)
        self.repoDescription.setVisible(True)
        self.filterWidget.setVisible(False)

    def showRepoTreePopupMenu(self, point):
        item = self.repoTree.selectedItems()[0]
        if isinstance(item, RepoItem):
            menu = QtGui.QMenu()
            addAction = QtGui.QAction(addIcon, "Add layer to repository...", None)
            addAction.triggered.connect(self.addLayer)
            menu.addAction(addAction)
            addMultipleAction = QtGui.QAction(addIcon, "Add multiple snapshots of a layer to repository...", None)
            addMultipleAction.triggered.connect(self.batchImport)
            menu.addAction(addMultipleAction)
            deleteAction = QtGui.QAction(deleteIcon, "Delete this repository", None)
            deleteAction.triggered.connect(lambda: self.deleteRepo(item))
            menu.addAction(deleteAction)
            deleteAction = QtGui.QAction(deleteIcon, "Delete this repository", None)
            deleteAction.triggered.connect(lambda: self.deleteRepo(item))
            menu.addAction(deleteAction)
            syncAction = QtGui.QAction(syncIcon, "Open Sync dialog for this repository...", None)
            syncAction.triggered.connect(lambda: self.syncRepo(item))
            menu.addAction(syncAction)
            point = self.repoTree.mapToGlobal(point)
            menu.exec_(point)

    def syncRepo(self, item):
        dlg = SyncDialog(item.repo.repo(), item.repo.title)
        dlg.exec_()
        if dlg.conflicts:
            self.statusWidget.updateLabelText()
        if dlg.pulled:
            updateTrackedLayers(item.repo.repo())
            self.versionsTree.updateCurrentBranchItem()
            self.statusWidget.updateLabelText()
        elif dlg.pushed:
            self.statusWidget.updateLabelText()
        self.updateCurrentRepoDescription()

    def batchImport(self):
        dlg = BatchImportDialog(self, repo = self.currentRepo.repo())
        dlg.exec_()
        if dlg.ok:
            self.versionsTree.updateCurrentBranchItem()
            self.statusWidget.updateLabelText()
            self.updateCurrentRepoDescription()

    def addLayer(self):
        layers = [layer for layer in getVectorLayers()
                        if layer.source().lower().endswith("shp")
                        and not isTracked(layer)]
        if layers:
            dlg = ImportDialog(self, repo = self.currentRepo.repo())
            dlg.exec_()
            if dlg.ok:
                self.versionsTree.updateCurrentBranchItem()
                self.statusWidget.updateLabelText()
                self.updateCurrentRepoDescription()
                setAsTracked(dlg.layer)
        else:
            QtGui.QMessageBox.warning(self, 'Cannot add layer',
                "No suitable layers can be found in your current QGIS project.\n"
                "Open the layers in QGIS before trying to add them.",
                QtGui.QMessageBox.Ok)

    def deleteRepo(self, item):
        ret = QtGui.QMessageBox.warning(config.iface.mainWindow(), "Delete repository",
                        "Are you sure you want to delete this repository?",
                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                        QtGui.QMessageBox.Yes);
        if ret == QtGui.QMessageBox.No:
            return
        self.lastSelectedRepoItem.parent().removeChild(self.lastSelectedRepoItem)
        self.updateCurrentRepo(None, None)
        tracked = getTrackedPathsForRepo(item.repo.repo())
        layers = getVectorLayers()
        for layer in layers:
            if layer.source() in tracked:
                setAsUntracked(layer)
        removeTrackedForRepo(item.repo.path)
        killGateway()
        try:
            shutil.rmtree(item.repo.repo().url)
        except:
            ret = QtGui.QMessageBox.warning(config.iface.mainWindow(), "Delete repository",
                    "Local copy of repository could not be removed.\n"
                    "It will have to be removed manually at the following path:\n"
                    + item.repo.repo().url, QtGui.QMessageBox.Ok);


    def openRepo(self, ref):
        exportFullRepo(self.currentRepo.repo())
        loadRepoExportedLayers(self.currentRepo.repo())
        config.iface.messageBar().pushMessage("Repository layers correctly added to QGIS project",
                                                  level = QgsMessageBar.INFO, duration = 4)


    def filterRepos(self):
        text = self.filterBox.text().strip()
        for i in xrange(self.repoTree.topLevelItemCount()):
            parent = self.repoTree.topLevelItem(i)
            for j in xrange(parent.childCount()):
                item = parent.child(j)
                itemText = item.text(0)
                item.setHidden(text != "" and text not in itemText)


    def treeItemClicked(self, item, i):
        if self.lastSelectedRepoItem == item:
            return
        self.lastSelectedRepoItem = item
        if isinstance(item, RepoItem):
            self.updateCurrentRepo(item.repo, item.text(0))
        else:
            self.updateCurrentRepo(None, None)
            url = QtCore.QUrl.fromLocalFile(resourceFile("localrepos_offline.html"))
            self.repoDescription.setSource(url)


    def updateCurrentRepo(self, repo, name):
        def _update():
            if repo != self.currentRepo:
                self.tabWidget.setCurrentIndex(0)
            self.filterWidget.setVisible(self.tabWidget.currentIndex() != 0)
            self.tabWidget.setTabEnabled(1, False)
            if repo is None:
                self.currentRepo = None
                self.currentRepoName = None
                self.repoDescription.setText("")
                self.lastSelectedRepoItem = None
                self.openButton.setEnabled(False)
            else:
                self.currentRepo = repo
                self.currentRepoName = name
                self.repoDescription.setText(repo.fullDescription)
                self.versionsTree.updateContent(repo.repo())
                self.openButton.setEnabled(True)
                self.repoLayers = [tree.path for tree in self.currentRepo.repo().trees]
                self.versionsTree.filterLayers = None
                if self.layersFilterDialog is not None:
                    self.layersFilterDialog.setLayers(self.repoLayers)
                self.tabWidget.setTabEnabled(1, True)

            self.statusWidget.updateRepository(repo)
        try:
            self.repoTree.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
            self.repoTree.blockSignals(True)
            execute(_update)
        finally:
            self.repoTree.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
            self.repoTree.blockSignals(False)

    def newRepo(self, name = None):
        title, ok = QtGui.QInputDialog.getText(self, 'Name',
                                          'Enter the new repository name:')
        if ok:
            try:
                repo = execute(lambda : createRepo(title))
                item = RepoItem(RepositoryWrapper(repo.url))
            except Exception, e:
                if "conflict" in unicode(e).lower():
                    text = "A repository with the specified name already exists"
                else:
                    text = "There has been a problem while creating the repository\n" + unicode(e)
                QtGui.QMessageBox.warning(self, "Problem creating repository",
                        text, QtGui.QMessageBox.Ok)
                return

            self.reposItem.addChild(item)
            self.repoTree.addTopLevelItem(self.reposItem)
            self.reposItem.setExpanded(True)
            self.repoTree.sortItems(0, QtCore.Qt.AscendingOrder)
            return repo


class OrderedParentItem(QtGui.QTreeWidgetItem):
    def __init__(self, text, order):
        QtGui.QTreeWidgetItem.__init__(self)
        self.setText(0, text)
        self.order = order
        self.setSizeHint(0, QtCore.QSize(self.sizeHint(0).width(), 25))

    def __lt__(self, o):
        if isinstance(o, OrderedParentItem):
            return o.order > self.order
        else:
            return True

    def __gt__(self, o):
        return not self.__lt__(o)

class RepoItem(QtGui.QTreeWidgetItem):
    def __init__(self, repo):
        QtGui.QTreeWidgetItem.__init__(self)
        self.repo = repo
        self.refreshTitle()
        self.setSizeHint(0, QtCore.QSize(self.sizeHint(0).width(), 25))

    def refreshTitle(self):
        self.setText(0, self.repo.title)
        self.setIcon(0, repoIcon)
        self.setForeground(1, QtGui.QBrush(QtGui.QColor("#5f6b77")))
        self.setText(1, "Updated " + relativeDate(self.repo.updated))

navigatorInstance = NavigatorDialog()



