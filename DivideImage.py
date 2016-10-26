"""
1. Load an image as a numpy array and divide it into small ones
2. Count the subMatrices with some standards
3. Extract point coords from valid subMatix and fit them into implicit surface
"""

# TODO: Visualise the fitting result

import os
import sys
import time
import qt
import slicer
import ctk
import numpy as np
# from multiprocessing import Pool
# from multiprocessing.dummy import Pool as ThreadPool

import vtk
from vtk.util import numpy_support
# from vtk.util import vtkImageImportFromArray
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
        1. Load an image as a numpy array and divide it into small ones
        <br><br>2. Count the subMatrices with some standards
        <br><br>3. Extract point coords from valid subMatix and fit them into implicit surface
        """
        self.parent.acknowledgementText = """
        Thanks.
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
        self.testBtn = qt.QPushButton("Divide Image")
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
        self.testBtn2.connect('clicked(bool)', self.onTestBtn2)

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
        """
        ctkCoordinatesWidget.coordinates needs unicode/str like: `u'10, 20, 30'`
        """
        if len(step) != 3:
            logging.debug("Step should be given as [intX, intY, intZ]")
            return False

        # unicodeStep = [unicode(i) for i in step]  # Wrong
        unicodeStep = str(step)[1: -1]  # trim the `[]` symbol
        print unicodeStep
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
        # self.numSubMatricesValue.setText('')
        self.testBtn.setText("TEST 1")
        self.divideStepWidget.coordinates = '33, 10, 10'

    def onTestBtn(self):
        """
        Divide the big image into small chunks
        Title of the button will change
        """
        logic = DivideImageLogic()
        logging.info("Logic is instantiated.")

        volumeNode = self.volumeSelector1.currentNode()
        ndarray = logic.getNdarray(volumeNode)
        ndarryShape = ndarray.shape
        self.volumeLabel.setText("Volume " + str(ndarryShape) + ':')
        logging.debug("The shape of the ndarray: " + str(ndarryShape))

        # Get subMatrices with given step
        self.setDivideStep(step=[20] * 3)
        divideStep = self.getDivideStep()
        # subMatrices = logic.getSubMatrices(volumeNode, divideStep)

        #
        # TEST: Use getValidSubMatrices
        # REVIEW: ~VERY slow~ -> It's been very quick by vectorisation
        startTime = time.time()
        subMatrices, isValidSubMatrices = logic.getValidSubMatrices(
            volumeNode, divideStep)
        # numValidSubMatrices = sum(item is True for item in isValidSubMatrices)
        numValidSubMatrices = np.sum(isValidSubMatrices)
        logging.info("--- getValidSubMatrices uses %s seconds ---" %
                     (time.time() - startTime))

        # logging.info("There are " + str(numValidSubMatrices) +
        #              " valid subMatrices")
        logging.info(str(numValidSubMatrices) + '/' + str(len(subMatrices)) +
                     " valid subMatrices generated")

        # TEST chop subMatrices
        startTime = time.time()
        for subMatrix in subMatrices:
            logic.chopSubMatrix(subMatrix)
        logging.info("Time taken: {}".format(time.time() - startTime))

        # TEST chop subMatrices with multiprocessing
        # threadNum = 8
        # startTime = time.time()
        # pool = ThreadPool(threadNum)
        # pool.map(logic.chopSubMatrix, subMatrices)
        # pool.close()
        # pool.join()
        # logging.info("Time taken: {}".format(time.time() - startTime))

        self.testBtn.setText(str(numValidSubMatrices) + '/' +
                             str(len(subMatrices)) + "\nValid Sub Matrices")

        # Update the image
        imageData = logic.getImageData(volumeNode)
        imageData.Modified()

        # logic.showVolume(self.volumeSelector1.currentNode())
        # logic.getImageInfo(imageData)

        # volume rendering
        lm = slicer.app.layoutManager()
        lm.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpView)
        logic.showVolumeRendering(volumeNode)
        # logic.showVtkImageData(imageData)

    def onTestBtn2(self):
        """
        Get the fitting points of a specific subMatix
        Not visulaised yet
        """
        logic = DivideImageLogic()
        logging.info("Logic is instantiated.")

        # Load data
        volumeNode = self.volumeSelector1.currentNode()

        # Get the imageData from the data
        imageData = logic.getImageData(volumeNode)
        imageInfo = logic.getImageInfo(imageData)
        logging.debug("ImageInfo:\n" + str(imageInfo))

        # Get the numpy array from the data
        ndarray = logic.getNdarray(volumeNode)
        ndarryShape = ndarray.shape
        self.volumeLabel.setText("Volume " + str(ndarryShape) + ':')
        logging.debug("The shape of the ndarray: " + str(ndarryShape))

        #
        # Get subMatrices with given step
        self.setDivideStep([20] * 3)
        divideStep = self.getDivideStep()
        # divideStep = [20] * 3
        # subMatrices = logic.getSubMatrices(volumeNode, divideStep)
        subMatrices, isValidSubMatrices = logic.getValidSubMatrices(
            volumeNode, divideStep)
        numValidSubMatrices = np.sum(isValidSubMatrices)
        logging.info(str(numValidSubMatrices) + '/' + str(len(subMatrices)) +
                     " valid subMatrices generated")

        # TEST: find a valid subMatrix and fitting the points
        # i = 3711
        idxValidMatrices = [i for i, x in enumerate(isValidSubMatrices) if x]
        testValidMatrix = np.random.choice(idxValidMatrices)
        # logging.info("This is subMatix " + str(testValidMatrix))
        coords = logic.getCoords(subMatrices[testValidMatrix])
        np.savetxt('/tmp/coords.txt', coords)
        logging.info("Random subMatix " + str(testValidMatrix) + " has " +
                     str(len(coords)) + " valid points")

        # vectorColume = logic.implicitFitting(coords)
        # logging.debug("Vector of colume:\n" + str(vectorColume))
        # fittingResult = logic.radialBasisFunc(vectorColume, coords)
        # logging.debug("Fitting Result as matrix:\n" + str(fittingResult))
        # # print fittingResult.shape
        #
        # # volume rendering
        # # logic.showVolumeRendering(volumeNode)
        #
        # # Show vtkImageData
        # imageData = logic.ndarray2vtkImageData(fittingResult)
        # # print type(imageData)
        # logic.showVtkImageData(imageData)

    # TEST cases
    def test_getValidSubMatrices(self):
        logic = DivideImageLogic()
        logging.info("Logic is instantiated.")

        volumeNode = self.volumeSelector1.currentNode()
        ndarray = logic.getNdarray(volumeNode)
        ndarryShape = ndarray.shape
        self.volumeLabel.setText("Volume " + str(ndarryShape) + ':')
        logging.debug("The shape of the ndarray: " + str(ndarryShape))

        # Get subMatrices with given step
        divideStep = self.getDivideStep()

        startTime = time.time()
        subMatrices, isValidSubMatrices = logic.getValidSubMatrices(
            volumeNode, divideStep)
        logging.info("--- getValidSubMatrices uses %s seconds ---" %
                     (time.time() - startTime))
        numValidSubMatrices = sum(item is True for item in isValidSubMatrices)

        # logging.info("There are " + str(numValidSubMatrices) +
        #              " valid subMatrices")
        logging.info("There are %s valid subMatrices" %
                     str(numValidSubMatrices))

    def test_getSubMatrices(self):
        logic = DivideImageLogic()
        logging.info("Logic is instantiated.")

        volumeNode = self.volumeSelector1.currentNode()
        ndarray = logic.getNdarray(volumeNode)
        ndarryShape = ndarray.shape
        self.volumeLabel.setText("Volume " + str(ndarryShape) + ':')
        logging.debug("The shape of the ndarray: " + str(ndarryShape))

        # Get subMatrices with given step
        divideStep = self.getDivideStep()

        startTime = time.time()
        subMatrices = logic.getSubMatrices(volumeNode, divideStep)
        numValidSubMatrices = 0
        for subMatrix in subMatrices:
            if logic.isValidMatrix(subMatrix):
                numValidSubMatrices = numValidSubMatrices + 1
        logging.info("--- getSubMatrices uses %s seconds ---" %
                     (time.time() - startTime))

        logging.info("There are %s valid subMatrices" %
                     str(numValidSubMatrices))

    def test_getCoords(self):
        """
        TEST getCoords
        Get coords from a valid random subMatrix
        """
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
        length = len(subMatrices)
        randomNum = np.random.randint(length * 0.3, length * 0.7)
        logging.info("This is subMatrix No." + str(randomNum))

        startTime = time.time()
        coords = logic.getCoords(subMatrices[randomNum])
        logging.info("--- getCoords uses %s seconds ---" %
                     (time.time() - startTime))

        if coords is not False:
            # self.delayDisplay("test")  # It should be used in `Test`
            logging.info("There are " + str(len(coords)) +
                         " valid points in subMatrix " + str(randomNum))
        else:
            logging.info("subMatix " + str(randomNum) + " is invalid")


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
        @param volumeNode   slicer.qMRMLNodeComboBox().currentNode()
        @param step         shape of subMatrix
        @return             an array containing these sub matrices
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
                    subMatrices.append(subMatrix)

        logging.debug("%d subMatrices generated" % len(subMatrices))

        return subMatrices

    def getValidSubMatrices(self, volumeNode, step=[40] * 3):
        """
        Divide the big matrix into small ones according with `step`
        Mark the valid subMatrices
        @param volumeNode   slicer.qMRMLNodeComboBox().currentNode()
        @param step         shape of subMatrix
        @return 1           an array containing these sub matrices
        @return 2           a boolean array shows the validation of sub matrices
        """

        bigMatrix = self.getNdarray(volumeNode)
        shape = bigMatrix.shape
        subMatrices = []
        isValidSubMatrices = []

        for i in range(0, shape[0], step[0]):
            for j in range(0, shape[1], step[1]):
                for k in range(0, shape[2], step[2]):
                    subMatrix = bigMatrix[i:i + step[0],
                                          j:j + step[1],
                                          k:k + step[2]
                                          ]
                    subMatrices.append(subMatrix)  # 1D list

                    isValid = self.isValidMatrix(subMatrix)
                    isValidSubMatrices.append(isValid)  # 1D list

        logging.debug("%d subMatrices generated" % len(subMatrices))

        return subMatrices, isValidSubMatrices

    def chopSubMatrix(self, subMatrix, value=0):
        """
        A test foo of Making the hull of the given subMatrix to be `value`
        @param subMatrix    a 3D array
        @param value        grey value of the hull
        @return boolen      `False` if the array is not 3D
        """
        if len(subMatrix.shape) == 3:
            subMatrix[0, :, :] = value
            subMatrix[:, 0, :] = value
            subMatrix[:, :, 0] = value
            return True
        else:
            logging.debug("Dimension of the give subMatix is not 3!")
            return False

    def isValidMatrix(self, subMatrix, range=[90, 100]):
        """
        Determine the validation of subMatrix with a standard
        The standard could be complex
        @param subMatrix    test array
        @param range        a grey value range
        @return boolen      `True` if contains at least 10% points in the range
        """
        length = len(subMatrix)
        num = 0

        # for index, item in np.ndenumerate(subMatrix):
        #     if item >= range[0] and item <= range[1]:
        #         num = num + 1

        # vectorise the loop. About 100 times faster than loop
        y1 = subMatrix >= range[0]  # boolean
        y2 = subMatrix <= range[1]
        y = y1 * y2
        num = np.sum(y)  # It is much much faster than its loop counterpart
        # num = sum(i for i in y.ravel())

        logging.debug("Number of valid point: " + str(num))  # SLOW!!

        if num / length >= 0.1:
            return True
        else:
            return False

    def getCoords(self, subMatrix, range=[90, 100]):
        """
        Get the coords of valid point from a subMatrix
        NOTE: `implicitFitting` requires `ndarray`
        @param subMatrix    array containing valide points
        @param range        a grey value range
        @return ndarray     a n*3 numpy array
        @retrun False       invalid array
        """
        coords = []
        # Method 1. Very slow
        # for coord, value in np.ndenumerate(subMatrix):
        #     if value >= range[0] and value <= range[1]:
        #         coords.append(coord)  # type 'list'

        y1 = subMatrix >= range[0]
        y2 = subMatrix <= range[1]
        y = y1 * y2

        # Method 2. About 100 times faster than Method 1
        # for coord, value in np.ndenumerate(y):
        #     if value:  # NOTE: CANNOT be `value is True`
        #         coords.append(coord)  # type 'list'

        # Method 3. About 4 times faster than Method 2
        coords = np.transpose(y.nonzero())  # type 'numpy.ndarray'

        if len(coords) / len(subMatrix) >= 0.1:
            logging.debug("Valid subMatrix")
            # return np.asarray(coords)  # type 'numpy.ndarray'
            return coords
        else:
            logging.error("Invalid subMatrix")
            return False

    def getImageInfo(self, imageData):
        """
        Record information of vtkImageData into a dict.
        All these info can be acquired by `imageData.GetXXX()`
        @param imageData    vtkImageData var
        @return dict        a dict containing these information
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

        logging.debug("imageInfo: \n" + str(imageInfo))
        return imageInfo

    def showVolume(self, volumeNode):
        # This is not 3D scene showing.
        applicationLogic = slicer.app.applicationLogic()
        selectionNode = applicationLogic.GetSelectionNode()
        selectionNode.SetSecondaryVolumeID(volumeNode.GetID())
        applicationLogic.PropagateForegroundVolumeSelection(0)

    def showVolumeRendering(self, volumeNode):
        """
        Show the volume rendering in the 4th view layout
        @volumeNode     `volumeSelector1.currentNode()`
        """
        logic = slicer.modules.volumerendering.logic()
        # REVIEW: Slicer 4.6 has fixed the GPU volume rendering issue on Mac!
        # if sys.platform == 'darwin':  # GPU rendering does not work on Mac
        #     displayNode = logic.CreateVolumeRenderingDisplayNode('vtkMRMLCPURayCastVolumeRenderingDisplayNode')
        # else:
        # displayNode = logic.CreateVolumeRenderingDisplayNode()  # GPU
        # rendering
        displayNode = logic.CreateVolumeRenderingDisplayNode()  # GPU rendering
        slicer.mrmlScene.AddNode(displayNode)
        displayNode.UnRegister(logic)
        logic.UpdateDisplayNodeFromVolumeNode(displayNode, volumeNode)
        volumeNode.AddAndObserveDisplayNodeID(displayNode.GetID())

    def showVtkImageData(self, imageData):
        """
        Create a volume node from scratch
        See "https://www.slicer.org/slicerWiki/index.php/Documentation/4.5/Modules/Volumes"
        """
        # imageData = vtk.vtkImageData()
        # imageData.SetDimensions(dims)
        # imageData.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)  # TODO: need
        # change
        volumeNode = slicer.vtkMRMLScalarVolumeNode()
        volumeNode.SetAndObserveImageData(imageData)
        displayNode = slicer.vtkMRMLScalarVolumeDisplayNode()
        slicer.mrmlScene.AddNode(volumeNode)
        slicer.mrmlScene.AddNode(displayNode)
        volumeNode.SetAndObserveDisplayNodeID(displayNode.GetID())
        displayNode.SetAndObserveColorNodeID('vtkMRMLColorTableNodeGrey')

        # displayNode.AddViewNode(volumeNode)

    def implicitFitting(self, data):
        """
        Find the fitting according to input dataset
        @param data     point_num*3 array, every row is a 3D point
        @return ndarray colume vector: point_num*1
        """

        num_points = len(data)

        A = np.zeros((num_points, num_points))

        for i in range(num_points):
            for j in range(i + 1, num_points):
                A[i, j] = np.linalg.norm(data[i, :] - data[j, :])
                A[j, i] = A[i, j]

        # NOTE: it's no use to transpose a 1D array
        # dx = data[:, 0].reshape(num_points, 1)
        # dy = data[:, 1].reshape(num_points, 1)
        # dz = data[:, 2].reshape(num_points, 1)

        dx = data[:, 0][None].T
        dy = data[:, 1][None].T
        dz = data[:, 2][None].T

        B = np.hstack((np.ones((num_points, 1)),
                       2 * dx, 2 * dy, 2 * dz,
                       2 * dx * dy, 2 * dx * dz, 2 * dy * dz,
                       dx * dx, dy * dy, dz * dz)
                      )

        M_t1 = np.concatenate((A, B.T))
        M_t2 = np.concatenate((B, np.zeros((10, 10))))
        M = np.concatenate((M_t1, M_t2), axis=1)  # It is sysmmetric

        k = np.random.randint(4, 10000)
        C0 = np.zeros((3, 3))
        C1 = np.diag([-k] * 3)
        C2 = np.ones((3, 3)) * (k - 2) / 2.0
        np.fill_diagonal(C2, -1)
        C11 = np.concatenate((C1, C0))
        C22 = np.concatenate((C0, C2))
        C = np.concatenate((C11, C22), axis=1)
        invC = np.linalg.inv(C)  # for Generalised Eigenvalue Problem

        M11 = M[0:-6, 0:-6]  # (num_points) * (num_points)
        M12 = M[0:-6, -6:]  # (num_point-6) * 6
        M22 = M[-6:, -6:]  # 6 * 6 zero matrix

        pinvM11 = np.linalg.pinv(M11)
        M0 = np.dot(pinvM11, M12)
        M00 = M22 - np.dot(M12.T, M0)

        # eigen_value, eigen_vec = np.linalg.eig(M00)
        # positive = eigen_value > 0
        # if np.sum(positive) < len(positive):  # Not positive. Always False
        #     M00 = np.dot(M00.T, M00)
        #     eigen_value, eigen_vec = np.linalg.eig(np.dot(invC, M00))
        #     logging.info("Not Positive Definite")

        eigen_value, eigen_vec = np.linalg.eig(np.dot(invC, M00))
        # D = np.diag(eigen_value)
        # max_eigen_value = np.amax(eigen_value)
        max_eigen_idx = np.argmax(eigen_value)

        # Find the fitting
        V1 = eigen_vec[:, max_eigen_idx]
        V0 = np.dot(-M0, V1)
        V = np.hstack((V0, V1))
        vector = V.reshape(num_points + 10, 1)  # a 1-column array
        # NOTE: V is the found fitting!

        return vector

    #
    # RBF Ellipsoid fitting
    def radialBasisFunc(self, vector, data):
        """
        Radial Basis Function fitting
        @param vector   found fitting
        @param data     point_num*3 array, every row is a 3D point
        @return ndarray an object in ndarray format
        """

        w = vector[-10:]
        num_points = len(data)

        # Step
        data_min = data.min(0)
        data_max = data.max(0)

        step = 0.1
        offset = 0.1
        step_x = np.arange(data_min[0] - offset, data_max[0] + offset, step)
        step_y = np.arange(data_min[1] - offset, data_max[1] + offset, step)
        step_z = np.arange(data_min[2] - offset, data_max[2] + offset, step)

        [x, y, z] = np.meshgrid(step_x, step_y, step_z)

        poly = w[0] * np.ones((x.shape)) + \
            2 * w[1] * x + 2 * w[2] * y + 2 * w[3] * z + \
            2 * w[4] * x * y + 2 * w[5] * x * z + 2 * w[6] * y * z + \
            w[7] * x * x + w[8] * y * y + w[9] * z * z

        radial = np.zeros((x.shape))
        for i in range(num_points):
            radial = radial + vector[i] * np.sqrt(
                (x - data[i, 0])**2 + (y - data[i, 1])**2 + (z - data[i, 2])**2)

        obj = poly + radial  # type 'numpy.ndarray'
        logging.debug("obj.shape: " + str(obj.shape))
        logging.debug("Type of obj: " + str(type(obj)))

        return obj

    def ndarray2vtkImageData(self, numpyArray, castType=0,
                             spacing=[1, 1, 1], origin=[-1, -1, -1]):
        """
        Convert a NumPy array to a vtkImageData, no cast by default
        @param numpyArray   input 3D NumPy array
        @param castType
            0 - No casting
            2 - VTK_CHAR
            3 - VTK_UNSIGNED_CHAR
            4 - VTK_SHORT
            5 - VTK_UNSIGNED_SHORT
            6 - VTK_INT
            7 - VTK_UNSIGNED_INT
            8 - VTK_LONG
            9 - VTK_UNSIGNED_LONG
            10 - VTK_FLOAT
            11 - VTK_DOUBLE
        @return vtkImageData
        """
        # numpy array --> VTK array (vtkFloatArray)
        vtk_data_array = numpy_support.numpy_to_vtk(
            num_array=numpyArray.transpose(2, 1, 0).ravel(),
            deep=True,
            array_type=vtk.VTK_FLOAT)

        # VTK array (vtkFloatArray) --> vtkImageData
        img_vtk = vtk.vtkImageData()
        img_vtk.SetDimensions(numpyArray.shape)
        img_vtk.SetSpacing(spacing)
        img_vtk.SetOrigin(origin)  # default numpy origina is [-1, -1, -1]
        img_vtk.GetPointData().SetScalars(vtk_data_array)  # is a vtkImageData

        # casting
        if castType == 0:  # No casting
            return img_vtk

        elif castType in [i for i in range(2, 12)]:
            cast = vtk.vtkImageCast()
            cast.SetInputData(img_vtk)
            # cast.SetInputConnection(reader.GetOutputPort())
            cast.SetOutputScalarType(castType)
            cast.Update()
            return cast.GetOutput()  # The output of `cast` is a vtkImageData

        # Wrong cast type. Return the no-cast vtkImageData
        else:
            logging.ERROR("Wrong Cast Type! It MUST be 2, 3, ..., or 11")
            return img_vtk


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
        # self.test_EmptyVolume()

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
        moduleWidget = slicer.modules.DivideImageWidget
        moduleWidget.volumeSelector1.setCurrentNode(volumeNode)
        # moduleWidget.onTestBtn()
        moduleWidget.onTestBtn2()

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
        # moduleWidget.onTestBtn2()
        # moduleWidget.test_getSubMatrices()  # ~29.6~ --> 0.039 seconds
        # moduleWidget.test_getValidSubMatrices()  # 29.2 seconds --> 0.3595s
        # moduleWidget.test_getCoords()  # 0.0004s --> 0.0001s

        logging.info("Test 4 finished.")

    def test_EmptyVolume(self):
        imageSize = [64] * 3
        imageSpacing = [1.0, 1.0, 1.0]
        voxelType = vtk.VTK_UNSIGNED_CHAR
        # Create an empty image volume
        imageData = vtk.vtkImageData()
        imageData.SetDimensions(imageSize)
        imageData.AllocateScalars(voxelType, 1)
        thresholder = vtk.vtkImageThreshold()
        thresholder.SetInputData(imageData)
        thresholder.SetInValue(0)
        thresholder.SetOutValue(0)
        # Create volume node
        volumeNode = slicer.vtkMRMLScalarVolumeNode()
        volumeNode.SetSpacing(imageSpacing)
        volumeNode.SetImageDataConnection(thresholder.GetOutputPort())
        # Add volume to scene
        slicer.mrmlScene.AddNode(volumeNode)
        displayNode = slicer.vtkMRMLScalarVolumeDisplayNode()
        slicer.mrmlScene.AddNode(displayNode)
        colorNode = slicer.util.getNode('Grey')
        displayNode.SetAndObserveColorNodeID(colorNode.GetID())
        volumeNode.SetAndObserveDisplayNodeID(displayNode.GetID())
        volumeNode.CreateDefaultStorageNode()
