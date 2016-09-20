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
        self.parent.contributors = ["Quan Qi (Univeristy of Hull)"]
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

        #
        # Divide step
        self.divideStepLabel = qt.QLabel()
        self.divideStepLabel.setText("Divide step: ")
        self.divideStepValue = qt.QLabel()
        _layout.addRow(self.divideStepLabel, self.divideStepValue)

        #
        # Number label for sub matrices
        self.numSubMatricesLabel = qt.QLabel()
        self.numSubMatricesLabel.setText("Number of sub matrices: ")
        self.numSubMatricesValue = qt.QLabel()
        _layout.addRow(self.numSubMatricesLabel, self.numSubMatricesValue)

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

        volumeNode = self.volumeSelector1.currentNode()
        ndarray = logic.getNdarray(volumeNode)
        ndarryShape = ndarray.shape
        logging.debug("The shape of the ndarray: " + str(ndarryShape))
        self.shapeValue.setText(ndarryShape)

        # Get subMatrices with given step
        divideStep = (10, 10, 10)
        self.divideStepValue.setText(divideStep)
        subMatrices = logic.getSubMatrices(volumeNode, divideStep)
        self.numSubMatricesValue.setText(len(subMatrices))



        imageData = logic.getImageData(volumeNode)
        imageData.Modified()

        # logic.showVolume(self.volumeSelector1.currentNode())
        logic.getImageInfo(imageData)

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
        else:
            logging.error("Error: Failed to get ImageData!")
            return False

    def getNdarray(self, volumeNode):

        if self.hasImageData(volumeNode):
            ndarray = slicer.util.array(volumeNode.GetID())
            logging.debug("Correspondent ndarray:\n" + str(ndarray))
            return ndarray
        else:
            logging.error("Error: Failed to get ndarray!")
            return False

    def getSubMatrices(self, volumeNode, step=[40] * 3):
        """
        Divide the big matrix into small ones according with `step`
        Return an array containing these sub matrices
        """

        bigMatrix = self.getNdarray(volumeNode)
        shape = bigMatrix.shape
        subMatrices = []
        # num = 0

        for i in range(0, shape[0], step[0]):
            for j in range(0, shape[1], step[1]):
                for k in range(0, shape[2], step[2]):
                    subMatrix = bigMatrix[i:i + step[0],
                                          j:j + step[1],
                                          k:k + step[2]
                                          ]
                    # num = num + 1
                    # # TEST
                    # # Make the hull of subMatrix to be 0
                    # subMatrix[0, :, :] = 0
                    # subMatrix[:, 0, :] = 0
                    # subMatrix[:, :, 0] = 0
                    #
                    # # TEST
                    # # Decide this matrix is valid or not
                    # isValid = self.isValidMatrix(subMatrix)
                    # logging.debug("Sub matrix No." + str(num) + " is " + str(isValid))

                    subMatrices.append(subMatrix)

        logging.info("%d subMatrices generated" % len(subMatrices))

        return subMatrices

    # TEST function
    def cropSubMatrix(self, subMatrix, value=0):
        """
        Make the hull of the given subMatrix to be `value`
        """
        if len(subMatrix.shape) == 3:
            subMatrix[0, :, :] = value
            subMatrix[:, 0, :] = value
            subMatrix[:, :, 0] = value
            return True
        else:
            logging.debug("Dimension of the give subMatix is not 3!")
            return False

    # Deprecated
    def isValidMatrix(self, subMatrix, range=[90, 100]):
        """
        Return `True` this matrix contains at least 10% points
        in the range
        """
        length = len(subMatrix)
        num = 0

        # for index, item in enumerate(subMatrix.flatten()):
        #     if item >= range[0] and item <= range[1]:
        #         num = num + 1

        for index, item in np.ndenumerate(subMatrix):
            if item >= range[0] and item <= range[1]:
                num = num + 1

        logging.info("Number of valid point: " + str(num))  # SLOW!!

        if num / length >= 0.1:
            return True
        else:
            return False

        # TODO: use ndenumerate to do the stuff. Done!

    def getCoords(self, subMatrix, range=[90, 100]):
        """
        Return coords of valid point from a subMatrix
        Return `False` if the subMatix is invalid
        """
        coords = []
        for coord, value in np.ndenumerate(subMatrix):
            if value >= range[0] and value <= range[1]:
                coords.append(coord)

        if len(coords) / len(subMatrix) >= 0.1:
            logging.debug("Valid subMatrix")
            return coords
        else:
            logging.info("Invalid subMatrix")
            return False

    def getImageInfo(self, imageData):
        """
        Record information of vtkImageData into a dict.
        All these info can be acquired by `imageData.GetXXX()`
        """
        imageInfo = {}
        origin = imageData.GetOrigin()
        spacing = imageData.GetSpacing()
        extent = imageData.GetExtent()
        centre = imageData.GetCenter()
        dimensions = imageData.GetDimensions()
        number = imageData.GetNumberOfPoints()
        valueMax = imageData.GetScalarTypeMax()
        valueMin = imageData.GetScalarTypeMin()
        length = imageData.GetLength()  # what is it?
        dataType = imageData.GetScalarTypeAsString()

        imageInfo = {'origin': origin,
                     'spacing': spacing,
                     'extent': extent,
                     'centre': centre,
                     'dimensions': dimensions,
                     'number': number,
                     'valueMax': valueMax,
                     'valueMin': valueMin,
                     'length': length,
                     'dataType': dataType
                     }

        logging.info("imageInfo: \n" + str(imageInfo))
        return imageInfo

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
        # self.test3_DivideImage()
        self.test4_DivideImage()

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

        # self.delayDisplay("Run Test No. 3")
        logging.info("\nRun Test No. 3.\n")

        # first, get some data
        import urllib
        downloads = (
            ("http://slicer.kitware.com/midas3/download/item/1697",
             "MR-head.nrrd", slicer.util.loadVolume),
        )

        for url, name, loader in downloads:
            # filePath = slicer.app.temporaryPath + '/' + name
            filePath = os.path.join(slicer.app.temporaryPath, name)
            if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
                logging.info(
                    "Requesting download %s from %s...\n" % (name, url))
                urllib.urlretrieve(url, filePath)
            if loader:
                logging.info("Loading %s..." % (name,))
                loader(filePath)
        self.delayDisplay("Finished with download and loading")

        volumeNode = slicer.util.getNode(pattern="MR-head")
        logic = DivideImageLogic()
        self.assertTrue(logic.hasImageData(volumeNode))

        # logic.getSubMatrix(volumeNode)  # Wrong! Do NOT access logic here
        moduleWidget = slicer.modules.DivideImageWidget

        moduleWidget.volumeSelector1.setCurrentNode(volumeNode)
        moduleWidget.onTestBtn()

        logging.info("Test 3 finished.")

    def test4_DivideImage(self):
        """
        Load an image from disk and do array conversion.
        """
        self.delayDisplay("Run Test No. 4")
        logging.info("\nRun Test No. 4.\n")

        filepath = "/Users/Quentan/Box Sync/IMAGE/MR-head.nrrd"
        slicer.util.loadVolume(filepath)
        volumeNode = slicer.util.getNode(pattern="MR-head")
        self.delayDisplay("Image loaded from: " + filepath)

        moduleWidget = slicer.modules.DivideImageWidget
        moduleWidget.volumeSelector1.setCurrentNode(volumeNode)
        moduleWidget.onTestBtn()

        logging.info("Test 4 finished.")
