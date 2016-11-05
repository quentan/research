def segmentPrev(self):
    array = slicer.util.array(self.inputVolume1.GetID())
    import tempfile, os, subprocess
    import numpy as np

    arrayFile = tempfile.NamedTemporaryFile(delete = False)
    np.save(arrayFile, array)
    arrayFile.close()
    #-E and -s necessary ! So we don't use slicer libraries
    segString = "python2 -E -s script.py " + arrayFile.name
    process = subprocess.Popen(segString, shell=True,stdout=subprocess.PIPE)
    process.wait()

    resultFile = process.stdout.read().strip(' \t\n\r')
    print "Result File : " + resultFile
    numpyArray = np.load(resultFile)
   numpyArray = numpyArray.astype(np.float32)

    importer = vtk.vtkImageImport()
    importer.CopyImportVoidPointer(numpyArray, numpyArray.nbytes)
    setDataType = 'importer.SetDataScalarTypeTo' + 'Float' + '()'
    eval(setDataType)
    importer.SetNumberOfScalarComponents(1)
    importer.SetWholeExtent(0,numpyArray.shape[1]-1,0,numpyArray.shape[0]-1,0,0)
    importer.SetDataExtentToWholeExtent()
    print importer.GetDataExtent()
    importer.Update()
    volume = slicer.vtkMRMLScalarVolumeNode()
    ijkToRAS = vtk.vtkMatrix4x4()
    self.inputVolume1.GetIJKToRASMatrix(ijkToRAS)
    volume.SetIJKToRASMatrix(ijkToRAS)
    volume.SetName("SegSlice1")
    volume.SetLabelMap(0)
    volume.SetAndObserveImageData(importer.GetOutput())
    slicer.mrmlScene.AddNode(volume)
    volumeDisplayNode = slicer.vtkMRMLScalarVolumeDisplayNode()
    slicer.mrmlScene.AddNode(volumeDisplayNode)
    greyColorTable = slicer.util.getNode('Grey')
    volumeDisplayNode.SetAndObserveColorNodeID(greyColorTable.GetID())

    volume.SetAndObserveDisplayNodeID(volumeDisplayNode.GetID())
    selectionNode = slicer.app.applicationLogic().GetSelectionNode()
    selectionNode.SetReferenceActiveVolumeID(volume.GetID())
    slicer.app.applicationLogic().PropagateVolumeSelection(0)


    # Re-orient the volume for display
    sliceNodes = slicer.util.getNodes('vtkMRMLSliceNode*')
    for name, node in sliceNodes.items():
        node.RotateToVolumePlane(volume)
    # snap to IJK to try and avoid rounding errors
    sliceLogics = slicer.app.layoutManager().mrmlSliceLogics()
    numLogics = sliceLogics.GetNumberOfItems()
    for n in range(numLogics):
        l = sliceLogics.GetItemAsObject(n)
        l.SnapSliceOffsetToIJK()
    selectionNode = slicer.app.applicationLogic().GetSelectionNode()
    selectionNode.SetReferenceActiveVolumeID(volume.GetID())
    slicer.app.applicationLogic().PropagateVolumeSelection(0)
