# A Playground for test Slicer module

import vtk
import qt
import ctk
import slicer
from slicer.ScriptedLoadableModule import *
import logging


class Playground(ScriptedLoadableModule):

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)

        self.parent.title = 'Playground'
        self.parent.categories = ['Examples']
        self.parent.dependencies = []
        self.parent.contributors = ["Quentan Qi (University of Hull)"]
        self.parent.helpText = """
        A playground for testing new script.
        """
        self.parent.acknowledgementText = """
        Thanks to the tutorials.
        """


class PlaygroundWidget(ScriptedLoadableModuleWidget):

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # Sample collasible Button
        pgCoBtn = ctk.ctkCollapsibleButton()
        pgCoBtn.text = "Playground Collasible Button"
        self.layout.addWidget(pgCoBtn)

        # Layout
        pgFormLayout = qt.QFormLayout(pgCoBtn)

        # Test Button
        testBtn = qt.QPushButton("Test Button")
        testBtn.toolTip = "Print 'Test Button Pressed.' in standard output"
        pgFormLayout.addWidget(testBtn)
        testBtn.connect('clicked()', self.onTestBtnClicked)

        # Spacer if needed
        self.layout.addStretch(1)

        # Set local variables as instance attributes
        self.testBtn = testBtn

    def onTestBtnClicked(self):
        print("Test Button Pressed!\n")

        # qt.QMessageBox.information(slicer.util.mainWindow(),
        #                            "TEST Window", "For test only!")
