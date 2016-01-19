# Python scripy for Slicer extension

import vtk
import qt
import ctk
import slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# Circular Region of Interest
#


class CircularROI(ScriptedLoadableModule):

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)

        self.parent.title = 'Circular ROI'
        self.parent.categories = ['Examples']
        self.parent.dependencies = []
        self.parent.contributors = ["Quentan Qi (Hull University)"]
        self.parent.helpText = """
        An example from Script Repository. It produces a circular Region of Interest.
        See: http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.5/ScriptRepository
        """
        self.parent.acknowledgementText = """
        Thanks to the tutorials.
        """

#
# CircularROIWidget
#


class CircularROIWidget(ScriptedLoadableModuleWidget):

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # Widget
        sampleCollasibleBtn = ctk.ctkCollapsibleButton()
        sampleCollasibleBtn.text = "A Collapsible Button"
        self.layout.addWidget(sampleCollasibleBtn)

        # Layout
        sampleFormLayout = qt.QFormLayout(sampleCollasibleBtn)

        # Button
        helloWorldBtn = qt.QPushButton("Hello World!")
        helloWorldBtn.toolTip = 'Print "Hello World" in standard output'
        sampleFormLayout.addWidget(helloWorldBtn)
        helloWorldBtn.connect('clicked()', self.onHelloWorldBtnClicked)

        # Vertical spacer
        self.layout.addStretch(1)

        # Set local var as instance attribute
        self.helloWorldBtn = helloWorldBtn

    def onHelloWorldBtnClicked(self):
        print("Hello World!")

        qt.QMessageBox.information(
            slicer.util.mainWindow(),
            'Slicer Python',
            'Hello World!'
            )
