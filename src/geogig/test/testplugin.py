import qgis.utils
import os
from geogig.gui.dialogs.navigatordialog import NavigatorDialog
from geogig import config
import shutil
import tempfile
from qgis.core import *
from geogig.tools.layertracking import getTrackingInfo, removeTrackedLayer
from geogig.gui.pyqtconnectordecorator import PyQtConnectorDecorator
from geogigpy.repo import Repository
from tools.exporter import exportFullRepo
from geogigpy.commitish import Commitish
try:
    from qgistester.utils import layerFromName
except:
    pass

# Tests for the QGIS Tester plugin. To know more see
# https://github.com/boundlessgeo/qgis-tester-plugin


#Some common methods
#-------------------

def openTestProject(name):
    projectFile = os.path.join(os.path.dirname(__file__), "data", "layers", name + ".qgs")
    if projectFile != QgsProject.instance().fileName():
        qgis.utils.iface.addProject(projectFile)

_navigatorDialog = None
_oldReposPath = None
_tempReposPath = None

def _setReposFolder(folder):

    global _oldReposPath
    global _tempReposPath
    _oldReposPath = config.getConfigValue(config.GENERAL, config.REPOS_FOLDER)
    reposPath = os.path.join(os.path.dirname(__file__), "data", "repos", folder)
    _tempReposPath = tempfile.mkdtemp()
    tempReposPath = os.path.join(_tempReposPath, "repos")
    shutil.copytree(reposPath, tempReposPath)
    config.setConfigValue(config.GENERAL, config.REPOS_FOLDER, tempReposPath)

def _restoreReposFolder():
    config.setConfigValue(config.GENERAL, config.REPOS_FOLDER, _oldReposPath)

def _openNavigator(folder):
    global _navigatorDialog
    _setReposFolder(folder)
    _navigatorDialog = NavigatorDialog()
    _navigatorDialog.show()

def _closeNavigatorAndRemoveTempRepoFolder():
    global _navigatorDialog
    if _navigatorDialog is not None:
        _navigatorDialog.close()
        _navigatorDialog = None
    _restoreReposFolder()
    shutil.rmtree(_tempReposPath, ignore_errors = True)

def _exportRepoLayers(reposFolder, repoFolder):
    global _tempReposPath
    _tempReposPath = os.path.join(tempfile.mkdtemp())
    tempRepoPath = os.path.join(_tempReposPath, repoFolder)
    repoPath = os.path.join(os.path.dirname(__file__), "data", "repos", reposFolder, repoFolder)
    shutil.copytree(repoPath, tempRepoPath)
    connector = PyQtConnectorDecorator()
    connector.checkIsAlive()
    repo =  Repository(tempRepoPath, connector)
    exportFullRepo(repo)
    layerPath = os.path.join(tempRepoPath, "points.shp")
    layer = QgsVectorLayer(layerPath, "points", 'ogr')
    QgsMapLayerRegistry.instance().addMapLayers([layer], True)

def _cleanRepoClone():
    _restoreReposFolder()
    qgis.utils.iface.newProject()
    if _tempReposPath is not None:
        shutil.rmtree(_tempReposPath, ignore_errors = True)

#TESTS

def _checkLayerInRepo():
    layer = layerFromName("points")
    tracking = getTrackingInfo(layer)
    assert tracking is not None
    connector = PyQtConnectorDecorator()
    connector.checkIsAlive()
    repo =  Repository(tracking.repoFolder, connector)
    layers = [tree.path for tree in repo.trees]
    assert "points" in layers
    removedTrackedLayer(layer)

def _checkLayerNotInRepo():
    layer = layerFromName("points")
    tracking = getTrackingInfo(layer)
    assert tracking is None
    connector = PyQtConnectorDecorator()
    connector.checkIsAlive()
    repo =  Repository(os.path.join(_tempReposPath, "pointsrepo"), connector)
    layers = [tree.path for tree in repo.trees]
    assert "points" not in layers

def _checkLayerInProject():
    layer = layerFromName("points")
    assert layer is not None

def _modifyFeature():
    layer = layerFromName("points")
    feature = layer.getFeatures().next()
    fid = feature.id()
    layer.startEditing()
    layer.changeAttributeValue(fid, 0, "100")
    layer.commitChanges()

def _checkFeatureModifiedInRepo():
    connector = PyQtConnectorDecorator()
    connector.checkIsAlive()
    repo =  Repository(os.path.join(_tempReposPath, "repo"), connector)
    diffs = repo.diff("master", Commitish(repo, "master").parent.ref)
    assert 1 == len(diffs)
    layer = layerFromName("points")
    feature = layer.getFeatures().next()
    geogigid = str(feature[1])
    assert "points/" + geogigid == diffs[0].path

