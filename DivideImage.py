"""
Load an image as a numpy array and divide it into small ones
"""
import os
import qt
import slicer
import ctk
# import math
import numpy as np
from slicer.ScriptedLoadableModule import ScriptedLoadableModule
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleWidget
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleLogic
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleTest

import logging
logging.getLogger('').handlers = []
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.WARNING)


#
# Module
#
class DivideImage(ScriptedLoadableModule):

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)

        self.parent.title = "Divide Image"
        self.parent.categories = ["Examples"]
        self.parent.dependencies = []
        self.parent.contributors = "Quentan Qi (Univeristy of Hull)"
        self.parent.helpText = """
        Load an image as a numpy array and divide it into small ones
        """
        self.parent.acknowledgementText = """
        Thanks for XXX.
        """


#
# Widget
#
class DivideImageWidget(ScriptedLoadableModuleWidget):

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # Parameter collapsible area
        collapsibleBtn = ctk.ctkCollapsibleButton()
        collapsibleBtn.text = "Parameters"
        self.layout.addWidget(collapsibleBtn)

        # Layout with the collapsible button
        _layout = qt.QFormLayout(collapsibleBtn)

        #
        # Fisrt input volume selector
        self.volumeSelector1 = slicer.qMRMLNodeComboBox()
        self.volumeSelector1.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        # self.volumeSelector1.addAttribute("vtkMRMLScalarVolumeNode",
        # "LabelMap", 0)  # deprecated
        self.volumeSelector1.selectNodeUponCreation = True
        self.volumeSelector1.addEnabled = False
        self.volumeSelector1.removeEnabled = False
        self.volumeSelector1.noneEnabled = False
        self.volumeSelector1.showHidden = False
        self.volumeSelector1.showChildNodeTypes = False
        self.volumeSelector1.setMRMLScene(slicer.mrmlScene)
        self.volumeSelector1.setToolTip("Pick up the volume.")
        _layout.addRow("Volume: ", self.volumeSelector1)

        #
        # Shape label of the image
        self.shapeLabel = qt.QLabel()
        self.shapeLabel.setText("Shape of the image: ")
        self.shapeValue = qt.QLabel()
        _layout.addRow(self.shapeLabel, self.shapeValue)

        # Test button
        self.testBtn = qt.QPushButton("TEST")
        self.testBtn.toolTip = "Do some test work"
        self.testBtn.enabled = False
        _layout.addRow(self.testBtn)

        # Vertical spacer
        self.layout.addStretch(1)

        #
        # Connection
        self.volumeSelector1.connect('nodeActivated(vtkMRMLNode*)',
                                     self.onVolumeSelect)
        self.testBtn.connect('clicked(bool)', self.onTestBtn)

    # Response functions

    def onTestBtn(self):
        logic = DivideImageLogic()
        logging.info("Logic is instantiated.")

        ndarray = logic.getNdarray(self.volumeSelector1.currentNode())
        ndarryShape = ndarray.shape
        logging.debug("The shape of the ndarray: " + str(ndarryShape))
        self.shapeValue.setText(ndarryShape)

        # TEST 1
        # ndarray[20:30] = 0
        imageData = logic.getImageData(self.volumeSelector1.currentNode())
        imageData.Modified()

        # TEST 2
        logic.getSubMatrices(self.volumeSelector1.currentNode(), step=[10] * 3)

        logic.showVolume(self.volumeSelector1.currentNode())

    def onVolumeSelect(self):
        self.testBtn.enabled = self.volumeSelector1.currentNode()


#
# Logic
#
class DivideImageLogic(ScriptedLoadableModuleLogic):

    def hasImageData(self, volumeNode):

        if not volumeNode:
            logging.debug("hasImageData failed: no volume node")
            return False
        if volumeNode.GetImageData() is None:
            logging.debug("hasImageData failed: no image data in volume node")
            return False
        return True

    def getImageData(self, volumeNode):

        if self.hasImageData(volumeNode):
            imageData = volumeNode.GetImageData()
            logging.debug("vtkImageData of the volume: " + str(imageData))
            return imageData

    def getNdarray(self, volumeNode):

        if self.hasImageData(volumeNode):
            ndarray = slicer.util.array(volumeNode.GetID())
            logging.debug("Correspondent ndarray:\n" + str(ndarray))
            return ndarray

    def getSubMatrices(self, volumeNode, step=[40] * 3):
        """
        Divide the big matrix into small ones according with `step`
        Return an array containing these sub matrices
        """

        bigMatrix = self.getNdarray(volumeNode)
        shape = bigMatrix.shape
        subMatrices = []

        for i in range(0, shape[0], step[0]):
            for j in range(0, shape[1], step[1]):
                for k in range(0, shape[2], step[2]):
                    subMatrix = bigMatrix[i:i + step[0],
                                          j:j + step[1],
                                          k:k + step[2]
                                          ]
                    # TEST
                    # Make the hull of subMatrix to be 0
                    subMatrix[0, :, :] = 0
                    subMatrix[:, 0, :] = 0
                    subMatrix[:, :, 0] = 0

                    subMatrices.append(subMatrix)

        logging.info("%d subMatrix generated" % len(subMatrices))

        return subMatrices

    def showVolume(self, volumeNode):
        # This is not 3D scene showing.
        applicationLogic = slicer.app.applicationLogic()
        selectionNode = applicationLogic.GetSelectionNode()
        selectionNode.SetSecondaryVolumeID(volumeNode.GetID())
        applicationLogic.PropagateForegroundVolumeSelection(0)


