import os
import sys
import inspect
from versio import config
import traceback
import logging
from qgis.core import *
from qgis.gui import *
from versio.tools.utils import userFolder, userLocalRepos, \
    deleteTempFolder, allLocalRepos, nameFromRepoPath, userFromRepoPath
from gui.dialogs.configdialog import ConfigDialog
from versio.gui.dialogs.geogigerrordialog import GeoGigErrorDialog
from geogigpy.py4jconnector import Py4JConnectionException
from geogigpy.geogigexception import GeoGigException
from versio.tools.infotool import MapToolGeoGigInfo
from versio.tools.layertracking import readTrackedLayers, isTracked, getTrackingInfo, \
    removeNonexistentTrackedLayers, removeTrackedLayer
from versio.tools.layertracker import LayerTracker
from py4j.protocol import Py4JNetworkError
from versio.gui.dialogs.gatewaynotavailabledialog import GatewayNotAvailableDialog
from versio.gui.pyqtconnectordecorator import killGateway, \
    PyQtConnectorDecorator
from versio.tools.layers import  setIdEditWidget
from versio.gui.dialogs.navigatordialog import NavigatorDialog
import keyring
from versio.tools.versioinstance import startInstance, instance
from versio.gui.dialogs.importdialog import ImportDialog
from geogigpy.repo import Repository
from versio.gui.dialogs.historyviewer import HistoryViewerDialog
import webbrowser
from versio.tools.localversio import LocalVersio, LocalOnlyRepository
from versio.tools.repodecorator import RepoWrapper
from versio.gui.executor import execute
from PyQt4 import QtCore, QtGui

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

logger = logging.getLogger("geogigpy")

trackers = []

browseActions = {}
addActions = {}
removeActions = {}

def trackLayer(layer):
    global trackers
    if layer.type() == layer.VectorLayer and not layer.isReadOnly():
        tracker = LayerTracker(layer)
        trackers.append(tracker)
        layer.featureDeleted.connect(tracker.featureDeleted)
        layer.committedFeaturesAdded.connect(tracker._featuresAdded)
        QtCore.QObject.connect(layer, QtCore.SIGNAL("geometryChanged(QgsFeatureId, QgsGeometry&)"), tracker._geomChanged)
        layer.attributeValueChanged.connect(tracker._attributeValueChanged)
        layer.attributeAdded.connect(tracker.featureTypeChanged)
        layer.attributeDeleted.connect(tracker.featureTypeChanged)
        layer.editingStopped.connect(tracker.editingStopped)
        layer.editingStarted.connect(tracker.editingStarted)
        layer.beforeRollBack.connect(tracker.beforeRollBack)

        setIdEditWidget(layer)

        if isTracked(layer):
            browseActions[layer] = QtGui.QAction(u"Browse layer history...", config.iface.legendInterface())
            config.iface.legendInterface().addLegendLayerAction(browseActions[layer], u"GeoGig", u"id1", QgsMapLayer.VectorLayer, False)
            config.iface.legendInterface().addLegendLayerActionForLayer(browseActions[layer], layer)
            browseActions[layer].triggered.connect(lambda: layerHistory(layer))

            removeActions[layer] = QtGui.QAction(u"Remove layer from repository", config.iface.legendInterface())
            config.iface.legendInterface().addLegendLayerAction(removeActions[layer], u"GeoGig", u"id1", QgsMapLayer.VectorLayer, False)
            config.iface.legendInterface().addLegendLayerActionForLayer(removeActions[layer], layer)
            removeActions[layer].triggered.connect(lambda: removeLayer(layer))
        else:
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
    if isinstance(instance(), LocalVersio):
        versioRepo = LocalOnlyRepository(repo.url)
        user = userFromRepoPath(repo.url)
    else:
        user = instance().user
        versioRepo = LocalOnlyRepository(repo.url)
    wrapper = RepoWrapper(versioRepo, user)
    dlg = HistoryViewerDialog(wrapper, layername)
    dlg.exec_()

def addLayer(layer):
    if not layer.source().lower().endswith("shp"):
        QtGui.QMessageBox.warning(config.iface.mainWindow(), 'Cannot add layer',
                "Only shapefile layers are supported at the moment",
                QtGui.QMessageBox.Ok)
        return
    if isinstance(instance(), LocalVersio):
        repos = allLocalRepos()
    else:
        repos = userLocalRepos(instance().user)
    if repos:
        dlg = ImportDialog(config.iface.mainWindow(), layer = layer)
        dlg.exec_()
        if dlg.ok:
            config.iface.messageBar().pushMessage("Layer correctly added to repository",
                                              level = QgsMessageBar.INFO, duration = 4)
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
    config.iface.legendInterface().removeLegendLayerAction(removeActions[layer])
    config.iface.legendInterface().removeLegendLayerAction(browseActions[layer])
    del browseActions[layer]
    del removeActions[layer]
    addActions[layer] = QtGui.QAction(u"Add layer to Repository...", config.iface.legendInterface())
    config.iface.legendInterface().addLegendLayerAction(addActions[layer], u"GeoGig", u"id2", QgsMapLayer.VectorLayer, False)
    config.iface.legendInterface().addLegendLayerActionForLayer(addActions[layer], layer)
    addActions[layer].triggered.connect(lambda: addLayer(layer))

