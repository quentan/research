# A ModifyVolume for test Slicer module

import vtk
import qt
import ctk
import slicer
from slicer.ScriptedLoadableModule import *
import logging

import math

class ModifyVolume(ScriptedLoadableModule):

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)

        self.parent.title = 'ModifyVolume'
        self.parent.categories = ['Examples']
        self.parent.dependencies = []
        self.parent.contributors = ["Quentan Qi (University of Hull)"]
        self.parent.helpText = """
        A playground for testing new script.
        """
        self.parent.acknowledgementText = """
        Thanks to the tutorials.
        """


class ModifyVolumeWidget(ScriptedLoadableModuleWidget):

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # Sample collasible Button
        pgCoBtn = ctk.ctkCollapsibleButton()
        pgCoBtn.text = "ModifyVolume Collasible Button"
        self.layout.addWidget(pgCoBtn)

        # Layout
        pgFormLayout = qt.QFormLayout(pgCoBtn)

        # Test Button
        testBtn = qt.QPushButton("Test Button")
        testBtn.toolTip = "Print 'Test Button Pressed.' in standard output"
        pgFormLayout.addWidget(testBtn)
        testBtn.connect('clicked()', self.onTestBtnClicked)

        # Gradient Button
        gradientBtn = qt.QPushButton("Gradient")
        pgFormLayout.addWidget(gradientBtn)
        gradientBtn.connect('clicked()', self.onGradientBtnClicked)

        # Create New Volume
        newVolBtn = qt.QPushButton("New Volume")
        pgFormLayout.addWidget(newVolBtn)
        newVolBtn.connect("clicked()", self.onNewVolBtnClicked)

        # Spacer if needed
        self.layout.addStretch(1)

        # Set local variables as instance attributes
        self.testBtn = testBtn
        self.gradentBtn = gradientBtn
        self.newVolBtn = newVolBtn

    def onTestBtnClicked(self):
        print("Test Button Pressed!\n")

        # qt.QMessageBox.information(slicer.util.mainWindow(),
        #                            "TEST Window", "For test only!")

        volumeNode = slicer.util.getNode('MRHead')
        ijkToRas = vtk.vtkMatrix4x4()
        volumeNode.GetIJKToRASMatrix(ijkToRas)
        imageData = volumeNode.GetImageData()
        extent = imageData.GetExtent()

        # image_np = slicer.util.array('MRHead')

        for k in xrange(extent[4], extent[5]/2+1):
            for j in xrange(extent[2], extent[3]/2+1):
                for i in xrange(extent[0], extent[1]/2+1):
                    position_Ijk = [i, j, k, 1]
                    position_Ras = ijkToRas.MultiplyPoint(position_Ijk)

                    r = position_Ras[0]
                    a = position_Ras[1]
                    s = position_Ras[2]

                    # print "r=%f, a=%f, s=%f, Value[r, a, s]=%f" % (r, a, s, image_np[r, a, s])
                    # print "i=%f, j=%f, k=%f, Value[i, j, k]=%f" % (i, j, k, image_np[k, j, i])

                    functionValue = (r-10)*(r-10) + (a+15)*(a+15) + s*s
                    # functionValue = (i-10)**2 + (j+15)**2 + s**2
                    # functionValue = math.sqrt((r-10)**2 + (a+15)**2 + s**2)
                    # functionValue = r-10 + a+15 + s
                    # functionValue += image_np[k, j, i]
                    imageData.SetScalarComponentFromDouble(
                        i, j, k, 0, functionValue)

        # imageData.SetScalarComponentFromFloat(distortionVerctorPosition_Ijk[0],
        #                                       distortionVerctorPosition_Ijk[1],
        #                                       distortionVerctorPosition_Ijk[2],
        #                                       0, fillValue)
        imageData.Modified()

    def onGradientBtnClicked(self):

        volumeNode = slicer.util.getNode('MRHead')
        ijkToRas = vtk.vtkMatrix4x4()
        volumeNode.GetIJKToRASMatrix(ijkToRas)
        imageData = volumeNode.GetImageData()
        extent = imageData.GetExtent()

        # npData = slicer.util.array('MRHead')
        impVol = vtk.vtkImplicitVolume()
        impVol.SetVolume(imageData)

        for k in xrange(extent[4], extent[5]/2+1):
            for j in xrange(extent[2], extent[3]/2+1):
                for i in xrange(extent[0], extent[1]/2+1):
                    g = impVol.FunctionGradient(i, j, k)
                    gradient = math.sqrt(g[0]**2 + g[1]**2 + g[2]**2)
                    imageData.SetScalarComponentFromFloat(i, j, k, 0, gradient)

        imageData.Modified()

    def onNewVolBtnClicked(self):
        imageSize = [128]*3
        imageSpacing = [1.0]*3
        voxelType = vtk.VTK_UNSIGNED_CHAR

        # Create an empty image volume
        imageData = vtk.vtkImageData()
        imageData.SetDimensions(imageSize)
        imageData.AllocateScalars(voxelType, 100)

        thresholder = vtk.vtkImageThreshold()
        thresholder.SetInputData(imageData)
        thresholder.SetInValue(0)
        thresholder.SetOutValue(0)

        # Create volume node
        volumeNode = slicer.vtkMRMLScalarVolumeNode()
        volumeNode.SetSpacing(imageSpacing)
        volumeNode.SetImageDataConnection(thresholder.GetOutputPort())

        # Add volume to scene
        scene = slicer.mrmlScene
        scene.AddNode(volumeNode)
        displayNode = slicer.vtkMRMLScalarVolumeDisplayNode()
        scene.AddNode(displayNode)
        colorNode = slicer.util.getNode('Grey')
        displayNode.SetAndObserveColorNodeID(colorNode.GetID())
        volumeNode.SetAndObserveDisplayNodeID(displayNode.GetID())
        volumeNode.CreateDefaultStorageNode()

        # Show the new volume in the Slice view
        applicationLogic = slicer.app.applicationLogic()
        selectionNode = applicationLogic.GetSelectionNode()
        selectionNode.SetSecondaryVolumeID(volumeNode.GetID())
        applicationLogic.PropagateForegroundVolumeSelection(0)

        # Center the 3D View on the scene
        # It works only after showing the 3D scene
        layoutManager = slicer.app.layoutManager()
        threeDWidget = layoutManager.threeDWidget(0)
        threeDView = threeDWidget.threeDView()
        threeDView.resetFocalPoint()