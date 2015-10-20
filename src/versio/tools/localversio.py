from geogigpy.repo import Repository
from versio.tools.utils import repoFolder, allLocalRepos, userFromRepoPath, \
    ownerFromRepoPath, nameFromRepoPath
import os
from datetime import datetime
from versio.gui.pyqtconnectordecorator import PyQtConnectorDecorator


class LocalVersio(object):

    user = None

    def repos(self, all = True):
        allRepos = allLocalRepos()
        repos = []
        for userrepos in allRepos.values():
            repos.extend([LocalOnlyRepository(path) for path in userrepos.values()])
        return repos


    def create_repo(self, username, title):
        safeName = "".join(x for x in title if x.isalnum())
        path = os.path.join(repoFolder(username, username, safeName))
        Repository(path, PyQtConnectorDecorator(), True)
        filename = os.path.join(path, "title")
        with open(filename, "w") as f:
            f.write(title)
        return LocalOnlyRepository(path)

    def delete_repo(self, reponame):
        pass


class LocalOnlyRepository(object):
    def __init__(self, path):
        self.owner = ownerFromRepoPath(path)
        self.user = userFromRepoPath(path)
        self.name = nameFromRepoPath(path)
        titlefile = os.path.join(path, "title")
        if os.path.exists(titlefile):
            with open(titlefile) as f:
                self.title = f.readline()
        else:
            self.title = self.name
        self.description = ""
        self.updated = datetime.fromtimestamp(os.path.getmtime(path + "/.geogig")).isoformat()
        self.created = None
        self.collaborators = []
        self.mine = self.owner == self.user
        self.private = True


