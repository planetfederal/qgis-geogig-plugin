# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
import os
from PyQt4 import QtCore
from geogigpy import geogig
from geogigpy.py4jconnector import Py4JCLIConnector

iface = None
explorer = None

GENERAL = "General"


GATEWAY_PORT = "GatewayPort"
AUTO_ADD_ID = "AutoAddId"
VERSIO_ENDPOINT = "VersioEndpoint"
USE_THREAD = "UseThread"
USE_MAIN_MENUBAR = "UseMainMenuBar"
REPOS_FOLDER = "ReposFolder"
TIMEOUT = "Timeout"
USE_SMART_UPDATE = "SmartUpdate"
AUTO_COMMIT = "AutoCommit"
USERNAME = "Username"
EMAIL = "Email"

TYPE_NUMBER, TYPE_STRING, TYPE_FOLDER, TYPE_BOOL = range(4)

def checkFolder(f):
    if os.path.isdir(f):
        return True
    try:
        os.makedirs(f)
        return True
    except:
        return False

def setEmail(email):
    email = email.strip()
    if email:
        con = Py4JCLIConnector()
        con.configglobal(geogig.USER_EMAIL, email)
    return True

def setUsername(name):
    name = name.strip()
    if name:
        con = Py4JCLIConnector()
        con.configglobal(geogig.USER_NAME, name)
    return True

generalParams = [
                 (AUTO_ADD_ID, "Automatically add 'geogigid' field without asking", False, TYPE_BOOL, lambda x: True),
                 (GATEWAY_PORT, "Port for GeoGig gateway", 25333, TYPE_NUMBER, lambda x: int(x) > 0),
                 (USE_THREAD, "Run operations on a separate thread", False, TYPE_BOOL, lambda x: True),
                 (USE_MAIN_MENUBAR, "Put GeoGig menus in main menu bar (requires restart)", True, TYPE_BOOL, lambda x: True),
                 (REPOS_FOLDER, "Base folder for repositories", "", TYPE_FOLDER, checkFolder),
                 (TIMEOUT, "Number of retries before timeout", 10, TYPE_NUMBER, lambda x: int(x) > 0),
                 (USERNAME, "User name", "", TYPE_STRING, lambda x: setUsername(x)),
                 (EMAIL, "User email", "", TYPE_STRING, lambda x: setEmail(x))]

def initConfigParams():
    folder = getConfigValue(GENERAL, REPOS_FOLDER)
    if folder.strip() == "":
        folder = os.path.join(os.path.expanduser('~'), 'geogig', 'repos')
        setConfigValue(GENERAL, REPOS_FOLDER, folder)

def getConfigValue(group, name):
    default = None
    for param in generalParams:
        if param[0] == name:
            default = param[2]

    if isinstance(default, bool):
        return QtCore.QSettings().value("/GeoGig/Settings/%s/%s" % (group, name), default, bool)
    else:
        return QtCore.QSettings().value("/GeoGig/Settings/%s/%s" % (group, name), default, str)

def setConfigValue(group, name, value):
    return QtCore.QSettings().setValue("/GeoGig/Settings/%s/%s" % (group, name), value)
