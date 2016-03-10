# -*- coding: utf-8 -*-
#
# (c) 2016 Boundless, http://boundlessgeo.com
# This code is licensed under the GPL 2.0 license.
#
from PyQt4 import  QtGui
class AddGeogigIdDialog(QtGui.QMessageBox):

    def __init__(self, parent = None):
        super(AddGeogigIdDialog, self).__init__()

        self.checkbox = QtGui.QCheckBox()
        #Access the Layout of the MessageBox to add the Checkbox
        layout = self.layout()
        layout.addWidget(self.checkbox, 1, 1)

        self.setWindowTitle("Missing Id field")
        self.setText("The layer to import doesn't have a 'geogigid' field\n"
                    "You need to create a 'geogigid' field before importing\n"
                    "Do you want to create one automatically before importing?")
        self.checkbox.setText("Do not ask again. Add 'geogigid' field automatically")
        self.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        self.setDefaultButton(QtGui.QMessageBox.Yes)
        self.setIcon(QtGui.QMessageBox.Warning)

    def exec_(self, *args, **kwargs):
        return QtGui.QMessageBox.exec_(self, *args, **kwargs), self.checkbox.isChecked()

