import os
import dateutil.parser
from versio.gui.executor import execute
from geogigpy.repo import Repository
from versio.gui.pyqtconnectordecorator import PyQtConnectorDecorator
from versio.tools.utils import resourceFile, repoFolder, relativeDate
from versio.tools.layertracking import removeTrackedForRepo
from versio.tools.localversio import LocalOnlyRepository
from versio import config
from versio.tools.versioinstance import instance
from geogigpy.geogigexception import GeoGigException
from geogigpy.commit import Commit
import datetime
import time

class RepoWrapper(object):


    def __init__(self, versioRepo, username):
        self.versioRepo = versioRepo
        self.username = username
        self.localRepo = None

    def localPath(self):
        return repoFolder(self.username, self.versioRepo.owner, self.versioRepo.name)

    def repo(self):
        if self.localCopyExists():
            if self.localRepo is None:
                connector = PyQtConnectorDecorator()
                connector.checkIsAlive()
                self.localRepo = Repository(self.localPath(), connector)
            return self.localRepo
        else:
            return self.versioRepo

    def getTitle(self):
        return self.versioRepo.title

    def setTitle(self, title):
        self.versioRepo.title = title
        if self.localCopyExists():
            filename = os.path.join(self.localPath(), "title")
            with open(filename, "w") as f:
                f.write(title)

    title = property(getTitle, setTitle)


    def cloneLocally(self):
        if not self.localCopyExists():
            connector = PyQtConnectorDecorator()
            connector.checkIsAlive()

            url = "/".join([self.versioRepo.connector.url.strip("/"), "repos",
                                   self.versioRepo.owner, self.versioRepo.name])
            self.localRepo = Repository.newrepofromclone(url, self.localPath(),
                connector, self.versioRepo.connector.user, self.versioRepo.connector.password)
            filename = os.path.join(self.localPath(), "title")
            with open(filename, "w") as f:
                f.write(self.versioRepo.title)
            removeTrackedForRepo(self.localPath())

    def localCopyExists(self):
        return os.path.exists(self.localPath())

    def uploadRepo(self):
        versioRepo = execute(lambda : instance().create_repo(self.title, "", self.versioRepo.name))
        url = "/".join([config.getConfigValue(config.GENERAL, config.VERSIO_ENDPOINT).strip("/"),
                            "repos", instance().user, self.versioRepo.name])
        try:
            self.repo().addremote("origin", url, instance().connector.user, instance().connector.password)
        except GeoGigException:
            self.repo().removeremote("origin")
            self.repo().addremote("origin", url, instance().connector.user, instance().connector.password)
        self.repo().push("origin")
        self.versioRepo = versioRepo

    def canPush(self):
        return (not isinstance(self.versioRepo, LocalOnlyRepository)
                and (self.versioRepo.owner == self.versioRepo.connector.user or
                self.versioRepo.connector.user in self.versioRepo.collaborators))

    def canEdit(self):
        return (not isinstance(self.versioRepo, LocalOnlyRepository)
                and self.versioRepo.owner == self.versioRepo.connector.user)

    @property
    def fullDescription(self):
        def _prepareDescription():
            footnote = ""
            try:
                if self.localCopyExists():
                    ref = self.repo().head.ref
                    footnote += "<p>Your current branch is set to <b>%s</b>. GeoGig will track and sync with this branch.</p>" % ref
                    c = Commit.fromref(self.repo(), ref)
                    epoch = time.mktime(c.committerdate.timetuple())
                    offset = datetime.datetime.fromtimestamp (epoch) - datetime.datetime.utcfromtimestamp (epoch)
                    d = c.committerdate + offset
                    lastDate = d.strftime("%b %d, %Y %I:%M%p")
                    author = c.authorname
                else:
                    footnote += "<p><b>To edit this repository, you must <a href='download'>download it first</a></b></p>"
                    c = self.versioRepo.log(1)[0]
                    lastDate = dateutil.parser.parse(c.date).strftime("%b %d, %Y %I:%M%p")
                    author = c.author
                lastVersion = "%s (%s by %s)" % (c.message.splitlines()[0], lastDate, author)
            except:
                lastVersion = ""
            filename = ("descriptiontemplate_edit.html" if self.canEdit()
                        else "descriptiontemplate.html")
            with open(resourceFile(filename)) as f:
                s = "".join(f.readlines())
            s = s.replace("[NAME]", self.versioRepo.name)
            s = s.replace("[TITLE]", self.versioRepo.title)
            if self.canEdit():
                editIcon = os.path.dirname(__file__) + "/../ui/resources/pencil-icon.png"
                s = s.replace("[EDIT]", "<img src='" + editIcon + "'>")
            s = s.replace("[LAST_VERSION]", lastVersion)
            s = s.replace("[FOOTNOTE]", footnote)
            if self.localCopyExists():
                layers = "<dl>%s</dl>" % "".join(["<dd>%s</dd>" % tree.path for tree in self.repo().trees])
            else:
                layers = "<dl>%s</dl>" % "".join(["<dd>%s</dd>" % layer.name for layer in self.versioRepo.layers()])
            s = s.replace("[LAYERS]", layers)
            return s
        return(execute(_prepareDescription))