#
# Test
#
class DivideImageTest(ScriptedLoadableModuleTest):

    def setUp(self):
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        self.setUp()
        # self.test1_DivideImage()
        # self.test2_DivideImage()
        self.test3_DivideImage()
        # self.test4_DivideImage()

    def test1_DivideImage(self):
        """
        Generate a 10*10 array and get its topleft and bottomright.
        """

        self.delayDisplay("Run Test No. 1")
        logging.info(
            "\nTest No. 1: Generate a 10*10 array and get its topleft and bottomright.")

        # arr = np.random.randint(0, 101, size=(30, 15))
        arr = np.arange(100).reshape(10, 10)
        logging.info("A 10*10 2D array: \n" + str(arr))

        slice1 = arr[:5, :5]
        slice2 = arr[5:, 5:]
        logging.info("Topleft: \n" + str(slice1))
        logging.info("Bottomright: \n" + str(slice2))
        logging.info("Topleft + Bottomright: \n" + str(slice1 + slice2))

    def test2_DivideImage(self):

        """
        Generate a 10*10 array and get its sub-arrays with given steps.
        """

        self.delayDisplay("Run Test No. 2")
        logging.info(
            "\nTest No. 2: Generate a 2D matrix and divide it into small ones.")

        # arr = np.random.randint(0, 101, size=(30, 15))
        arr = np.arange(100).reshape(10, 10)
        logging.info("A random 2D array: \n" + str(arr))

        step_x, step_y = [3, 3]  # Change the step to see more
        num = 0
        shape_x, shape_y = arr.shape
        for i in range(0, shape_x, step_x):
            for j in range(0, shape_y, step_y):
                slice = arr[i:i + step_x, j:j + step_y]
                num = num + 1
                logging.info("No. %d: \n" % num + str(slice))

        logging.info("%d sub arrays printed" % num)

    def test3_DivideImage(self):

        self.delayDisplay("Run Test No. 3")
        logging.info("\nRun Test No. 3.\n")

        # first, get some data
        import urllib
        downloads = (
            ("http://slicer.kitware.com/midas3/download/item/1697",
             "MR-head.nrrd", slicer.util.loadVolume),
        )

        for url, name, loader in downloads:
            filePath = slicer.app.temporaryPath + '/' + name
            if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
                logging.info(
                    "Requesting download %s from %s...\n" % (name, url))
                urllib.urlretrieve(url, filePath)
            if loader:
                logging.info("Loading %s..." % (name,))
                loader(filePath)
        self.delayDisplay("Finished with download and loading")

        volumeNode = slicer.util.getNode(pattern="MR-head")
        # logging.debug("FA: \n" + str(volumeNode))
        # logic = DivideImageLogic()
        # self.assertTrue(logic.hasImageData(volumeNode))

        # logic.getSubMatrix(volumeNode)  # Wrong! Do NOT access logic here
        moduleWidget = slicer.modules.DivideImageWidget

        moduleWidget.volumeSelector1.setCurrentNode(volumeNode)
        moduleWidget.onTestBtn()

    def test4_DivideImage(self):
        """
        Load an image from disk and do array conversion.
        """
        self.delayDisplay("Run Test No. 4")
        logging.info("\nRun Test No. 4.\n")

        filepath = "/Users/Quentan/Box Sync/IMAGE/spgr.nhdr"
        # filepath = "/Users/Quentan/Develop/IMAGE/MIDAS/Normal-001/MRA/Normal001-MRA.mha"
        slicer.util.loadVolume(filepath)
        volumeNode = slicer.util.getNode(pattern="spgr")
        self.delayDisplay("Image loaded from: " + filepath)

        moduleWidget = slicer.modules.DivideImageWidget
        moduleWidget.volumeSelector1.setCurrentNode(volumeNode)
        moduleWidget.onTestBtn()

        logging.info("Test 4 finished.")
