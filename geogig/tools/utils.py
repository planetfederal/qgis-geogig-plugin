# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import os
import uuid
import time
from qgis.core import *
import tempfile
import shutil
import dateutil.parser
from datetime import tzinfo, timedelta, datetime
from geogig import config
from PyQt4 import QtCore
from geogig.gui.pyqtconnectordecorator import PyQtConnectorDecorator
from geogigpy.repo import Repository

def userFolder():
    folder = os.path.join(os.path.expanduser('~'), 'geogig')
    mkdir(folder)
    return folder

def parentReposFolder():
    folder = config.getConfigValue(config.GENERAL, config.REPOS_FOLDER)
    if folder.strip() == "":
        folder = os.path.join(os.path.expanduser('~'), 'geogig', 'repos')
    mkdir(folder)
    return folder

def repoFolder(reponame):
    return os.path.join(parentReposFolder(), reponame)

_tempFolder = None
def tempFolder():
    global _tempFolder
    if _tempFolder is None:
        _tempFolder = tempfile.mkdtemp()
    return _tempFolder

def deleteTempFolder():
    if _tempFolder is not None:
        shutil.rmtree(_tempFolder, True)

def tempFilename(ext):
    path = tempFolder()
    ext = "" if ext is None else ext
    filename = path + os.sep + str(time.time()) + "." + ext
    return filename

def tempFilenameInTempFolder(basename):
    '''returns a temporary filename for a given file, putting it into a temp folder but not changing its basename'''
    path = tempFolder()
    folder = os.path.join(path, str(uuid.uuid4()).replace("-", ""))
    mkdir(folder)
    filename = os.path.join(folder, basename)
    return filename

def mkdir(newdir):
    if os.path.isdir(newdir):
        pass
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            mkdir(head)
        if tail:
            os.mkdir(newdir)

def repoPaths():
    'returns a dict with titles as keys and folders as values'
    repos = {}
    parentFolder = parentReposFolder()
    subfolders = [os.path.join(parentFolder, subfolder) for subfolder
                  in os.listdir(parentFolder)
                  if os.path.isdir(os.path.join(parentFolder, subfolder))]
    for subfolder in subfolders:
        titlefile = os.path.join(subfolder, "title")
        geogigfolder = os.path.join(subfolder, ".geogig")
        if os.path.exists(geogigfolder):
            if os.path.exists(titlefile):
                with open(titlefile) as f:
                    title = f.readline()
            else:
                title = os.path.basename(subfolder)
            repos[title] = subfolder
    return repos



def getRepoTitle(repo):
    titlefile = os.path.join(repo.url, "title")
    if os.path.exists(titlefile):
        with open(titlefile) as f:
            title = f.readline()
    else:
        title = os.path.basename(repo.url)
    return title

def relativeDate(s):
    d = dateutil.parser.parse(s)
    try:
        now = datetime.now()
        diff = now - d
    except TypeError:
        ZERO = timedelta(0)
        class UTC(tzinfo):
            def utcoffset(self, dt):
                return ZERO
            def tzname(self, dt):
                return "UTC"
            def dst(self, dt):
                return ZERO
        utc = UTC()
        now = datetime.now(utc)
        diff = now - d
    s = ''
    secs = diff.seconds
    if diff.days == 1:
        s = "1 day ago"
    elif diff.days > 1:
        s = "{} days ago".format(diff.days)
    elif secs < 120:
        s = "1 minute ago"
    elif secs < 3600:
        s = "{} minutes ago".format(secs / 60)
    elif secs < 7200:
        s = "1 hour ago"
    else:
        s = '{} hours ago'.format(secs / 3600)
    return s

def resourceFile(f):
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", f)

def nameFromRepoPath(path):
    return os.path.basename(path)

def userFromRepoPath(path):
    return os.path.basename(os.path.dirname(os.path.dirname(path)))

def ownerFromRepoPath(path):
    return os.path.basename(os.path.dirname(path))

def loadLayerNoCrsDialog(filename, layername, provider):
    settings = QtCore.QSettings()
    prjSetting = settings.value('/Projections/defaultBehaviour')
    settings.setValue('/Projections/defaultBehaviour', '')
    layer = QgsVectorLayer(filename, layername, provider)
    settings.setValue('/Projections/defaultBehaviour', prjSetting)
    return layer


def createRepo(title):
    safeName = "".join(x for x in title if x.isalnum())
    path = os.path.join(repoFolder(safeName))
    repo = Repository(path, PyQtConnectorDecorator(), True)
    filename = os.path.join(path, "title")
    with open(filename, "w") as f:
        f.write(title)
    return repo
