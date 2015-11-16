from PyQt4 import QtGui

class UserPasswordDialog(QtGui.QDialog):

    def __init__(self, parent = None, title = None, user = None):
        super(UserPasswordDialog, self).__init__(parent)
        self.user = None
        self.password = None
        self.title = title or 'Credentials'
        self.initGui()
        if user:
            self.usernameBox.setText(user)

    def initGui(self):
        self.setWindowTitle(self.title)
        verticalLayout = QtGui.QVBoxLayout()

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        usernameLabel = QtGui.QLabel('Username')
        self.usernameBox = QtGui.QLineEdit()
        horizontalLayout.addWidget(usernameLabel)
        horizontalLayout.addWidget(self.usernameBox)
        verticalLayout.addLayout(horizontalLayout)

        horizontalLayout = QtGui.QHBoxLayout()
        horizontalLayout.setSpacing(30)
        horizontalLayout.setMargin(0)
        passwordLabel = QtGui.QLabel('Password')
        self.passwordBox = QtGui.QLineEdit()
        self.passwordBox.setEchoMode(QtGui.QLineEdit.Password)
        horizontalLayout.addWidget(passwordLabel)
        horizontalLayout.addWidget(self.passwordBox)
        verticalLayout.addLayout(horizontalLayout)

        self.groupBox = QtGui.QGroupBox()
        self.groupBox.setTitle("Please provide credentials")
        self.groupBox.setLayout(verticalLayout)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.groupBox)
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

        self.buttonBox.accepted.connect(self.okPressed)
        self.buttonBox.rejected.connect(self.cancelPressed)

        self.resize(400, 200)

    def okPressed(self):
        self.user = unicode(self.usernameBox.text())
        self.password = unicode(self.passwordBox.text())
        self.close()

    def cancelPressed(self):
        self.user = None
        self.password = None
        self.close()
