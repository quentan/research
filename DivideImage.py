"""
1. Load an image as a numpy array and divide it into small ones
2. Count the subMatrices with some standards
3. Extract point coords from valid subMatix and fit them into implicit surface
"""

# TODO: Refer `ContourWidget.py` to add some interactive operation
# TODO: design a `MedicalMatrix` class

import os
# import sys
import time
import urllib
import qt
import slicer
import ctk
import numpy as np
# from multiprocessing import Pool
# from multiprocessing.dummy import Pool as ThreadPool

import vtk
from vtk.util import numpy_support
from vtk.util import colors
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
# class: `MedicalMatrix`
#
class MedicalMatrix(vtk.vtkImageData):
    """
    - The class `MedicalMatrix` should:
      - designed for subMatrices
      - keeps a copy of the original medical image part.
      - or keeps a pointer to the original medical image part.
      - keeps a same-size auxiliary 3D ndarray
      - keeps data structure to find its 6-neighbours
      - keeps its "origin point" in the original medical image
      - keeps a flag: whether it is valid
      - keeps a coordinates array, if it is valid
      - be able to convert `vtkImageData` to `ndarray` and vice versa.
      - ?? be able to slice the 3D matrix to a set of 2D arrays
      - have basic matrix operations. (for 3D or 2D?)
      - keeps a "density" parameter
      - keeps both "1st, 2nd, 3rd..." and "[x, y, z]" orders
      - ...
    - Notice
      - list or dict?
    """
    pass


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

    def onReload(self):
        ScriptedLoadableModuleWidget.onReload(self)

        # DivideImageVTKLogic().clearActors()
        # Clear vtkActor when reloading. But remain outline and direction symbols
        renderer = slicer.app.layoutManager().threeDWidget(0).threeDView().renderWindow().GetRenderers().GetFirstRenderer()
        getActors = renderer.GetActors()
        numActor = getActors.GetNumberOfItems()
        logging.debug("numActor in onReload: " + str(numActor))
        if numActor > 10:  # renderer has 10 actors when start
            counter = numActor - 10
            while counter > 0:
                renderer.RemoveActor(getActors.GetLastActor())
                counter -= 1

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
# VTK
#
class DivideImageVTKLogic(ScriptedLoadableModuleLogic):

    def __init__(self, isInsideRenWin=True):
        # ScriptedLoadableModuleLogic.__init__(self, parent)
        iren = vtk.vtkRenderWindowInteractor()

        if isInsideRenWin:
            renderWin = slicer.app.layoutManager().threeDWidget(0).threeDView().renderWindow()
            renderer = renderWin.GetRenderers().GetFirstRenderer()
        else:
            renderWin = vtk.vtkRenderWindow()
            renderWin.SetSize(640, 480)
            renderWin.SetWindowName("VTK Rendering View")

            renderer = vtk.vtkRenderer()
            renderer.SetBackground(0.2, 0.3, 0.4)

            interactorStyle = vtk.vtkInteractorStyleTrackballCamera()
            iren.SetInteractorStyle(interactorStyle)

        self.renderWin = renderWin
        self.renderer = renderer
        self.iren = iren

        numActorInit = renderer.GetActors().GetNumberOfItems()
        self.numActorInit = numActorInit
        self.numActor = numActorInit

        self.isInsideRenWin = isInsideRenWin

    def __del__(self):
        self.clearActors()

    def getActor(self, vtkSource, color=colors.light_salmon):
        """
        @vtkSource  type 'vtkobject'
        @return     vtkActor
        """
        # Generate Normals
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputConnection(vtkSource.GetOutputPort())
        normals.SetFeatureAngle(60.0)
        normals.ReleaseDataFlagOn()

        stripper = vtk.vtkStripper()
        stripper.SetInputConnection(normals.GetOutputPort())
        stripper.ReleaseDataFlagOn()

        mapper = vtk.vtkPolyDataMapper()
        # mapper.SetInputConnection(vtkSource.GetOutputPort())
        mapper.SetInputConnection(stripper.GetOutputPort())
        mapper.SetScalarVisibility(False)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetDiffuseColor(color)
        actor.GetProperty().SetSpecular(0.3)
        actor.GetProperty().SetSpecularPower(20)
        actor.GetProperty().SetInterpolation(2)
        actor.GetProperty().SetRepresentation(2)
        # actor.GetProperty().SetEdgeVisibility(True)
        # actor.GetProperty().SetOpacity(opacity)

        return actor

    def addActor(self, actor):
        if actor:
            self.renderer.AddActor(actor)

        self.numActor = self.renderer.GetActors().GetNumberOfItems()

    def addPoint(self, position=[0, 0, 0],
                 color=colors.banana, radius=1):
        """
        Add ONE point to the given position
        """
        point = vtk.vtkSphereSource()
        point.SetCenter(position)
        point.SetRadius(radius)
        point.SetPhiResolution(10)
        point.SetThetaResolution(10)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(point.GetOutputPort())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(color)

        self.renderer.AddActor(actor)

    def addPoints(self, coords, color=colors.chartreuse, radius=0.3):
        """
        Add a set of points to vtkRenderer with a given coords array
        """
        numPoints = len(coords)
        startTime = time.time()
        for i in range(numPoints):
            self.addPoint(coords[i, :], color, radius)
        logging.debug(str(numPoints) + " points rendering takes time: " + str(time.time() - startTime))

        # NOTE: the following is correct, but slower.
        # threadNum = 4
        # startTime = time.time()
        # pool = ThreadPool(threadNum)
        # pool.map(self.addPoint, coords)
        # pool.close()
        # pool.join()
        # logging.info("Time taken: {}".format(time.time() - startTime))

    def addText(self, position=[0, 0, 0], texts="Origin",
                color=colors.olive, scale=5):
        """
        Create tet with X-Y-Z coordinate
        """
        text = vtk.vtkVectorText()
        text.SetText(texts)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(text.GetOutputPort())

        actor = vtk.vtkFollower()
        actor.SetCamera(self.renderer.GetActiveCamera())
        actor.SetMapper(mapper)
        actor.SetScale(scale, scale, scale)
        actor.GetProperty().SetColor(color)
        actor.AddPosition([sum(x) for x in zip(position, [0, -0.1, 0])])

        self.renderer.AddActor(actor)

    def addXYZCoord(self, position=[0, 0, 0], scale=100):
        """
        Add a X-Y-Z coordinate at the given point
        """
        axes = vtk.vtkAxes()
        axes.SetOrigin(0, 0, 0)
        axes.SetScaleFactor(scale)
        # axes.SetSymmetric(True)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(axes.GetOutputPort())

        actor = vtk.vtkActor()
        # print actor.GetBounds()
        actor.SetMapper(mapper)

        self.renderer.AddActor(actor)

    def clearActors(self):
        """
        Clear all vtkActor but remain Slicer's outline and direction symbols
        """
        counter = self.numActor - self.numActorInit
        while counter > 0:
            self.renderer.RemoveActor(self.renderer.GetActors().GetLastActor())
            counter -= 1
            self.numActor -= 1

    def vtkShow(self,
                hasXYZCoord=True,
                hasOriginPoint=True,
                hasOriginText=True,
                hasAnnotedCube=False):
        """
        Construction of VTK renderering workflow
        """
        renderWin = self.renderWin
        renderer = self.renderer
        iren = self.iren

        renderWin.AddRenderer(renderer)

        iren = vtk.vtkRenderWindowInteractor()
        iren.SetRenderWindow(renderWin)
        iren.Initialize()

        #
        # Start: Add an Annoted Cube with Arrows
        # NOTE: Slicer has its own 'orientation cube', which is conflit with these code
        # FIXME: This cube cannot be cleared when reLoading
        if hasAnnotedCube:
            cube = vtk.vtkAnnotatedCubeActor()
            cube.SetXPlusFaceText('R')
            cube.SetXMinusFaceText('L')
            cube.SetYPlusFaceText('A')
            cube.SetYMinusFaceText('P')
            cube.SetZPlusFaceText('I')
            cube.SetZMinusFaceText('S')
            cube.SetXFaceTextRotation(180)
            cube.SetYFaceTextRotation(180)
            cube.SetZFaceTextRotation(-90)
            cube.SetFaceTextScale(0.65)
            cube.GetCubeProperty().SetColor(0.5, 1.0, 1.0)
            cube.GetTextEdgesProperty().SetLineWidth(1)
            cube.GetTextEdgesProperty().SetColor(0.18, 0.28, 0.23)
            cube.GetTextEdgesProperty().SetDiffuse(0)
            cube.GetTextEdgesProperty().SetAmbient(1)

            cube.GetXPlusFaceProperty().SetColor(1, 0, 0)
            cube.GetXPlusFaceProperty().SetInterpolationToFlat()
            cube.GetXMinusFaceProperty().SetColor(1, 0, 0)
            cube.GetXMinusFaceProperty().SetInterpolationToFlat()

            cube.GetYPlusFaceProperty().SetColor(0, 1, 0)
            cube.GetYPlusFaceProperty().SetInterpolationToFlat()
            cube.GetYMinusFaceProperty().SetColor(0, 1, 0)
            cube.GetYMinusFaceProperty().SetInterpolationToFlat()

            cube.GetZPlusFaceProperty().SetColor(0, 0, 1)
            cube.GetZPlusFaceProperty().SetInterpolationToFlat()
            cube.GetZMinusFaceProperty().SetColor(0, 0, 1)
            cube.GetZMinusFaceProperty().SetInterpolationToFlat()

            text_property = vtk.vtkTextProperty()
            text_property.ItalicOn()
            text_property.ShadowOn()
            text_property.BoldOn()
            text_property.SetFontFamilyToTimes()
            text_property.SetColor(1, 0, 0)

            text_property_2 = vtk.vtkTextProperty()
            text_property_2.ShallowCopy(text_property)
            text_property_2.SetColor(0, 1, 0)
            text_property_3 = vtk.vtkTextProperty()
            text_property_3.ShallowCopy(text_property)
            text_property_3.SetColor(0, 0, 1)

            axes = vtk.vtkAxesActor()
            axes.SetShaftTypeToCylinder()
            axes.SetXAxisLabelText('X')
            axes.SetYAxisLabelText('Y')
            axes.SetZAxisLabelText('Z')
            axes.SetTotalLength(1.5, 1.5, 1.5)
            axes.GetXAxisCaptionActor2D().SetCaptionTextProperty(text_property)
            axes.GetYAxisCaptionActor2D().SetCaptionTextProperty(text_property_2)
            axes.GetZAxisCaptionActor2D().SetCaptionTextProperty(text_property_3)

            assembly = vtk.vtkPropAssembly()
            assembly.AddPart(axes)
            assembly.AddPart(cube)

            marker = vtk.vtkOrientationMarkerWidget()
            marker.SetOutlineColor(0.93, 0.57, 0.13)
            marker.SetOrientationMarker(assembly)
            marker.SetViewport(0.0, 0.0, 0.15, 0.3)
            marker.SetInteractor(iren)
            marker.EnabledOn()
            marker.InteractiveOn()
        # Finish: Add an Annoted Cube with Arrows
        #

        if hasXYZCoord:
            self.addXYZCoord()

        if hasOriginPoint:
            self.addPoint()

        if hasOriginText:
            self.addText()

        renderer.ResetCamera()
        # renderer.SetActiveCamera(renderer.GetActiveCamera())
        renderer.GetActiveCamera()
        renderWin.Render()

        iren.Start()


