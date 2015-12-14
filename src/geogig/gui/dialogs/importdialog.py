from qgis.core import *
from qgis.gui import *
from PyQt4 import QtGui, QtCore
from geogig.tools.layers import *
import os
from geogigpy.geogigexception import GeoGigException, UnconfiguredUserException
from geogigpy import geogig
from geogig.gui.dialogs.userconfigdialog import UserConfigDialog
from geogig.tools.exporter import exportVectorLayer
from geogig.tools.layertracking import addTrackedLayer, isTracked
from geogig.gui.dialogs.addgeogigiddialog import AddGeogigIdDialog
from geogig.tools.utils import *
from geogigpy.repo import Repository
from geogig.gui.pyqtconnectordecorator import PyQtConnectorDecorator
from geogig.tools.repowrapper import localRepos

class ImportDialog(QtGui.QDialog):

    def __init__(self, parent, repo = None, layer = None):
        super(ImportDialog, self).__init__(parent)
        self.repo = repo
        self.layer = layer
        self.ok = False
        self.initGui()

    def initGui(self):
        self.setWindowTitle('Add layer to GeoGig repository')
        verticalLayout = QtGui.QVBoxLayout()

        if self.repo is None:
            repos = localRepos()
            self.repos = {r.title:r.path for r in repos}
            layerLabel = QtGui.QLabel('Repository')
            verticalLayout.addWidget(layerLabel)
            self.repoCombo = QtGui.QComboBox()
            self.repoCombo.addItems(self.repos.keys())
            verticalLayout.addWidget(self.repoCombo)
        if self.layer is None:
            layerLabel = QtGui.QLabel('Layer')
            verticalLayout.addWidget(layerLabel)
            self.layerCombo = QtGui.QComboBox()
            layerNames = [layer.name() for layer in getVectorLayers()
                          if layer.source().lower().endswith("shp")
                          and not isTracked(layer)]
            self.layerCombo.addItems(layerNames)
            verticalLayout.addWidget(self.layerCombo)

        messageLabel = QtGui.QLabel('Message to describe this update')
        verticalLayout.addWidget(messageLabel)

        self.messageBox = QtGui.QPlainTextEdit()
        self.messageBox.textChanged.connect(self.messageHasChanged)
        verticalLayout.addWidget(self.messageBox)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Cancel)
        self.importButton = QtGui.QPushButton("Add layer")
        self.importButton.clicked.connect(self.importClicked)
        self.importButton.setEnabled(False)
        self.buttonBox.addButton(self.importButton, QtGui.QDialogButtonBox.ApplyRole)
        self.buttonBox.rejected.connect(self.cancelPressed)
        verticalLayout.addWidget(self.buttonBox)

        self.setLayout(verticalLayout)

        self.resize(400, 200)

    def messageHasChanged(self):
        self.importButton.setEnabled(self.messageBox.toPlainText() != "")


    def importClicked(self):
        if self.repo is None:
            connector = PyQtConnectorDecorator()
            connector.checkIsAlive()
            self.repo = Repository(self.repos[self.repoCombo.currentText()], connector)
        if self.layer is None:
            text = self.layerCombo.currentText()
            self.layer = resolveLayer(text)

        source = self.layer.source()
        hasIdField = self.layer.dataProvider().fieldNameIndex("geogigid") != -1

        if not hasIdField:
            autoAddId = config.getConfigValue(config.GENERAL, config.AUTO_ADD_ID)
            if not autoAddId:
                dlg = AddGeogigIdDialog(self)
                ok, check = dlg.exec_()
                if ok == QtGui.QMessageBox.No:
                    self.close()
                    return
                if check:
                    config.setConfigValue(config.GENERAL, config.AUTO_ADD_ID, True)

            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
            addIdField(self.layer)
            QtGui.QApplication.restoreOverrideCursor()
            hasIdField = self.layer.dataProvider().fieldNameIndex("geogigid") != -1
            if not hasIdField:
                QtGui.QMessageBox.warning(self, "Error",
                            "Could not add 'geogigid' field to layer.\n"
                            "Possible causes for this are:\n"
                            "- No permission to edit the layer.\n",
                            QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
                return

        self.repo.importshp(source, False, self.layer.name(), "geogigid", True)
        message = self.messageBox.toPlainText()
        self.repo.add()
        try:
            self.repo.commit(message)
        except UnconfiguredUserException, e:
            configdlg = UserConfigDialog(config.iface.mainWindow())
            configdlg.exec_()
            if configdlg.user is not None:
                self.repo.config(geogig.USER_NAME, configdlg.user)
                self.repo.config(geogig.USER_EMAIL, configdlg.email)
                self.repo.commit(message)
            else:
                return
        except GeoGigException, e:
            if "Nothing to commit" in e.args[0]:
                    config.iface.messageBar().pushMessage("No version has been created. Repository is already up to date",
                                                          level = QgsMessageBar.INFO, duration = 4)
            self.close()
            return
        except:
            self.close()
            raise

        ref = self.repo.revparse(geogig.HEAD)
        reponame = nameFromRepoPath(self.repo.url)
        addTrackedLayer(self.layer or source, reponame, self.layer.name(), ref)
        self.ok = True
        config.iface.messageBar().pushMessage("Layer was correctly added to repository",
                                                  level = QgsMessageBar.INFO, duration = 4)
        self.close()


    def cancelPressed(self):
        self.close()
