# Locating coordinates of vascular wall

import vtk
import qt
import ctk
import slicer
from slicer.ScriptedLoadableModule import *
import logging


#
# VascularWall
#
class VascularWall(ScriptedLoadableModule):

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)

        self.parent.title = "Vascular Wall"
        self.parent.categories = ['Examples']
        self.dependencies = []
        self.parent.contributors = ["Quentan Qi (University of Hull)"]
        self.parent.helpText = """
        Locating coordinates of vascular wall by initialising a sphere of vessel.
        """
        self.parent.acknowledgementText = """
        Thanks to tutorials.
        """


#
# VascularWallWidget
#
class VascularWallWidget(ScriptedLoadableModuleWidget):

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        #
        # Parameters Area
        #
        parameterCollapsibleButton = ctk.ctkCollapsibleButton()
        parameterCollapsibleButton.text = 'Parameters'
        self.layout.addWidget(parameterCollapsibleButton)

        # Layout with the collapsible button
        parameterFormLayout = qt.QFormLayout(parameterCollapsibleButton)

        #
        # Input volume selector
        #
        self.volumeSelector = slicer.qMRMLNOdeComboBox()
        self.volumeSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        self.volumeSelector.noneEnabled = False
        self.volumeSelector.selectNodeUponCreation = True

        self.volumeSelector.setMRMLScene(slicer.mrmlScene)
        self.volumeSelector.setToolTip("Select input volume")
        parameterFormLayout.addRow("Input Volume: ", slef.volumeSelector)

        #
        # Ruler selector
        #
        self.rulerSelector = slicer.qMRMLNOdeComboBox()
        self.rulerSelector.nodeTypes = ("vtkMRMLAnnotationRulerNode", "")
        self.rulerSelector.noneEnabled = False
        self.rulerSelector.selectNodeUponCreation = True

        self.rulerSelector.setMRMLScene(slicer.mrmlScene)
        self.rulerSelector.setToolTip("Pick the ruler to make a sphere")
        parameterFormLayout.addRow("Ruler: ", self.rulerSelector)

        #
        # Show/Hide sphere ChechBox
        self.showCheckBox = qt.QCheckBox("Show/Hide Sphere")
        self.showCheckBox.toolTip("Show or hide the sphere")

        #
        # Apply Button
        #
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Generate a sphere according to the sphere"
        # parameterFormLayout.addWidget(self.applyButton)
        # parameterFormLayout.addRow("A test label", self.applyButton)
        parameterFormLayout.addRow(self.showCheckBox, self.applyButton)

        #
        # Results
        #
        self.currentCenterLabel = qt.QLabel()
        self.currentCenterLabel.setText("Current Centre: ")
        self.currentCenterCoord = qt.QLabel()
        parameterFormLayout.addRow(
            self.currentCenterLabel, self.currentCenterCoord)

        #
        # Connections
        #
        self.showCheckBox.connect('toggled(bool)', self.onShowCheckBoxToggled)
        self.applyButton.connect('clicked()', self.onApplyButtonClicked)

    def onShowCheckBoxToggled(self):
        logging.info("Toggled status of showCheckBox - %s" %
                     self.showCheckBox.isChecked())

    def onApplyButtonClicked(self):
        """
        Real algorithm should be in class VascularWallLogic.
        """
        logging.info("applyButton is clicked.")

        # logic = VascularWallLogic()


#
# Logic
#
class VascularWallLogic(ScriptedLoadableModuleLogic):

    def hasImageData(self, volumeNode):
        if not volumeNode:
            logging.debug("hasImageData failed: no volume node!")
            return False

        if volumeNode.GetImageData() is None:
            logging.debug("hasImageData failed: no image data in volume node")
            return False

        return True

    def isValidInputData(self, inputVolumeNode):
        if not inputVolumeNode:
            logging.debug(
                "isValidInputData failed: no input volume node defined!")
            return False

        return True

    def run(self, volumeNode, rulerNode):
        logging.info("VascularWallLogic.run() is called!")


#
# Test Case
#
class VascularWallTest(ScriptedLoadableModuleTest):

    def setUp(self):
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        self.setUp()
        self.test1_VascularWall()

    def test1_VascularWall(self):
        self.delayDisplay("Starting test")
        # Get data here

        self.delayDisplay("Finished with download and loading")

        # Do testing code here

        self.delayDisplay("Testing finished.o")
