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
        self.volumeLabel = qt.QLabel()
        self.volumeLabel.setText("Volume:")
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
        _layout.addRow(self.volumeLabel, self.volumeSelector1)

        #
        # Divide step
        self.divideStepLabel = qt.QLabel()
        self.divideStepLabel.setText("Divide step (X, Y, Z): ")
        self.divideStepWidget = ctk.ctkCoordinatesWidget()
        self.divideStepWidget.decimals = 0
        self.divideStepWidget.minimum = 10  # pixel
        self.divideStepWidget.maximum = 100  # pixel
        _layout.addRow(self.divideStepLabel, self.divideStepWidget)

        # Test button No. 1
        self.testBtn = qt.QPushButton("TEST 1")
        self.testBtn.toolTip = "Autometic test work"
        self.testBtn.enabled = self.volumeSelector1.currentNode()

        # Test button No. 2
        self.testBtn2 = qt.QPushButton("TEST 2")
        self.testBtn2.toolTip = "Divide Image and Get 1 valid subMatix"
        self.testBtn2.enabled = self.volumeSelector1.currentNode()

        # Clean Scene button
        self.cleanSceneBtn = qt.QPushButton("Clean Scene")
        self.cleanSceneBtn.toolTip = "Clean the current mrmlScene"
        self.cleanSceneBtn.enabled = self.volumeSelector1.currentNode()

        # TEST layout, 3 columns
        testLayout = qt.QFormLayout()
        testLayout.addRow(self.testBtn, self.testBtn2)
        _layout.addRow(self.cleanSceneBtn, testLayout)

        # Vertical spacer
        self.layout.addStretch(1)

        # Connection
        self.volumeSelector1.connect('currentNodeChanged(bool)',
                                     self.onVolumeSelectChanged)
        self.cleanSceneBtn.connect('clicked(bool)', self.onCleanSceneBtn)
        self.testBtn.connect('clicked(bool)', self.onTestBtn)

    #
    # Getter & Setter
    #
    def getDivideStep(self):
        unicodeStep = self.divideStepWidget.coordinates  # unicode list
        if unicodeStep:
            divideStep = [int(x) for x in unicodeStep.split(',')]  # int list
            return divideStep
        else:
            logging.info("Divide Step is invalid")
            return False

    def setDivideStep(self, step=[10] * 3):
        if len(step) is not 3:
            logging.debug("Step should be given as [intX, intY, intZ]")
            return False

        unicodeStep = [unicode(i) for i in step]  # coordinates need unicode
        self.divideStepWidget.coordinates = unicodeStep

        return True

    #
    # Response functions
    #
    def onVolumeSelectChanged(self):
        if self.volumeSelector1.currentNode()is None:
            self.testBtn.enabled = False
            self.testBtn2.enabled = False
            self.cleanSceneBtn.enabled = False
        else:
            self.testBtn.enabled = True
            self.testBtn2.enabled = True
            self.cleanSceneBtn.enabled = True

    def onCleanSceneBtn(self):
        slicer.mrmlScene.Clear(0)
        self.cleanSceneBtn.enabled = False
        self.testBtn.enabled = False
        self.testBtn2.enabled = False
        self.volumeLabel.setText("Volume:")
        self.numSubMatricesValue.setText('')
        self.testBtn.setText("TEST 1")
        self.divideStepWidget.coordinates = '10, 10, 10'

    def onTestBtn(self):
        logic = DivideImageLogic()
        logging.info("Logic is instantiated.")

        volumeNode = self.volumeSelector1.currentNode()
        ndarray = logic.getNdarray(volumeNode)
        ndarryShape = ndarray.shape
        self.volumeLabel.setText("Volume " + str(ndarryShape) + ':')
        logging.debug("The shape of the ndarray: " + str(ndarryShape))

        # Get subMatrices with given step
        divideStep = self.getDivideStep()
        subMatrices = logic.getSubMatrices(volumeNode, divideStep)
        self.testBtn.setText(str(len(subMatrices)) + "\nSub Matrices")

        # TEST chop subMatrices
        # for subMatrix in subMatrices:
        #     logic.chopSubMatrix(subMatrix)

        # TEST getCoords
        length = len(subMatrices)
        randomNum = np.random.randint(length * 0.3, length * 0.7)
        logging.info("This is subMatrix No." + str(randomNum))
        coords = logic.getCoords(subMatrices[randomNum])
        if coords:
            # self.delayDisplay("test")  # It should be used in `Test`
            logging.info("There are " + str(len(coords)) + " valid points in subMatrix " + str(randomNum))
            # num = 1
            # logging.info("Coords of valide point in subMatrix " + str(randomNum) + ":")
            # for coord in coords:
            #     logging.info("No. " + str(num) + ": " + str(coord))  # SLOW!
            #     num = num + 1
        else:
            logging.info("subMatix " + str(randomNum) + " is invalid")

        # Update the image
        imageData = logic.getImageData(volumeNode)
        imageData.Modified()

        # logic.showVolume(self.volumeSelector1.currentNode())
        # logic.getImageInfo(imageData)


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
                    subMatrices.append(subMatrix)

        logging.info("%d subMatrices generated" % len(subMatrices))

        return subMatrices

    # TEST function
    def chopSubMatrix(self, subMatrix, value=0):
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
        logging.info("\n\nRun Test No. 4.\n")

        filepath = "/Users/Quentan/Box Sync/IMAGE/MR-head.nrrd"
        slicer.util.loadVolume(filepath)
        volumeNode = slicer.util.getNode(pattern="MR-head")
        self.delayDisplay("Image loaded from: " + filepath)

        moduleWidget = slicer.modules.DivideImageWidget
        moduleWidget.volumeSelector1.setCurrentNode(volumeNode)
        moduleWidget.onTestBtn()

        logging.info("Test 4 finished.")
