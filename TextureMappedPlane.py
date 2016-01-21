# Python scripy for Slicer extension
# Texture Mapped Plane to the scene as a model
# http://wiki.slicer.org/slicerWiki/index.php/Documentation/4.5/ScriptRepository

import vtk
import qt
import ctk
import slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# Class in every Slicer script.
# Note the parent class
#


# The name MUST be same as the file name!
class TextureMappedPlane(ScriptedLoadableModule):

    """
    Inherited from `ScriptedLoadableModule` makes the widget require "Reload" function.
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)

        self.parent.title = 'Add Texture Mapped Plane as a Model'
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


class TextureMappedPlaneWidget(ScriptedLoadableModuleWidget):

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # Widget
        sampleCollasibleBtn = ctk.ctkCollapsibleButton()
        sampleCollasibleBtn.text = "A Collapsible Button"
        self.layout.addWidget(sampleCollasibleBtn)

        # Layout
        sampleFormLayout = qt.QFormLayout(sampleCollasibleBtn)

        # Example Button
        helloWorldBtn = qt.QPushButton("Hello World!")
        helloWorldBtn.toolTip = 'Print "Hello World" in standard output'
        sampleFormLayout.addWidget(helloWorldBtn)
        helloWorldBtn.connect('clicked()', self.onHelloWorldBtnClicked)

        # Button for Texture Mapped Plane
        textureBtn = qt.QPushButton("Add Texture Mapped Plane")
        textureBtn.toolTip = "Add a texture mapped plane to the scene as a model"
        sampleFormLayout.addWidget(textureBtn)
        textureBtn.connect('clicked()', self.onTextureBtnClicked)

        # Vertical spacer
        self.layout.addStretch(1)

        # Set local var as instance attribute
        self.helloWorldBtn = helloWorldBtn
        self.textureBtn = textureBtn

    def onTextureBtnClicked(self):
        # use dummy image data here
        e = vtk.vtkImageEllipsoidSource()

        scene = slicer.mrmlScene

        # Create model node
        model = slicer.vtkMRMLModelNode()
        model.SetScene(scene)
        model.SetName(scene.GenerateUniqueName("2DImageModel"))

        planeSource = vtk.vtkPlaneSource()
        model.SetAndObservePolyData(planeSource.GetOutput())

        # Create display node
        modelDisplay = slicer.vtkMRMLModelDisplayNode()
        modelDisplay.SetColor(1, 1, 0)  # yellow
        # modelDisplay.SetBackfaceCulling(0)
        modelDisplay.SetScene(scene)
        scene.AddNode(modelDisplay)
        model.SetAndObserveDisplayNodeID(modelDisplay.GetID())

        modelDisplay.SetSliceIntersectionVisibility(True)
        modelDisplay.SetVisibility(True)

        # Add to scene
        modelDisplay.SetTextureImageDataConnection(e.GetOutputPort())
        # modelDisplay.SetInputPolyDataConnection(model.GetPolyDataConnection())
        scene.AddNode(model)

        transform = slicer.vtkMRMLLinearTransformNode()
        scene.AddNode(transform)
        model.SetAndObserveTransformNodeID(transform.GetID())

        vTransform = vtk.vtkTransform()
        vTransform.Scale(50, 50, 50)
        vTransform.RotateX(30)
        # transform.SetAndObserveMatrixTransformToParent(vTransform.GetMatrix())
        transform.SetMatrixTransformToParent(vTransform.GetMatrix())

    def onHelloWorldBtnClicked(self):
        print("Hello World!")

        qt.QMessageBox.information(
            slicer.util.mainWindow(),
            'Slicer Python',
            'Hello Slicer!!'  # Change here to test "Reload" button
        )
