import os
import unittest
import vtk
import qt
import ctk
import slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# LineIntersityProfile
#


class LineIntersityProfile(ScriptedLoadableModule):

    """
    Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        # TODO make this more human readable by adding spaces
        self.parent.title = "LineIntersityProfile"
        self.parent.categories = ["Examples"]
        self.parent.dependencies = []
        # replace with "Firstname Lastname (Organization)"
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]
        self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    It performs a simple thresholding on the input volume and optionally captures a screenshot.
    """
        self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""  # replace with organization, grant and thanks.

#
# LineIntersityProfileWidget
#


class LineIntersityProfileWidget(ScriptedLoadableModuleWidget):

    """
    Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # Instantiate and connect widgets ...

        #
        # Parameters Area
        #
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "Parameters"
        self.layout.addWidget(parametersCollapsibleButton)

        # Layout within the dummy collapsible button
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

        #
        # Fisrt input volume selector
        #
        self.inputSelector1 = slicer.qMRMLNodeComboBox()
        self.inputSelector1.nodeTypes = (("vtkMRMLScalarVolumeNode"), "")
        self.inputSelector1.addAttribute(
            "vtkMRMLScalarVolumeNode", "LabelMap", 0)
        self.inputSelector1.selectNodeUponCreation = True
        self.inputSelector1.addEnabled = False
        self.inputSelector1.removeEnabled = False
        self.inputSelector1.noneEnabled = False
        self.inputSelector1.showHidden = False
        self.inputSelector1.showChildNodeTypes = False
        self.inputSelector1.setMRMLScene(slicer.mrmlScene)
        self.inputSelector1.setToolTip("Pick the first input")
        parametersFormLayout.addRow("First Volume", self.inputSelector1)

        #
        # Second input volume selector
        #
        self.inputSelector2 = slicer.qMRMLNodeComboBox()
        self.inputSelector2.nodeTypes = (("vtkMRMLScalarVolumeNode"), "")
        self.inputSelector2.addAttribute(
            "vtkMRMLScalarVolumeNode", "LabelMap", 0)
        self.inputSelector2.selectNodeUponCreation = True
        self.inputSelector2.addEnabled = False
        self.inputSelector2.removeEnabled = False
        self.inputSelector2.noneEnabled = False
        self.inputSelector2.showHidden = False
        self.inputSelector2.showChildNodeTypes = False
        self.inputSelector2.setMRMLScene(slicer.mrmlScene)
        self.inputSelector2.setToolTip("Pick the second input")
        parametersFormLayout.addRow("Second Volume", self.inputSelector2)
        #
        # output volume selector
        #
        # self.outputSelector = slicer.qMRMLNodeComboBox()
        # self.outputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        # self.outputSelector.selectNodeUponCreation = True
        # self.outputSelector.addEnabled = True
        # self.outputSelector.removeEnabled = True
        # self.outputSelector.noneEnabled = True
        # self.outputSelector.showHidden = False
        # self.outputSelector.showChildNodeTypes = False
        # self.outputSelector.setMRMLScene(slicer.mrmlScene)
        # self.outputSelector.setToolTip("Pick the output to the algorithm.")
        # parametersFormLayout.addRow("Output Volume: ", self.outputSelector)

        #
        # Ruler selector
        #
        self.rulerSelector = slicer.qMRMLNodeComboBox()
        self.rulerSelector.nodeTypes = (("vtkMRMLAnnotationRulerNode"), "")
        self.rulerSelector.selectNodeUponCreation = True
        self.rulerSelector.addEnabled = False
        self.rulerSelector.removeEnabled = False
        self.rulerSelector.noneEnabled = False
        self.rulerSelector.showHidden = False
        self.rulerSelector.showChildNodeTypes = False
        self.rulerSelector.setMRMLScene(slicer.mrmlScene)
        self.rulerSelector.setToolTip("Pick the ruler to sample along.")
        parametersFormLayout.addRow("Ruler: ", self.rulerSelector)

        #
        # Apply Button
        #
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Run the algorithm."
        self.applyButton.enabled = True
        parametersFormLayout.addRow(self.applyButton)

        # connections
        self.applyButton.connect('clicked(bool)', self.onApplyButton)
        # self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
        # self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

        # Add vertical spacer
        self.layout.addStretch(1)

        # Refresh Apply button state
        self.onSelect()

    def cleanup(self):
        pass

    def onSelect(self):
        self.applyButton.enabled = self.inputSelector1.currentNode(
        ) and self.inputSelector2.currentNode()

    def onApplyButton(self):
        logic = LineIntersityProfileLogic()
        print("Run the algorithm")
        logic.run(self.inputSelector1.currentNode(),
                  self.inputSelector2.currentNode(),
                  self.rulerSelector.currentNode())

#
# LineIntersityProfileLogic
#


class LineIntersityProfileLogic(ScriptedLoadableModuleLogic):

    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def hasImageData(self, volumeNode):
        """This is an example logic method that
        returns true if the passed in volume"E202"
        node has valid image data
        """
        if not volumeNode:
            logging.debug('hasImageData failed: no volume node')
            return False
        if volumeNode.GetImageData() is None:
            logging.debug('hasImageData failed: no image data in volume node')
            return False
        return True

    def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
        """Validates if the output is not the same as input
        """
        if not inputVolumeNode:
            logging.debug(
                'isValidInputOutputData failed: no input volume node defined')
            return False
        if not outputVolumeNode:
            logging.debug(
                'isValidInputOutputData failed: no output volume node defined')
            return False
        if inputVolumeNode.GetID() == outputVolumeNode.GetID():
            logging.debug(
                'isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
            return False
        return True

    def takeScreenshot(self, name, description, type=-1):
        # show the message even if not taking a screen shot
        slicer.util.delayDisplay(
            'Take screenshot: '+description+'.\nResult is available in the Annotations module.', 3000)

        lm = slicer.app.layoutManager()
        # switch on the type to get the requested window
        widget = 0
        if type == slicer.qMRMLScreenShotDialog.FullLayout:
            # full layout
            widget = lm.viewport()
        elif type == slicer.qMRMLScreenShotDialog.ThreeD:
            # just the 3D window
            widget = lm.threeDWidget(0).threeDView()
        elif type == slicer.qMRMLScreenShotDialog.Red:
            # red slice window
            widget = lm.sliceWidget("Red")
        elif type == slicer.qMRMLScreenShotDialog.Yellow:
            # yellow slice window
            widget = lm.sliceWidget("Yellow")
        elif type == slicer.qMRMLScreenShotDialog.Green:
            # green slice window
            widget = lm.sliceWidget("Green")
        else:
            # default to using the full window
            widget = slicer.util.mainWindow()
            # reset the type so that the node is set correctly
            type = slicer.qMRMLScreenShotDialog.FullLayout

        # grab and convert to vtk image data
        qpixMap = qt.QPixmap().grabWidget(widget)
        qimage = qpixMap.toImage()
        imageData = vtk.vtkImageData()
        slicer.qMRMLUtils().qImageToVtkImageData(qimage, imageData)

        annotationLogic = slicer.modules.annotations.logic()
        annotationLogic.CreateSnapShot(name, description, type, 1, imageData)

    def run(self, volumeNode1, volumeNode2, rulerNode):
        """
        Run the actual algorith
        """
        print('LineIntensityProfileLogic run() called')

        """
        S1. Get the list of intensity samples along the ruler
        S2. Set up quantitative layout
        S3. Use the chart view to plot the intensity samples
        """

        # S1. Get the list of samples
        if not rulerNode or (not volumeNode1 and not volumeNode2):
            print('Inputs are not initialised!')
            return

        volumeSamples1 = None
        volumeSamples2 = None

        if volumeNode1:
            volumeSamples1 = self.probeVolume(volumeNode1, rulerNode)
        if volumeNode2:
            volumeSamples2 = self.probeVolume(volumeNode2, rulerNode)

        print('VolumeSamples1 = ' + str(volumeSamples1))
        print('VolumeSamples2 = ' + str(volumeSamples2))

        # Running showChart() method
        imageSamples = [volumeSamples1, volumeSamples2]
        legendNames = [volumeNode1.GetName()+' - '+rulerNode.GetName(),
                       volumeNode2.GetName()+' - '+rulerNode.GetName()]
        self.showChart(imageSamples, legendNames)

        return True

    def probeVolume(self, volumeNode, rulerNode):

        # get ruler ednpoints coordinates in RAS
        # make the coordinate from (x,y,z) to (x,y,z,1) by adding (1,)
        p0ras = rulerNode.GetPolyData().GetPoint(0) + (1,)
        p1ras = rulerNode.GetPolyData().GetPoint(1) + (1,)

        # RAS --> IJK (vtkImageData)
        ras2ijk = vtk.vtkMatrix4x4()
        volumeNode.GetRASToIJKMatrix(ras2ijk)
        p0ijk = [int(round(c)) for c in ras2ijk.MultiplyPoint(p0ras)[:3]]  # Not understand
        p1ijk = [int(round(c)) for c in ras2ijk.MultiplyPoint(p1ras)[:3]]

        # Create VTK line that will be used for sampling
        line = vtk.vtkLineSource()
        line.SetResolution(100)
        line.SetPoint1(p0ijk)
        line.SetPoint2(p1ijk)

        # Create VTK probe filter and sample the image
        """
        vtkProbeFilter is a filter that computes point attributes (e.g., scalars, vectors, etc.) at specified point positions.
        The filter has two inputs: the Input and Source. The Input geometric structure is passed through the filter. The point attributes are computed at the Input point positions by interpolating into the source data. For example, we can compute data values on a plane (plane specified as Input) from a volume (Source). The cell data of the source data is copied to the output based on in which source cell each input point is. If an array of the same name exists both in source's point and cell data, only the one from the point data is probed.
        """
        probe = vtk.vtkProbeFilter()
        probe .SetInputConnection(line.GetOutputPort())
        probe.SetSourceData(volumeNode.GetImageData())
        probe.Update()

        # Return VTK array
        """
        probe: vtkProbeFilter
        probe.GetOutput(): vtkDataSet
        probe.GetOutput().GetPointData(): vtkPointData
        probe.GetOutput().GetPointData().GetArray(): vtkDataArray
        """
        return probe.GetOutput().GetPointData().GetArray('ImageScalars')  # returns a vtkDataArray

    def showChart(self, samples, names):
        print('Logic showing chart\n')

        # S2. Switch to a layout containing a chart viewer
        lm = slicer.app.layoutManager()
        lm.setLayout(
            slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpQuantitativeView)

        # Initialise double array MRML node for each sample list
        # since this is what chart view MRML node needs
        doubleArrays = []
        for sample in samples:
            arrayNode = slicer.mrmlScene.AddNode(
                slicer.vtkMRMLDoubleArrayNode())
            array = arrayNode.GetArray()
            nDataPoints = sample.GetNumberOfTuples()
            array.SetNumberOfTuples(nDataPoints)
            array.SetNumberOfComponents(3)
            for i in range(nDataPoints):
                array.SetComponent(i, 0, i)
                array.SetComponent(i, 1, sample.GetTuple1(i))
                array.SetComponent(i, 2, 0)

            doubleArrays.append(arrayNode)

        # S3. Get the chart view MRML node
        cvNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLChartViewNode')
        cvNodes.SetReferenceCount(cvNodes.GetReferenceCount()-1)
        cvNodes.InitTraversal()
        cvNode = cvNodes.GetNextItemAsObject()

        # Create a new chart node
        chartNode = slicer.mrmlScene.AddNode(slicer.vtkMRMLChartNode())
        for pairs in zip(names, doubleArrays):
            chartNode.AddArray(pairs[0], pairs[1].GetID())
        cvNode.SetChartNodeID(chartNode.GetID())

        return


class LineIntersityProfileTest(ScriptedLoadableModuleTest):

    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_LineIntersityProfile1()

    def test_LineIntersityProfile1(self):
        """
        Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")
        #
        # first, get some data
        #
        import urllib
        downloads = (
            ('http://slicer.kitware.com/midas3/download?items=5767',
             'FA.nrrd', slicer.util.loadVolume),
        )

        for url, name, loader in downloads:
            filePath = slicer.app.temporaryPath + '/' + name
            if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
                logging.info(
                    'Requesting download %s from %s...\n' % (name, url))
                urllib.urlretrieve(url, filePath)
            if loader:
                logging.info('Loading %s...' % (name,))
                loader(filePath)
        self.delayDisplay('Finished with download and loading')

        volumeNode = slicer.util.getNode(pattern="FA")
        logic = LineIntersityProfileLogic()
        self.assertTrue(logic.hasImageData(volumeNode))
        # self.delayDisplay('Test passed!')

        # Add Test
        # Initialise rule node in a know location
        rulerNode = slicer.vtkMRMLAnnotationRulerNode()
        slicer.mrmlScene.AddNode(rulerNode)
        rulerNode.SetPosition1(-65, 110, 60)
        rulerNode.SetPosition2(-15, 60, 60)
        rulerNode.SetName('Test')

        # Initialise input selectors
        moduleWidget = slicer.modules.LineIntersityProfileWidget
        # Note: the end has no "()", or a __init__ function required!

        moduleWidget.rulerSelector.setCurrentNode(rulerNode)
        moduleWidget.inputSelector1.setCurrentNode(volumeNode)
        moduleWidget.inputSelector2.setCurrentNode(volumeNode)

        self.delayDisplay("Inputs initialised!")

        # run the logic with the initialised inputs
        moduleWidget.onApplyButton()

        self.delayDisplay("if you see a ruler and a plot - test passed!")
