# Python scripy for Slicer extension

import vtk
import qt
import ctk
import slicer
from slicer.ScriptedLoadableModule import *
import logging

import math

#
# Circular Region of Interest
#


class CircularROI(ScriptedLoadableModule):

    """
    Inherited from `ScriptedLoadableModule` makes the widget require "Reload" function.
    """

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
        # sampleFormLayout.addWidget(helloWorldBtn)
        # helloWorldBtn.connect('clicked()', self.onHelloWorldBtnClicked)

        circularROIBtn = qt.QPushButton("CircularROI")
        circularROIBtn.toolTip = "Get a circular Region of Interst"
        sampleFormLayout.addWidget(circularROIBtn)
        circularROIBtn.connect('clicked()', self.onCircularROIBtn)

        showCheckBox = qt.QCheckBox('Show/Hide Sphere')
        sampleFormLayout.addWidget(showCheckBox)
        showCheckBox.connect('clicked()', self.onShowCheckBox)

        # Vertical spacer
        self.layout.addStretch(1)

        # Set local var as instance attribute
        self.helloWorldBtn = helloWorldBtn
        self.circularROIBtn = circularROIBtn
        self.showCheckBox = showCheckBox

    def onShowCheckBox(self):
        if self.showCheckBox.isChecked():
            self.modelDisplay.SetVisibility(True)

        else:
            self.modelDisplay.SetVisibility(False)

    def onHelloWorldBtnClicked(self):
        print("Hello World!")

        qt.QMessageBox.information(
            slicer.util.mainWindow(),
            'Slicer Python',
            'Hello Slicer!!'
        )

    def onCircularROIBtn(self):
        self.markups = slicer.util.getNode('F')
        self.sphere = vtk.vtkSphereSource()

        self.UpdateSphere(0, 0)

        model = slicer.vtkMRMLModelNode()
        model.SetAndObservePolyData(self.sphere.GetOutput())
        modelDisplay = slicer.vtkMRMLModelDisplayNode()

        modelDisplay.SetSliceIntersectionVisibility(True)
        modelDisplay.SetVisibility(True)

        slicer.mrmlScene.AddNode(modelDisplay)
        model.SetAndObserveDisplayNodeID(modelDisplay.GetID())
        modelDisplay.SetInputPolyDataConnection(model.GetPolyDataConnection())

        slicer.mrmlScene.AddNode(model)

        self.markups.AddObserver('ModifiedEvent', self.UpdateSphere, 2)

        self.modelDisplay = modelDisplay

    # Update the sphere from the fiducial points
    def UpdateSphere(self, p1, p2):
        p1 = [0.0, 0.0, 0.0]  # center point
        self.markups.GetNthFiducialPosition(0, p1)
        p2 = [0.0, 0.0, 0.0]  # circumference point
        self.markups.GetNthFiducialPosition(1, p2)
        self.sphere.SetCenter(p1)
        radius = math.sqrt((p1[0]-p2[0])**2 +
                           (p1[1]-p2[1])**2 +
                           (p1[2]-p2[2])**2)
        self.sphere.SetRadius(radius)
        self.sphere.SetPhiResolution(30)
        self.sphere.SetThetaResolution(30)
        self.sphere.Update()
