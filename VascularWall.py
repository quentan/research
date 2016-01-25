# Locating coordinates of vascular wall

import vtk
import qt
import ctk
import slicer
from slicer.ScriptedLoadableModule import *
import logging
logging.basicConfig(level=logging.INFO)

import numpy as np


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
        self.volumeSelector = slicer.qMRMLNodeComboBox()
        self.volumeSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        self.volumeSelector.noneEnabled = False
        self.volumeSelector.selectNodeUponCreation = True

        self.volumeSelector.setMRMLScene(slicer.mrmlScene)
        self.volumeSelector.setToolTip("Select input volume")
        parameterFormLayout.addRow("Input Volume: ", self.volumeSelector)

        #
        # Ruler selector
        #
        self.rulerSelector = slicer.qMRMLNodeComboBox()
        self.rulerSelector.nodeTypes = ("vtkMRMLAnnotationRulerNode", "")
        self.rulerSelector.noneEnabled = False
        self.rulerSelector.selectNodeUponCreation = True

        self.rulerSelector.setMRMLScene(slicer.mrmlScene)
        self.rulerSelector.setToolTip("Pick the ruler to make a sphere")
        parameterFormLayout.addRow("Ruler: ", self.rulerSelector)

        #
        # Show/Hide sphere ChechBox
        #
        self.showCheckBox = qt.QCheckBox("Show/Hide Sphere")
        # self.showCheckBox.setToolTip("Show or hide the sphere")
        self.showCheckBox.toolTip = "Show or hide the sphere"

        #
        # Apply Button
        #
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Generate a sphere according to the sphere"
        self.applyButton.enabled = True

        # parameterFormLayout.addWidget(self.applyButton)
        # parameterFormLayout.addRow("A test label:", self.applyButton)
        parameterFormLayout.addRow(self.showCheckBox, self.applyButton)

        #
        # Results
        #
        self.currentCenterLabel = qt.QLabel()
        self.currentCenterLabel.setText("Current Centre: ")
        self.currentCenterCoord = qt.QLabel()
        parameterFormLayout.addRow(
            self.currentCenterLabel, self.currentCenterCoord)

        self.currentRadiusLabel = qt.QLabel()
        self.currentRadiusLabel.setText("Current Radius: ")
        self.currentRadiusLength = qt.QLabel()
        parameterFormLayout.addRow(
            self.currentRadiusLabel, self.currentRadiusLength)

        #
        # Connections
        #
        self.showCheckBox.connect('toggled(bool)', self.onShowCheckBoxToggled)
        self.applyButton.connect('clicked()', self.onApplyButtonClicked)
        self.volumeSelector.connect(
            'currentNodeChanged(vtkMRMLNode*)', self.onSelect)

        # Add vertical spacer
        self.layout.addStretch(1)

        # Refresh applyButton state
        self.onSelect()

    def cleanup(self):
        pass

    def onSelect(self):
        self.applyButton.enabled = self.volumeSelector.currentNode()

    def onShowCheckBoxToggled(self):
        logging.info("Toggled status of showCheckBox - %s" %
                     self.showCheckBox.isChecked())

        if self.showCheckBox.isChecked():
            self.modelDisplay.SetVisibility(True)

        else:
            self.modelDisplay.SetVisibility(False)

    def onApplyButtonClicked(self):
        """
        Real algorithm should be in class VascularWallLogic.
        """
        logging.info("applyButton is clicked.")

        # Initialise VascularWallLogic object
        # self.logic = VascularWallLogic(self.rulerSelector.currentNode())

        self.UpdateSphereParameter(0, 0)
        self.rulerSelector.currentNode().AddObserver(
            'ModifiedEvent', self.UpdateSphereParameter)

        # Create models for sphere

        self.sphere = vtk.vtkSphereSource()
        # Model node
        model = slicer.vtkMRMLModelNode()
        model.SetAndObservePolyData(self.sphere.GetOutput())

        # Display node
        self.modelDisplay = slicer.vtkMRMLModelDisplayNode()
        self.modelDisplay.SetSliceIntersectionVisibility(True)
        self.modelDisplay.SetVisibility(True)
        self.modelDisplay.SetOpacity(0.1)
        slicer.mrmlScene.AddNode(self.modelDisplay)
        model.SetAndObserveDisplayNodeID(self.modelDisplay.GetID())

        # Add to scene
        self.modelDisplay.SetInputPolyDataConnection(
            model.GetPolyDataConnection())
        slicer.mrmlScene.AddNode(model)

        self.rulerSelector.currentNode().AddObserver(
            'ModifiedEvent', self.UpdateSphere)

    def UpdateSphereParameter(self, obj, event):
        logic = VascularWallLogic(self.rulerSelector.currentNode())
        centralPoint = logic.getCentralPoint()
        radius = logic.getRadius()

        self.currentCenterCoord.setText([round(n, 2) for n in centralPoint])
        self.currentRadiusLength.setText(round(radius, 2))

        # self.logic = logic

    def UpdateSphere(self, obj, event):
        logic = VascularWallLogic(self.rulerSelector.currentNode())
        centerPoint = logic.getCentralPoint()
        radius = logic.getRadius()

        self.sphere.SetCenter(centerPoint)
        self.sphere.SetRadius(radius)
        self.sphere.SetPhiResolution(30)
        self.sphere.SetThetaResolution(30)
        self.sphere.Update()


#
# Logic
#
class VascularWallLogic(ScriptedLoadableModuleLogic):

    def __init__(self, rulerNode):
        self.info = {}  # Info of the rulerNode

        if rulerNode:
            startPoint = [0.0] * 3  # central point
            endPoint = [0.0] * 3
            radius = 0.0

            rulerNode.GetPosition1(startPoint)
            rulerNode.GetPosition2(endPoint)
            radius = rulerNode.GetDistanceMeasurement()

            self.info['startPoint'] = startPoint
            self.info['endPoint'] = endPoint
            self.info['radius'] = radius

            self.rulerNode = rulerNode

    def hasSphereParameter(self, rulerNode):
        if not rulerNode:
            logging.debug(
                "hasSphereParameter failed: no central point and radius in ruler node!")
            return False

        return True

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

    def getCentralPoint(self):
        if self.hasSphereParameter(self.rulerNode):
            return self.info['startPoint']

    def getRadius(self):
        if self.hasSphereParameter(self.rulerNode):
            return self.info['radius']

    def getSphere(self):
        sphere = vtk.vtkSphereSource()
        centerPoint = self.getCentralPoint()
        radius = self.getRadius()

        sphere.SetCenter(centerPoint)
        sphere.SetRadius(radius)
        return sphere

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

        self.delayDisplay("Testing finished.")
