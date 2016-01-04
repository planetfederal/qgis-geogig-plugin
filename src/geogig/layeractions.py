from geogig import config
from qgis.core import *
from qgis.gui import *
from geogig.tools.utils import *
from geogigpy.py4jconnector import Py4JConnectionException
from geogigpy.geogigexception import GeoGigException, UnconfiguredUserException
from geogigpy import geogig
from geogig.tools.layertracking import *
from geogig.tools.layertracker import LayerTracker
from geogig.gui.dialogs.gatewaynotavailabledialog import GatewayNotAvailableDialog, GatewayNotAvailableWhileEditingDialog
from geogig.gui.pyqtconnectordecorator import createRepository, PyQtConnectorDecorator
from geogig.gui.dialogs.importdialog import ImportDialog
from geogigpy.repo import Repository
from geogig.gui.dialogs.historyviewer import HistoryViewerDialog
from geogig.gui.executor import execute
from geogig.tools.repowrapper import RepositoryWrapper, localRepos
from geogig.gui.dialogs.commitdialog import CommitDialog
from geogig.gui.dialogs.userconfigdialog import UserConfigDialog
from geogig.tools.exporter import exportVectorLayer
from PyQt4 import QtGui

browseActions = {}
addActions = {}
removeActions = {}
commitActions = {}

def setAsTracked(layer):
    global browseActions
    global removeActions
    global commitActions
    global addActions
    if layer in addActions:
        config.iface.legendInterface().removeLegendLayerAction(addActions[layer])
        del addActions[layer]
    browseActions[layer] = QtGui.QAction(u"Browse layer history...", config.iface.legendInterface())
    config.iface.legendInterface().addLegendLayerAction(browseActions[layer], u"GeoGig", u"id1", QgsMapLayer.VectorLayer, False)
    config.iface.legendInterface().addLegendLayerActionForLayer(browseActions[layer], layer)
    browseActions[layer].triggered.connect(lambda: layerHistory(layer))
    removeActions[layer] = QtGui.QAction(u"Remove layer from repository", config.iface.legendInterface())
    config.iface.legendInterface().addLegendLayerAction(removeActions[layer], u"GeoGig", u"id1", QgsMapLayer.VectorLayer, False)
    config.iface.legendInterface().addLegendLayerActionForLayer(removeActions[layer], layer)
    removeActions[layer].triggered.connect(lambda: removeLayer(layer))
    commitActions[layer] = QtGui.QAction(u"Update repository with this version", config.iface.legendInterface())
    config.iface.legendInterface().addLegendLayerAction(commitActions[layer], u"GeoGig", u"id1", QgsMapLayer.VectorLayer, False)
    config.iface.legendInterface().addLegendLayerActionForLayer(commitActions[layer], layer)
    commitActions[layer].triggered.connect(lambda: commitLayer(layer))

def setAsUntracked(layer):
    global browseActions
    global removeActions
    global commitActions
    global addActions
    if layer in removeActions:
        config.iface.legendInterface().removeLegendLayerAction(removeActions[layer])
        config.iface.legendInterface().removeLegendLayerAction(browseActions[layer])
        config.iface.legendInterface().removeLegendLayerAction(commitActions[layer])
        del browseActions[layer]
        del removeActions[layer]
        del commitActions[layer]
    addActions[layer] = QtGui.QAction(u"Add layer to Repository...", config.iface.legendInterface())
    config.iface.legendInterface().addLegendLayerAction(addActions[layer], u"GeoGig", u"id2", QgsMapLayer.VectorLayer, False)
    config.iface.legendInterface().addLegendLayerActionForLayer(addActions[layer], layer)
    addActions[layer].triggered.connect(lambda: addLayer(layer))

def _repoForLayer(layer):
    tracking = getTrackingInfo(layer)
    connector = PyQtConnectorDecorator()
    connector.checkIsAlive()
    return Repository(tracking.repoFolder(), connector), tracking.layername

def layerHistory(layer):
    repo, layername = _repoForLayer(layer)
    wrapper = RepositoryWrapper(repo.url)
    dlg = HistoryViewerDialog(wrapper, layername)
    dlg.exec_()

def addLayer(layer):
    if not layer.source().lower().endswith("shp"):
        QtGui.QMessageBox.warning(config.iface.mainWindow(), 'Cannot add layer',
                "Only shapefile layers are supported at the moment",
                QtGui.QMessageBox.Ok)
        return
    repos = localRepos()
    if repos:
        dlg = ImportDialog(config.iface.mainWindow(), layer = layer)
        dlg.exec_()
        if dlg.ok:
            config.iface.messageBar().pushMessage("Layer correctly added to repository",
                                              level = QgsMessageBar.INFO, duration = 4)
            setAsTracked(layer)
    else:
        QtGui.QMessageBox.warning(config.iface.mainWindow(), 'Cannot add layer',
                "No local repositories were found",
                QtGui.QMessageBox.Ok)

def removeLayer(layer):
    ret = QtGui.QMessageBox.warning(config.iface.mainWindow(), "Delete layer",
                        "Are you sure you want to delete this layer?",
                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                        QtGui.QMessageBox.Yes);
    if ret == QtGui.QMessageBox.No:
        return
    repo, layername = _repoForLayer(layer)
    repo.removetrees([layername])
    repo.addandcommit("Removed layer '%s'" % layername)
    removeTrackedLayer(layer)
    config.iface.messageBar().pushMessage("Layer correctly removed from repository",
                                           level = QgsMessageBar.INFO, duration = 4)
    setAsUntracked(layer)

def commitLayer(layer):
    trackedLayer = getTrackingInfo(layer)
    try:
        repo = createRepository(trackedLayer.repoFolder(), False)
    except Py4JConnectionException:
        QtGui.QApplication.restoreOverrideCursor()
        dlg = GatewayNotAvailableWhileEditingDialog(config.iface.mainWindow())
        dlg.exec_()
        return
    QtGui.QApplication.restoreOverrideCursor()

    if layer.dataProvider().fieldNameIndex("geogigid") == -1:
        config.iface.messageBar().pushMessage("Cannot update GeoGig repository. Layer has no 'geogigid' field",
                                                  level = QgsMessageBar.WARNING, duration = 4)
        return

    exported = exportVectorLayer(layer)
    repo.importshp(exported, False, trackedLayer.layername, "geogigid", True)
    setInSync(layer, True)

    unstaged = repo.difftreestats(geogig.HEAD, geogig.WORK_HEAD)
    total = 0
    for counts in unstaged.values():
        total += sum(counts)
    if total == 0:
        config.iface.messageBar().pushMessage("No changes detected. Repository was already up to date",
                                              level = QgsMessageBar.INFO, duration = 4)
        return

    dlg = CommitDialog(repo, config.iface.mainWindow())
    dlg.exec_()
    try:
        repo.addandcommit(dlg.getMessage())
    except UnconfiguredUserException, e:
        #It should not raise this exception unless config file has been manually deleted
        configdlg = UserConfigDialog(config.iface.mainWindow())
        configdlg.exec_()
        if configdlg.user is not None:
            repo.config(geogig.USER_NAME, configdlg.user)
            repo.config(geogig.USER_EMAIL, configdlg.email)
            repo.commit(dlg.getMessage())
        else:
            return
    headid = repo.revparse(geogig.HEAD)
    setRef(layer, headid)
    config.iface.messageBar().pushMessage("Repository correctly updated",
                                              level = QgsMessageBar.INFO, duration = 4)
    setInSync(layer, True)
