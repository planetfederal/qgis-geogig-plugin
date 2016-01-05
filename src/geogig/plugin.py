import os
import sys
import inspect
from geogig import config
import traceback
import logging
from qgis.core import *
from qgis.gui import *
from geogig.tools.utils import *
from gui.dialogs.configdialog import ConfigDialog
from geogig.gui.dialogs.geogigerrordialog import GeoGigErrorDialog
from geogigpy.py4jconnector import Py4JConnectionException
from geogigpy.geogigexception import GeoGigException, UnconfiguredUserException
from geogigpy import geogig
from geogig.tools.infotool import MapToolGeoGigInfo
from geogig.tools.layertracking import *
from geogig.tools.layertracker import LayerTracker
from py4j.protocol import Py4JNetworkError
from geogig.gui.dialogs.gatewaynotavailabledialog import GatewayNotAvailableDialog, GatewayNotAvailableWhileEditingDialog
from geogig.gui.pyqtconnectordecorator import killGateway, createRepository, PyQtConnectorDecorator
from geogig.tools.layers import  setIdEditWidget
from geogig.gui.dialogs.navigatordialog import NavigatorDialog
from geogig.gui.dialogs.importdialog import ImportDialog
from geogigpy.repo import Repository
from geogig.gui.dialogs.historyviewer import HistoryViewerDialog
from geogig.gui.executor import execute
from geogig.tools.repowrapper import RepositoryWrapper, localRepos
from geogig.gui.dialogs.commitdialog import CommitDialog
from geogig.gui.dialogs.userconfigdialog import UserConfigDialog
from geogig.tools.exporter import exportVectorLayer
from layeractions import setAsTracked, setAsUntracked
from PyQt4 import QtGui

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

logger = logging.getLogger("geogigpy")

trackers = {}

def trackLayer(layer):
    global trackers
    if layer.type() == layer.VectorLayer and not layer.isReadOnly():
        tracker = LayerTracker(layer)
        trackers[layer] = tracker
        layer.committedFeaturesAdded.connect(tracker._featuresAdded)
        layer.editingStopped.connect(tracker.editingStopped)
        layer.editingStarted.connect(tracker.editingStarted)

        setIdEditWidget(layer)

        if isTracked(layer):
            setAsTracked(layer)
        else:
            setAsUntracked(layer)

def layerRemoved(layer):
    global trackers
    layer = QgsMapLayerRegistry.instance().mapLayer(layer)
    setAsUntracked(layer)
    if layer in trackers:
        del trackers[layer]

class GeoGigPlugin:

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

        try:
            from qgistester.tests import addTestModule
            from geogig.test import testplugin
            addTestModule(testplugin, "GeoGig")
        except:
            pass

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
        QgsMapLayerRegistry.instance().layerRemoved.connect(layerRemoved)

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
                if "geogig" in trace.lower():
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








