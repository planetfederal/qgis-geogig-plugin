from PyQt4 import QtGui, QtCore
import os
import webbrowser

errorIcon = os.path.dirname(__file__) + "/../../ui/resources/error.png"
addupdateIcon = os.path.dirname(__file__) + "/../../ui/resources/addupdate.png"

class GatewayNotAvailableDialog(QtGui.QDialog):

    def __init__(self, parent = None):
        super(GatewayNotAvailableDialog, self).__init__(parent)
        self.initGui()

    def initGui(self):
        layout = QtGui.QVBoxLayout()
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Close)
        class MyBrowser(QtGui.QTextBrowser):
            def loadResource(self, type_, name):
                return None
        self.textBrowser = MyBrowser()
        self.textBrowser.connect(self.textBrowser, QtCore.SIGNAL("anchorClicked(const QUrl&)"), self.linkClicked)
        text = '"<html><img src="' + errorIcon + '"/><h3>Cannot initialize the GeoGig engine.</h3>'
        text += ("<p>The GeoGig engine cannot be started or is not responding correctly."
        "Please, retry the GeoGig operation that you were performing.</p>\n"
        "<p>If the problem disappears when retrying, the error might have been caused by a time out "
        "when connecting to the GeoGig engine. You can increase the amount of time before considering a timeout, "
        "by going the GeoGig configuration settings and modifying the <i>Number of retries before timeout</i> parameter.")

        self.textBrowser.setHtml(text)
        layout.addWidget(self.textBrowser)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

        self.connect(buttonBox, QtCore.SIGNAL("rejected()"), self.close)

        self.resize(500, 400)
        self.setWindowTitle("Error connecting to GeoGig")

    def linkClicked(self):
        webbrowser.open_new_tab("http://geogig.com")
        self.close()

class GatewayNotAvailableWhileEditingDialog(GatewayNotAvailableDialog):

    def initGui(self):
        GatewayNotAvailableDialog.initGui(self)
        text = self.textBrowser.toHtml()
        text += "<p>The layer has been modified, but the changes haven't been incorporated in the repository."
        text += " To update the repository once you have started the gateway, use the <i>Add/update<i> button</p>."
        text += '<img src="' + addupdateIcon + '"/>'
        self.textBrowser.setHtml(text)
