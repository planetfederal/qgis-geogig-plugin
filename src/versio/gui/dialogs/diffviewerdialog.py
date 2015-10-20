import os
import logging
from PyQt4 import QtGui, QtCore
from qgis.core import *
from qgis.gui import *
from versio.ui.diffviewerdialog import Ui_DiffViewerDialog
from versio.gui.dialogs.geogigref import RefPanel
from geogigpy.diff import *
from geogigpy import geogig
from geogigpy.geogigexception import GeoGigException
from geogigpy.commit import Commit
from geogigpy.geometry import Geometry
from versio import config
from versio.tools.exporter import exportVersionDiffs
from versio.gui.executor import execute
from versio.gui.dialogs.geometrydiffviewerdialog import GeometryDiffViewerDialog

_logger = logging.getLogger("geogigpy")

MODIFIED, ADDED, REMOVED = "M", "A", "R"
GEOMETRY_FIELD = "geometry"

class DiffViewerDialog(QtGui.QDialog):

    def __init__(self, parent, repo, refa, refb):
        QtGui.QDialog.__init__(self, parent,
                               QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint)
        self.repo = repo
        self.layers = []
        self.allchanges = {}
        self.currentPath = None

        if (isinstance(refa, Commit) and isinstance(refb, Commit)
                and refa.committerdate > refb.committerdate):
            refa, refb = refb, refa

        self.ui = Ui_DiffViewerDialog()
        self.ui.setupUi(self)

        self.setWindowFlags(self.windowFlags() |
                              QtCore.Qt.WindowSystemMenuHint |
                              QtCore.Qt.WindowMinMaxButtonsHint)

        self.commit1 = refa
        self.commit1Panel = RefPanel(self.repo, refa, onlyCommits = False)
        layout = QtGui.QHBoxLayout()
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.addWidget(self.commit1Panel)
        self.ui.commit1Widget.setLayout(layout)
        self.commit2 = refb
        self.commit2Panel = RefPanel(self.repo, refb, onlyCommits = False)
        layout = QtGui.QHBoxLayout()
        layout.setSpacing(0)
        layout.setMargin(0)
        layout.addWidget(self.commit2Panel)
        self.ui.commit2Widget.setLayout(layout)
        self.commit1Panel.refChanged.connect(self.refsHaveChanged)
        self.commit2Panel.refChanged.connect(self.refsHaveChanged)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.setSpacing(0)
        horizontalLayout.setMargin(0)
        self.mapCanvas = QgsMapCanvas()
        self.mapCanvas.setCanvasColor(QtCore.Qt.white)
        settings = QtCore.QSettings()
        self.mapCanvas.enableAntiAliasing(settings.value("/qgis/enable_anti_aliasing", False, type = bool))
        self.mapCanvas.useImageToRender(settings.value("/qgis/use_qimage_to_render", False, type = bool))
        action = settings.value("/qgis/wheel_action", 0, type = float)
        zoomFactor = settings.value("/qgis/zoom_factor", 2, type = float)
        self.mapCanvas.setWheelAction(QgsMapCanvas.WheelAction(action), zoomFactor)
        horizontalLayout.addWidget(self.mapCanvas)
        self.ui.mapContainer.setLayout(horizontalLayout)

        self.panAndSelectTool = MapToolPanAndSelect(self.mapCanvas, self)
        self.mapCanvas.setMapTool(self.panAndSelectTool)

        self.ui.attributesTable.horizontalHeader().sectionClicked.connect(self.sortByColumn)
        self.ui.attributesTable.customContextMenuRequested.connect(self.showContextMenu)
        self.ui.layerCombo.currentIndexChanged.connect(self.layerChanged)

        def _zoomToFullExtent():
            extent = self.getFullExtent()
            self.mapCanvas.setExtent(extent)
            self.mapCanvas.refresh()
        self.ui.zoomToExtentButton.clicked.connect(_zoomToFullExtent)

        self.ui.baseLayerCheck.setChecked(True)
        self.ui.compareLayerCheck.setChecked(True)

        self.computeDiffs()

        self.ui.baseLayerCheck.stateChanged.connect(self.showLayers)
        self.ui.compareLayerCheck.stateChanged.connect(self.showLayers)

        self.showMaximized()

    def refsHaveChanged(self):
        self.computeDiffs()


    def showContextMenu(self, point):
        row = self.ui.attributesTable.selectionModel().currentIndex().row()
        model = self.ui.attributesTable.model()
        index = model.index(row, self.geogigIdx)
        geogigid = model.data(index)
        menu = QtGui.QMenu()
        zoomAction = QtGui.QAction("Zoom to this feature", None)
        zoomAction.triggered.connect(lambda: self.zoomToFeature(geogigid))
        menu.addAction(zoomAction)
        viewAction = QtGui.QAction("View geometry changes...", None)
        viewAction.triggered.connect(lambda: self.viewGeometryChanges(geogigid))
        menu.addAction(viewAction)
        globalPoint = self.ui.attributesTable.mapToGlobal(point)
        menu.exec_(globalPoint)

    def zoomToFeature(self, geogigid):
        geometries = [g for g in self.features[geogigid][GEOMETRY_FIELD] if g is not None]
        extent = geometries[0].boundingBox()
        for geom in geometries:
            extent.combineExtentWith(geom.boundingBox())
        self.mapCanvas.setExtent(extent)
        self.mapCanvas.refresh()

    def viewGeometryChanges(self, geogigid):
        geometries = self.features[geogigid][GEOMETRY_FIELD]
        dlg = GeometryDiffViewerDialog(geometries, self.layers[0].crs())
        dlg.exec_()

    def sortByColumn(self, col):
        self.ui.attributesTable.sortByColumn(col, QtCore.Qt.DescendingOrder)

    def getFullExtent(self):
        layers = [lay for lay in self.layers if lay is not None]
        extent = layers[0].extent()
        for layer in layers:
            extent.combineExtentWith(layer.extent())
        return extent

    def selectionChanged(self):
        row = self.ui.attributesTable.selectionModel().currentIndex().row()
        model = self.ui.attributesTable.model()
        index = model.index(row, self.geogigIdx)
        geogigid = model.data(index)
        def _filter(feature):
            return feature["geogigid"] == geogigid
        for layer in self.layers:
            if layer is not None:
                features = filter(_filter, layer.getFeatures())
                layer.setSelectedFeatures([feature.id() for feature in features])
        self.mapCanvas.refresh()


    def createTableDataFromLayers(self):
        self.attribs = []
        self.features = {}
        for layer in self.layers:
            if layer is not None:
                fields = layer.pendingFields().toList()
                for f in fields:
                    if f.name() not in self.attribs:
                        self.attribs.append(f.name())
        self.attribs.remove("changetype")
        self.attribs.insert(0, "changetype")
        if self.layers[0] is not None:
            layer = self.layers[0]
            fields = [f.name() for f in layer.pendingFields().toList()]
            features = layer.getFeatures()
            geogigidIdx = fields.index("geogigid")
            for feature in features:
                attrs = feature.attributes()
                geogigid = attrs[geogigidIdx]
                if not isinstance(geogigid, QtCore.QPyNullVariant):
                    featuredict = {}
                    for field in self.attribs:
                        try:
                            idx = fields.index(field)
                            value = attrs[idx]
                        except ValueError:
                            value = None
                        featuredict[field] = [value, None]
                    featuredict[GEOMETRY_FIELD] = [QgsGeometry(feature.geometry()), None]
                    self.features[geogigid] = featuredict
        if self.layers[1] is not None:
            layer = self.layers[1]
            fields = [f.name() for f in layer.pendingFields().toList()]
            features = layer.getFeatures()
            geogigidIdx = fields.index("geogigid")
            for feature in features:
                attrs = feature.attributes()
                geogigid = attrs[geogigidIdx]
                if not isinstance(geogigid, QtCore.QPyNullVariant):
                    if geogigid not in self.features:
                        self.features[geogigid] = {attr: [None, None] for attr in self.attribs}
                        self.features[geogigid][GEOMETRY_FIELD] = [None, None]
                    featuredict = self.features[geogigid]
                    for field in self.attribs:
                        try:
                            idx = fields.index(field)
                            value = attrs[idx]
                            featuredict[field][1] = value
                        except ValueError:
                            pass
                    featuredict[GEOMETRY_FIELD][1] = QgsGeometry(feature.geometry())

        self.attribs.insert(1, GEOMETRY_FIELD)
        self.geogigIdx = self.attribs.index("geogigid")


    def layerChanged(self):
        layername = self.ui.layerCombo.currentText()
        self.computeLayerDiffs(layername)

    def computeDiffs(self):
        self.commit1 = self.commit1Panel.getRef()
        self.commit2 = self.commit2Panel.getRef()

        self.unloadLayers()

        allchanges = exportVersionDiffs(self.commit1, self.commit2)
        self.allchanges = {}
        for path, layers in allchanges.iteritems():
            self.allchanges[path] = layers
            for layer in layers:
                if layer is not None:
                    QgsMapLayerRegistry.instance().addMapLayer(layer, False)
        if self.allchanges:
            self.layers = self.allchanges.values()[0]

            self.ui.layerCombo.blockSignals(True)
            self.ui.layerCombo.clear()
            self.ui.layerCombo.addItems(self.allchanges.keys())
            self.ui.layerCombo.blockSignals(False)

            self.computeLayerDiffs(self.allchanges.keys()[0])
        else:
            self.mapCanvas.clear()
            self.proxyModel.deleteLater()


    def computeLayerDiffs(self, layername):
        def _computeLayerDiff():
            self.layers = self.allchanges[layername]
            self.createTableDataFromLayers()
            self.geogigidIdx = self.attribs.index("geogigid")
            self.changeTypeIdx = self.attribs.index("changetype")

            model = DiffTableModel(self.attribs, self.features)
            self.proxyModel = QtGui.QSortFilterProxyModel();
            self.proxyModel.setSourceModel(model)
            self.ui.attributesTable.setModel(self.proxyModel)
            self.ui.attributesTable.selectionModel().selectionChanged.connect(self.selectionChanged)
            self.ui.attributesTable.setColumnHidden(self.geogigidIdx, True)
            self.ui.attributesTable.resizeColumnsToContents()
            self.ui.attributesTable.setVisible(False)
            vporig = self.ui.attributesTable.viewport().geometry()
            vpnew = vporig;
            vpnew.setWidth(10000);
            self.ui.attributesTable.viewport().setGeometry(vpnew);
            self.ui.attributesTable.resizeRowsToContents()
            self.ui.attributesTable.viewport().setGeometry(vporig);
            self.ui.attributesTable.setVisible(True)

            self.showLayers()

        execute(_computeLayerDiff)

    def showLayers(self):
        layers = [lay for lay in self.layers if lay is not None]
        self.mapCanvas.setDestinationCrs(layers[0].crs())
        extent = self.getFullExtent()
        self.mapCanvas.setRenderFlag(False)
        self.mapCanvas.clear()
        visibility = [self.ui.compareLayerCheck.isChecked(), self.ui.baseLayerCheck.isChecked()]
        mapLayers = [QgsMapCanvasLayer(lay) for i, lay in enumerate(reversed(self.layers)) if visibility[i]]
        self.mapCanvas.setLayerSet(mapLayers)
        self.mapCanvas.setRenderFlag(True)
        self.mapCanvas.refresh()
        self.mapCanvas.setExtent(extent)

    def reject(self):
        QtGui.QDialog.reject(self)
        self.unloadLayers()

    def unloadLayers(self):
        for layers in self.allchanges.values():
            for layer in layers:
                if layer is not None:
                    QgsMapLayerRegistry.instance().removeMapLayer(layer.id())


