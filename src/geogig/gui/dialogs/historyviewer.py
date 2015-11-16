import os
from collections import defaultdict
from qgis.core import *
from PyQt4 import QtGui, QtCore
from geogigpy.commitish import Commitish
from geogigpy.commit import Commit
from geogigpy import geogig
from geogigpy.geogigexception import GeoGigException, GeoGigConflictException
from geogig.tools.layertracking import updateTrackedLayers
from geogig.gui.dialogs.diffviewerdialog import DiffViewerDialog
from geogig.gui.dialogs.createbranch import CreateBranchDialog
from geogig.gui.dialogs.statuswidget import StatusWidget
from geogig.gui.executor import execute
from geogig.tools.exporter import exportAndLoadVersion, exportVersionDiffs
from geogig.gui.dialogs.htmldialog import HtmlDialog
from geogig import config


def icon(f):
    return QtGui.QIcon(os.path.join(os.path.dirname(__file__),
                            os.pardir, os.pardir, "ui", "resources", f))

resetIcon = icon("reset.png")
branchIcon = icon("branch-active.png")
disabledBranchIcon = icon("branch-inactive.png")
mergeIcon = icon("merge.png")
newBranchIcon = icon("create_branch.png")
diffIcon = icon("diff-selected.png")
switchIcon = icon("checkout.png")
deleteIcon = icon("delete.gif")
exportDiffIcon = icon("checkout.png")
exportLayersIcon = icon("checkout.png")
infoIcon = icon("repo-summary.png")
tagIcon = icon("tag.gif")
conflictIcon = icon("conflicts-found.png")

