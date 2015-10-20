import os
import keyring
import logging
import shutil
import getpass
from PyQt4 import QtGui, QtCore
from qgis.core import *
from qgis.gui import *
from versio.ui.navigatordialog import Ui_NavigatorDialog
from versio.gui.dialogs.userpasswd import UserPasswordDialog
from versio import config
from createversiorepodialog import CreateVersioRepoDialog
from versio.gui.executor import execute
from versio.tools.versioinstance import startInstance, instance, logout
from versio.tools.repodecorator import RepoWrapper
from versio.tools.exporter import loadRepoExportedLayers, exportFullRepo
from versio.tools.layertracking import removeTrackedForRepo, isTracked, \
    updateTrackedLayers
from geogigpy import geogig
from geogigpy.geogigexception import GeoGigException, GeoGigConflictException
from versio.tools.utils import relativeDate, resourceFile, userLocalRepos, \
    ownerFromRepoPath, nameFromRepoPath
from versio.gui.dialogs.historyviewer import HistoryViewer
from versio.gui.dialogs.statuswidget import StatusWidget
from versio.gui.dialogs.layerfilter import LayersFilterDialog
from versio.gui.pyqtconnectordecorator import killGateway
from versio.gui.dialogs.importdialog import ImportDialog
from versio.tools.layers import getVectorLayers
from versio.gui.dialogs.batchimportdialog import BatchImportDialog
from versio.tools.localversio import LocalVersio, LocalOnlyRepository
from versio.gui.dialogs.createlocalversiorepodialog import CreateLocalVersioRepoDialog
import webbrowser
from versio.gui.dialogs.syncdialog import SyncDialog
from versio.gui.dialogs.searchdialog import SearchDialog


def icon(f):
    return QtGui.QIcon(os.path.join(os.path.dirname(__file__),
                            os.pardir, os.pardir, "ui", "resources", f))

addIcon = icon("new-repo.png")
resetIcon = icon("reset.png")
refreshIcon = icon("refresh.png")
versioIcon = icon("versio-16.png")
privateReposIcon = icon("your-repos.png")
sharedReposIcon = icon("shared-repos.png")
repoIcon = icon("repo-downloaded.png")
disabledRepoIcon = QtGui.QIcon(repoIcon.pixmap(16, 16, mode = QtGui.QIcon.Disabled))
searchIcon = icon("search-repos.png")
newBranchIcon = icon("create_branch.png")
deleteIcon = icon("delete.gif")
syncIcon = icon("sync-repo.png")

logger = logging.getLogger("geogigpy")

