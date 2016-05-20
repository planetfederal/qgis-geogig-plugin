# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import os
from qgis.core import *
from geogig.tools.utils import userFolder, repoFolder
import json
from json.decoder import JSONDecoder
from json.encoder import JSONEncoder
from geogig.tools.layers import  resolveLayerFromSource, \
    WrongLayerSourceException
from geogigpy.repo import Repository
from geogigpy import geogig
from PyQt4 import QtGui
from geogig import config
from geogig.tools.utils import loadLayerNoCrsDialog

tracked = []

class Encoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

def decoder(jsonobj):
    if 'source' in jsonobj:
        return TrackedLayer(jsonobj['source'],
                            jsonobj['repoFolder'], jsonobj['layername'],
                            jsonobj['ref'])
    else:
        return jsonobj

class TrackedLayer(object):
    def __init__(self, source, repoFolder, layername, ref):
        self.repoFolder = repoFolder
        self.layername = layername
        self.ref = ref
        self.source = source


def setRef(layer, ref):
    source = _formatSource(layer)
    for obj in tracked:
        if obj.source == source:
            obj.ref = ref
    saveTracked()


def addTrackedLayer(source, repoFolder, layername, ref):
    global tracked
    source = _formatSource(source)
    layer = TrackedLayer(source, repoFolder, layername, ref)
    if layer not in tracked:
        for lay in tracked:
            if lay.source == source:
                tracked.remove(lay)
        tracked.append(layer)
        saveTracked()


def removeTrackedLayer(layer):
    global tracked
    source = _formatSource(layer)
    for i, obj in enumerate(tracked):
        if obj.source == source:
            del tracked[i]
            saveTracked()
            return

def removeTrackedForRepo(repoFolder):
    global tracked
    for i in xrange(len(tracked) - 1, -1, -1):
        layer = tracked[i]
        if layer.repoFolder == repoFolder:
            del tracked[i]
    saveTracked()

def removeNonexistentTrackedLayers():
    global tracked
    for i in xrange(len(tracked) - 1, -1, -1):
        layer = tracked[i]
        if not os.path.exists(layer.source):
            del tracked[i]
    saveTracked()

def saveTracked():
    filename = os.path.join(userFolder(), "trackedlayers")
    with open(filename, "w") as f:
        f.write(json.dumps(tracked, cls = Encoder))

def readTrackedLayers():
    try:
        global tracked
        filename = os.path.join(userFolder(), "trackedlayers")
        if os.path.exists(filename):
            with open(filename) as f:
                lines = f.readlines()
            jsonstring = "\n".join(lines)
            if jsonstring:
                tracked = JSONDecoder(object_hook = decoder).decode(jsonstring)
    except KeyError:
        pass

def isTracked(layer):
    return getTrackingInfo(layer) is not None

def getTrackingInfo(layer):
    source = _formatSource(layer)
    for obj in tracked:
        if obj.source == source:
            return obj

def getTrackingInfoForGeogigLayer(repoFolder, layername):
    for t in tracked:
        if (t.repoFolder == repoFolder and t.layername == layername):
            return t

def getTrackedPathsForRepo(repo):
    repoLayers = [tree.path for tree in repo.trees]
    trackedPaths = [layer.source for layer in tracked
                if repo.url == layer.repoFolder and layer.layername in repoLayers]
    return trackedPaths

def updateTrackedLayers(repo):
    head = repo.revparse(geogig.HEAD)
    repoLayers = [tree.path for tree in repo.trees]
    repoLayersInProject = False
    notLoaded = []
    toUnload = []
    for trackedlayer in tracked:
        if trackedlayer.repoFolder == repo.url:
            if trackedlayer.layername in repoLayers:
                if (trackedlayer.ref != head
                            or not os.path.exists(trackedlayer.source)):
                    repo.exportshp(geogig.HEAD, trackedlayer.layername, trackedlayer.source, 'utf-8')
                    try:
                        layer = resolveLayerFromSource(trackedlayer.source)
                        layer.reload()
                        layer.triggerRepaint()
                        repoLayersInProject = True
                    except WrongLayerSourceException:
                        notLoaded.append(trackedlayer)
                    trackedlayer.ref = head
                else:
                    try:
                        layer = resolveLayerFromSource(trackedlayer.source)
                        repoLayersInProject = True
                    except WrongLayerSourceException:
                        notLoaded.append(trackedlayer)
            else:
                try:
                    layer = resolveLayerFromSource(trackedlayer.source)
                    toUnload.append(layer)
                except WrongLayerSourceException:
                    pass
    saveTracked()
    if repoLayersInProject:
        if notLoaded:
            ret = QtGui.QMessageBox.warning(config.iface.mainWindow(), "Update layers",
                        "The current QGIS project only contains certain layers from the\n"
                        "current version of the repository.\n"
                        "Do you want to load the remaining ones?",
                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                        QtGui.QMessageBox.Yes);
            if ret == QtGui.QMessageBox.Yes:
                layersToLoad = []
                for layer in notLoaded:
                    layersToLoad.append(loadLayerNoCrsDialog(layer.source, layer.layername, "ogr"))
                QgsMapLayerRegistry.instance().addMapLayers(layersToLoad)
        if toUnload:
            ret = QtGui.QMessageBox.warning(config.iface.mainWindow(), "Update layers",
                        "The following layers are not present anymore in the repository:\n"
                        "\t- " + "\n\t- ".join([layer.name() for layer in toUnload]) +
                        "\nDo you want to remove them from the current QGIS project?",
                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                        QtGui.QMessageBox.Yes);
            if ret == QtGui.QMessageBox.Yes:
                for layer in toUnload:
                    QgsMapLayerRegistry.instance().removeMapLayer(layer.id())
        config.iface.mapCanvas().refresh()

def _formatSource(obj):
    if isinstance(obj, QgsVectorLayer):
        if obj.dataProvider().name() == "postgres":
            uri = QgsDataSourceURI(obj.dataProvider().dataSourceUri())
            return " ".join([uri.database(), uri.schema(), uri.table()])
        else:
            return os.path.normcase(obj.source())
    else:
        return os.path.normcase(unicode(obj))



