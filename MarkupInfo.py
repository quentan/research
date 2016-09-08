"""
This is example script from "MarkupsInfo.py"
Some changes are done in this script.
"""
import qt
import slicer
import ctk
import math
from slicer.ScriptedLoadableModule import ScriptedLoadableModule
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleWidget
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleLogic
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleTest


#
# MarkupInfo module
#
class MarkupInfo(ScriptedLoadableModule):

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)

        self.parent.title = "Markup Info"
        self.parent.categories = ["Examples"]
        self.parent.dependencies = []
        self.parent.contributors = ["Quentan Qi (Univeristy of Hull)"]
        self.parent.helpText = """
        This is an example to calculate the total distance of fiducial points.
        """
        self.parent.acknowledgementText = """
        Thanks for XXX.
        """


#
# MarkupInfoWidget
#
class MarkupInfoWidget(ScriptedLoadableModuleWidget):

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        #
        # Parameter collapsible area
        #
        collapsibleBtn = ctk.ctkCollapsibleButton()
        collapsibleBtn.text = "Parameters"
        self.layout.addWidget(collapsibleBtn)

        # Layout with the collapsible button
        _layout = qt.QFormLayout(collapsibleBtn)

        #
        # Ruler selector
        #
        self.markupSelector = slicer.qMRMLNodeComboBox()
        self.markupSelector.nodeTypes = ("vtkMRMLMarkupsFiducialNode", "")
        self.markupSelector.noneEnabled = False
        self.markupSelector.selectNodeUponCreation = True
        self.markupSelector.setMRMLScene(slicer.mrmlScene)
        self.markupSelector.setToolTip("Pick the Markup")
        _layout.addRow("Markup list", self.markupSelector)

        #
        # Result label
        #
        self.lengthLabel = qt.QLabel()
        self.lengthLabel.setText("Total length of the points: ")
        self.lengthValue = qt.QLabel()
        _layout.addRow(self.lengthLabel, self.lengthValue)
        # _layout.addRow("test", self.lengthLabel, self.lengthValue)  # Wrong!

        # Vertical spacer
        self.layout.addStretch(1)

        #
        # Apply Button
        #
        self.applyBtn = qt.QPushButton("Apply")
        self.applyBtn.toolTip = "Compute the total distance of the points"
        self.applyBtn.enabled = True
        _layout.addRow(self.applyBtn)
        # _layout.addWidget(self.applyBtn)

        #
        # Connections
        #
        self.applyBtn.connect('clicked(bool)', self.onApplyBtn)
        self.markupSelector.connect('currentNodeChanged(vtkMRMLNode*)',
                                    self.onMarkupSelect)

    def onMarkupSelect(self):
        self.applyBtn.enabled = self.markupSelector.currentNode()

    def onApplyBtn(self):
        logic = MarkupInfoLogic()
        print("Run the Logic")
        value = logic.run(self.markupSelector.currentNode())
        self.lengthValue.setText('%.2f' % value)


#
# Logic
#
class MarkupInfoLogic(ScriptedLoadableModuleLogic):

    def run(self, markupNode):

        print('MarkupInfoLogic run() called')

        p0 = [0.0]*3
        p1 = [0.0]*3

        totalLength = 0.0

        for idx in xrange(markupNode.GetNumberOfFiducials()-1):
            markupNode.GetNthFiducialPosition(idx, p0)
            markupNode.GetNthFiducialPosition(idx+1, p1)

            length = math.sqrt((p0[0]-p1[0])**2 +
                               (p0[1]-p1[1])**2 +
                               (p0[2]-p1[2])**2)
            totalLength = totalLength + length

        return totalLength


#
# Test
#
class MarkupInfoTest(ScriptedLoadableModuleTest):

    def setUp(self):
        slicer.mrmlScene.Clear(0)  # a scene clear is enough

    def runTest(self):
        self.setUp()
        self.test2_MarkupInfo()

    # Many tests can be set as test2_MarkupInfo, etc.
    def test1_MarkupInfo(self):
        # Fixed points generated
        self.delayDisplay("Starting the test")

        #
        # Get some data if needed
        #

        #
        # Add test
        #
        fiducialNode = slicer.vtkMRMLMarkupsFiducialNode()
        slicer.mrmlScene.AddNode(fiducialNode)
        fiducialNode.AddFiducial(10, 20, 30)
        fiducialNode.AddFiducial(-15, 50, 100)
        fiducialNode.AddFiducial(35, -60, 90)
        fiducialNode.SetName('Test')

        # Initialise input selector(s)
        # Note: the end has no "()", or a __init__ function required!
        moduleWidget = slicer.modules.MarkupInfoWidget

        moduleWidget.markupSelector.setCurrentNode(fiducialNode)

        self.delayDisplay("Inputs initialised!")

        # Run the logic with the initialised input(s)
        moduleWidget.onApplyBtn()

        self.delayDisplay("If a distance is shown - test passed!")

    def test2_MarkupInfo(self):
        # Random points for test
        self.delayDisplay("Starting the test - random points")

        #
        # Add test
        #
        fiducialNode = slicer.vtkMRMLMarkupsFiducialNode()
        slicer.mrmlScene.AddNode(fiducialNode)
        import random
        num = random.randint(5, 15)  # Get an integer 5<=N<=15
        print('\n%d random points are generated:' % num)
        for i in range(num):
            p = random.sample(range(-100, 100), 3)  # a random 3D point
            fiducialNode.AddFiducialFromArray(p)
            print i+1, ': ', p

        fiducialNode.SetName('%d Random Points' % num)

        # Initialise input selector(s)
        # Note: the end has no "()", or a __init__ function required!
        moduleWidget = slicer.modules.MarkupInfoWidget

        moduleWidget.markupSelector.setCurrentNode(fiducialNode)

        self.delayDisplay("Inputs initialised!\n")

        # Run the logic with the initialised input(s)
        moduleWidget.onApplyBtn()

        self.delayDisplay("If a distance is shown - test passed!")
