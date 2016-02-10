from PyQt4 import QtCore, QtGui
from qgis.core import *
from qgis.gui import *
from geogig.tools import layertracking
from geogig.gui.dialogs.blamedialog import BlameDialog
from geogig.gui.pyqtconnectordecorator import PyQtConnectorDecorator
from geogigpy.repo import Repository
from geogigpy.geogigexception import GeoGigException
from geogig.gui.dialogs.versionsviewer import VersionViewerDialog
from geogig import config
import os


class MapToolGeoGigInfo(QgsMapTool):

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.setCursor(QtCore.Qt.CrossCursor)

    def canvasPressEvent(self, e):
        layer = config.iface.activeLayer()
        if layer is None or not isinstance(layer, QgsVectorLayer):
            config.iface.messageBar().pushMessage("No layer selected or the current active layer is not a valid vector layer",
                                                  level = QgsMessageBar.WARNING, duration = 4)
            return
        if not layertracking.isRepoLayer(layer):
            config.iface.messageBar().pushMessage("The current active layer is not being tracked as part of a GeoGig repo",
                                                  level = QgsMessageBar.WARNING, duration = 4)
            return

        trackedlayer = layertracking.getTrackingInfo(layer)
        point = self.toMapCoordinates(e.pos())
        searchRadius = self.canvas().extent().width() * .01;
        r = QgsRectangle()
        r.setXMinimum(point.x() - searchRadius);
        r.setXMaximum(point.x() + searchRadius);
        r.setYMinimum(point.y() - searchRadius);
        r.setYMaximum(point.y() + searchRadius);

        r = self.toLayerCoordinates(layer, r);

        fit = layer.getFeatures(QgsFeatureRequest().setFilterRect(r).setFlags(QgsFeatureRequest.ExactIntersect));
        fid = None
        try:
            feature = fit.next()
            try:
                fid = unicode(feature["geogigid"])
            except:
                pass
        except StopIteration, e:
            return
        if fid is None:
            config.iface.messageBar().pushMessage("No 'geogigid' field found in layer. Cannot identify features.",
                                                  level = QgsMessageBar.WARNING, duration = 4)
            return
        try:
            connector = PyQtConnectorDecorator()
            connector.checkIsAlive()
            repo = Repository(trackedlayer.repoFolder, connector, False)
        except Exception, e:
            config.iface.messageBar().pushMessage("The repository linked to the active layer is not valid",
                                                  level = QgsMessageBar.WARNING, duration = 4)
            return

        menu = QtGui.QMenu()
        versionsAction = QtGui.QAction("Show all versions of this feature...", None)
        versionsAction.triggered.connect(lambda: self.versions(repo, trackedlayer.layername, fid))
        menu.addAction(versionsAction)
        blameAction = QtGui.QAction("Show authorship...", None)
        blameAction.triggered.connect(lambda: self.blame(repo, trackedlayer.layername, fid))
        menu.addAction(blameAction)
        point = config.iface.mapCanvas().mapToGlobal(e.pos())
        menu.exec_(point)

    def versions(self, repo, tree, fid):
        path = unicode(tree) + "/" + unicode(fid)
        try:
            dlg = VersionViewerDialog(repo, path)
            dlg.exec_()
        except GeoGigException, e:
            config.iface.messageBar().pushMessage(str(e),
                                                  level = QgsMessageBar.WARNING, duration = 4)

    def blame(self, repo, tree, fid):
        path = tree + "/" + fid
        dlg = BlameDialog(repo, path)
        dlg.exec_()

