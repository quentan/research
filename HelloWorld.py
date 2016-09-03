# Python scripy for Slicer extension
# Most basic widget

import vtk
import qt
import ctk
import slicer
from slicer.ScriptedLoadableModule import *  # for "Reload" button
import logging

#
# Class in every Slicer script.
# Note the parent class
#


# The name MUST be same as the file name!
class HelloWorld(ScriptedLoadableModule):

    """
    Inherited from `ScriptedLoadableModule` makes the widget require "Reload" function.
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)

        self.parent.title = 'Hello World!'
        self.parent.categories = ['Examples']
        self.parent.dependencies = []
        self.parent.contributors = ["Quentan Qi (Hull University)"]
        self.parent.helpText = """
        An example from Script Repository. It has a QPushButton to pop a Slicer Window.
        See: https://www.slicer.org/slicerWiki/images/c/c0/Slicer4_ProgrammingTutorial_Slicer4.5.pdf
        """
        self.parent.acknowledgementText = """
        Thanks to the tutorials.
        """

#
# HellowWorldWidget
# Note the parent class
#


class HelloWorldWidget(ScriptedLoadableModuleWidget):

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
            'Hello Slicer!!\nNote: This is different from the title of the button'  # Change here to test "Reload" button
            )
