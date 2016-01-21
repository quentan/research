# A Playground for test Slicer module

import vtk
import qt
import ctk
import slicer
from slicer.ScriptedLoadableModule import *
import logging

import math

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

        volumeNode = slicer.util.getNode('MRHead')
        ijkToRas = vtk.vtkMatrix4x4()
        volumeNode.GetIJKToRASMatrix(ijkToRas)
        imageData = volumeNode.GetImageData()
        extent = imageData.GetExtent()

        image_np = slicer.util.array('MRHead')

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
                    # functionValue = math.sqrt((r-10)**2 + (a+15)**2 + s**2)
                    # functionValue = r-10 + a+15 + s
                    functionValue += image_np[k, j, i]
                    imageData.SetScalarComponentFromDouble(
                        i, j, k, 0, functionValue)

        # imageData.SetScalarComponentFromFloat(distortionVerctorPosition_Ijk[0],
        #                                       distortionVerctorPosition_Ijk[1],
        #                                       distortionVerctorPosition_Ijk[2],
        #                                       0, fillValue)
        imageData.Modified()