#
# Logic
#
class DivideImageLogic(ScriptedLoadableModuleLogic):

    def hasImageData(self, volumeNode):

        if not volumeNode:
            # logging.debug("hasImageData failed: no volume node")
            # return False
            raise UnboundLocalError("hasImageData failed: no volume node")
        if volumeNode.GetImageData() is None:
            # logging.debug("hasImageData failed: no image data in volume node")
            # return False
            raise UnboundLocalError("hasImageData failed: no image data in volume node")
        return True

    def getImageData(self, volumeNode):

        if self.hasImageData(volumeNode):
            imageData = volumeNode.GetImageData()
            logging.debug("vtkImageData of the volume: " + str(imageData))
            return imageData
        else:
            # logging.error("Error: Failed to get ImageData!")
            # return False
            raise IOError("Error: Failed to get ImageData!")

    def setStep(self, step=0.1):
        # if step > 0:
        #     self.step = step
        #     return True
        # else:
        #     logging.error("Step requires a positive value.")
        #     return False
        if step <= 0:
            raise ValueError("Step requires a positive value!", step)
        else:
            self.step = step
            return True

    def getNdarray(self, node):

        # if self.hasImageData(volumeNode):
        #     ndarray = slicer.util.array(volumeNode.GetID())
        #     logging.debug("Correspondent ndarray:\n" + str(ndarray))
        #     return ndarray
        # else:
        #     # logging.error("Error: Failed to get ndarray!")
        #     # return False
        #     raise Exception("Failed to get ndarray!")

        if node.GetClassName() in ('vtkMRMLScalarVolumeNode',
                                   'vtkMRMLLabelMapVolumeNode'):  # scalarTypes
            ndarray = slicer.util.array(node.GetID())
        elif node.GetClassName() == 'vtkImageData':
            shape = list(node.GetDimensions())
            shape.reverse()
            ndarray = vtk.util.numpy_support.vtk_to_numpy(node.GetPointData().GetScalars()).reshape(shape)
        else:
            raise TypeError("The node cannot be converted to NumPy array!")

        return ndarray

    def getSubMatrices(self, volumeNode, step=[40] * 3):
        """
        Divide the big matrix into small ones according with `step`
        @param volumeNode   slicer.qMRMLNodeComboBox().currentNode()
        @param step         shape of subMatrix
        @return             an array containing these sub matrices
        """

        bigMatrix = self.getNdarray(volumeNode)
        shape = bigMatrix.shape
        # print("shape: " + str(shape))
        subMatrices = []
        for i in range(0, shape[0], step[0]):
            for j in range(0, shape[1], step[1]):
                for k in range(0, shape[2], step[2]):
                    subMatrix = bigMatrix[i:i + step[0],
                                          j:j + step[1],
                                          k:k + step[2]
                                          ]
                    subMatrices.append(subMatrix)
                    # Record the index of subMatrixm (VOI)
                    x, y, z = subMatrix.shape

        logging.debug("%d subMatrices generated" % len(subMatrices))

        return subMatrices

    def getIndexVOI(self, volumeNode, step=[40] * 3):
        """
        Retrieve index of VOI and index of [i, j, k]
        1. NumPy's index is very fast
        2. Sync the `vtkImageData` and its NumPy array counterpart
        @return1    VOIs: `extend` of every subMatrix, NumPy's order
        @return2    indices: [i, j, k] order of every subMatrix
        """
        bigMatrix = self.getNdarray(volumeNode)
        shape = bigMatrix.shape
        VOIs = []
        indices = []

        ii = 0  # index of subMatrix
        for i in range(0, shape[0], step[0]):
            ii += 1
            jj = 0
            for j in range(0, shape[1], step[1]):
                jj += 1
                kk = 0
                for k in range(0, shape[2], step[2]):
                    kk += 1
                    subMatrix = bigMatrix[i:i + step[0],
                                          j:j + step[1],
                                          k:k + step[2]
                                          ]
                    # Record the index of subMatrix (VOI extent)
                    x, y, z = subMatrix.shape
                    VOI = [i, i + x, j, j + y, k, k + z]
                    index = [ii, jj, kk]
                    VOIs.append(np.asarray(VOI).T)
                    indices.append(np.asarray(index).T)

        return np.asarray(VOIs), np.asarray(indices) - 1  # index starts at `0`

    def getSubMatrix(self, node, VOI=[0, 10] * 3):
        """
        Extract a subMatrix from given matrix and VOI
        @param1     node: 3D `ndarray`, or `volumeNode`, or `vtkImageData`
        @param2     VOI: a 3D region: [x1, x2, y1, y2, z1, z2]
        @return     a small 3D ndarray
        """
        if isinstance(node, np.ndarray):
            bigMatrix = node
        elif node.GetClassName() in ('vtkMRMLScalarVolumeNode',  # scalarTypes
                                     'vtkMRMLLabelMapVolumeNode',  # scalarTypes
                                     'vtkImageData'):
            bigMatrix = self.getNdarray(node)
        else:
            raise TypeError("The node cannot be converted to NumPy array!")

        subMatrix = bigMatrix[VOI[0]:VOI[1],
                              VOI[2]:VOI[3],
                              VOI[4]:VOI[5]]
        return subMatrix

    def getSubMatrixFromIndex(self, node, index=[0] * 3):
        """
        Extract a subMatrix for its order number
        The number should be valid
        """
        if isinstance(node, np.ndarray):
            bigMatrix = node
        elif node.GetClassName() in ('vtkMRMLScalarVolumeNode',
                                     'vtkMRMLLabelMapVolumeNode'):  # scalarTypes
            bigMatrix = self.getNdarray(node)
        elif node.GetClassName() == 'vtkImageData':
            shape = list(node.GetImageData().GetDimensions())
            shape.reverse()
            bigMatrix = vtk.util.numpy_support.vtk_to_numpy(node.GetPointData().GetScalars()).reshape(shape)
        else:
            raise TypeError("The node cannot be converted to NumPy array!")

        pass  # not finished yet

    def getSubImage(self, bigImageData, VOI=[0, 10] * 3):
        """
        Extract a subImageData from given `vtkImageData` and VOI
        NOTE! The order has be converted to NumPy's order!!
        @param1     bigImageData: a big `vtkImageData`
        @param2     VOI: __in NumPy's order!__
        @return     a small `vtkImageData`
        """
        t = np.asarray(VOI) + np.asarray([0, -1] * 3)  # index of vtk is different
        VOI = np.asarray([t[4], t[5], t[2], t[3], t[0], t[1]])  # swap to adpot to NumPy
        logging.debug("VOI[1::2]: " + str(VOI[1::2]))

        dims = bigImageData.GetDimensions()
        if np.sum(VOI[1::2] <= dims) != 3:  # overflow
            raise Exception("VOI overflow!")

        extract = vtk.vtkExtractVOI()
        extract.SetInputData(bigImageData)
        extract.SetVOI(VOI)
        extract.Update()
        subImageData = extract.GetOutput()

        return subImageData

    def getSubImages(self, volumeNode, step=[40] * 3):
        """
        Divide big vtkImageData into small ones.
        Note: the order is opposite with its NumPy counterpart
        """
        bigImageData = self.getImageData(volumeNode)
        dims = bigImageData.GetDimensions()  # Inversed order with numpy's counterpart
        shape = dims[::-1]  # Note the order is reversed against NumPy's order
        step = step[::-1]
        # print("dims: " + str(dims))
        # extent = bigImageData.GetExtent()

        extract = vtk.vtkExtractVOI()
        extract.SetInputData(bigImageData)
        # extract.SetVOI(0, 29, 0, 29, 15, 15)
        extract.SetSampleRate(1, 1, 1)

        subImages = []
        for i in range(0, shape[0], step[0]):
            if shape[0] - i < step[0]:
                step[0] = shape[0] - i
            for j in range(0, shape[1], step[1]):
                if shape[1] - j < step[1]:
                    step[1] = shape[1] - j
                for k in range(0, shape[2], step[2]):
                    if shape[2] - k < step[2]:
                        step[2] = shape[2] - k
                    extract.SetVOI(i, i + step[0] - 1,
                                   j, j + step[1] - 1,
                                   k, k + step[2] - 1)
                    extract.Update()  # NOTE: this is indispensible!!
                    subImage = extract.GetOutput()  # vtkImageData
                    subImages.append(subImage)

        return subImages

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
                    isValidSubMatrices.append(isValid)  # 1D boolen list

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
        This function is for testing ALL subMatrices
        @param subMatrix    test array
        @param range        a grey value range
        @return boolen      `True` if contains at least 10% points in the range
        """
        # numItem = len(subMatrix)  # Wrong!
        numItem = subMatrix.size
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

        ratio = float(num) / numItem
        if ratio >= 0.1:
            return True
        else:
            return False

    def getCoords(self, subMatrix, range=[90, 100]):
        """
        Get the coords of valid point from a subMatrix
        This function is for testing ONE subMatrix.
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
        y = y1 * y2  # 3-dimentional matrix
        # print y.shape

        # Method 2. About 100 times faster than Method 1
        # for coord, value in np.ndenumerate(y):
        #     if value:  # NOTE: CANNOT be `value is True`
        #         coords.append(coord)  # type 'list'
        # coords = np.array(coords)  # list --> ndarray
        # print coords.shape

        # Method 3. About 4 times faster than Method 2
        coords = np.transpose(y.nonzero())  # type 'numpy.ndarray', 2-dimensional
        # print coords.shape

        # ratio = len(coords) / len(subMatrix)  # Wrong!
        ratio = float(len(coords)) / subMatrix.size  # NOTE: the division
        logging.debug("ratio: " + str(ratio))
        if ratio >= 0.1:
            logging.debug("Valid subMatrix")
            # return np.asarray(coords)  # type 'numpy.ndarray'
            return coords
        else:
            # logging.info("Invalid subMatrix")
            # return False
            raise Exception("getCoords: Invalid subMatrix")

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
        # displayNode = logic.CreateVolumeRenderingDisplayNode()  # GPU rendering

        displayNode = logic.CreateVolumeRenderingDisplayNode()  # GPU rendering
        slicer.mrmlScene.AddNode(displayNode)
        displayNode.UnRegister(logic)
        logic.UpdateDisplayNodeFromVolumeNode(displayNode, volumeNode)
        volumeNode.AddAndObserveDisplayNodeID(displayNode.GetID())

    def showVtkImageData(self, imageData):
        # NOTE: not work!
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
    def radialBasisFunc(self, vector, data, step=0.1):
        """
        Radial Basis Function fitting
        @param vector   found fitting
        @param data     point_num*3 array, every row is a 3D point
        @return1        a ndarray object in ndarray format
        @return2        spacing
        """

        w = vector[-10:]
        num_points = len(data)

        # Step
        data_min = data.min(0)
        data_max = data.max(0)

        step = self.setStep()
        offset = 0.1
        step_x = np.arange(data_min[0] - offset, data_max[0] + offset, step)
        step_y = np.arange(data_min[1] - offset, data_max[1] + offset, step)
        step_z = np.arange(data_min[2] - offset, data_max[2] + offset, step)

        [x, y, z] = np.meshgrid(step_x, step_y, step_z)

        dim_x, dim_y, dim_z = x.shape

        spacing = [(data_max[0] - data_min[0]) / (dim_x - 1.0),
                   (data_max[1] - data_min[1]) / (dim_y - 1.0),
                   (data_max[2] - data_min[2]) / (dim_z - 1.0)]

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

        return obj, spacing

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
            num_array=numpyArray.transpose(2, 0, 1).ravel(),
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
            logging.error("Wrong Cast Type! It MUST be 2, 3, ..., or 11")
            return img_vtk


