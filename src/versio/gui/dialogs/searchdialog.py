from PyQt4 import QtGui, QtWebKit, QtCore
from qgis.core import *
from qgis.gui import *
import os
from versio.tools.versioinstance import instance
from versio.gui.executor import execute
from versio.tools.utils import repoFolder, resourceFile
from requests.exceptions import RequestException

class SearchDialog(QtGui.QDialog):

    def __init__(self, navigator, searchTerms):
        super(SearchDialog, self).__init__(navigator)
        self.navigator = navigator
        self.initGui(searchTerms)
        self.repo = None

    def initGui(self, searchTerms):
        hlayout = QtGui.QHBoxLayout()
        layout = QtGui.QVBoxLayout()
        self.searchBox = QtGui.QLineEdit()
        self.searchBox.returnPressed.connect(self.search)
        self.searchBox.setText(searchTerms)
        self.searchBox.setPlaceholderText("[Enter search string and press enter to search public repositories]")
        hlayout.addWidget(self.searchBox)
        icon = QtGui.QIcon(os.path.join(os.path.dirname(__file__),
                            os.pardir, os.pardir, "ui", "resources", "search-repos.png"))
        self.button = QtGui.QToolButton()
        self.button.setIcon(icon)
        self.button.clicked.connect(self.search)
        self.button.adjustSize()
        self.searchBox.setFixedHeight(self.button.height())
        hlayout.addWidget(self.button)
        layout.addLayout(hlayout)

        w = QtGui.QFrame()
        self.browser = QtWebKit.QWebView()
        w.setStyleSheet("QFrame{border:1px solid rgb(0, 0, 0);}")
        innerlayout = QtGui.QHBoxLayout()
        innerlayout.setSpacing(0)
        innerlayout.setMargin(0)
        innerlayout.addWidget(self.browser)
        w.setLayout(innerlayout)
        layout.addWidget(w)
        self.setLayout(layout)

        self.browser.page().setLinkDelegationPolicy(QtWebKit.QWebPage.DelegateAllLinks)
        self.browser.settings().setUserStyleSheetUrl(QtCore.QUrl("file://" + resourceFile("search.css").replace("\\", "/")))
        self.browser.linkClicked.connect(self.linkClicked)
        self.resize(600, 500)
        self.setWindowTitle("Search public repositories")

        self.search()

    def linkClicked(self, url):
        print url.path()
        self.repo = url.path()
        self.close()

    def search(self):
        text = self.searchBox.text().strip()
        if text:
            try:
                repos = execute(lambda : instance().search(text))
                if repos:
                    s = "<div><ul>"
                    for repo in repos:
                        localPath = repoFolder(instance().user, repo.owner, repo.name)
                        if os.path.exists(localPath) or repo.owner == instance().user:
                            continue
                        link = "<a href='%s&%s' class='button'>Copy locally</a>" % (repo.owner, repo.name)
                        s += "<li>%s<h3>%s</h3> %s <br> </li>" % (link, repo.title, repo.description)
                    s += "</ul></div>"
                else:
                    s = "<h2>No repositories matching your search criteria were found.</h1>"
                self.browser.setHtml(s)
            except RequestException, e:
                    QtGui.QMessageBox.warning(self, "Search",
                        u"There has been a problem performing the search:\n" + unicode(e.args[0]),
                        QtGui.QMessageBox.Ok)
