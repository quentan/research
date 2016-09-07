"""
Load an image as a numpy array and divide it into small ones
"""
import qt, slicer, ctk
import math
import numpy as np
from slicer.ScriptedLoadableModule import *
import logging
logging.basicConfig(level=logging.WARNING)

#
# MarkupInfo module
#

class DivideImage(ScriptedLoadableModule):

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)

        self.parent.title = "Divide Image"
        self.parent.categories = ["Examples"]
        self.parent.dependencies = []
        self.parent.contributors = ["Quentan Qi (Univeristy of Hull)"]
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
        # self.volumeSelector1.addAttribute("vtkMRMLScalarVolumeNode", "LabelMap", 0)  # deprecated
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

        # Get Shape button
        # self.getShapeBtn = qt.QPushButton("Get Shape")
        # self.getShapeBtn.toolTip = "Get the shape of the loaded image"
        # self.getShapeBtn.enabled = True
        # _layout.addRow(self.getShapeBtn, self.shapeValue)

        # Vertical spacer
        self.layout.addStretch(1)

        #
        # Connection
        self.volumeSelector1.connect('currentNodeChanged(vtkMRMLNode*)', self.onVolumeSelect)

    # Response functions
    def onVolumeSelect(self):

        logic = DivideImageLogic()
        logging.info('Logic is running')

        ndarray = logic.getNdarray(self.volumeSelector1.currentNode())
        ndarryShape = ndarray.shape
        logging.info('The shape of the ndarray: ' + str(ndarryShape))
        self.shapeValue.setText(ndarryShape)

        # TEST
        ndarray[50:60] = 0
        imageData = logic.getImageData(self.volumeSelector1.currentNode())
        imageData.Modified()


#
# Logic
#
class DivideImageLogic(ScriptedLoadableModuleLogic):

    def hasImageData(self, volumeNode):

        if not volumeNode:
            logging.debug('hasImageData failed: no volume node')
            return False
        if volumeNode.GetImageData() is None:
            logging.debug('hasImageData failed: no image data in volume node')
            return False
        return True

    def getImageData(self, volumeNode):

        if self.hasImageData(volumeNode):
            imageData = volumeNode.GetImageData()
            logging.info('vtkImageData of the volume: ' + str(imageData))
            return imageData

    def getNdarray(self, volumeNode):

        if self.hasImageData(volumeNode):
            ndarray = slicer.util.array(volumeNode.GetID())
            logging.info('Correspondent ndarray:\n' + str(ndarray))
            return ndarray

    def getSubMatrix(self, bigMatrix, size=[10, 10, 10]):

        subMatrix = np.zeros(size)

