import os
import re
from PyQt4 import QtGui, QtCore
from qgis.core import *
from geogigpy import geogig
from geogigpy.commit import Commit
from geogigpy.tree import Tree
from geogigpy import geogig
from geogigpy.geogigexception import GeoGigException
from geogig.ui.batchimportdialog import Ui_BatchImportDialog
from geogig.tools.exporter import exportVectorLayerAddingId
from geogig import config
from geogig.tools.utils import loadLayerNoCrsDialog

class BatchImportDialog(QtGui.QDialog):

    GEOGIGID = "geogigid"

    def __init__(self, parent, repo):
        QtGui.QDialog.__init__(self, parent, QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint)
        self.ui = Ui_BatchImportDialog()
        self.ui.setupUi(self)
        self.repo = repo
        self.ui.commitTextBox.textChanged.connect(self.messageHasChanged)
        self.ui.addLayersButton.clicked.connect(self.addLayers)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.layersList.setDragEnabled(True)
        self.ui.fidFieldsButton.clicked.connect(self.showFieldsMenu)
        self.ok = False
        self._commonFields = None


    def messageHasChanged(self):
        if self.ui.commitTextBox.toPlainText() != "":
            pass

    def accept(self):
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        try:
            self.ui.featureIdBox.setStyleSheet("QLineEdit{background: white}")
            self.ui.destTreeBox.setStyleSheet("QLineEdit{background: white}")
            self.ui.commitTextBox.setStyleSheet("QPlainTextEdit{background: white}")
            dest = self.ui.destTreeBox.text().strip()
            if dest == '':
                self.ui.destTreeBox.setStyleSheet("QLineEdit{background: yellow}")
                return
            fid = self.ui.featureIdBox.text().strip()
            pattern = self.ui.commitTextBox.toPlainText().strip()
            if pattern == '':
                self.ui.commitTextBox.setStyleSheet("QPlainTextEdit{background: yellow}")
                return
            layers = []
            fieldsInFid = [f[1:-1] for f in re.findall("\[.*?\]", fid)]
            for i in xrange(self.ui.layersList.count()):
                item = self.ui.layersList.item(i)
                path = item.path
                item.setBackground(QtCore.Qt.white)
                layer = loadLayerNoCrsDialog(path, "layer", "ogr")
                if not layer.isValid() or layer.type() != QgsMapLayer.VectorLayer:
                    raise Exception ("Error reading file %s or it is not a valid vector layer file" % path)
                provider = layer.dataProvider()
                for field in fieldsInFid:
                    idx = provider.fieldNameIndex(field)
                    if idx == -1:
                        raise Exception("Field %s not found in layer %s " % (field, path))
                layers.append(layer)
            try:
                self.repo.connector.setShowProgress(False)
                for i, layer in enumerate(layers):
                    item = self.ui.layersList.item(i)
                    path = layer.source()
                    exported = exportVectorLayerAddingId(layer, fid)
                    self.repo.importshp(exported, False, dest, self.GEOGIGID, True)
                    message = pattern.replace("%f", os.path.basename(path)).replace("%d", dest)
                    self.repo.add()
                    self.repo.commit(message)
                    item.setBackground(QtCore.Qt.green)
                    QtCore.QCoreApplication.processEvents()
            except GeoGigException, e:
                raise Exception("Cannot import layer " + path)
            finally:
                self.repo.connector.setShowProgress(True)

            self.ok = True
            QtGui.QApplication.restoreOverrideCursor()
            config.iface.messageBar().pushMessage("Layer files correctly added to repository",
                                                  level = QgsMessageBar.INFO, duration = 4)
            self.reject()
        except Exception, e:
            QtGui.QApplication.restoreOverrideCursor()
            QtGui.QMessageBox.critical(self, "Error", e.args[0])


    def commonFields(self):
        if self._commonFields is None:
            for i in xrange(self.ui.layersList.count()):
                item = self.ui.layersList.item(i)
                path = item.path
                layer = loadLayerNoCrsDialog(path, "layer", "ogr")
                fields = set(f.name() for f in layer.dataProvider().fields())
                if self._commonFields is None:
                    self._commonFields = fields
                else:
                    self._commonFields = self._commonFields & fields
        return self._commonFields

    def showFieldsMenu(self):
        fields = self.commonFields()
        if not fields:
            return
        def addText(text):
            self.ui.featureIdBox.insert("[%s]" % self.sender().text())
        popupmenu = QtGui.QMenu()
        self.action = QtGui.QAction("Available attributes:", self.ui.fidFieldsButton)
        popupmenu.addAction(self.action)
        self.action = QtGui.QAction("", self.ui.fidFieldsButton)
        self.action.setSeparator(True)
        popupmenu.addAction(self.action)
        for field in self.commonFields():
            self.action = QtGui.QAction(field, self.ui.fidFieldsButton)
            self.action.triggered.connect(lambda: addText(field))
            popupmenu.addAction(self.action)
        popupmenu.exec_(QtGui.QCursor.pos())

    def addLayers(self):
        formats = QgsVectorFileWriter.supportedFiltersAndFormats()
        exts = ['shp']
        for extension in formats.keys():
            extension = unicode(extension)
            extension = extension[extension.find('*.') + 2:]
            extension = extension[:extension.find(' ')]
            if extension.lower() != 'shp':
                exts.append(extension)
        for i in range(len(exts)):
            exts[i] = exts[i].upper() + ' files(*.' + exts[i].lower() + ')'
        filefilter = ';;'.join(exts)
        files = QtGui.QFileDialog.getOpenFileNames(self, 'Add layers', '', filefilter)

        for f in files:
            layer = loadLayerNoCrsDialog(f, "layer", "ogr")
            if not layer.isValid() or layer.type() != QgsMapLayer.VectorLayer:
                QtGui.QMessageBox.critical(self, "Error", "Error reading file %s or it is not a valid vector layer file" % f)
                return

        for f in files:
            item = LayerItem(f)
            self.ui.layersList.addItem(item)
            widget = LayerWidget(item, self.ui.layersList)
            self.ui.layersList.setItemWidget(item, widget)
        self._commonFields = None

    def reject(self):
        QtGui.QDialog.reject(self)
        self.close()