def _addFeature():
    pass

def _checkFeatureAddedInRepo():
    pass


def functionalTests():
    try:
        from qgistester.test import Test
    except:
        return []

    tests = []
    test = Test("Create new repository")
    test.addStep("Open navigator", lambda: _openNavigator("new"))
    test.addStep("Create new repo and verify it is correctly added to the list")
    test.setCleanup(_closeNavigatorAndRemoveTempRepoFolder)
    tests.append(test)

    test = Test("Create new repository with existing name")
    test.addStep("Open navigator", lambda: _openNavigator("emptyrepo"))
    test.addStep("Create new repo named 'testrepo' and verify it cannot be created")
    test.setCleanup(_closeNavigatorAndRemoveTempRepoFolder)
    tests.append(test)

    test = Test("Change repository title")
    test.addStep("Open navigator", lambda: _openNavigator("emptyrepo"))
    test.addStep("Edit repository title and check it is updated in the repo summary")
    test.setCleanup(_closeNavigatorAndRemoveTempRepoFolder)
    tests.append(test)

    test = Test("Delete repository")
    test.addStep("Open navigator", lambda: _openNavigator("emptyrepo"))
    test.addStep("Delete repository and check it is removed from the list")
    test.setCleanup(_closeNavigatorAndRemoveTempRepoFolder)
    tests.append(test)

    test = Test("Add layer to repository")
    test.addStep("Open navigator", lambda: _openNavigator("emptyrepo"))
    test.addStep("Open test data", lambda: openTestProject("points"))
    test.addStep("Add layer 'points' to the 'testrepo' repository")
    test.addStep("Check layer has been added to repo", _checkLayerInRepo)
    test.setCleanup(_closeNavigatorAndRemoveTempRepoFolder)
    tests.append(test)


    test = Test("Open repository layers in QGIS")
    test.addStep("Open navigator", lambda: _openNavigator("pointsrepo"))
    test.addStep("New project", qgis.utils.iface.newProject)
    test.addStep("Select the 'testrepo' repository and click on 'Open repository in QGIS'")
    test.addStep("Check layer has been added to project", _checkLayerInProject)
    test.setCleanup(_closeNavigatorAndRemoveTempRepoFolder)
    tests.append(test)

    test = Test("Update repository when there are no changes")
    test.addStep("New project", qgis.utils.iface.newProject)
    test.addStep("Export repo layers", lambda:_exportRepoLayers("pointsrepo", "repo"))
    test.addStep("Right click on 'points' layer and select 'GeoGig/Update repository with this version'\n"
                 "Verify that the plugin shows that there are no changes to add")
    test.setCleanup(_cleanRepoClone)
    tests.append(test)

    test = Test("Modify feature and create new version")
    test.addStep("New project", qgis.utils.iface.newProject)
    test.addStep("Export repo layers", lambda:_exportRepoLayers("pointsrepo", "repo"))
    test.addStep("Edit layer", _modifyFeature)
    test.addStep("Right click on 'points' layer and select 'GeoGig/Update repository with this version'")
    test.addStep("Check layer has been updated", _checkFeatureModifiedInRepo)
    test.setCleanup(_cleanRepoClone)
    tests.append(test)

    test = Test("Add feature and create new version")
    test.addStep("New project", qgis.utils.iface.newProject)
    test.addStep("Export repo layers", lambda:_exportRepoLayers("pointsrepo", "repo"))
    test.addStep("Edit layer", _addFeature)
    test.addStep("Right click on 'points' layer and select 'GeoGig/Update repository with this version'")
    test.addStep("Check layer has been updated", _checkFeatureAddedInRepo)
    test.setCleanup(_cleanRepoClone)
    tests.append(test)

    test = Test("Add layer to repository from context menu")
    test.addStep("Open test data", lambda: openTestProject("points"))
    test.addStep("Set repos folder", _setReposFolder("emptyrepo"))
    test.addStep("Add layer using context menu")
    test.addStep("Check layer has been added to repo", _checkLayerInRepo)
    test.setCleanup(_cleanRepoClone)
    tests.append(test)

    test = Test("Remove layer from repository")
    test.addStep("New project", qgis.utils.iface.newProject)
    test.addStep("Export repo layers", lambda:_exportRepoLayers("pointsrepo", "repo"))
    test.addStep("Right click on 'points' layer and select 'GeoGig/Remove layer from repository'")
    test.addStep("Check layer has been correctly deleted", _checkLayerNotInRepo)
    test.setCleanup(_cleanRepoClone)
    tests.append(test)

    return tests

def unitTests():
    _tests = []
    #_tests.extend(pkiSuite())
    return _tests