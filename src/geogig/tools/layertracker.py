import os
from qgis.core import *
from qgis.gui import *
from PyQt4 import QtCore, QtGui
from geogig.gui.dialogs.commitdialog import CommitDialog
from geogig.gui.pyqtconnectordecorator import createRepository
import logging
from geogigpy import geogig
from layertracking import getTrackingInfo, isTracked
import traceback
from geogigpy.geogigexception import UnconfiguredUserException, GeoGigException
from geogig.tools.exporter import exportVectorLayer
from geogig.tools.layertracking import setInSync, setRef
from geogigpy.py4jconnector import Py4JConnectionException
from geogig.gui.dialogs.gatewaynotavailabledialog import GatewayNotAvailableWhileEditingDialog
import uuid
from geogig.gui.dialogs.userconfigdialog import UserConfigDialog
from qgis.utils import iface
from geogig import config

_logger = logging.getLogger("geogigpy")

class LayerTracker(object):

    def __init__(self, layer):
        self.layer = layer
        self.featuresToUpdate = set()
        self.featuresToRemove = []
        self.newFeatures = []
        self.canUseSmartUpdate = True
        self.hasChanges = False
        self.rollback = False
        self.canUseSmartUpdate = config.getConfigValue(config.GENERAL, config.USE_SMART_UPDATE)

    def _featuresAdded(self, layername, features):
        self.featuresAdded(features)
    def _geomChanged(self, fid, geom):
        self.featureChanged(fid)
    def _attributeValueChanged(self, fid, idx, value):
        self.featureChanged(fid)

    def featureChanged(self, fid):
        if isTracked(self.layer):
            self.hasChanges = True
            self.featuresToUpdate.add(fid)

    def featureTypeChanged(self):
        if isTracked(self.layer):
            self.hasChanges = True
            self.canUseSmartUpdate = False

    def editingStarted(self):
        _logger.debug("Editing started for layer %s." % self.layer.name())
        self.featuresToUpdate = set()
        self.newFeatures = []
        self.featuresToRemove = []
        self.canUseSmartUpdate = config.getConfigValue(config.GENERAL, config.USE_SMART_UPDATE)
        self.hasChanges = False

    def featuresAdded(self, features):
        if not isTracked(self.layer):
            return
        self.hasChanges = True
        for feature in features:
            self.featuresToUpdate.add(feature.id())
            self.newFeatures.append(feature.id())

    def featureDeleted(self, fid):
        self.hasChanges = True
        if not isTracked(self.layer):
            return
        if not self.canUseSmartUpdate:
            return
        if fid >= 0:

            fIterator = self.layer.dataProvider().getFeatures(QgsFeatureRequest(fid));
            try:
                geogigfid = self._getFid(fIterator.next())
                self.featuresToRemove.append(geogigfid)
            except Exception, e:
                _logger.error(str(e))
                self.canUseSmartUpdate = False
                return

    def ensureUniqueIDs(self):
        self.layer.blockSignals(True)
        try:
            if self.newFeatures:
                idx = self.layer.dataProvider().fieldNameIndex("geogigid")
                self.layer.startEditing()
                for fid in self.newFeatures:
                    self.layer.changeAttributeValue(fid, idx, str(uuid.uuid4()))
                self.layer.commitChanges()
        finally:
            self.layer.blockSignals(False)


    def beforeRollBack(self):
        self.rollback = True

    def editingStopped(self):
        if self.rollback:
            _logger.debug("Editing stopped for layer '%s'. Layer changes are rolled back" % self.layer.name())
            self.rollback = False
            return
        if not isTracked(self.layer):
            _logger.debug("Editing stopped for layer '%s'. Layer is not tracked" % self.layer.name())
            return
        if not self.hasChanges:
            _logger.debug("Editing stopped for layer '%s' without changes" % self.layer.name())
            return
        _logger.debug("Editing stopped for layer '%s'." % self.layer.name())

        trackedlayer = getTrackingInfo(self.layer)
        insync = trackedlayer.insync
        setInSync(self.layer, False)

        self.ensureUniqueIDs()
        self.hasChanges = False

        autoCommit = config.getConfigValue(config.GENERAL, config.AUTO_COMMIT)
        if not autoCommit:
            return

        try:
            repo = createRepository(trackedlayer.repoFolder, False)
        except Py4JConnectionException:
            _logger.debug("Could not connect to repository for updating layer '%s'" % self.layer.name())
            QtGui.QApplication.restoreOverrideCursor()
            dlg = GatewayNotAvailableWhileEditingDialog(iface.mainWindow())
            dlg.exec_()
            setInSync(self.layer, False)
            return
        QtGui.QApplication.restoreOverrideCursor()
        if insync and self.canUseSmartUpdate:
            try:
                _logger.debug("Trying smart update on layer %s and repo %s"
                              % (self.layer.source(), trackedlayer.reponame))
                self.doSmartUpdate(trackedlayer.layername, repo)
            except Exception, e:
                _logger.error(traceback.format_exc())
                _logger.debug("Smart update failed. Using import update instead")
                self.doUpdateLayer(trackedlayer.layername, repo)
        else:
            self.doUpdateLayer(trackedlayer.layername, repo)
        unstaged = repo.difftreestats(geogig.HEAD, geogig.WORK_HEAD)
        total = 0
        for counts in unstaged.values():
            total += sum(counts)
        if total == 0:
            return
            #TODO: maybe show message dialog?
        dlg = CommitDialog(repo, iface.mainWindow())
        dlg.exec_()
        try:
            repo.addandcommit(dlg.getMessage())
        except UnconfiguredUserException, e:
            #It should not raise this exception unless config file has been manually deleted
            configdlg = UserConfigDialog(iface.mainWindow())
            configdlg.exec_()
            if configdlg.user is not None:
                repo.config(geogig.USER_NAME, configdlg.user)
                repo.config(geogig.USER_EMAIL, configdlg.email)
                repo.commit(dlg.getMessage())
            else:
                return
        headid = repo.revparse(geogig.HEAD)
        setRef(self.layer, headid)
        iface.messageBar().pushMessage("Repository correctly updated",
                                                  level = QgsMessageBar.INFO, duration = 4)
        setInSync(self.layer, True)


    def _getFid(self, feature):
        try:
            return  feature['geogigid']
        except:
            raise Exception("No ID field found in layer")


    def doSmartUpdate(self, dest, repo):
        features = {}
        geomField = "geom"
        try:
            ftype = repo.featuretype(geogig.HEAD, dest)
            for fieldName, fieldType in ftype.iteritems():
                if fieldType in geogig.GEOMTYPES:
                    geomField = fieldName
                    break
        except GeoGigException, e:
            pass

        for fid in self.featuresToUpdate:
            fIterator = self.layer.getFeatures(QgsFeatureRequest(fid));
            try:
                feature = fIterator.next()
            except StopIteration, e: # might happen if a newly added feature is then edited
                continue #we just ignore the feature, since it will be added anyway
            geom = feature.geometry()
            wkt = geom.exportToWkt()
            geogigfid = unicode(self._getFid(feature))
            geogigfid = dest + "/" + geogigfid
            attrValues = [f if not isinstance(f, QtCore.QPyNullVariant) else None for f in feature.attributes() ]
            attributes = dict(zip([f.name() for f in feature.fields()], attrValues))
            attributes[geomField] = str(wkt)
            features[geogigfid] = attributes
        if features:
            repo.insertfeatures(features)

        toRemove = [dest + "/" + unicode(fid) for fid in self.featuresToRemove]
        if toRemove:
            repo.removefeatures(toRemove)


    def doUpdateLayer(self, dest, repo):
        if self.layer.dataProvider().fieldNameIndex("geogigid") == -1:
            iface.messageBar().pushMessage("Cannot update GeoGig repository. Layer has no 'geogigid' field",
                                                      level = QgsMessageBar.WARNING, duration = 4)
        else:
            exported = exportVectorLayer(self.layer)
            repo.importshp(exported, False, dest, "geogigid", True)
            setInSync(self.layer, True)