class LayerItem(QtGui.QListWidgetItem):
    def __init__(self, path):
        QtGui.QTreeWidgetItem.__init__(self)
        self.path = path
        self.setSizeHint(QtCore.QSize(0, 22))
        self.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled)

class LayerWidget(QtGui.QWidget):

    def __init__(self, item, listWidget):
        QtGui.QWidget.__init__(self)
        self.path = item.path
        self.item = item
        self.listWidget = listWidget
        layout = QtGui.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.hlayout = QtGui.QHBoxLayout()
        self.hlayout.setContentsMargins(0, 0, 0, 0)
        self.hlayout.setSpacing(0)
        layerLabel = QtGui.QLabel()
        layerLabel.setPixmap(QtGui.QPixmap(os.path.join(os.path.dirname(__file__),
                                                        os.pardir, os.pardir, "ui", "resources", "layer.png")))
        self.hlayout.addWidget(layerLabel)
        nameLabel = QtGui.QLabel(self.path)
        self.hlayout.addWidget(nameLabel)
        spacerItem = QtGui.QSpacerItem(10, 20, QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Minimum)
        self.hlayout.addItem(spacerItem)
        deleteButton = QtGui.QToolButton()
        deleteIcon = QtGui.QIcon(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir,
                                              "ui", "resources", "remove.gif"))
        deleteButton.setIcon(deleteIcon)
        deleteButton.setAutoRaise(True)
        deleteButton.setToolTip("Remove")
        deleteButton.clicked.connect(self.delete)
        self.hlayout.addWidget(deleteButton)

        layout.addLayout(self.hlayout)
        self.setLayout(layout)

    def delete(self):
        row = self.listWidget.indexFromItem(self.item).row()
        self.listWidget.takeItem(row)
