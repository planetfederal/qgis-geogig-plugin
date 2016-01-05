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

def openNavigator(folder):
    global _navigatorDialog
    global _oldReposPath
    global _tempReposPath
    _oldReposPath = config.getConfigValue(config.GENERAL, config.REPOS_FOLDER)
    reposPath = os.path.join(os.path.dirname(__file__), "data", "repos", folder)
    _tempReposPath = tempfile.mkdtemp()
    tempReposPath = os.path.join(_tempReposPath, "repos")
    shutil.copytree(reposPath, tempReposPath)
    config.setConfigValue(config.GENERAL, config.REPOS_FOLDER, tempReposPath)
    _navigatorDialog = NavigatorDialog()
    _navigatorDialog.show()

def closeNavigatorAndRemoveTempRepoFolder():
    global _navigatorDialog
    if _navigatorDialog is not None:
        _navigatorDialog.close()
        _navigatorDialog = None
    config.setConfigValue(config.GENERAL, config.REPOS_FOLDER, _oldReposPath)
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
    qgis.utils.iface.newProject()
    if _tempReposPath is not None:
        shutil.rmtree(_tempReposPath, ignore_errors = True)

#TESTS

def _checkLayerInRepo():
    from qgistester.utils import layerFromName
    layer = layerFromName("points")
    tracking = getTrackingInfo(layer)
    assert tracking is not None
    connector = PyQtConnectorDecorator()
    connector.checkIsAlive()
    repo =  Repository(tracking.repoFolder(), connector)
    layers = [tree.path for tree in repo.trees]
    assert "points" in layers
    removedTrackedLayer(layer)

def _checkLayerInProject():
    from qgistester.utils import layerFromName
    layer = layerFromName("points")
    assert layer is not None



def functionalTests():
    try:
        from qgistester.test import Test
        from qgistester.utils import layerFromName
    except:
        return []

    tests = []
    test = Test("Create new repository")
    test.addStep("Open navigator", lambda: openNavigator("new"))
    test.addStep("Create new repo and verify it is correctly added to the list")
    test.setCleanup(closeNavigatorAndRemoveTempRepoFolder)
    tests.append(test)

    test = Test("Create new repository with existing name")
    test.addStep("Open navigator", lambda: openNavigator("emptyrepo"))
    test.addStep("Create new repo named 'testrepo' and verify it cannot be created")
    test.setCleanup(closeNavigatorAndRemoveTempRepoFolder)
    tests.append(test)

    test = Test("Change repository title")
    test.addStep("Open navigator", lambda: openNavigator("emptyrepo"))
    test.addStep("Edit repository title and check it is updated in the repo summary")
    test.setCleanup(closeNavigatorAndRemoveTempRepoFolder)
    tests.append(test)

    test = Test("Delete repository")
    test.addStep("Open navigator", lambda: openNavigator("emptyrepo"))
    test.addStep("Delete repository and check it is removed from the list")
    test.setCleanup(closeNavigatorAndRemoveTempRepoFolder)
    tests.append(test)

    test = Test("Add layer to repository")
    test.addStep("Open navigator", lambda: openNavigator("emptyrepo"))
    test.addStep("Open test data", lambda: openTestProject("points"))
    test.addStep("Add layer 'points' to the 'testrepo' repository")
    test.addStep("Check layer has been added to repo", _checkLayerInRepo)
    test.setCleanup(closeNavigatorAndRemoveTempRepoFolder)
    tests.append(test)


    test = Test("Open repository layers in QGIS")
    test.addStep("Open navigator", lambda: openNavigator("pointsrepo"))
    test.addStep("New project", qgis.utils.iface.newProject)
    test.addStep("Select the 'testrepo' repository and click on 'Open repository in QGIS'")
    test.addStep("Check layer has been added to project", _checkLayerInProject)
    test.setCleanup(closeNavigatorAndRemoveTempRepoFolder)
    tests.append(test)

    test = Test("Update repository when there are no changes")
    test.addStep("New project", qgis.utils.iface.newProject)
    test.addStep("Export repo layers", lambda:_exportRepoLayers("pointsrepo", "repo"))
    test.addStep("Right click on 'points' layer and select 'GeoGig/Update repository with this version'\n"
                 "Verify that the plugin shows that there are no changes to add")
    test.setCleanup(_cleanRepoClone)
    tests.append(test)

    test = Test("Modify geometry and create new version")
    tests.append(test)
    test = Test("Modify attributes and create new version")
    tests.append(test)
    test = Test("Delete feature and create new version")
    tests.append(test)
    test = Test("Add feature and create new version")
    tests.append(test)
    test = Test("Add layer to repository from context menu")
    tests.append(test)
    test = Test("Remove layer from repository")
    tests.append(test)

    return tests

def unitTests():
    _tests = []
    #_tests.extend(pkiSuite())
    return _tests