class MapToolPanAndSelect(QgsMapTool):

    def __init__(self, canvas, viewer):
        self.canvas = canvas
        self.viewer = viewer
        self.featureSelected = False
        self.dragging = False
        QgsMapTool.__init__(self, self.canvas)
        self.setCursor(QtCore.Qt.CrossCursor)

    def canvasReleaseEvent(self, e):
        if e.button() == QtCore.Qt.LeftButton:
            if (self.dragging):
                self.canvas.panActionEnd(e.pos())
                self.dragging = False

    def canvasMoveEvent(self, e):
        if e.buttons() & QtCore.Qt.LeftButton:
            self.dragging = True
            self.canvas.panAction(e)

    def canvasPressEvent(self, e):
        point = self.toMapCoordinates(e.pos())
        searchRadius = self.canvas.extent().width() * .01;
        r = QgsRectangle()
        r.setXMinimum(point.x() - searchRadius);
        r.setXMaximum(point.x() + searchRadius);
        r.setYMinimum(point.y() - searchRadius);
        r.setYMaximum(point.y() + searchRadius);

        self.viewer.ui.attributesTable.selectionModel().clear()
        for layer in self.canvas.layers():
            layer.setSelectedFeatures([])
        for layer in self.canvas.layers():
            r = self.toLayerCoordinates(layer, r);
            features = layer.getFeatures(QgsFeatureRequest().setFilterRect(r).setFlags(QgsFeatureRequest.ExactIntersect));
            try:
                geogigid = features.next()["geogigid"]
                model = self.viewer.ui.attributesTable.model()
                for row in xrange(model.rowCount()):
                    index = model.index(row, self.viewer.geogigIdx)
                    geogigid2 = model.data(index)
                    if geogigid == geogigid2:
                        self.viewer.ui.attributesTable.selectRow(row)
                        return
            except StopIteration, e:
                pass