class VersioPlugin:

    def __init__(self, iface):
        self.iface = iface
        config.iface = iface

        class QgisLogHandler(logging.Handler):
            def __init__(self):
                logging.Handler.__init__(self)

            def emit(self, record):
                try:
                    QgsMessageLog.logMessage(self.format(record), "GeoGig")
                except AttributeError: #prevent error in case the log object is None
                    pass

        logFile = os.path.join(userFolder(), "geogig.log")
        handler = logging.FileHandler(logFile)
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        qgisHandler = QgisLogHandler()
        qgisFormatter = logging.Formatter('%(levelname)s - %(message)s')
        qgisHandler.setFormatter(qgisFormatter)
        qgisHandler.setLevel(logging.DEBUG)
        logger.addHandler(qgisHandler)

        config.initConfigParams()

    def unload(self):
        QgsMapLayerRegistry.instance().layerWasAdded.disconnect(trackLayer)
        self.menu.deleteLater()
        self.toolButton.deleteLater()
        sys.excepthook = self.qgisHook
        killGateway()
        removeNonexistentTrackedLayers()
        deleteTempFolder()

    def initGui(self):
        readTrackedLayers()

        QgsMapLayerRegistry.instance().layerWasAdded.connect(trackLayer)

        icon = QtGui.QIcon(os.path.dirname(__file__) + "/ui/resources/versio-16.png")
        self.explorerAction = QtGui.QAction(icon, "GeoGig Navigator", self.iface.mainWindow())
        self.explorerAction.triggered.connect(self.openNavigator)
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/ui/resources/config.png")
        self.configAction = QtGui.QAction(icon, "GeoGig Settings", self.iface.mainWindow())
        self.configAction.triggered.connect(self.openSettings)
        icon = QtGui.QIcon(os.path.dirname(__file__) + "/ui/resources/identify.png")
        self.toolAction = QtGui.QAction(icon, "GeoGig Feature Info Tool", self.iface.mainWindow())
        self.toolAction.setCheckable(True)
        self.toolAction.triggered.connect(self.setTool)
        self.menu = QtGui.QMenu(self.iface.mainWindow())
        self.menu.setTitle("GeoGig")
        self.menu.addAction(self.explorerAction)
        self.menu.addAction(self.toolAction)
        self.menu.addAction(self.configAction)
        bar = self.iface.layerToolBar()
        self.toolButton = QtGui.QToolButton()
        self.toolButton.setMenu(self.menu)
        self.toolButton.setPopupMode(QtGui.QToolButton.MenuButtonPopup)
        self.toolButton.setDefaultAction(self.explorerAction)
        useMainMenu = config.getConfigValue(config.GENERAL, config.USE_MAIN_MENUBAR)
        bar.addWidget(self.toolButton)
        if useMainMenu:
            menuBar = self.iface.mainWindow().menuBar()
            menuBar.insertMenu(self.iface.firstRightStandardMenu().menuAction(), self.menu)
        else:
            self.iface.addPluginToMenu(u"&GeoGig", self.explorerAction)
            self.iface.addPluginToMenu(u"&GeoGig", self.configAction)
            self.iface.addPluginToMenu(u"&GeoGig", self.toolAction)

        self.qgisHook = sys.excepthook;

        def pluginHook(t, value, tb):
            if isinstance(value, GeoGigException):
                trace = "".join(traceback.format_exception(t, value, tb))
                logger.error(trace)
                self.setWarning(unicode(value))
            elif isinstance(value, (Py4JConnectionException, Py4JNetworkError)):
                dlg = GatewayNotAvailableDialog(self.iface.mainWindow())
                dlg.exec_()
            else:
                trace = "".join(traceback.format_exception(t, value, tb))
                QgsMessageLog.logMessage(trace, "GeoGig", QgsMessageLog.CRITICAL)
                if "versio" in trace.lower():
                    dlg = GeoGigErrorDialog(trace, self.iface.mainWindow())
                    dlg.exec_()
                else:
                    self.qgisHook(t, value, tb)
        sys.excepthook = pluginHook

        self.mapTool = MapToolGeoGigInfo(self.iface.mapCanvas())
        #This crashes QGIS, so we comment it out until finding a solution
        #self.mapTool.setAction(self.toolAction)

    def setWarning(self, msg):
        QtGui.QMessageBox.warning(None, 'Could not complete GeoGig command',
                            msg,
                            QtGui.QMessageBox.Ok)

    def setTool(self):
        self.toolAction.setChecked(True)
        self.iface.mapCanvas().setMapTool(self.mapTool)


    def openNavigator(self):
        dlg = NavigatorDialog()
        dlg.exec_()


    def openSettings(self):
        dlg = ConfigDialog()
        dlg.exec_()








