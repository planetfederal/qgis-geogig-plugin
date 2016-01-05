import logging
from geogigpy import geogig
from layertracking import isTracked
from geogigpy.py4jconnector import Py4JConnectionException
import uuid


_logger = logging.getLogger("geogigpy")

class LayerTracker(object):

    def __init__(self, layer):
        self.layer = layer
        self.newFeatures = []

    def _featuresAdded(self, layername, features):
        self.featuresAdded(features)

    def editingStarted(self):
        self.newFeatures = []

    def featuresAdded(self, features):
        if not isTracked(self.layer):
            return
        for feature in features:
            self.newFeatures.append(feature.id())

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


    def editingStopped(self):
        self.ensureUniqueIDs()