#
# Test
#
class DivideImageTest(ScriptedLoadableModuleTest):

    def setUp(self):
        slicer.mrmlScene.Clear(0)
        # renderer = slicer.app.layoutManager().threeDWidget(
        #     0).threeDView().renderWindow().GetRenderers().GetFirstRenderer()
        # renderer.RemoveAllViewProps()

    def runTest(self):
        self.setUp()
        # self.test1_DivideImage()
        # self.test2_DivideImage()
        # self.test3_DivideImage()
        # self.test4_DivideImage()
        # self.test_EmptyVolume()
        # self.test_Vtk(False)
        # self.test_VTKLogic()
        # self.test_implicitFunction()
        # self.test_implicitFitting()
        self.test_getSub()
        # self.test_Extract()

    def getDataFromURL(self):
        """
        Auxiliary function to download 'MR-head.nrrd' from url
        @return     volumeNode
        """

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

        return volumeNode

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
        # import urllib
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

    def test_Extract(self):
        # Quadric definition. This is a type of implicit function. Here the
        # coefficients to the equations are set.

        vtkLogic = DivideImageVTKLogic(False)

        quadric = vtk.vtkQuadric()
        quadric.SetCoefficients(.5, 1, .2, 0, .1, 0, 0, .2, 0, 0)

        sample = vtk.vtkSampleFunction()
        sample.SetSampleDimensions(30, 30, 30)
        sample.SetImplicitFunction(quadric)
        sample.ComputeNormalsOff()
        sample.Update()

        extract = vtk.vtkExtractVOI()
        extract.SetInputConnection(sample.GetOutputPort())
        extract.SetVOI(0, 29, 0, 29, 15, 20)
        # extract.SetSampleRate(1, 2, 3)
        extract.Update()  # NOTE: This is indispensible!
        print extract.GetOutput()

        transform = vtk.vtkTransform()
        transform.Scale(100, 100, 10)

        transformFilter = vtk.vtkTransformFilter()
        transformFilter.SetInputConnection(extract.GetOutputPort())
        transformFilter.SetTransform(transform)

        # The image is contoured to produce contour lines. Thirteen contour values
        # ranging from (0,1.2) inclusive are produced.
        contours = vtk.vtkContourFilter()
        contours.SetInputConnection(transformFilter.GetOutputPort())
        contours.GenerateValues(13, 0.0, 1.2)

        # The contour lines are mapped to the graphics library.
        contMapper = vtk.vtkPolyDataMapper()
        contMapper.SetInputConnection(contours.GetOutputPort())
        contMapper.SetScalarRange(0.0, 1.2)

        contActor = vtk.vtkActor()
        contActor.SetMapper(contMapper)

        # Create outline an outline of the sampled data.
        outline = vtk.vtkOutlineFilter()
        outline.SetInputConnection(transformFilter.GetOutputPort())

        outlineMapper = vtk.vtkPolyDataMapper()
        outlineMapper.SetInputConnection(outline.GetOutputPort())

        outlineActor = vtk.vtkActor()
        outlineActor.SetMapper(outlineMapper)
        outlineActor.GetProperty().SetColor(0, 0, 0)

        vtkLogic.addActor(contActor)
        vtkLogic.addActor(outlineActor)
        vtkLogic.vtkShow()

    def test_getSub(self):
        """
        Test running time of getSubImages and getSubMatrices
        """
        filepath = "/Users/Quentan/Box Sync/IMAGE/MR-head.nrrd"
        slicer.util.loadVolume(filepath)
        volumeNode = slicer.util.getNode(pattern="MR-head")
        self.delayDisplay("Image loaded from: " + filepath)

        moduleWidget = slicer.modules.DivideImageWidget
        moduleWidget.volumeSelector1.setCurrentNode(volumeNode)

        logic = DivideImageLogic()
        divideStep = [22, 33, 44]

        VOIs, indices = logic.getIndexVOI(volumeNode, divideStep)
        # print VOIs.shape
        # print indices.shape

        bigMatrix = logic.getNdarray(volumeNode)
        bigImageData = logic.getImageData(volumeNode)
        print("bigMatrix.shape: " + str(bigMatrix.shape))
        print("bigImageData.dim: " + str(bigImageData.GetDimensions()))

        rand = np.random.randint(0, len(VOIs))
        subMatrix = logic.getSubMatrix(bigMatrix, VOIs[rand])
        subImage = logic.getSubImage(bigImageData, VOIs[rand])
        # print subImage
        subMatrixFromImage = logic.getNdarray(subImage)

        print rand
        print subMatrix.shape
        print subImage.GetDimensions()
        # print subMatrixFromImage.shape

        print np.array_equal(subMatrix, subMatrixFromImage)

        #
        # Test `getSubMatrices`
        # startTime = time.time()
        # subMatrices = logic.getSubMatrices(volumeNode, divideStep)
        # i = np.random.randint(0, len(subMatrices))
        # logging.info("--- getSubMatrices uses %s seconds ---" %
        #              (time.time() - startTime))
        # print("length of subMatrices: " + str(len(subMatrices)))
        # print("subMatrix No." + str(i) + ": " + str(subMatrices[i].shape))
        #
        # #
        # # The shape of every subMatrix
        # i = 0
        # lengthSubMatrices = len(subMatrices)
        # while i < lengthSubMatrices:
        #     print("shape of subMatrix " + str(i) + ": " + str(subMatrices[i].shape))
        #     i += 10

        #
        # Test `getSubImages`
        # startTime = time.time()
        # subImages = logic.getSubImages(volumeNode, divideStep)
        # logging.info("--- getSubImages uses %s seconds ---" %
        #              (time.time() - startTime))
        # print("length of subImages: " + str(len(subImages)))
        # print("subImage No." + str(i) + ": " + str(subImages[i].GetDimensions()))

        # a = vtk.util.numpy_support.vtk_to_numpy(i.GetPointData().GetScalars()).reshape(shape)
        # i = 7000
        # while i < len(subImages):
        #     print("subMatrices No. " + str(i) + ": " + str(subMatrices[i].shape))
        #     print("subImages No. " + str(i) + ": " + str(subImages[i].GetDimensions()))
        #     i += 1

    def test_EmptyVolume(self):
        """
        Generate an empty volume
        """
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

    def test_Vtk(self, isInsideRenWin=True):
        """
        Test basic VTK rendering in Slicer.
        This code can also be run independetly
        """
        vtkVersion = vtk.vtkVersion()
        logging.debug("VTK version: " + vtkVersion.GetVTKVersion())

        color_diffuse = [247.0 / 255.0, 150.0 / 255.0, 155.0 / 255.0]

        # This creates a polygonal cylinder model with eight circumferential
        # facets.
        cylinder = vtk.vtkCylinderSource()
        cylinder.SetResolution(5)
        cylinder.SetHeight(100)
        cylinder.SetRadius(50)

        # The mapper is responsible for pushing the geometry into the graphics
        # library. It may also do color mapping, if scalars or other
        # attributes are defined.
        cylinderMapper = vtk.vtkPolyDataMapper()
        cylinderMapper.SetInputConnection(cylinder.GetOutputPort())

        # The actor is a grouping mechanism: besides the geometry (mapper), it
        # also has a property, transformation matrix, and/or texture map.
        # Here we set its color and rotate it -22.5 degrees.
        cylinderActor = vtk.vtkActor()
        cylinderActor.SetMapper(cylinderMapper)
        cylinderActor.GetProperty().SetColor(color_diffuse)
        cylinderActor.RotateX(30.0)
        cylinderActor.RotateY(-45.0)

        # Create the graphics structure. The renderer renders into the render
        # window. The render window interactor captures mouse events and will
        # perform appropriate camera or actor manipulation depending on the
        # nature of the events.
        if isInsideRenWin:  # Render in Slicer's 3D view panel
            renWin = slicer.app.layoutManager().threeDWidget(0).threeDView().renderWindow()
            ren = renWin.GetRenderers().GetFirstRenderer()
        else:  # An independent VTK render window
            ren = vtk.vtkRenderer()
            renWin = vtk.vtkRenderWindow()
        # REVIEW: it's not wise to remove ALL vtkActor --> See onReload()
        # ren.RemoveAllViewProps()  # Remove previous vtkActor
        renWin.AddRenderer(ren)
        iren = vtk.vtkRenderWindowInteractor()
        iren.SetRenderWindow(renWin)

        # Add the actors to the renderer, set the background and size
        ren.AddActor(cylinderActor)
        ren.SetBackground(0.2, 0.3, 0.4)
        # renWin.SetSize(200, 200)  # Makes vtkActor too small

        # This allows the interactor to initalize itself. It has to be
        # called before an event loop.
        iren.Initialize()

        # We'll zoom in a little by accessing the camera and invoking a "Zoom"
        # method on it.
        ren.ResetCamera()
        ren.GetActiveCamera().Zoom(1.5)
        renWin.Render()

        # Start the event loop.
        iren.Start()

    def test_VTKLogic(self):
        # vtkLogic = DivideImageVTKLogic(isInsideRenWin=False)
        vtkLogic = DivideImageVTKLogic()

        source = vtk.vtkSphereSource()
        source.SetPhiResolution(20)
        source.SetThetaResolution(20)

        transform = vtk.vtkTransform()
        transform.Scale(200, 100, 50)

        transformFilter = vtk.vtkTransformFilter()
        transformFilter.SetInputConnection(source.GetOutputPort())
        transformFilter.SetTransform(transform)

        # source.SetHeight(100)
        # source.SetRadius(50)

        actor = vtkLogic.getActor(transformFilter)
        vtkLogic.addActor(actor)
        logging.debug("numActor in test_VTKLogic: " + str(vtkLogic.numActor))
        vtkLogic.vtkShow()

    def test_implicitFunction(self):

        bounds = [-100, 100, -100, 100, -100, 100]
        vtkLogic = DivideImageVTKLogic()

        coef = np.random.standard_normal(10)
        contourVal = 0.0

        quadric = vtk.vtkQuadric()
        quadric.SetCoefficients(coef)

        sample = vtk.vtkSampleFunction()
        sample.SetImplicitFunction(quadric)
        sample.ComputeNormalsOff()
        # Slicer's default bounds are: [-100, 100, -100, 100, -100, 100]
        sample.SetModelBounds(bounds)

        contour = vtk.vtkContourFilter()
        contour.SetInputConnection(sample.GetOutputPort())
        contour.SetValue(0, contourVal)

        actor = vtkLogic.getActor(contour)
        vtkLogic.addActor(actor)
        logging.info("numActor in test_implicitFunction: " + str(vtkLogic.numActor))
        vtkLogic.vtkShow()

    def test_implicitFitting(self):

        contourVal = 0.0

        logic = DivideImageLogic()

        # filepath = "/Users/Quentan/Box Sync/IMAGE/MR-head.nrrd"
        # slicer.util.loadVolume(filepath)
        # volumeNode = slicer.util.getNode(pattern="MR-head")
        # self.delayDisplay("Image loaded from: " + filepath)

        volumeNode = self.getDataFromURL()

        moduleWidget = slicer.modules.DivideImageWidget
        moduleWidget.volumeSelector1.setCurrentNode(volumeNode)

        # Get subMatrices with given step
        divideStep = [10, 10, 10]
        subMatrices, isValidSubMatrices = logic.getValidSubMatrices(
            volumeNode, divideStep)
        numValidSubMatrices = np.sum(isValidSubMatrices)
        logging.info(str(numValidSubMatrices) + '/' + str(len(subMatrices)) +
                     " valid subMatrices generated")

        # Randomly pick up a valid subMatrix and fitting the points
        idxValidMatrices = [i for i, x in enumerate(isValidSubMatrices) if x]
        testValidMatrix = np.random.choice(idxValidMatrices)
        # print testValidMatrix, type(testValidMatrix)
        # testValidMatrix = 243
        # print subMatrices[testValidMatrix]
        coords = logic.getCoords(subMatrices[testValidMatrix])
        # coords = logic.getCoords(subMatrices[243])
        # print("coords: " + str(coords))
        logging.info("Random subMatix " + str(testValidMatrix) + " has " +
                     str(len(coords)) + " valid points")

        vectorColumn = logic.implicitFitting(coords)
        logging.debug("Vector of column:\n" + str(vectorColumn))
        fittingResult, spacing = logic.radialBasisFunc(vectorColumn, coords)
        logging.debug("Fitting Result as matrix:\n" + str(fittingResult))
        # print fittingResult.shape

        imageData = logic.ndarray2vtkImageData(fittingResult, spacing=spacing)

        dims = imageData.GetDimensions()
        bounds = imageData.GetBounds()
        logging.debug("Bounds of the sub image: " + str(bounds))
        # spacing = imageData.GetSpacing()
        # origin = imageData.GetOrigin()

        #
        # Start: VTK rendering
        vtkLogic = DivideImageVTKLogic()
        # FIXME: the outside rendering has problem.

        implicitVolume = vtk.vtkImplicitVolume()
        implicitVolume.SetVolume(imageData)

        sample = vtk.vtkSampleFunction()
        sample.SetImplicitFunction(implicitVolume)
        sample.SetModelBounds(bounds)
        sample.SetSampleDimensions(dims)
        sample.ComputeNormalsOff()

        contour = vtk.vtkContourFilter()
        contour.SetInputConnection(sample.GetOutputPort())
        contour.SetValue(0, contourVal)

        outline = vtk.vtkOutlineFilter()
        outline.SetInputConnection(contour.GetOutputPort())

        outlineMapper = vtk.vtkPolyDataMapper()
        outlineMapper.SetInputConnection(outline.GetOutputPort())

        outlineActor = vtk.vtkActor()
        outlineActor.SetMapper(outlineMapper)
        outlineActor.GetProperty().SetColor(0, 0, 0)

        actor = vtkLogic.getActor(contour)
        vtkLogic.addActor(actor)
        vtkLogic.addActor(outlineActor)
        logging.debug("numActor in test_implicitFitting: " + str(vtkLogic.numActor))

        # Render the points
        vtkLogic.addPoints(coords)

        vtkLogic.vtkShow()
        # Finish: VTK rendering
        #
