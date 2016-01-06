from qgis.core import *
from PyQt4 import QtCore
import uuid
import os
from qgis.utils import iface

ALL_TYPES = -1

class WrongLayerNameException(BaseException) :
    pass

class WrongLayerSourceException(BaseException) :
    pass

def resolveLayer(name):
    layers = getAllLayers()
    for layer in layers:
        if layer.name() == name:
            return layer
    raise WrongLayerNameException()

def resolveLayerFromSource(source):
    layers = getAllLayers()
    for layer in layers:
        if os.path.normcase(layer.source()) == os.path.normcase(source):
            return layer
    raise WrongLayerSourceException()


def getVectorLayers(shapetype = -1):
    layers = iface.legendInterface().layers()
    vector = list()
    for layer in layers:
        if layer.type() == layer.VectorLayer:
            if shapetype == ALL_TYPES or layer.geometryType() == shapetype:
                uri = unicode(layer.source())
                if not uri.lower().endswith("csv") and not uri.lower().endswith("dbf"):
                    vector.append(layer)
    return vector

def getAllLayers():
    return getVectorLayers()

def getGroups():
    groups = {}
    rels = iface.legendInterface().groupLayerRelationship()
    for rel in rels:
        groupName = rel[0]
        if groupName != '':
            groupLayers = rel[1]
            groups[groupName] = [QgsMapLayerRegistry.instance().mapLayer(layerid) for layerid in groupLayers]
    return groups

def setIdEditWidget(layer):
    provider = layer.dataProvider()
    idx = provider.fieldNameIndex("geogigid")
    if idx != -1:
        layer.setFieldEditable(idx, False)
        layer.setEditorWidgetV2(idx, "UuidGenerator")

def addIdField(layer):
    layer.blockSignals(True)
    try:
        provider = layer.dataProvider()
        provider.addAttributes([QgsField("geogigid", QtCore.QVariant.String)])
        layer.updateFields()
        idx = provider.fieldNameIndex("geogigid")
        layer.startEditing()
        features = layer.getFeatures()
        for feature in features:
            fid = int(feature.id())
            layer.changeAttributeValue(fid, idx, str(uuid.uuid4()))
        layer.commitChanges()
        setIdEditWidget(layer)
    finally:
        layer.blockSignals(False)