class DiffTableModel(QtCore.QAbstractTableModel):
    def __init__(self, attribs, features, parent = None, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.attribs = attribs
        self.features = features

    def rowCount(self, parent = None):
        return len(self.features)

    def columnCount(self, parent = None):
        return len(self.attribs)

    def data(self, index, role = QtCore.Qt.DisplayRole):
        if index.isValid():
            values = self.features.values()[index.row()][self.attribs[index.column()]]
            if role == QtCore.Qt.DisplayRole:
                if isinstance(values[0], QgsGeometry) or isinstance(values[1], QgsGeometry):
                    if values[0] != values[1] and values[0] is not None and values[1] is not None:
                        return 'Old geometry\nNew geometry'
                    elif values[1] is None:
                        return "Geometry"#unicode(values[0])
                    else:
                        return "Geometry"#unicode(values[1])
                else:
                    if values[0] != values[1] and values[0] is not None and values[1] is not None:
                        return '%s\n%s' % (unicode(values[0]), unicode(values[1]))
                    elif values[1] is None:
                        return unicode(values[0])
                    else:
                        return unicode(values[1])
            elif role == QtCore.Qt.ForegroundRole:
                if index.column() != 0:
                    if values[1] is None:
                        return QtGui.QBrush(QtCore.Qt.red)
                    elif values[0] is None:
                        return QtGui.QBrush(QtCore.Qt.green)
                    elif values[1] != values[0]:
                        return QtGui.QBrush(QtGui.QColor(255, 170, 0))
                    else:
                        return QtGui.QBrush(QtCore.Qt.black)
                else:
                    return QtGui.QBrush(QtCore.Qt.black)
            elif role == QtCore.Qt.BackgroundRole:
                if index.column() == 0:
                    if values[1] is None:
                        return QtGui.QBrush(QtCore.Qt.red)
                    elif values[0] is None:
                        return QtGui.QBrush(QtCore.Qt.green)
                    else:
                        return QtGui.QBrush(QtGui.QColor(255, 170, 0))
                else:
                    return QtGui.QBrush(QtCore.Qt.white)

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.attribs[section]
            else:
                return str(section + 1)



