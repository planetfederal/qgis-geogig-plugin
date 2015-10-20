from qgis.core import *
from versio.tools.versioinstance import config
from PyQt4 import QtCore
from versio.tools.postgis_utils import GeoDB, TableConstraint, TableField
from versio.gui.dialogs.userpasswd import UserPasswordDialog
import uuid
import os

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
    layers = config.iface.legendInterface().layers()
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
    rels = config.iface.legendInterface().groupLayerRelationship()
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
        layer.setEditType(idx, QgsVectorLayer.UuidGenerator)


def addIdField(layer):
    layer.blockSignals(True)
    try:
        provider = layer.dataProvider()
        caps = provider.capabilities()
        if provider.name() == "postgres":
            uri = QgsDataSourceURI(provider.dataSourceUri())
            username, password = getDatabaseCredentials(uri)
            db = GeoDB(uri.host(), int(uri.port()), uri.database(), username, password)
            db.table_add_geogigid_column(uri.schema(), uri.table())
            layer.reload()
            setIdEditWidget(layer)
        elif caps & QgsVectorDataProvider.AddAttributes:
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

_credentials = {}

def getDatabaseCredentials(uri):
    if uri.password() and uri.username():
        return uri.username(), uri.password()
    global _credentials
    if uri.database() in _credentials:
        return _credentials[uri.database()]
    dlg = UserPasswordDialog(title = "Credentials for PostGIS layer")
    dlg.exec_()
    if dlg.user is None:
        return None, None
    u = dlg.user
    p = dlg.password
    _credentials[uri.database()] = (u, p)
    return u, p

def removeCredentials(database):
    global _credentials
    if database in _credentials:
        del _credentials[database]

