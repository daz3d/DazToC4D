import os
import sys
import c4d
from c4d import documents

from .CustomCmd import Cinema4DCommands as dzc4d
from .CustomIterators import ObjectIterator


class AllSceneToZero:
    doc = documents.GetActiveDocument()

    def getMinY(self, obj):
        doc = documents.GetActiveDocument()
        if obj.GetType() == 5100:
            mg = obj.GetMg()
            minPos = c4d.Vector(obj.GetPoint(0) * mg).y
            minId = None
            for i in range(obj.GetPointCount()):
                bufferMin = c4d.Vector(obj.GetPoint(i) * mg).y
                minPos = min(minPos, bufferMin)
                if minPos == bufferMin:
                    minId = i
            return minPos

    def rasterizeObj(self, obj):
        doc = documents.GetActiveDocument()
        collapsedName = obj.GetName() + "_Collapsed"
        c4d.CallCommand(100004767, 100004767)  # Deselect All
        obj.SetBit(c4d.BIT_ACTIVE)
        c4d.CallCommand(100004820)  # Copy
        c4d.CallCommand(100004821)  # Paste
        objPasted = doc.GetFirstObject()
        if objPasted.GetDown():
            if "Poses" in objPasted.GetDown().GetName():
                objPasted.GetDown().Remove()

        c4d.CallCommand(100004772)  # Group Objects
        c4d.CallCommand(100004768)  # Select Children
        c4d.CallCommand(16768, 16768)  # Connect Objects + Delete
        collapsedObj = doc.GetFirstObject()
        collapsedObj.SetName(collapsedName)
        minY = self.getMinY(collapsedObj)
        collapsedObj.Remove()

        return minY

    def sceneLowestYobj(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()

        scene = ObjectIterator(obj)
        sceneYvalues = []
        sceneLowestY = 0.0
        dictYvalues = {}
        for obj in scene:
            if obj.GetUp() == None and obj.GetType() == 5100:
                objPos = obj.GetAbsPos()  # The absolute object position.
                objCenterOffset = obj.GetMp()  # The bounding box center.
                boundBox = obj.GetRad()  # The bounding box width, height and depth.
                realPos = objPos[1] + objCenterOffset[1]
                lowestY = realPos - boundBox[1]
                sceneYvalues.append(lowestY)
                dictYvalues[lowestY] = obj

        sceneLowestObj = 0
        if len(sceneYvalues) > 0:
            sceneLowestY = min(sceneYvalues)
            sceneLowestObj = dictYvalues[sceneLowestY]

        return sceneLowestObj

    def moveAllToZero(self, baseObjs, posY):
        c4d.EventAdd()
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        c4d.EventAdd()
        doc = documents.GetActiveDocument()
        baseObjs = []
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for obj in scene:
            if obj.GetUp() == None:
                baseObjs.append(obj)

        newNull = c4d.BaseObject(c4d.Onull)  # Create new cube
        doc.InsertObject(newNull)
        newNull[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y] = posY
        c4d.EventAdd()

        for obj in baseObjs:
            if obj.GetUp() == None:
                mg = obj.GetMg()
                obj.InsertUnder(newNull)
                obj.SetMg(mg)

        c4d.EventAdd()
        newNull[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y] = 0
        dzc4d.deselect_all()  # Deselect All
        newNull.SetBit(c4d.BIT_ACTIVE)
        c4d.CallCommand(100004773, 100004773)  # Expand Object Group
        newNull.Remove()
        c4d.EventAdd()

    def sceneToZero(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        baseObjs = []
        errorDetected = False

        for obj in scene:
            if scene.depth == 0:
                if obj.GetType() == 5100:
                    baseObjs.append(obj)
                if obj.GetType() == 1007455:
                    objSub = obj
                    objMesh = obj.GetDown()
                    c4d.CallCommand(100004767, 100004767)  # Deselect All
                    objSub.SetBit(c4d.BIT_ACTIVE)
                    c4d.CallCommand(100004773)  # Expand Object Group
                    objSub.Remove()
                    c4d.EventAdd()
                    if objMesh:
                        if objMesh.GetType() == 5100:
                            baseObjs.append(objMesh)

        if len(baseObjs) > 0:
            if errorDetected == False:
                getLowestY = self.rasterizeObj(self.sceneLowestYobj())
                self.moveAllToZero(baseObjs, getLowestY)
                c4d.DrawViews(
                    c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
                    | c4d.DRAWFLAGS_NO_THREAD
                    | c4d.DRAWFLAGS_STATICBREAK
                )
                c4d.EventAdd()