class HistoryViewer(QtGui.QTreeWidget):

    repoChanged = QtCore.pyqtSignal()
    headChanged = QtCore.pyqtSignal()

    def __init__(self):
        super(HistoryViewer, self).__init__()
        self.repo = None
        self._filterLayers = None
        self._filterText = ""
        self.initGui()

    def initGui(self):
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.header().setStretchLastSection(True)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.header().setVisible(False)
        self.customContextMenuRequested.connect(self.showPopupMenu)
        self.itemExpanded.connect(self._itemExpanded)

    def setFilterLayers(self, layers):
        self._filterLayers = layers
        for i in xrange(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.childCount():
                item.takeChildren()
                item.populate()
        self.setFilterText(self._filterText)

    def getFilterLayers(self):
        return self._filterLayers

    filterLayers = property(getFilterLayers, setFilterLayers)

    def setFilterText(self, text):
        self._filterText = text
        for i in xrange(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            for j in xrange(item.childCount()):
                subitem = item.child(j)
                w = self.itemWidget(subitem, 0)
                subitemText = w.text()
                subitem.setHidden(text != "" and text not in subitemText)

    def getFilterText(self):
        return self._filterText

    filterText = property(getFilterText, setFilterText)

    def showPopupMenu(self, point):
        selected = self.selectedItems()
        if len(selected) == 1:
            item = selected[0]
            hasConflicts = len(self.repo.conflicts()) > 0
            if isinstance(item, CommitTreeItem):
                menu = QtGui.QMenu()
                describeAction = QtGui.QAction(infoIcon, "Show detailed description of this version", None)
                describeAction.triggered.connect(lambda: self.describeVersion(item.commit))
                menu.addAction(describeAction)
                resetAction = QtGui.QAction(resetIcon, "Revert current branch to this version", None)
                resetAction.triggered.connect(lambda: self.revertToVersion(item.commit))
                resetAction.setEnabled(item.parent().isCurrentBranch and not hasConflicts)
                menu.addAction(resetAction)
                diffAction = QtGui.QAction(diffIcon, "Show changes introduced by this version...", None)
                diffAction.triggered.connect(lambda: self.showDiffs(item.commit))
                menu.addAction(diffAction)
                createBranchAction = QtGui.QAction(newBranchIcon, "Create new branch at this version...", None)
                createBranchAction.triggered.connect(lambda: self.createBranch(item.commit.commitid))
                menu.addAction(createBranchAction)
                createTagAction = QtGui.QAction(tagIcon, "Create new tag at this version...", None)
                createTagAction.triggered.connect(lambda: self.createTag(item))
                menu.addAction(createTagAction)
                deleteTagsAction = QtGui.QAction(tagIcon, "Delete tags at this version", None)
                deleteTagsAction.triggered.connect(lambda: self.deleteTags(item))
                menu.addAction(deleteTagsAction)
                exportLayersAction = QtGui.QAction(exportLayersIcon, "Add layers from this version to QGIS", None)
                exportLayersAction.triggered.connect(lambda: exportAndLoadVersion(item.commit))
                menu.addAction(exportLayersAction)
                exportDiffLayersAction = QtGui.QAction(exportDiffIcon, "Add changes introduced by this version as QGIS layers", None)
                exportDiffLayersAction.triggered.connect(lambda: self.exportAndLoadVersionDiffs(item.commit))
                menu.addAction(exportDiffLayersAction)
                point = self.mapToGlobal(point)
                menu.exec_(point)
            elif isinstance(item, BranchTreeItem):
                menu = QtGui.QMenu()
                switchAction = QtGui.QAction(switchIcon, "Make this branch the current branch", None)
                switchAction.triggered.connect(lambda: self.switchToBranch(item.text(0)))
                switchAction.setEnabled(not item.isCurrentBranch and not hasConflicts)
                menu.addAction(switchAction)
                deleteAction = QtGui.QAction(deleteIcon, "Delete this branch", None)
                deleteAction.triggered.connect(lambda: self.deleteBranch(item.text(0)))
                deleteAction.setEnabled(not item.isCurrentBranch and not hasConflicts)
                menu.addAction(deleteAction)
                mergeAction = QtGui.QAction(mergeIcon, "Merge this branch into current one", None)
                mergeAction.triggered.connect(lambda: self.mergeBranch(item.text(0)))
                mergeAction.setEnabled(not item.isCurrentBranch and not hasConflicts)
                menu.addAction(mergeAction)
                point = self.mapToGlobal(point)
                menu.exec_(point)
        elif len(selected) == 2:
            if isinstance(selected[0], CommitTreeItem) and isinstance(selected[1], CommitTreeItem):
                menu = QtGui.QMenu()
                diffAction = QtGui.QAction(diffIcon, "Show changes between selected versions...", None)
                diffAction.triggered.connect(lambda: self.showDiffs(selected[0].commit, selected[1].commit))
                menu.addAction(diffAction)
                exportDiffLayersAction = QtGui.QAction(exportDiffIcon, "Add changes between selected versions as QGIS layers", None)
                exportDiffLayersAction.triggered.connect(lambda: self.exportAndLoadVersionDiffs(selected[0].commit, selected[1].commit))
                menu.addAction(exportDiffLayersAction)
                point = self.mapToGlobal(point)
                menu.exec_(point)

    def _itemExpanded(self, item):
        if item is not None and isinstance(item, BranchTreeItem):
            item.populate()

    def describeVersion(self, commit):
        stats = commit.difftreestats()
        layer = stats.keys()[0]
        a, d, m = stats[layer]
        layers = "<ul>%s</ul>" % "".join(["<li>%s</li>" % tree.path for tree in commit.root.trees])
        html = ("<p><b>Author:</b> %s </p>"
                "<p><b>Created at:</b> %s</p>"
                "<p><b>Description message:</b> %s</p>"
                "<p><b>Layers in this version:</b> %s </p>"
                "<p><b>Layer affected by this version:</b> %s </p>"
                "<p><b>Changes added by this version </b>:"
                "<ul><li><b><font color='#FBB117'>%i features modified</font></b></li>"
                "<li><b><font color='green'>%i features added</font></b></li>"
                "<li><b><font color='red'>%i features deleted</font></b></li></ul></p>"
                % (commit.authorname, commit.authordate.strftime(" %m/%d/%y %H:%M"),
                   commit.message.replace("\n", "<br>"), layers, layer, m, a, d))
        dlg = HtmlDialog("Version description", html, self)
        dlg.exec_()


    def revertToVersion(self, commit):
        head = self.repo.head.id
        self.repo.reset(commit.commitid, geogig.RESET_MODE_HARD)
        self.repo.reset(head, geogig.RESET_MODE_MIXED)
        self.repo.addandcommit("Reverted to version %s (%s)" % (commit.commitid[:10], commit.message))
        self.updateCurrentBranchItem()
        self.repoChanged.emit()
        updateTrackedLayers(self.repo)

    def exportAndLoadVersionDiffs(self, commita, commitb = None):
        diffs = exportVersionDiffs(commita, commitb)
        allLayers = []
        for layers in diffs.values():
            allLayers.extend(reversed([l for l in layers if l is not None]))
        QgsMapLayerRegistry.instance().addMapLayers(allLayers)

    def showDiffs(self, commita, commitb = None):
        if commitb is None:
            commitb = commita
            commita = commita.parent
        else:
            pass
        dlg = DiffViewerDialog(self, self.repo, commita, commitb)
        dlg.exec_()

    def mergeBranch(self, branch):
        try:
            self.repo.merge(branch)
            updateTrackedLayers(self.repo)
            self.updateCurrentBranchItem()
        except GeoGigConflictException:
            QtGui.QMessageBox.warning(self, conflictIcon, 'Edit Conflicts',
                    "Some of your edits in the current branch with edits in the merged branch.\n\n"
                    + "OPTION A - MERGE:\n\n1. Solve your conflicts\n"
                     + "OPTION B - UNDO: Revert the merge operation to have only your current branch edits\n",
                    QtGui.QMessageBox.Ok)
        finally:
            self.repoChanged.emit()

    def createTag(self, item):
        tagname, ok = QtGui.QInputDialog.getText(self, 'Tag name',
                                              'Enter the tag name:')
        if ok:
            self.repo.createtag(item.commit.commitid, tagname, tagname)
            w = self.itemWidget(item, 0)
            w.tags = [tagname]
            w.updateText()

    def deleteTags(self, item):
        w = self.itemWidget(item, 0)
        for tag in w.tags:
            self.repo.deletetag(tag)
            w.tags = []
            w.updateText()

    def createBranch(self, ref):
        dlg = CreateBranchDialog(self.topLevelWidget())
        dlg.exec_()
        if dlg.ok:
            self.repo.createbranch(ref, dlg.getName(), dlg.isForce(), dlg.isCheckout())
            item = BranchTreeItem(dlg.getName(), self.repo)
            self.addTopLevelItem(item)
            if dlg.isCheckout():
                self.switchToBranch(dlg.getName())
            else:
                ref = self.repo.head.ref
                item.updateForCurrentBranch(ref)

    def deleteBranch(self, branch):
        self.repo.deletebranch(branch)
        for i in xrange(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.text(0) == branch:
                self.takeTopLevelItem(i)
                return

    def switchToBranch(self, branch):
        self.repo.checkout(branch)
        updateTrackedLayers(self.repo)
        self.head = self.updateForCurrentBranch()
        self.headChanged.emit()
        self.repoChanged.emit()

    def updateContent(self, repo):
        self.repo = repo
        self.clear()
        branches = repo.branches.keys()
        for branch in branches:
            item = BranchTreeItem(branch, repo)
            self.addTopLevelItem(item)
        self.resizeColumnToContents(0)
        self.head = self.updateForCurrentBranch()


    def updateCurrentBranchItem(self):
        for i in xrange(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.isCurrentBranch:
                item.takeChildren()
                item.populate()

    def updateForCurrentBranch(self):
        ref = self.repo.head.ref
        for i in xrange(self.topLevelItemCount()):
            self.topLevelItem(i).updateForCurrentBranch(ref)
        return ref

class BranchTreeItem(QtGui.QTreeWidgetItem):

    def __init__(self, branch, repo):
        QtGui.QTreeWidgetItem.__init__(self)
        self.branch = branch
        self.repo = repo
        self.setChildIndicatorPolicy(QtGui.QTreeWidgetItem.ShowIndicator)
        self.setText(0, branch)
        #self.setSizeHint(0, QtCore.QSize(self.sizeHint(0).width(), 25))

        self.isCurrentBranch = False

    def populate(self):
        if not self.childCount():
            tags = defaultdict(list)
            for k, v in self.repo.tags.iteritems():
                tags[v.commit.commitid].append(k)
            try:
                commits = self.repo.log(tip = self.branch, path = self.treeWidget().filterLayers)
            except GeoGigException, e:
                if "master does not resolve" in str(e):
                    return
                else:
                    raise e
            for commit in commits:
                item = CommitTreeItem(commit)
                self.addChild(item)
                w = CommitTreeItemWidget(commit, tags.get(commit.commitid, []))
                self.treeWidget().setItemWidget(item, 0, w)
                filterText = self.treeWidget().filterText
                w.setHidden(filterText != "" and filterText in w.text())
            self.treeWidget().resizeColumnToContents(0)

    def updateForCurrentBranch(self, currentBranch):
        self.isCurrentBranch = self.branch == currentBranch
        font = self.font(0)
        font.setBold(self.isCurrentBranch)
        self.setFont(0, font)
        if self.isCurrentBranch:
            self.setIcon(0, branchIcon)
        else:
            self.setIcon(0, disabledBranchIcon)


class CommitTreeItemWidget(QtGui.QLabel):
    def __init__(self, commit, tags):
        QtGui.QTextEdit.__init__(self)
        self.setWordWrap(False)
        self.tags = tags
        self.commit = commit
        self.updateText()

    def updateText(self):
        if self.tags:
            tags = "&nbsp;" + "&nbsp;".join(['<font color="black" style="background-color:yellow">&nbsp;%s&nbsp;</font>'
                                             % t for t in self.tags]) + "&nbsp;"
        else:
            tags = ""
        size = self.font().pointSize()
        text = ('%s<b><font style="font-size:%spt">%s</font></b>'
            '<br><font color="#5f6b77" style="font-size:%spt"><b>%s</b> by <b>%s</b></font> '
            '<font color="#5f6b77" style="font-size:%spt; background-color:rgb(225,225,225)"> %s </font>' %
            (tags, str(size), self.commit.message.splitlines()[0], str(size - 1),
             self.commit.authorprettydate(), self.commit.authorname, str(size - 1), self.commit.id[:10]))
        self.setText(text)


class CommitTreeItem(QtGui.QTreeWidgetItem):

    def __init__(self, commit):
        QtGui.QListWidgetItem.__init__(self)
        self.commit = commit

class HistoryViewerDialog(QtGui.QDialog):

    def __init__(self, repo, layer):
        self.repo = repo
        self.layer = layer
        QtGui.QDialog.__init__(self, config.iface.mainWindow(),
                               QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint)
        execute(self.initGui)

    def initGui(self):
        layout = QtGui.QVBoxLayout()
        history = HistoryViewer()
        history.updateContent(self.repo.repo())
        history.filterLayers = [self.layer]
        layout.addWidget(history)
        status = StatusWidget()
        status.updateRepository(self.repo)
        layout.addWidget(status)

        history.repoChanged.connect(status.updateLabelText)
        status.repoChanged.connect(history.updateCurrentBranchItem)

        self.setLayout(layout)

        self.resize(400, 500)
        self.setWindowTitle("Repository history")