class NavigatorDialog(QtGui.QDialog):

    def __init__(self):
        QtGui.QDialog.__init__(self, config.iface.mainWindow(),
                               QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint)

        self.currentRepo = None
        self.currentRepoName = None
        self.privateVersioReposItem = None
        self.sharedVersioReposItem = None
        self.localVersioReposItem = None
        self.localOnlyVersioReposItem = None
        self.ui = Ui_NavigatorDialog()
        self.ui.setupUi(self)

        self.ui.filterBox.adjustSize()
        tabHeight = self.ui.filterBox.height() + self.ui.filterBox.parent().layout().spacing()
        self.ui.tabWidget.setStyleSheet("QTabWidget::pane {border: 0;} QTabBar::tab { height: %ipx}" % tabHeight);

        self.ui.newVersioRepoButton.clicked.connect(self.newVersioRepo)
        self.ui.openButton.clicked.connect(self.openRepo)
        self.ui.downloadButton.clicked.connect(self.downloadRepo)
        self.ui.filterBox.textChanged.connect(self.filterRepos)
        self.ui.repoTree.itemClicked.connect(self.treeItemClicked)
        self.ui.filterButton.clicked.connect(self.showFilterPopup)
        self.ui.clearFilterButton.clicked.connect(self.clearFilter)
        self.ui.tabWidget.currentChanged.connect(self.tabChanged)
        self.ui.repoTree.customContextMenuRequested.connect(self.showRepoTreePopupMenu)
        self.ui.repoDescription.setOpenLinks(False)
        self.ui.repoTree.setFocusPolicy(QtCore.Qt.NoFocus)

        with open(resourceFile("repodescription.css")) as f:
            sheet = "".join(f.readlines())
        self.ui.repoDescription.document().setDefaultStyleSheet(sheet)
        self.ui.repoTree.header().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.ui.repoTree.header().setResizeMode(1, QtGui.QHeaderView.ResizeToContents)

        self.statusWidget = StatusWidget()
        layout = QtGui.QVBoxLayout()
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.addWidget(self.statusWidget)
        self.ui.statusWidget.setLayout(layout)

        self.versionsTree = HistoryViewer()
        layout = QtGui.QVBoxLayout()
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.addWidget(self.versionsTree)
        self.ui.versionsWidget.setLayout(layout)

        self.ui.tabWidget.setCornerWidget(self.ui.filterWidget)
        self.ui.clearFilterButton.setEnabled(False)

        self.versionsTree.headChanged.connect(self.updateBranchLabel)
        self.versionsTree.repoChanged.connect(self.statusWidget.updateLabelText)
        self.statusWidget.repoChanged.connect(self.versionsTree.updateCurrentBranchItem)
        self.statusWidget.repoUploaded.connect(self.currentRepoWasUploaded)

        self.lastSelectedRepoItem = None

        self.updateVersioReposItem()
        self.updateCurrentRepo(None, None)

        self.layersFilterDialog = None
        self.repoLayers = []


    def showFilterPopup(self):
        if self.layersFilterDialog is None:
            self.layersFilterDialog = LayersFilterDialog(self.repoLayers, self.ui.filterButton, self)
            self.layersFilterDialog.filterLayersChanged.connect(self.filterLayersChanged)
            self.layersFilterDialog.filterTextChanged.connect(self.filterTextChanged)
        self.layersFilterDialog.setFilterLayers(self.versionsTree.filterLayers)
        self.layersFilterDialog.setFilterText(self.versionsTree.filterText)
        self.layersFilterDialog.show()

    def clearFilter(self):
        self.versionsTree.filterLayers = None
        self.versionsTree.filterText = ""
        self.ui.clearFilterButton.setEnabled(False)

    def tabChanged(self, i):
        self.ui.filterButton.setVisible(i != 0)

    def filterLayersChanged(self):
        enabled = self.layersFilterDialog.filterText.strip() != "" or self.versionsTree.filterLayers is not None
        self.ui.clearFilterButton.setEnabled(enabled)
        self.versionsTree.filterLayers = self.layersFilterDialog.filterLayers

    def filterTextChanged(self):
        enabled = self.layersFilterDialog.filterText.strip() != "" or self.versionsTree.filterLayers is not None
        self.ui.clearFilterButton.setEnabled(enabled)
        self.versionsTree.filterText = self.layersFilterDialog.filterText

    def showHistoryTab(self):
        self.ui.historyTabButton.setAutoRaise(False)
        self.ui.descriptionTabButton.setAutoRaise(True)
        self.ui.versionsWidget.setVisible(True)
        self.ui.repoDescription.setVisible(False)
        self.ui.filterButton.setVisible(True)
        self.ui.filterButton.setEnabled(len(self.repoLayers) != 0)

    def showDescriptionTab(self):
        self.ui.historyTabButton.setAutoRaise(True)
        self.ui.descriptionTabButton.setAutoRaise(False)
        self.ui.versionsWidget.setVisible(False)
        self.ui.repoDescription.setVisible(True)
        self.ui.filterButton.setVisible(False)

    def showRepoTreePopupMenu(self, point):
        item = self.ui.repoTree.selectedItems()[0]
        if isinstance(item, RepoItem):
            menu = QtGui.QMenu()
            if item.repo.localCopyExists():
                addAction = QtGui.QAction(addIcon, "Add layer to repository...", None)
                addAction.triggered.connect(self.addLayer)
                menu.addAction(addAction)
                addMultipleAction = QtGui.QAction(addIcon, "Add multiple snapshots of a layer to repository...", None)
                addMultipleAction.triggered.connect(self.batchImport)
                menu.addAction(addMultipleAction)
            if item.repo.versioRepo.mine:
                deleteAction = QtGui.QAction(deleteIcon, "Delete this repository", None)
                deleteAction.triggered.connect(lambda: self.deleteRepo(item))
                menu.addAction(deleteAction)
            elif item.repo.localCopyExists():
                deleteAction = QtGui.QAction(deleteIcon, "Delete this repository (local copy only)", None)
                deleteAction.triggered.connect(lambda: self.deleteRepo(item))
                menu.addAction(deleteAction)
            if item.repo.localCopyExists():
                syncAction = QtGui.QAction(syncIcon, "Open Sync dialog for this repository...", None)
                syncAction.triggered.connect(lambda: self.syncRepo(item))
                menu.addAction(syncAction)
            if not menu.isEmpty():
                point = self.ui.repoTree.mapToGlobal(point)
                menu.exec_(point)

    def syncRepo(self, item):
        dlg = SyncDialog(item.repo.repo(), item.repo.title)
        dlg.exec_()
        if dlg.conflicts:
            self.statusWidget.updateLabelText()
        if dlg.pulled:
            updateTrackedLayers(item.repo.repo())
            self.versionsTree.updateCurrentBranchItem
            self.statusWidget.updateLabelText()
        elif dlg.pushed:
            self.statusWidget.updateLabelText()

    def uploadRepo(self):
        self.currentRepo.uploadRepo()
        self.currentRepoWasUploaded()

    def currentRepoWasUploaded(self):
        item = RepoItem(self.currentRepo)
        self.privateVersioReposItem.addChild(item)
        self.ui.repoTree.sortItems(0, QtCore.Qt.AscendingOrder)
        self.lastSelectedRepoItem.parent().removeChild(self.lastSelectedRepoItem)
        self.updateCurrentRepo(None, None)


    def batchImport(self):
        dlg = BatchImportDialog(self, repo = self.currentRepo.repo())
        dlg.exec_()
        if dlg.ok:
            self.versionsTree.updateCurrentBranchItem()
            self.statusWidget.updateLabelText()

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
        reponame = item.repo.versioRepo.name
        if item.repo.versioRepo.mine:
            execute(lambda: instance().delete_repo(reponame))
        if (item.repo.versioRepo.mine or isinstance(item.repo.versioRepo, LocalOnlyRepository)
                    or item.parent() == self.downloadedPublicVersioReposItem):
            self.lastSelectedRepoItem.parent().removeChild(self.lastSelectedRepoItem)
        if item.parent() == self.sharedVersioReposItem:
            self.lastSelectedRepoItem.setIcon(0, disabledRepoIcon)
        self.updateCurrentRepo(None, None)
        if item.repo.localCopyExists():
            removeTrackedForRepo(item.repo.localPath())
            killGateway()
            try:
                shutil.rmtree(item.repo.repo().url)
            except:
                ret = QtGui.QMessageBox.warning(config.iface.mainWindow(), "Delete repository",
                        "Local copy of repository could not be removed.\n"
                        "It will have to be removed manually at the following path:\n"
                        + item.repo.repo().url, QtGui.QMessageBox.Ok);

    def downloadRepo(self):
        self.currentRepo.cloneLocally()
        self.updateCurrentRepo(self.currentRepo, self.currentRepoName)
        self.lastSelectedRepoItem.setIcon(0, repoIcon)

    def openRepo(self, ref):
        exportFullRepo(self.currentRepo.repo())
        loadRepoExportedLayers(self.currentRepo.repo())
        config.iface.messageBar().pushMessage("Repository layers correctly added to QGIS project",
                                                  level = QgsMessageBar.INFO, duration = 4)


    def searchVersioRepos(self):
        text = self.ui.filterBox.text().strip()
        dlg = SearchDialog(self, text)
        dlg.exec_()
        if dlg.repo is not None:
            owner, name = dlg.repo.split("&")
            wrapper = RepoWrapper(instance().repo(name, owner), instance().user)
            wrapper.cloneLocally()
            item = RepoItem(wrapper)
            self.downloadedPublicVersioReposItem.addChild(item)
            if self.downloadedPublicVersioReposItem.childCount() == 1:
                self.ui.repoTree.addTopLevelItem(self.downloadedPublicVersioReposItem)


    def removeVersioSearchItems(self):
        for item in self.searchedVersioReposItem:
            self.ui.repoTree.invisibleRootItem().removeChild(item)

        self.updateCurrentRepo(None, None)


    def cloneRepoLinkClicked(self, url):
        self.currentRepo.cloneLocally()
        self.updateCurrentRepo(self.currentRepo, self.currentRepoName)


    def filterRepos(self):
        text = self.ui.filterBox.text().strip()
        for i in xrange(self.ui.repoTree.topLevelItemCount()):
            parent = self.ui.repoTree.topLevelItem(i)
            for j in xrange(parent.childCount()):
                item = parent.child(j)
                itemText = item.text(0)
                item.setHidden(text != "" and text not in itemText)

    _groupDescription = {"Your Repositories": "yourrepos.html",
                         "Shared Repositories": "sharedrepos.html",
                         "Downloaded Public Repositories": "publicrepos.html",
                         "Local-only Repositories": "localrepos.html"
                         }

    def treeItemClicked(self, item, i):
        if self.lastSelectedRepoItem == item:
            return
        self.lastSelectedRepoItem = item
        if isinstance(item, RepoItem):
            self.updateCurrentRepo(item.repo, item.text(0))
        else:
            self.updateCurrentRepo(None, None)
            if isinstance(instance(), LocalVersio):
                url = QtCore.QUrl.fromLocalFile(resourceFile("localrepos_offline.html"))
            else:
                url = QtCore.QUrl.fromLocalFile(resourceFile(self._groupDescription[item.text(0)]))
            self.ui.repoDescription.setSource(url)


    def updateCurrentRepo(self, repo, name):
        def _update():
            if repo != self.currentRepo:
                self.ui.tabWidget.setCurrentIndex(0)
            self.ui.filterButton.setVisible(self.ui.tabWidget.currentIndex() != 0)
            self.ui.tabWidget.setTabEnabled(1, False)
            if repo is None:
                self.currentRepo = None
                self.currentRepoName = None
                self.ui.repoDescription.setText("")
                self.lastSelectedRepoItem = None
                self.ui.openButton.setVisible(False)
                self.ui.repoWidget.setVisible(False)
                self.ui.downloadButton.setVisible(False)
                self.ui.placeholderWidget.setVisible(True)
            else:
                self.currentRepo = repo
                self.currentRepoName = name
                self.ui.repoDescription.setText(repo.fullDescription)
                if repo.localCopyExists():
                    self.versionsTree.updateContent(repo.repo())
                    self.ui.openButton.setVisible(True)
                    self.ui.downloadButton.setVisible(False)
                    self.updateBranchLabel()
                    self.ui.repoWidget.setVisible(True)
                    self.ui.placeholderWidget.setVisible(False)
                    self.repoLayers = [tree.path for tree in self.currentRepo.repo().trees]
                    self.versionsTree.filterLayers = None
                    if self.layersFilterDialog is not None:
                        self.layersFilterDialog.setLayers(self.repoLayers)
                    self.ui.tabWidget.setTabEnabled(1, True)
                else:
                    self.ui.downloadButton.setVisible(True)
                    self.ui.repoWidget.setVisible(False)
                    self.ui.placeholderWidget.setVisible(False)
            self.statusWidget.updateRepository(repo)
            self.statusWidget.button.setFixedHeight(self.ui.downloadButton.height())
            self.statusWidget.adjustSize()
            self.ui.downloadButton.setFixedHeight(self.ui.statusWidget.height())
            self.ui.repoWidget.setFixedHeight(self.ui.statusWidget.height())
            self.ui.placeholderWidget.setFixedHeight(self.ui.statusWidget.height())
        try:
            self.ui.repoTree.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
            self.ui.repoTree.blockSignals(True)
            execute(_update)
        finally:
            self.ui.repoTree.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
            self.ui.repoTree.blockSignals(False)

    def updateBranchLabel(self):
        self.ui.branchLabel.setText("The current branch is <b>%s</b>" % self.versionsTree.head)
        self.ui.repoDescription.setText(self.currentRepo.fullDescription)


    def updateVersioReposItem(self):
        self.updateCurrentRepo(None, None)
        self.ui.repoTree.clear()
        self.localVersioReposItem = None
        self.privateVersioReposItem = None
        self.sharedVersioReposItem = None
        self.localOnlyVersioReposItem = None
        self.downloadedPublicVersioReposItem = None
        repos = execute(instance().repos)
        if not isinstance(instance(), LocalVersio):
            self.privateVersioReposItem = OrderedParentItem("Your Repositories", 0)
            self.privateVersioReposItem.setIcon(0, privateReposIcon)
            self.sharedVersioReposItem = OrderedParentItem("Shared Repositories", 1)
            self.sharedVersioReposItem.setIcon(0, sharedReposIcon)
            self.downloadedPublicVersioReposItem = OrderedParentItem("Downloaded Public Repositories", 2)
            self.downloadedPublicVersioReposItem.setIcon(0, sharedReposIcon)
            self.localOnlyVersioReposItem = OrderedParentItem("Local-only Repositories", 3)
            self.localOnlyVersioReposItem.setIcon(0, privateReposIcon)
            repoPaths = []
            for repo in repos:
                wrapper = RepoWrapper(repo, instance().user)
                repoPaths.append(wrapper.localPath())
                item = RepoItem(wrapper)
                if repo.mine:
                    self.privateVersioReposItem.addChild(item)
                else:
                    self.sharedVersioReposItem.addChild(item)
            localRepos = userLocalRepos(instance().user)
            for repoPath in localRepos.values():
                if repoPath not in repoPaths:
                    owner = ownerFromRepoPath(repoPath)
                    name = nameFromRepoPath(repoPath)
                    if instance().user != owner:
                        wrapper = RepoWrapper(LocalOnlyRepository(repoPath), instance().user)
                        item = RepoItem(wrapper)
                        self.localOnlyVersioReposItem.addChild(item)
                    else:
                        wrapper = RepoWrapper(LocalOnlyRepository(repoPath), instance().user)
                        item = RepoItem(wrapper)
                        self.localOnlyVersioReposItem.addChild(item)

            self.ui.repoTree.addTopLevelItem(self.privateVersioReposItem)
            self.ui.repoTree.addTopLevelItem(self.sharedVersioReposItem)
            if self.localOnlyVersioReposItem.childCount():
                self.ui.repoTree.addTopLevelItem(self.localOnlyVersioReposItem)
            if self.downloadedPublicVersioReposItem.childCount():
                self.ui.repoTree.addTopLevelItem(self.downloadedPublicVersioReposItem)
            self.ui.repoTree.sortItems(0, QtCore.Qt.AscendingOrder)
            self.filterRepos()
            self.privateVersioReposItem.setExpanded(True)
            self.sharedVersioReposItem.setExpanded(True)
            self.localOnlyVersioReposItem.setExpanded(True)
            self.downloadedPublicVersioReposItem.setExpanded(True)
        else:
            self.localVersioReposItem = OrderedParentItem("Local Repositories", 0)
            self.localVersioReposItem.setIcon(0, privateReposIcon)
            for repo in repos:
                item = RepoItem(RepoWrapper(repo, repo.user))
                self.localVersioReposItem.addChild(item)
            if self.localVersioReposItem.childCount():
                self.ui.repoTree.addTopLevelItem(self.localVersioReposItem)
                self.filterRepos()
                self.localVersioReposItem.setExpanded(True)
        self.ui.repoTree.sortItems(0, QtCore.Qt.AscendingOrder)

    def newVersioRepo(self, name = None):
        if isinstance(instance(), LocalVersio):
            title, ok = QtGui.QInputDialog.getText(self, 'Name',
                                              'Enter the new repository name:')
        else:
            dlg = CreateVersioRepoDialog()
            dlg.exec_()
            ok = dlg.title is not None
        if ok:
            try:
                if isinstance(instance(), LocalVersio):
                    versioRepo = execute(lambda : instance().create_repo(getpass.getuser(), title))
                    item = RepoItem(RepoWrapper(versioRepo, getpass.getuser()))
                else:
                    versioRepo = execute(lambda : instance().create_repo(dlg.title, dlg.description, dlg.name))
                    item = RepoItem(RepoWrapper(versioRepo, instance().user))
            except Exception, e:
                if "conflict" in unicode(e).lower():
                    text = "A repository with the specified name already exists"
                else:
                    text = "There has been a problem while creating the repository\n" + unicode(e)
                QtGui.QMessageBox.warning(self, "Problem creating repository",
                        text, QtGui.QMessageBox.Ok)
                return

            parentItem = self.privateVersioReposItem or self.localVersioReposItem
            parentItem.addChild(item)
            if parentItem.parent() is None:
                self.ui.repoTree.addTopLevelItem(parentItem)
                parentItem.setExpanded(True)
            self.ui.repoTree.sortItems(0, QtCore.Qt.AscendingOrder)
            return versioRepo


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
        if instance().user == self.repo.versioRepo.owner:
            self.setText(0, self.repo.title)
        else:
            self.setText(0, self.repo.title)
        if self.repo.localCopyExists():
            self.setIcon(0, repoIcon)
        else:
            self.setIcon(0, disabledRepoIcon)
        self.setForeground(1, QtGui.QBrush(QtGui.QColor("#5f6b77")))
        self.setText(1, "Updated " + relativeDate(self.repo.versioRepo.updated))






