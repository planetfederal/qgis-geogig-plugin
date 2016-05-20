# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
'''
This module provides methods to export layers so they can be used as valid data
for importing to GeoGig.

It also includes method to export from GeoGig to QGIS
'''

import utils
import logging
from qgis.core import *
from geogig.tools.layertracking import (addTrackedLayer,
                getTrackingInfoForGeogigLayer, setRef, getTrackedPathsForRepo)
import os
from geogigpy import geogig
from geogig.tools.utils import tempFolder, ownerFromRepoPath, userFromRepoPath, \
    nameFromRepoPath, loadLayerNoCrsDialog
from geogigpy.geogigexception import GeoGigException
from geogig.tools.layers import resolveLayerFromSource, WrongLayerSourceException
import re
from PyQt4 import QtCore

_logger = logging.getLogger("geogigpy")

def exportVectorLayer(layer):
    '''accepts a QgsVectorLayer'''
    settings = QtCore.QSettings()
    filename = unicode(layer.source())
    destFilename = unicode(layer.name())
    if not filename.lower().endswith("shp"):
        output = utils.tempFilenameInTempFolder(destFilename + ".shp")
        provider = layer.dataProvider()
        fields = layer.pendingFields()
        writer = QgsVectorFileWriter(output, "utf-8", fields, provider.geometryType(), layer.crs())
        for feat in layer.getFeatures():
            writer.addFeature(feat)
        del writer
        return output, "utf-8"
    else:
        # determine encoding
        # first look in .cpg file
        cpgPath = filename.replace('.shp', '.cpg')
        if os.path.exists(cpgPath):
            with open(cpgPath) as f:
                charset = f.readline().strip('\r\n')
        else:
            # try to get encoding from provider
            charset = self.layer.dataProvider().encoding()
            if charset.lower() == 'system':
                # get encoding from system
                charset = locale.getpreferredencoding()

        return filename, charset

def exportFullRepo(repo, ref = geogig.HEAD):
    trees = repo.trees
    ref = repo.revparse(ref)
    for tree in trees:
        trackedlayer = getTrackingInfoForGeogigLayer(repo.url, tree.path)
        if trackedlayer is None or not os.path.exists(trackedlayer.source):
            filepath = os.path.join(repo.url, tree.path + ".shp")
            repo.exportshp(ref, tree.path, filepath, "utf-8")
            addTrackedLayer(filepath, repo.url, tree.path, ref)
        elif trackedlayer.ref != ref:
            repo.exportshp(ref, tree.path, trackedlayer.source, "utf-8")
            setRef(trackedlayer.source, ref)

def exportAndLoadVersion(commit):
    trees = commit.root.trees
    layers = []
    for tree in trees:
        filepath = os.path.join(tempFolder(), "%s_%s.shp" % (tree.path, commit.commitid))
        if not os.path.exists(filepath):
            commit.repo.exportshp(commit.commitid, tree.path, filepath, "utf-8")
        layer = loadLayerNoCrsDialog(filepath, tree.path + "_[%s]" % commit.commitid[:8], "ogr")
        layer.setReadOnly(True)
        layers.append(layer)
    QgsMapLayerRegistry.instance().addMapLayers(layers)

resourcesPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources")
ptStyleAfter = os.path.join(resourcesPath, "pt_after.qml")
lineStyleAfter = os.path.join(resourcesPath, "line_after.qml")
polygonStyleAfter = os.path.join(resourcesPath, "polygon_after.qml")
ptStyleBefore = os.path.join(resourcesPath, "pt_before.qml")
lineStyleBefore = os.path.join(resourcesPath, "line_before.qml")
polygonStyleBefore = os.path.join(resourcesPath, "polygon_before.qml")
styles = [(ptStyleBefore, ptStyleAfter), (lineStyleBefore, lineStyleAfter),
                  (polygonStyleBefore, polygonStyleAfter)]

def exportVersionDiffs(commita, commitb = None):
    layers = {}
    if commitb is None:
        commitb = commita
        commita = commita.parent
    layernames = commita.repo.difftreestats(commita, commitb).keys()
    name = "%s_%s" % (commita.id[:8], commitb.id[:8])
    for layername in layernames:
        layers[layername] = []
        filepath = os.path.join(tempFolder(), "diff_%s_%s_before.shp" % (layername, name))
        try:
            if not os.path.exists(filepath):
                commita.repo.exportdiffs(commita, commitb, layername, filepath, True, True, "utf-8")
            beforeLayer = loadLayerNoCrsDialog(filepath, layername + "_[%s][before]" % name, "ogr")
            beforeLayer.setReadOnly(True)
            vectorType = beforeLayer.geometryType()
            styleBefore, _ = styles[vectorType]
            beforeLayer.loadNamedStyle(styleBefore)
            layers[layername].append(beforeLayer)
        except GeoGigException:
            layers[layername].append(None)
        try:
            filepath = os.path.join(tempFolder(), "diff_%s_%s_after.shp" % (layername, name))
            if not os.path.exists(filepath):
                commitb.repo.exportdiffs(commita, commitb, layername, filepath, False, True, "utf-8")
            afterLayer = loadLayerNoCrsDialog(filepath, layername + "_[%s][after]" % name, "ogr")
            afterLayer.setReadOnly(True)
            vectorType = afterLayer.geometryType()
            _, styleAfter = styles[vectorType]
            afterLayer.loadNamedStyle(styleAfter)
            layers[layername].append(afterLayer)
        except GeoGigException:
            layers[layername].append(None)
    return layers


def loadRepoExportedLayers(repo):
    paths = getTrackedPathsForRepo(repo)
    layers = []
    for f in paths:
        try:
            layer = resolveLayerFromSource(f)
            layer.reload()
            layer.triggerRepaint()
        except WrongLayerSourceException:
            layername = os.path.splitext(os.path.basename(f))[0]
            layer = loadLayerNoCrsDialog(f, layername, "ogr")
            layers.append(layer)
    if layers:
        QgsMapLayerRegistry.instance().addMapLayers(layers)


def exportVectorLayerAddingId(layer, fid):
    '''accepts a QgsVectorLayer'''
    settings = QtCore.QSettings()
    destFilename = unicode(layer.name())
    output = utils.tempFilenameInTempFolder(destFilename + ".shp")
    provider = layer.dataProvider()
    fields = layer.pendingFields()
    fieldsInFid = re.findall("\[.*?\]", fid)
    fidattrs = {}
    for field in fieldsInFid:
        name = field[1:-1]
        idx = provider.fieldNameIndex(name)
        if idx == -1:
            raise Exception("Field %s not found in layer" % name)
        fidattrs[field] = idx
    fields.append(QgsField("geogigid", QtCore.QVariant.String))
    writer = QgsVectorFileWriter(output, "utf-8", fields, provider.geometryType(), layer.crs())
    outFeat = QgsFeature()
    for feat in layer.getFeatures():
        inGeom = feat.geometry()
        outFeat.setGeometry(inGeom)
        attrs = feat.attributes()
        if fid:
            geogitid = fid
            for k, v in fidattrs.iteritems():
                geogitid = geogitid.replace(k, unicode(attrs[v]))
        else:
            geogitid = str(hash(tuple(attrs)))
        attrs.append(geogitid)
        outFeat.setAttributes(attrs)
        writer.addFeature(outFeat)
        writer.addFeature(feat)
    del writer
    return output, "utf-8"
