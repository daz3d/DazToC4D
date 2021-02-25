from __future__ import division
import os
import sys
import hashlib
import c4d
from c4d import gui, documents
from c4d import utils
from c4d import plugins
from random import randint
from shutil import copyfile
import webbrowser
import json
from xml.etree import ElementTree

folder = os.path.dirname(__file__)
if folder not in sys.path:
    sys.path.insert(0, folder)

from Util import DazToC4dUtils
from Iterators import TagIterator, ObjectIterator
from Globals import *
from DtcAutoIk import *
from DtcGui import *
from DtcMaterials import *
from DtcMorphs import *

"""
Converted to Python 3 to deal with changes in Cinema 4D R23
Manual Changes to the code:
Removed  c4d.DRAWFLAGS_NO_REDUCTION as it was removed from the Python SDK
Changes for Division from / to // to achieve an integer instead of a float
Added Backwards Support for __next__ for Python 2 Versions
"""
try:
    import redshift
except:
    print('Redshift not found')

def _GetNextHierarchyObject(op):
    """Return the next object in hieararchy.
    """
    if op is None:
        return None
    down = op.GetDown()
    if down:
        return down
    next = op.GetNext()
    if next:
        return next
    prev = op.GetUp()
    while prev:
        next = prev.GetNext()
        if next:
            return next
        prev = prev.GetUp()
    return None

class AllSceneToZero:
    doc = documents.GetActiveDocument()

    def getMinY(self, obj):
        doc = documents.GetActiveDocument()
        # objs = doc.GetActiveObjects(0)
        # pts = obj.GetAllPoints()
        if obj.GetType() == 5100:
            # message = obj.GetName() + ' ' + str(len(pts))
            # c4d.gui.MessageDialog()
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
        collapsedName = obj.GetName() + '_Collapsed'
        c4d.CallCommand(100004767, 100004767)  # Deselect All
        obj.SetBit(c4d.BIT_ACTIVE)
        c4d.CallCommand(100004820)  # Copy
        c4d.CallCommand(100004821)  # Paste
        objPasted = doc.GetFirstObject()
        if objPasted.GetDown():
            if 'Poses' in objPasted.GetDown().GetName():
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
                # The bounding box width, height and depth.
                boundBox = obj.GetRad()
                realPos = objPos[1] + objCenterOffset[1]
                lowestY = realPos - boundBox[1]
                sceneYvalues.append(lowestY)
                dictYvalues[lowestY] = obj
        # gui.MessageDialog(len(sceneYvalues))
        sceneLowestObj = 0
        if len(sceneYvalues) > 0:
            sceneLowestY = min(sceneYvalues)
            sceneLowestObj = dictYvalues[sceneLowestY]

        return sceneLowestObj

    def moveAllToZero(self, baseObjs, posY):
        c4d.EventAdd()
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                      c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        c4d.EventAdd()
        doc = documents.GetActiveDocument()
        baseObjs = []
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for obj in scene:
            if obj.GetUp() == None:
                baseObjs.append(obj)
                # mg = obj.GetMg()
                # obj.InsertUnder(newNull)
                # obj.SetMg(mg)
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
        c4d.CallCommand(12113, 12113)  # Deselect All
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
                    # gui.MessageDialog(objMesh)
                    #errorDetected = True
        # gui.MessageDialog(baseObjs)
        if len(baseObjs) > 0:
            if errorDetected == False:
                getLowestY = self.rasterizeObj(self.sceneLowestYobj())
                self.moveAllToZero(baseObjs, getLowestY)
                c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                              c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
                c4d.EventAdd()


class autoAlignArms():
    def constraintObj(self, obj, target):
        doc = c4d.documents.GetActiveDocument()

        constraintTAG = c4d.BaseTag(1019364)
        constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM] = True
        constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_MAINTAIN] = True
        constraintTAG[20001] = target

        obj.InsertTag(constraintTAG)

        c4d.EventAdd()
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                      c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        return constraintTAG

    def newNullfromJoint(self, jointName, nullName):
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject(jointName)
        nullTemp = None
        if obj:
            tempMg = obj.GetMg()

            nullTemp = c4d.BaseObject(c4d.Onull)
            doc.InsertObject(nullTemp)
            nullTemp.SetMg(tempMg)
            nullTemp.SetName(nullName)
            nullTemp[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0.0
            nullTemp[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0.0
            nullTemp[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0.0
            # nullTemp[c4d.NULLOBJECT_DISPLAY] = 10
            # nullTemp[c4d.NULLOBJECT_ORIENTATION] = 1

            c4d.EventAdd()
        return nullTemp

    def alignJoint(self, side, jointName, jointTarget):
        doc = documents.GetActiveDocument()
        jointSource = doc.SearchObject(side + jointName)
        objSource = self.newNullfromJoint(side + jointName, 'ROTATOR')
        objTarget = self.newNullfromJoint(side + jointTarget, 'TARGET')
        if jointSource != None:
            xtag = self.constraintObj(jointSource, objTarget)
            objTarget.SetMg(objSource.GetMg())
            if side == 'l':
                xValue = 100
            if side == 'r':
                xValue = -100
            objTarget[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X] += xValue
            c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                          c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
            c4d.EventAdd()
            xtag.Remove()
            objSource.Remove()
            objTarget.Remove()

    def __init__(self):
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject('lShldrTwist')
        if obj:
            self.alignJoint('l', 'ShldrBend', 'ForearmBend')
            self.alignJoint('l', 'ShldrTwist', 'ForearmBend')
            self.alignJoint('l', 'ForearmBend', 'Hand')
            self.alignJoint('l', 'ForearmTwist', 'Hand')

            self.alignJoint('l', 'Index1', 'Index2')
            self.alignJoint('l', 'Index2', 'Index3')
            self.alignJoint('l', 'Mid1', 'Mid2')
            self.alignJoint('l', 'Mid2', 'Mid3')
            self.alignJoint('l', 'Ring1', 'Ring2')
            self.alignJoint('l', 'Ring2', 'Ring3')
            self.alignJoint('l', 'Pinky1', 'Pinky2')
            self.alignJoint('l', 'Pinky2', 'Pinky3')

            self.alignJoint('r', 'ShldrBend', 'ForearmBend')
            self.alignJoint('r', 'ShldrTwist', 'ForearmBend')
            self.alignJoint('r', 'ForearmBend', 'Hand')
            self.alignJoint('r', 'ForearmTwist', 'Hand')

            self.alignJoint('r', 'Index1', 'Index2')
            self.alignJoint('r', 'Index2', 'Index3')
            self.alignJoint('r', 'Mid1', 'Mid2')
            self.alignJoint('r', 'Mid2', 'Mid3')
            self.alignJoint('r', 'Ring1', 'Ring2')
            self.alignJoint('r', 'Ring2', 'Ring3')
            self.alignJoint('r', 'Pinky1', 'Pinky2')
            self.alignJoint('r', 'Pinky2', 'Pinky3')

        obj = doc.SearchObject('lShldr')
        if obj:
            self.alignJoint('l', 'Shldr', 'ForeArm')
            self.alignJoint('l', 'ForeArm', 'Hand')
            self.alignJoint('r', 'Shldr', 'ForeArm')
            self.alignJoint('r', 'ForeArm', 'Hand')


class connectEyeLashesMorphXpresso:
    xtag = None

    def connectMorphsXpresso(self, morphMain, morphTagMain, morphTagSlave):
        xtag = c4d.BaseTag(c4d.Texpresso)

        # Set Tag priority to Animation
        pd = xtag[c4d.EXPRESSION_PRIORITY]
        pd.SetPriorityValue(c4d.PRIORITYVALUE_MODE, 1)
        # pd.SetPriorityValue(c4d.PRIORITYVALUE_PRIORITY, Value)
        xtag[c4d.EXPRESSION_PRIORITY] = pd
        xtag[c4d.ID_BASELIST_NAME] = 'DazToC4D Morphs Connect'
        morphMain.InsertTag(xtag)

        nodemaster = xtag.GetNodeMaster()
        # print nodemaster.GetOwner().GetName()

        def connectMorphNodes(x):
            morphNumber = 1001 + x*100
            node1 = nodemaster.CreateNode(
                nodemaster.GetRoot(), c4d.ID_OPERATOR_OBJECT, None, 50, 50 * x)
            node1[c4d.GV_OBJECT_OBJECT_ID] = morphTagMain
            node2 = nodemaster.CreateNode(
                nodemaster.GetRoot(), c4d.ID_OPERATOR_OBJECT, None, 400, 50 * x)
            node2[c4d.GV_OBJECT_OBJECT_ID] = morphTagSlave

            node1out = node1.AddPort(c4d.GV_PORT_OUTPUT, c4d.DescID(
                c4d.DescLevel(4000), c4d.DescLevel(morphNumber)))
            node2in = node2.AddPort(c4d.GV_PORT_INPUT, c4d.DescID(
                c4d.DescLevel(4000), c4d.DescLevel(morphNumber)))

            c4d.modules.graphview.RedrawMaster(nodemaster)
            try:
                node1out.Connect(node2in)
            except:
                return None

        for x in range(1, morphTagMain.GetMorphCount()):
            connectMorphNodes(x)
        c4d.EventAdd()

    def findMorphTag(self, obj):
        objTags = TagIterator(obj)
        for t in objTags:
            if 'Morph' in t.GetName():
                return t

    def __init__(self):
        morphMain = DazToC4DUtils().getDazMesh()
        morphSlave = ''

        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for obj in scene:
            if 'Eyelashes' in obj.GetName():
                if obj.GetType() == 5100:
                    if self.findMorphTag(obj):
                        morphSlave = obj
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for obj in scene:  # TOON GENERATION FIX
            if 'ToonBrows' in obj.GetName():
                if obj.GetType() == 5100:
                    if self.findMorphTag(obj):
                        morphSlave = obj

        if morphSlave != '':
            morphTagMain = self.findMorphTag(morphMain)  # GET FIGURE MESH OBJ!
            morphTagSlave = self.findMorphTag(morphSlave)
            self.connectMorphsXpresso(morphMain, morphTagMain, morphTagSlave)

    def __repr__(self):
        return self.xtag


def getJointFromSkin(obj, jointName):
    # obj = doc.SearchObject(objSkinName)
    objTags = TagIterator(obj)
    for t in objTags:
        if 'Weight' in t.GetName():
            for j in range(t.GetJointCount()):
                if jointName in t.GetJoint(j).GetName():
                    return t.GetJoint(j)
    return None


def getJointFromConstraint(jointName):
    # obj = doc.SearchObject('hip')
    objTags = TagIterator(jointName)
    for t in objTags:
        if 'Constraint' in t.GetName():
            return t[10001]

    return None


class forceTpose():
    def dazRotFix(self, master, mode='', jointToFix='', rotValue=0):
        doc = documents.GetActiveDocument()

        nullObj = c4d.BaseObject(c4d.Onull)  # Create new cube
        nullObj.SetName('TempNull')
        doc.InsertObject(nullObj)
        armJoint = doc.SearchObject('lShldrBend')
        handJoint = doc.SearchObject('lForearmBend')

        mg = jointToFix.GetMg()
        nullObj.SetMg(mg)

        nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0
        nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0
        nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0
        c4d.EventAdd()

        slaveObj = nullObj
        masterObj = master

        def addConstraint(slaveObj, masterObj, mode='Parent'):
            if mode == "Parent":
                constraintTAG = c4d.BaseTag(1019364)

                constraintTAG[c4d.EXPRESSION_ENABLE] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR_MAINTAIN] = True
                # constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PARENT_FROZEN] = False
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
                constraintTAG[10005] = True
                constraintTAG[10007] = True
                constraintTAG[10001] = masterObj

                PriorityDataInitial = c4d.PriorityData()
                PriorityDataInitial.SetPriorityValue(
                    c4d.PRIORITYVALUE_MODE, c4d.CYCLE_EXPRESSION)
                PriorityDataInitial.SetPriorityValue(
                    c4d.PRIORITYVALUE_PRIORITY, 0)
                PriorityDataInitial.SetPriorityValue(
                    c4d.PRIORITYVALUE_CAMERADEPENDENT, 0)
                constraintTAG[c4d.EXPRESSION_PRIORITY] = PriorityDataInitial
            slaveObj.InsertTag(constraintTAG)

        mg = slaveObj.GetMg()
        constraintTAG = c4d.BaseTag(1019364)

        if mode == "ROTATION":
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
            constraintTAG[10005] = False
            constraintTAG[10006] = False
            constraintTAG[10001] = masterObj
        if mode == "AIM":
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM] = True
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_MAINTAIN] = False
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_X] = True
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_Y] = False
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_Z] = False
            constraintTAG[20004] = 5  # Axis X-
            constraintTAG[20001] = masterObj

        slaveObj.InsertTag(constraintTAG)
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        c4d.EventAdd()

        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        constraintTAG.Remove()

        addConstraint(jointToFix, slaveObj)

        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        slaveObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = rotValue
        # slaveObj[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Y] = 0
        # slaveObj[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_Z] = 0

    def dazRotationsFix(self, jointToFix, jointToAim, oppositeJoint, rotValue=0, allToZero=False):
        doc = documents.GetActiveDocument()

        mainJoint = doc.SearchObject(jointToFix)
        goalJoint = doc.SearchObject(jointToAim)
        self.dazRotFix(goalJoint, 'AIM', mainJoint, rotValue)

        jointOposite = doc.SearchObject(oppositeJoint)
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)

        rx = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X]
        ry = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y]
        rz = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z]

        jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = rx * -1
        if allToZero == True:
            jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0
            jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0

        tempNull = doc.SearchObject('TempNull')
        tempNull.Remove()
        caca = mainJoint.GetFirstTag()
        caca.Remove()

        c4d.EventAdd()

    def dazFix_All_To_T_Pose(self):
        # Genesis2
        doc = documents.GetActiveDocument()
        if doc.SearchObject('lShldr'):
            self.dazRotationsFix('lShldr', 'lForeArm', 'rShldr', 1.571)
        if doc.SearchObject('lForeArm'):
            self.dazRotationsFix('lForeArm', 'lHand', 'rForeArm', 1.571)

        # # Genesis3
        # if doc.SearchObject('lForearmBend'):
        #     self.dazRotationsFix('lForearmBend', 'lHand', 'rForearmBend', 1.571, True)
        # if doc.SearchObject('lShldrBend'):
        #     self.dazRotationsFix('lShldrBend', 'lForearmBend', 'rShldrBend', 1.571)
        #
        # if doc.SearchObject('lHand'):
        #     self.dazRotationsFix('lHand', 'lMid1', 'rHand', 1.571)

        # All Genesis..Maybe...
        if doc.SearchObject('lFoot'):
            self.dazRotationsFix('lFoot', 'lToe', 'rFoot')


class alignFingersFull():

    def fixRotations(self, jointName):
        doc = documents.GetActiveDocument()
        try:
            obj = doc.SearchObject(jointName)
            obj[c4d.ID_BASEOBJECT_ROTATION_ORDER] = 5

            objRotX = obj.GetAbsRot()[0]
            objRotY = obj.GetAbsRot()[1]
            objRotZ = obj.GetAbsRot()[2]
            obj.SetAbsRot(c4d.Vector(objRotX, 0, 0))
        except:
            print('FixR skipped...')

    def AlignBoneChain(self, rootBone, upAxis, primaryAxis=1, primaryDirection=0, upDirection=4):
        doc = documents.GetActiveDocument()
        try:
            c4d.CallCommand(12113, 12113)  # Deselect All
            joint = doc.SearchObject(rootBone)

            normalNull = doc.SearchObject('normalNull')  # Normal Null ...!!..

            doc.SetActiveObject(joint, c4d.SELECTION_NEW)
            # c4d.CallCommand(1021334, 1021334)
            c4d.CallCommand(1021334)  # Joint Align Tool
            tool = c4d.plugins.FindPlugin(doc.GetAction(), c4d.PLUGINTYPE_TOOL)
            if tool is not None:
                tool[c4d.ID_CA_JOINT_ALIGN_PRIMARY_AXIS] = primaryAxis
                tool[c4d.ID_CA_JOINT_ALIGN_PRIMARY_DIRECTION] = primaryDirection
                tool[c4d.ID_CA_JOINT_ALIGN_UP_AXIS] = upAxis
                tool[c4d.ID_CA_JOINT_ALIGN_UP_DIRECTION] = upDirection
                tool[c4d.ID_CA_JOINT_ALIGN_UP_FROMPREV] = True
                tool[c4d.ID_CA_JOINT_ALIGN_CHILDREN] = True
                tool[c4d.ID_CA_JOINT_ALIGN_UP_LINK] = normalNull
                c4d.CallButton(tool, c4d.ID_CA_JOINT_ALIGN)
        except:
            print('AlignBC Skipped...')
        c4d.EventAdd()

    def alignJoints(self, jointName):
        doc = documents.GetActiveDocument()
        try:
            obj = doc.SearchObject(jointName)

            obj[c4d.ID_CA_JOINT_OBJECT_BONE_AXIS] = 1
            c4d.CallCommand(1019883)  # Align
        except:
            print('alignPass skipped...')
        c4d.EventAdd()

    def constraintClamp(self, obj, normalPolyObj):
        doc = documents.GetActiveDocument()
        constraintTAG = c4d.BaseTag(1019364)
        constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_CLAMP] = True
        constraintTAG[50004, 1] = 4  # To: Surface
        constraintTAG[50004, 3] = 5  # Align: Z-
        constraintTAG[50004, 2] = 3  # Mode: Fix Axis
        constraintTAG[50004, 4] = 4  # As: Normal
        constraintTAG[50001] = normalPolyObj
        # PriorityDataInitial = c4d.PriorityData()
        # PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_MODE, c4d.CYCLE_GENERATORS)
        # PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_PRIORITY, 0)
        # PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_CAMERADEPENDENT, 0)
        # constraintTAG[c4d.EXPRESSION_PRIORITY] = PriorityDataInitial
        obj.InsertTag(constraintTAG)
        # constraintTAG[50004, 9] = 0 #Distance: 0
        c4d.EventAdd()

    def generateNormalFromObjs(self, target1, target2, target3):
        doc = documents.GetActiveDocument()
        obj1 = doc.SearchObject('normalNull')
        obj2 = doc.SearchObject('normalPoly')
        obj3 = doc.SearchObject('normalPos1')
        obj4 = doc.SearchObject('normalPos2')
        obj5 = doc.SearchObject('normalPos3')

        try:
            obj1.Remove()
        except:
            pass
        try:
            obj2.Remove()
        except:
            pass
        try:
            obj3.Remove()
        except:
            pass
        try:
            obj4.Remove()
        except:
            pass
        try:
            obj5.Remove()
        except:
            pass

        objNull = c4d.BaseObject(c4d.Onull)
        objNull.SetName('normalNull')
        doc.InsertObject(objNull)
        c4d.EventAdd()

        obj1 = c4d.BaseObject(c4d.Onull)
        obj1.SetName('normalPos1')
        doc.InsertObject(obj1)
        obj2 = c4d.BaseObject(c4d.Onull)
        doc.InsertObject(obj2)
        obj2.SetName('normalPos2')
        obj3 = c4d.BaseObject(c4d.Onull)
        doc.InsertObject(obj3)
        obj3.SetName('normalPos3')

        targetObj1 = doc.SearchObject(target1)
        targetObj2 = doc.SearchObject(target2)
        targetObj3 = doc.SearchObject(target3)

        obj1.SetMg(targetObj1.GetMg())
        obj2.SetMg(targetObj2.GetMg())
        obj3.SetMg(targetObj3.GetMg())

        mypoly = c4d.BaseObject(c4d.Opolygon)  # Create an empty polygon object
        # New number of points, New number of polygons
        mypoly.ResizeObject(4, 1)

        mypoly.SetPoint(0, obj1.GetAbsPos())
        mypoly.SetPoint(1, obj2.GetAbsPos())
        mypoly.SetPoint(2, obj3.GetAbsPos())
        mypoly.SetPoint(3, obj3.GetAbsPos())

        mypoly.SetName('normalPoly')
        # The Polygon's index, Polygon's points
        mypoly.SetPolygon(0, c4d.CPolygon(0, 1, 2, 3))
        doc.InsertObject(mypoly, None, None)
        mypoly.Message(c4d.MSG_UPDATE)

        doc.SetActiveObject(mypoly, c4d.SELECTION_NEW)
        c4d.CallCommand(14039)  # Optimize...
        c4d.CallCommand(1011982)  # Center Axis to

        objNull.SetMg(mypoly.GetMg())

        c4d.EventAdd()

        self.constraintClamp(objNull, mypoly)
        c4d.EventAdd()

    def start(self, modelName, lastFinger=''):
        doc = c4d.documents.GetActiveDocument()
        # modelName = 'Human_Builder_' #Replace with model name....
        jHand = modelName + 'jHand'
        jIndex1 = modelName + 'jIndex1'
        jIndex2 = modelName + 'jIndex2'
        jIndex3 = modelName + 'jIndex3'
        jMiddle1 = modelName + 'jMiddle1'
        jMiddle2 = modelName + 'jMiddle2'
        jMiddle3 = modelName + 'jMiddle3'
        jRing1 = modelName + 'jRing1'
        jRing2 = modelName + 'jRing2'
        jRing3 = modelName + 'jRing3'
        jPink1 = modelName + 'jPink1'
        jPink2 = modelName + 'jPink2'
        jPink3 = modelName + 'jPink3'
        fingersList = ['jIndex1', 'jIndex2', 'jIndex3',
                       'jMiddle1', 'jMiddle2', 'jMiddle3',
                       'jRing1', 'jRing2', 'jRing3',
                       'jPink1', 'jPink2', 'jPink3']

        for j in fingersList:
            self.alignJoints(modelName + j)  # Replace with model name....

        # Generate plane if at least jIndex and other finger present...
        if lastFinger == 'jPink':
            self.generateNormalFromObjs(jHand, jIndex1, jPink1)
        if lastFinger == 'jRing':
            self.generateNormalFromObjs(jHand, jIndex1, jRing1)
        if lastFinger == 'jMiddle':
            self.generateNormalFromObjs(jHand, jIndex1, jMiddle1)

        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                      c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)

        self.AlignBoneChain(modelName + 'jIndex1', 2, 3, 0, 2)
        self.AlignBoneChain(modelName + 'jMiddle1', 2, 3, 0, 2)
        self.AlignBoneChain(modelName + 'jRing1', 2, 3, 0, 2)
        self.AlignBoneChain(modelName + 'jPink1', 2, 3, 0, 2)

        self.fixRotations(jIndex2)
        self.fixRotations(jIndex3)
        self.fixRotations(jMiddle2)
        self.fixRotations(jMiddle3)
        self.fixRotations(jRing2)
        self.fixRotations(jRing3)
        self.fixRotations(jPink2)
        self.fixRotations(jPink3)

        obj1 = doc.SearchObject('normalNull')
        obj2 = doc.SearchObject('normalPoly')
        obj3 = doc.SearchObject('normalPos1')
        obj4 = doc.SearchObject('normalPos2')
        obj5 = doc.SearchObject('normalPos3')
        try:
            obj1.Remove()
        except:
            pass
        try:
            obj2.Remove()
        except:
            pass
        try:
            obj3.Remove()
        except:
            pass
        try:
            obj4.Remove()
        except:
            pass
        try:
            obj5.Remove()
        except:
            pass

        c4d.EventAdd()


class DazToC4D():
    dialog = None

    def AUTH(self):
        # authhh = authDialogDazToC4D()

        bc = c4d.plugins.GetWorldPluginData(PLUGIN_ID)
        if bc is not None:
            # result = bc.GetBool(101)
            result = bc.GetString(101)
            if result is not None:
                if result:
                    return True

        #print ("3DtoAll: DazToC4D - Activation Needed")

        screen = c4d.gui.GeGetScreenDimensions(0, 0, True)

        if self.authDialogDazToC4D is None:
            self.authDialogDazToC4D = authDialogDazToC4D()
        self.authDialogDazToC4D.Open(
            c4d.DLG_TYPE_MODAL, PLUGIN_ID, screen['sx2'] / 2 - 220, screen['sy2'] / 2 - 220, 0, 0)

        return False

    def VersionCheck_C4D(self):

        VersionNum = int(str(c4d.GetC4DVersion())[0:2])
        if VersionNum < 18:
            self.R18 = False
        if VersionNum < 16:
            self.R16 = False

        if (self.R18):
            self.REFLECTION_LAYERID = 4
        else:
            self.REFLECTION_LAYERID = 5

        if int(str(c4d.GetC4DVersion())[0:2]) > 21:
            gui.MessageDialog(
                "This version of the DazToC4D plugin does not officially support versions of Cinema4D above R20.")

    def stdMatExtrafixes(self):
        doc = c4d.documents.GetActiveDocument()

        # --- Fix duplicated Moisture material...??
        myMaterials = doc.GetMaterials()
        for mat in myMaterials:
            if "EyeMoisture" in mat.GetName():
                mat.SetName('EyeMoisture2')
                return True

        def setRenderToPhysical():
            try:
                rdata = doc.GetActiveRenderData()
                vpost = rdata.GetFirstVideoPost()
                rdata[c4d.RDATA_RENDERENGINE] = c4d.RDATA_RENDERENGINE_PHYSICAL

                while vpost:
                    if vpost.CheckType(c4d.VPxmbsampler):
                        break
                    vpost = vpost.GetNext()

                if not vpost:
                    vpost = c4d.BaseList2D(c4d.VPxmbsampler)
                    rdata.InsertVideoPost(vpost)

                c4d.EventAdd()
            except:
                pass

        setRenderToPhysical()
        figureModel = 'Genesis8'

        def findMatName(matToFind):
            matFound = None
            sceneMats = doc.GetMaterials()
            for mat in sceneMats:
                matName = mat.GetName()
                if matToFind in matName:
                    matFound = mat
                    return matFound
            return matFound

        if findMatName('EyeReflection'):
            figureModel = 'Genesis2'
        if findMatName('Fingernails'):
            figureModel = 'Genesis3'

        # FIX MATERIAL NAMES etc... USE THIS FOR ALL CONVERTIONS NOT JUST OCTANE!
        if findMatName('1_SkinFace') == None and findMatName('1_Nostril') != None:
            try:
                findMatName('1_Nostril').SetName('1_SkinFace')
            except:
                pass
        if findMatName('3_SkinHand') == None and findMatName('3_SkinFoot') != None:
            try:
                findMatName('3_SkinFoot').SetName('3_ArmsLegs')
            except:
                pass
        # ////
        doc = documents.GetActiveDocument()
        sceneMats = doc.GetMaterials()

        for mat in sceneMats:
            matName = mat.GetName()
            try:
                mat[c4d.MATERIAL_ALPHA_SHADER][c4d.BITMAPSHADER_WHITEPOINT] = 0.5
            except:
                pass
            try:
                layerTransp = mat.GetReflectionLayerTrans()
                mat[layerTransp.GetDataID() +
                    c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS] = 0.0
            except:
                pass

            # GENESIS 3 Patches -------------------------
            if figureModel == 'Genesis3' or figureModel == 'Genesis2' or figureModel == 'Genesis8':
                if 'Cornea' in matName:
                    bmpPath = 'CACA'
                    # create a bitmap shader for the material
                    shaderColor = c4d.BaseList2D(c4d.Xcolor)
                    # bmpShader[c4d.BITMAPSHADER_FILENAME] = bmpPath
                    mat.InsertShader(shaderColor)
                    mat[c4d.MATERIAL_USE_ALPHA] = True
                    mat[c4d.MATERIAL_ALPHA_SHADER] = shaderColor
                    mat[c4d.MATERIAL_ALPHA_SHADER][c4d.COLORSHADER_BRIGHTNESS] = 0.0

                if 'Moisture' in matName or 'Tear' in matName:
                    mat[c4d.MATERIAL_USE_ALPHA] = True
                    mat[c4d.MATERIAL_ALPHA_SHADER] = None
                    mat[c4d.MATERIAL_COLOR_COLOR] = c4d.Vector(0, 0, 0)
                    mat[c4d.MATERIAL_TRANSPARENCY_REFRACTION] = 1.0

                if 'Sclera' in matName:
                    try:
                        mat[c4d.MATERIAL_COLOR_SHADER][c4d.BITMAPSHADER_WHITEPOINT] = 0.8
                    except:
                        pass

        c4d.EventAdd()

    def specificFiguresFixes(self):
        doc = c4d.documents.GetActiveDocument()

        figureModel = ''

        def findMatName(matToFind):
            matFound = None
            sceneMats = doc.GetMaterials()
            for mat in sceneMats:
                matName = mat.GetName()
                if matToFind in matName:
                    matFound = mat
                    return matFound
            return matFound

        # TOON GENERATION 2
        doc = documents.GetActiveDocument()
        sceneMats = doc.GetMaterials()
        # ZOMBIE ... GEN3...
        if findMatName('Cornea') != None and findMatName('EyeMoisture') == None:
            mat = findMatName('Cornea')
            mat[c4d.MATERIAL_USE_ALPHA] = False

        for mat in sceneMats:
            matName = mat.GetName()
            if 'Eyelashes' in matName:
                if mat[c4d.MATERIAL_ALPHA_SHADER] == None:
                    try:
                        # create a bitmap shader for the material
                        shaderColor = c4d.BaseList2D(c4d.Xcolor)
                        mat.InsertShader(shaderColor)
                        mat[c4d.MATERIAL_USE_ALPHA] = True
                        mat[c4d.MATERIAL_ALPHA_SHADER] = shaderColor
                        mat[c4d.MATERIAL_ALPHA_SHADER][c4d.COLORSHADER_BRIGHTNESS] = 0.0
                    except:
                        pass

        c4d.EventAdd()

    def figureFixBrute(self):
        doc = c4d.documents.GetActiveDocument()

        def checkIfBrute():
            isBrute = False
            docMaterials = doc.GetMaterials()
            for mat in docMaterials:
                mapDiffuse = ''
                try:
                    mapDiffuse = mat[c4d.MATERIAL_COLOR_SHADER][c4d.BITMAPSHADER_FILENAME]
                except:
                    pass
                if 'Brute8' in mapDiffuse:
                    isBrute = True
            return isBrute

        def nullSize(nullName, rad=1, ratio=1):
            daz_name = 'Genesis8Male_'  # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            obj = doc.SearchObject(daz_name + nullName)
            if obj:
                obj[c4d.NULLOBJECT_RADIUS] = rad
                obj[c4d.NULLOBJECT_ASPECTRATIO] = ratio
                c4d.EventAdd()

        if checkIfBrute():  # If BRUTE8! Change Null Sizes!
            nullSize('Pelvis_ctrl', 40, 0.8)
            nullSize('Spine_ctrl', 30, 0.8)
            nullSize('Chest_ctrl', 30, 0.8)
            nullSize('Foot_PlatformBase', 9.3, 1.52)
            nullSize('Foot_PlatformBase___R', 9.3, 1.52)
            nullSize('Collar_ctrl', 20, 0.3)
            nullSize('Collar_ctrl___R', 20, 0.3)

            nullSize('ForearmTwist_ctrl', 11, 1.0)
            nullSize('ForearmTwist_ctrl___R', 11, 1.0)

            nullSize('IK_Hand', 7, 1.4)
            nullSize('IK_Hand___R', 7, 1.4)

    def hidePolys(self):
        # USEFUL TO HIDE POLYGONS WHEN CONVERTING TO OCTANE OR REDSHIFT..
        # ...BECAUSE NO TRANSP ON VIEWPORT

        # validate object and selectiontag
        doc = documents.GetActiveDocument()
        # if not op:return
        # if not op.IsInstanceOf(c4d.Opolygon):return

        def hidePolysFromObj(op):
            tags = op.GetTags()

            # deselect current polygonselection and store a backup to reselect
            polyselection = op.GetPolygonS()
            store = c4d.BaseSelect()
            polyselection.CopyTo(store)

            # loop through the tags and check if name and type fits
            # if so split
            t = op.GetFirstTag()
            while t:
                if t.GetType() == c4d.Tpolygonselection:
                    if 'EyeMoisture' in t.GetName() or 'Cornea' in t.GetName():

                        # select polygons from selectiontag
                        tagselection = t.GetBaseSelect()
                        tagselection.CopyTo(polyselection)

                        # split: polygonselection to a new object
                        sec = utils.SendModelingCommand(command=c4d.MCOMMAND_HIDESELECTED,
                                                        list=[op],
                                                        mode=c4d.MODELINGCOMMANDMODE_POLYGONSELECTION,
                                                        doc=doc)

                        if not sec:
                            return
                        print(sec)
                        # sec[0].InsertAfter(op)

                t = t.GetNext()

            store.CopyTo(polyselection)
            c4d.EventAdd()

        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()

        scene = ObjectIterator(obj)
        for obj in scene:
            if obj.GetType() == 5100:
                hidePolysFromObj(obj)

    def hidePolyTagByName(self, op, tagName):
        doc = documents.GetActiveDocument()
        tags = op.GetTags()
        polyselection = None
        try:
            polyselection = op.GetPolygonS()
        except:
            pass
        if polyselection:
            store = c4d.BaseSelect()
            polyselection.CopyTo(store)

            t = op.GetFirstTag()
            while t:
                if t.GetType() == c4d.Tpolygonselection:
                    if tagName in t.GetName():
                        tagselection = t.GetBaseSelect()
                        tagselection.CopyTo(polyselection)
                        sec = utils.SendModelingCommand(command=c4d.MCOMMAND_HIDESELECTED,
                                                        list=[op],
                                                        mode=c4d.MODELINGCOMMANDMODE_POLYGONSELECTION,
                                                        doc=doc)
                        if not sec:
                            return
                        # sec[0].InsertAfter(op)
                t = t.GetNext()

            store.CopyTo(polyselection)
            c4d.EventAdd()

    def hideEyePolys(self):
        doc = documents.GetActiveDocument()

        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)

        for obj in scene:
            self.hidePolyTagByName(obj, 'EyeMoisture')
            self.hidePolyTagByName(obj, 'Cornea')

    
    def moveMorphsToGroup(self, figureObj):
        doc = documents.GetActiveDocument()
        newNull = None
        groupNull = None

        def makeGroup():
            newNull = c4d.BaseObject(c4d.Onull)  # Create new null
            doc.InsertObject(newNull)
            c4d.EventAdd()
            newNull.SetName('Morphs')
            return newNull

        def moveMorphTag(sourceObj, targetObj):
            doc = documents.GetActiveDocument()
            morphTag = None
            tags = TagIterator(sourceObj)
            for tag in tags:
                if 'Pose Morph' in tag.GetName():
                    morphTag = tag

            if morphTag:
                print(morphTag)
                targetObj.InsertTag(morphTag)

            c4d.EventAdd()

        firstObj = doc.GetFirstObject()
        scene = ObjectIterator(firstObj)
        morphGroups = []
        for obj in scene:
            objName = obj.GetName()
            if 'Poses' in objName:
                morphGroups.append(obj)

        print(len(morphGroups))
        if len(morphGroups) > 0:
            groupNull = makeGroup()
            for x in morphGroups:
                print(x)
                x.InsertUnder(groupNull)
            moveMorphTag(figureObj, groupNull)

        c4d.EventAdd()
        return groupNull

    def xpressoTagToMorphsGroup(self, morphsGroup):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()

        scene = ObjectIterator(obj)
        objTags = TagIterator(obj)
        xtag = None

        for ob in scene:
            objTags = TagIterator(ob)
            if objTags:
                for tag in objTags:
                    if tag.GetName() == 'DazToC4D Morphs Connect':
                        morphsGroup.InsertTag(tag)
                        mtag = morphsGroup.GetLastTag()
                        morphsGroup.InsertTag(mtag)

        c4d.EventAdd()

    def morphsFixRemoveAndRename(self):
        def morphsRemoveAndRename(obj):
            pmTag = obj.GetTag(c4d.Tposemorph)  # Gets the pm tag
            pmTag.ExitEdit(doc, True)

            def morphRemove():
                listMorphsToRemove = ['RIG',
                                      'HDLv2',
                                      'HDLv3',
                                      'pNeckHead',
                                      'Genesis8Male_',
                                      'Genesis8MaleEyelashes_',
                                      'Genesis8Female_',
                                      'Genesis8FemaleEyelashes_'
                                      ]

                morphsAmount = len(list(range(pmTag.GetMorphCount())))
                for x in range(0, morphsAmount):
                    try:
                        pmTag.SetActiveMorphIndex(x)
                        morphName = pmTag.GetActiveMorph().GetName()
                        for morphToRemove in listMorphsToRemove:
                            try:
                                if morphToRemove in morphName:
                                    pmTag.RemoveMorph(x)
                                    try:
                                        obj = doc.SearchObject(morphName)
                                        obj.Remove()
                                    except:
                                        pass
                                    return
                            except:
                                print('skip remove')
                    except:
                        pass
                c4d.EventAdd()

            def morphRename():
                # pmTag = obj.GetTag(c4d.Tposemorph)  # Gets the pm tag
                # pmTag.ExitEdit(doc, True)

                morphsAmount = len(list(range(pmTag.GetMorphCount())))
                for x in range(0, morphsAmount):
                    try:
                        pmTag.SetActiveMorphIndex(x)
                        morphName = pmTag.GetActiveMorph().GetName()
                        try:
                            newMorphName = morphName.replace('head__', '')
                            newMorphName = newMorphName.replace('eCTRLM7', '')
                            newMorphName = newMorphName.replace('eCTRL', '')
                            newMorphName = newMorphName.replace(
                                '3duTG2_10yo_', '')
                            newMorphName = newMorphName.replace(
                                'PBMSTEDIM7', '')
                            newMorphName = newMorphName.replace('PHM', '')
                            newMorphName = newMorphName.replace('CTRLB', '')
                            newMorphName = newMorphName.replace('CTRL', '')
                            newMorphName = newMorphName.replace('_', '')
                            pmTag.GetActiveMorph().SetName(newMorphName)
                        except Exception as e:
                            pass
                    except Exception as e:
                        pass
                c4d.EventAdd()

            morphsAmount = len(list(range(pmTag.GetMorphCount())))

            for x in range(0, morphsAmount):
                morphRename()
            for x in range(0, morphsAmount):
                morphRemove()  # REMOVE
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for ob in scene:
            pmTag = ob.GetTag(c4d.Tposemorph)  # Gets the pm tag
            if pmTag:
                morphsRemoveAndRename(ob)

    def morphsGroupMoveUp(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        objTags = TagIterator(obj)

        for ob in scene:
            if ob.GetUp() == None and ob.GetType() == 5140:
                objTags = TagIterator(ob)
                if objTags:
                    for tag in objTags:
                        if tag.GetType() == 1024237:  # Morph Tag Type
                            # Deselect All
                            c4d.CallCommand(100004767, 100004767)
                            ob.SetBit(c4d.BIT_ACTIVE)
                            c4d.CallCommand(100004819)  # Cut
                            c4d.CallCommand(100004821)  # Paste
                            # Deselect All
                            c4d.CallCommand(100004767, 100004767)

        c4d.EventAdd()

    def morphTagsToGroups(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()

        scene = ObjectIterator(obj)
        objTags = TagIterator(obj)
        xtag = None

        for ob in scene:
            objTags = TagIterator(ob)
            if objTags:
                for tag in objTags:
                    if tag.GetType() == 1024237:
                        print(ob.GetName(), tag.GetName())
                        mGroup = doc.SearchObject('Poses: ' + ob.GetName())
                        if mGroup:
                            mGroup.InsertTag(tag)

        c4d.EventAdd()

    def addLipsMaterial(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        objTags = TagIterator(obj)
        for ob in scene:
            objTags = TagIterator(ob)
            if objTags:
                for tag in objTags:
                    matSel = tag[c4d.TEXTURETAG_RESTRICTION]
                    if matSel == 'Lips':
                        try:
                            old_mat = tag[c4d.TEXTURETAG_MATERIAL]

                            doc.SetActiveMaterial(old_mat)
                            c4d.CallCommand(300001022, 300001022)  # Copy
                            c4d.CallCommand(300001023, 300001023)  # Paste
                            newMat = doc.GetFirstMaterial()
                            newMat[c4d.ID_BASELIST_NAME] = 'Lips'

                            tag[c4d.TEXTURETAG_MATERIAL] = newMat
                        except:
                            pass

        c4d.EventAdd()

    def reduceMatFix(self):
        doc = c4d.documents.GetActiveDocument()
        myMaterials = doc.GetMaterials()
        matHead = False
        matTorso = False
        matLegs = False
        matHands = False
        for mat in myMaterials:
            # print mat.GetName()
            if 'Torso' in mat.GetName():
                matTorso = mat
            if 'Hands' in mat.GetName():
                matHands = mat
            if 'Legs' in mat.GetName():
                matLegs = mat
            if 'Head' in mat.GetName():
                matHead = mat

        if matTorso == False and matHead != False:
            matHead.SetName('MainSkin')
        if matHands == False and matLegs != False:
            matLegs.SetName('LegsAndArms')

        c4d.EventAdd()

    def removeDisp(self):
        doc = c4d.documents.GetActiveDocument()
        myMaterials = doc.GetMaterials()
        for mat in myMaterials:
            mat[c4d.MATERIAL_USE_DISPLACEMENT] = False

        c4d.EventAdd()

    def findMesh(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)

        foundMesh = False

        for obj in scene:
            if obj.GetType() == 5100:
                foundMesh = True

        return foundMesh

    def mirrorPose(self):
        doc = documents.GetActiveDocument()

        def mirrorPose(jointName):
            # jointName = 'lShldrBend'
            jointNameR = 'r' + jointName[1:100]
            jointObjL = doc.SearchObject(jointName)
            jointObjR = doc.SearchObject(jointNameR)
            if jointObjL:
                objLRot = jointObjL[c4d.ID_BASEOBJECT_REL_ROTATION]
                jointObjR[c4d.ID_BASEOBJECT_REL_ROTATION,
                          c4d.VECTOR_X] = -objLRot[0]
                jointObjR[c4d.ID_BASEOBJECT_REL_ROTATION,
                          c4d.VECTOR_Y] = objLRot[1]
                jointObjR[c4d.ID_BASEOBJECT_REL_ROTATION,
                          c4d.VECTOR_Z] = -objLRot[2]

        mirrorPose('lCollar')
        mirrorPose('lShldr')  # ----Genesis 2
        mirrorPose('lForeArm')  # ----Genesis 2
        mirrorPose('lShldrBend')
        mirrorPose('lShldrTwist')
        mirrorPose('lForearmBend')
        mirrorPose('lForearmTwist')
        mirrorPose('lHand')

        mirrorPose('lThumb1')
        mirrorPose('lThumb2')
        mirrorPose('lThumb3')
        mirrorPose('lCarpal1')
        mirrorPose('lIndex1')
        mirrorPose('lIndex2')
        mirrorPose('lIndex3')
        mirrorPose('lCarpal2')
        mirrorPose('lMid1')
        mirrorPose('lMid2')
        mirrorPose('lMid3')
        mirrorPose('lCarpal3')
        mirrorPose('lRing1')
        mirrorPose('lRing2')
        mirrorPose('lRing3')
        mirrorPose('lCarpal4')
        mirrorPose('lPinky1')
        mirrorPose('lPinky2')
        mirrorPose('lPinky3')

        mirrorPose('lThigh')  # ----Genesis 2
        mirrorPose('lShin')  # ----Genesis 2
        mirrorPose('lToe')  # ----Genesis 2

        mirrorPose('lThighBend')
        mirrorPose('lThighTwist')
        mirrorPose('lShin')
        mirrorPose('lFoot')
        mirrorPose('lMetatarsals')
        mirrorPose('lToe')

        mirrorPose('lSmallToe4')
        mirrorPose('lSmallToe4_2')
        mirrorPose('lSmallToe3')
        mirrorPose('lSmallToe3_2')
        mirrorPose('lSmallToe2')
        mirrorPose('lSmallToe2_2')
        mirrorPose('lSmallToe1')
        mirrorPose('lSmallToe1_2')
        mirrorPose('lBigToe')
        mirrorPose('lBigToe_2')

        c4d.EventAdd()

    def eyeLashAndOtherFixes(self):
        doc = c4d.documents.GetActiveDocument()
        docMaterials = doc.GetMaterials()
        irisMap = ''
        for mat in docMaterials:  # Lashes fix... Gen2 and maybe others...
            matName = mat.GetName()
            if 'Lashes' in matName:
                try:
                    mat[c4d.MATERIAL_COLOR_SHADER] = None
                except:
                    print('mat skip...')
                    pass
            if 'Iris' in matName:
                try:
                    irisMap = mat[c4d.MATERIAL_COLOR_SHADER][c4d.BITMAPSHADER_FILENAME]
                except:
                    pass

        for mat in docMaterials:  # Iris fix Gen2 and maybe others...
            if mat[c4d.MATERIAL_COLOR_SHADER]:
                if mat[c4d.MATERIAL_COLOR_SHADER].GetType() == 5833:
                    matTexture = mat[c4d.MATERIAL_COLOR_SHADER][c4d.BITMAPSHADER_FILENAME]
                    matName = mat.GetName()
                    if irisMap == matTexture:
                        if 'Sclera' not in matName:
                            mat[c4d.MATERIAL_USE_REFLECTION] = False

        for mat in docMaterials:  # Fix to Tear.. Gen2...
            matName = mat.GetName()
            if 'Tear' in matName:
                mat[c4d.MATERIAL_TRANSPARENCY_COLOR] = c4d.Vector(
                    0.94, 0.94, 0.94)

    def checkIfPosedResetPose(self, checkAndReset=True):
        doc = documents.GetActiveDocument()
        # isPosed = False

        def checkIfPosed():
            obj = doc.GetFirstObject()
            scene = ObjectIterator(obj)
            jointsList = ['Collar', 'head', 'ShldrTwist',
                          'Forearm', 'pelvis', 'abdomen', 'Shldr']
            caca = False

            def checkJoint(jointName):
                joint = doc.SearchObject(jointName)
                if joint:
                    rotRX = abs(
                        joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                    rotRY = abs(
                        joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                    rotRZ = abs(
                        joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
                    # print(rotRX)
                    # print(rotRY)
                    # print(rotRZ)
                    if rotRX == rotRY == rotRZ == 0.0:
                        return False
                    else:
                        return True

            def compareJoints(jointName):
                jointR = doc.SearchObject('r' + jointName)
                jointL = doc.SearchObject('l' + jointName)
                if jointR:
                    rotRX = abs(
                        jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                    rotRY = abs(
                        jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                    rotRZ = abs(
                        jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
                    rotLX = abs(
                        jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                    rotLY = abs(
                        jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                    rotLZ = abs(
                        jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
                    rotRX = round(rotRX, 2)
                    rotRY = round(rotRY, 2)
                    rotRZ = round(rotRZ, 2)
                    rotLX = round(rotLX, 2)
                    rotLY = round(rotLY, 2)
                    rotLZ = round(rotLZ, 2)
                    # print(rotRX, rotLX)
                    # print(rotRY, rotLY)
                    # print(rotRZ, rotLZ)
                    if rotRX == rotLX and rotRY == rotLY and rotRZ == rotLZ:
                        return False
                    else:
                        return True

            isPosed = False

            if compareJoints('ForeArm'):
                isPosed = True
            if compareJoints('Shldr'):
                isPosed = True
            if compareJoints('ShldrBend'):
                isPosed = True
            if compareJoints('ForearmBend'):
                isPosed = True
            if compareJoints('Hand'):
                isPosed = True
            if compareJoints('ThighBend'):
                isPosed = True
            if checkJoint('chestUpper'):
                isPosed = True
            if checkJoint('chestLower'):
                isPosed = True
            if checkJoint('abdomenLower'):
                isPosed = True
            if checkJoint('abdomenUpper'):
                isPosed = True
            if checkJoint('neckLower'):
                isPosed = True

            return isPosed

        if checkAndReset == False:
            return checkIfPosed()

        jointHip = doc.SearchObject('hip')  # CAMBIIIIIIIIIIIIIIIAAARRR
        jointRig = ObjectIterator(jointHip)
        if checkIfPosed():
            answer = gui.MessageDialog(
                'Reset Pose first before Auto-Ik.\nReset Pose now?\n\nWarning: No Undo', c4d.GEMB_YESNO)
            if answer == 6:
                for x in jointRig:
                    x[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0.0
                    x[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0.0
                    x[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0.0
                jointHip[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0.0
                jointHip[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0.0
                jointHip[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0.0

                try:
                    mainJoint = jointHip.GetUp()
                    mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION,
                              c4d.VECTOR_X] = 0.0
                    mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION,
                              c4d.VECTOR_Y] = 0.0
                    mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION,
                              c4d.VECTOR_Z] = 0.0
                    mainJoint[c4d.ID_BASEOBJECT_REL_POSITION,
                              c4d.VECTOR_X] = 0.0
                    # mainJoint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y] = 0.0
                    mainJoint[c4d.ID_BASEOBJECT_REL_POSITION,
                              c4d.VECTOR_Z] = 0.0
                except:
                    pass

                DazToC4D().dazManualRotationFixTpose()
                # DazToC4DUtils().sceneToZero()

                c4d.EventAdd()
                c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                              c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
                c4d.EventAdd()

                AllSceneToZero().sceneToZero()
                c4d.CallCommand(12168, 12168)  # Delete Unused Materials
                answer = gui.MessageDialog('Auto-Ik now?', c4d.GEMB_YESNO)
                if answer == 6:
                    DazToC4D().autoIK()
                    return False
                else:
                    return True
        else:
            DazToC4D().autoIK()

    def lockLayerOnOff(self):
        doc = documents.GetActiveDocument()
        root = doc.GetLayerObjectRoot()  # Gets the layer manager
        layer = ''
        LayersList = root.GetChildren()
        for layers in LayersList:
            name = layers.GetName()
            if (name == 'IKM_Lock'):
                layer = layers
        if layer:
            if layer.GetName() == "IKM_Lock":
                layer_data = layer.GetLayerData(doc)
                lockValue = layer_data['locked']
                # Gets the plugin's directory
                dir, file = os.path.split(__file__)
                # Adds the res folder to the path
                LogoFolder_Path = os.path.join(dir, 'res')
                # Adds the res folder to the path
                LogoFolder_PathIcons = os.path.join(LogoFolder_Path, 'icons')
                img_lock = os.path.join(LogoFolder_PathIcons, 'm_lock.png')
                img_lockON = os.path.join(LogoFolder_PathIcons, 'm_lockON.png')

                print(lockValue)
                if lockValue == True:
                    layer_data['locked'] = False
                    guiDazToC4DLayerLockButton.SetImage(img_lock, True)
                else:
                    layer_data['locked'] = True
                    guiDazToC4DLayerLockButton.SetImage(img_lockON, True)

                layer.SetLayerData(doc, layer_data)

        c4d.EventAdd()

    def limitTwistPosition(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()

        def addProtTag(obj):
            xtag = c4d.BaseTag(c4d.Tprotection)
            xtag[c4d.PROTECTION_P] = 1
            xtag[c4d.PROTECTION_S] = False
            xtag[c4d.PROTECTION_R] = 1
            xtag[c4d.PROTECTION_R_X] = True
            xtag[c4d.PROTECTION_R_Y] = False
            xtag[c4d.PROTECTION_R_Z] = True

            obj.InsertTag(xtag)

        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for obj in scene:
            if 'ForearmTwist' in obj.GetName():
                addProtTag(obj)

    def freezeTwistBones(self):
        doc = c4d.documents.GetActiveDocument()

        nullForeArm = doc.SearchObject(daz_name + 'ForearmTwist_ctrl')
        nullForeArmR = doc.SearchObject(daz_name + 'ForearmTwist_ctrl___R')
        if nullForeArm:
            nullForeArm.SetFrozenPos(nullForeArm.GetAbsPos())
            nullForeArm.SetFrozenRot(nullForeArm.GetAbsRot())
            nullForeArmR.SetFrozenPos(nullForeArmR.GetAbsPos())
            nullForeArmR.SetFrozenRot(nullForeArmR.GetAbsRot())

            nullForeArm.SetRelPos(c4d.Vector(0, 0, 0))
            nullForeArm.SetRelRot(c4d.Vector(0, 0, 0))
            nullForeArmR.SetRelPos(c4d.Vector(0, 0, 0))
            nullForeArmR.SetRelRot(c4d.Vector(0, 0, 0))

    def findIK(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        ikfound = 0
        for obj in scene:
            if 'Foot_PlatformBase' in obj.GetName():
                ikfound = 1
        return ikfound

    def lockAllModels(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for obj in scene:
            if obj.GetType() == 5100:
                lockLayer = IkMaxUtils().layerSettings(obj, 1, 1)

    def limitFloorContact(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()

        def addProtTag(obj):
            xtag = c4d.BaseTag(c4d.Tprotection)
            xtag[c4d.PROTECTION_P] = 2
            xtag[c4d.PROTECTION_S] = False
            xtag[c4d.PROTECTION_R] = False
            xtag[c4d.PROTECTION_P_X] = False
            xtag[c4d.PROTECTION_P_Y] = True
            xtag[c4d.PROTECTION_P_Z] = False
            xtag[c4d.PROTECTION_P_MIN_Y] = 0
            xtag[c4d.PROTECTION_P_MAX_Y] = 1000000
            obj.InsertTag(xtag)

        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for obj in scene:
            if 'Foot_PlatformBase' in obj.GetName():
                addProtTag(obj)

        c4d.EventAdd()

    def matBumpFix(self):
        doc = c4d.documents.GetActiveDocument()
        docMaterials = doc.GetMaterials()
        for mat in docMaterials:
            try:
                mat[c4d.MATERIAL_BUMP_STRENGTH] = 0.2
            except:
                pass
            try:
                mat[c4d.MATERIAL_DISPLAY_USE_BUMP] = False
            except:
                pass
            try:
                mat[c4d.MATERIAL_PREVIEWSIZE] = 9
            except:
                pass

    def unparentObjsFromRig(self):
        doc = documents.GetActiveDocument()
        jointHip = doc.SearchObject('hip')
        if jointHip:
            dazRig = jointHip.GetUp()
            rigChildren = IkMaxUtils().iterateObjChilds(dazRig)
            for obj in rigChildren:
                if obj.GetUp() == dazRig:
                    if obj.GetType() == 5100:
                        geoDetected = True
                        obj.SetBit(c4d.BIT_ACTIVE)
                        c4d.CallCommand(12106, 12106)  # Cut
                        c4d.CallCommand(12108, 12108)  # Paste
                        c4d.CallCommand(12113, 12113)  # Deselect All
            c4d.EventAdd()

    def hideSomeJoints(self):
        doc = documents.GetActiveDocument()
        jointHip = doc.SearchObject('hip')
        jointHead = doc.SearchObject('head')
        if not jointHip:
            return 0
        dazRig = jointHip.GetUp()
        facialRig = jointHead.GetUp()
        rigJoints = IkMaxUtils().iterateObjChilds(jointHip)
        facialJoints = IkMaxUtils().iterateObjChilds(facialRig)
        for obj in rigJoints:
            obj()[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 0
            obj()[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 0
        jointHip()[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 0
        jointHip()[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 0
        for obj in facialJoints:
            obj()[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 1
            obj()[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 1
        dazRig()[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 1
        dazRig()[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 1

        c4d.EventAdd()

    def buttonsChangeState(self, btnState):
        c4d.StatusClear()
        c4d.EventAdd()
        c4d.EventAdd(c4d.EVENT_FORCEREDRAW)
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                      c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        c4d.DrawViews(c4d.EVMSG_CHANGEDSCRIPTMODE)
        c4d.EventAdd(c4d.EVENT_ANIMATE)
        c4d.StatusClear()
        if btnState == False:
            # Add the image to the button
            guiDazToC4dMainLogo.SetImage(guiDazToC4dMain().img_d2c4d_loading, False)
            try:
                guiDazToC4dMainLogo.LayoutChanged()
                guiDazToC4dMainLogo.Redraw()
            except:
                print("DazToC4D: LayoutChanged skip...")

            # guiDazToC4dMainImp.SetImage(guiDazToC4dMain().img_btnManualImportOff, False)  # Add the image to the button
            # Add the image to the button
            guiDazToC4dMainAutoImp.SetImage(
                guiDazToC4dMain().img_btn_auto_import_off, False)
            guiDazToC4dMainConvert.SetImage(guiDazToC4dMain(
            ).img_btn_convert_materials_off, False)  # Add the image to the button
            # Add the image to the button
            guiDazToC4dMainIK.SetImage(
                guiDazToC4dMain().img_btn_auto_ik_off, False)
            # guiDazToC4dMain().LayoutChanged(9353535)
        if btnState == True:
            # Add the image to the button
            guiDazToC4dMainLogo.SetImage(
                guiDazToC4dMain().img_d2c4d_logo, False)
            # guiDazToC4dMainImp.SetImage(guiDazToC4dMain().img_btnManualImport, False)  # Add the image to the button
            # Add the image to the button
            guiDazToC4dMainAutoImp.SetImage(
                guiDazToC4dMain().img_btn_auto_ik, False)
            guiDazToC4dMainConvert.SetImage(
                guiDazToC4dMain().img_btn_convert_materials, False)  # Add the image to the button
            # Add the image to the button
            guiDazToC4dMainIK.SetImage(guiDazToC4dMain().img_btn_auto_ik, False)
        # c4d.StatusClear()
        # c4d.EventAdd()
        # c4d.EventAdd(c4d.EVENT_FORCEREDRAW)
        # c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)
        # c4d.DrawViews()
        # c4d.EventAdd(c4d.EVENT_FORCEREDRAW)
        # c4d.DrawViews(c4d.DRAWFLAGS_FORCEFULLREDRAW)
        # doc = documents.GetActiveDocument()
        bc = c4d.BaseContainer()
        c4d.gui.GetInputState(c4d.BFM_INPUT_MOUSE, c4d.BFM_INPUT_CHANNEL, bc)

        return True

    def checkStdMats(self):
        doc = c4d.documents.GetActiveDocument()
        docMaterials = doc.GetMaterials()
        noStd = True
        for mat in docMaterials:
            matName = mat.GetName()
            if mat.GetType() == 5703:
                noStd = False
        if noStd == True:
            gui.MessageDialog(
                'No standard mats found. This scene was already converted')

        return noStd

    def getAllObjs(self):  # Return All OBJS from Scene! Works!
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()

        def GetAllChildren(topObj, childList):  # Get all objects down the hierarchy
            childList.extend(topObj.GetChildren())

            for each in topObj.GetChildren():
                if each.GetDown() != None:
                    GetAllChildren(each, childList)

            return childList

        objList = []
        while obj:
            allChildren = GetAllChildren(obj, [])
            if allChildren:
                for o in allChildren:
                    objList.append(o)
            objList.append(obj)
            obj = obj.GetNext()

        return objList
    
    #Not in Use
    def replaceMat(self, oldMat, newMat):
        doc = documents.GetActiveDocument()

        def tagsIterator(obj):
            doc = documents.GetActiveDocument()

            fTag = obj.GetFirstTag()
            if fTag:
                tagsList = []
                tagsList.append(fTag)
                tagNext = fTag.GetNext()
                while tagNext:
                    tagsList.append(tagNext)
                    tagNext = tagNext.GetNext()

                # Clean list in case of empty tags...
                caca = []
                for x in tagsList:
                    if len(x.GetName()) > 2:
                        caca.append(x)

                return caca

        # Script starts here:
        for o in self.getAllObjs():
            objTags = tagsIterator(o)
            if objTags:
                for t in objTags:
                    if t.GetType() == 5616:
                        if t[c4d.TEXTURETAG_MATERIAL] == oldMat:
                            t[c4d.TEXTURETAG_MATERIAL] = newMat

        c4d.EventAdd()
    #Not in Use
    def reduceSimilarMaterials(self):
        doc = c4d.documents.GetActiveDocument()

        # Process for all materials of scene
        docMaterials = doc.GetMaterials()

        def getMatTextures(mat):
            try:
                doc = c4d.documents.GetActiveDocument()
                matName = mat.GetName()
                matDiffuseText = ''
                matAlphaText = ''
                if mat[c4d.MATERIAL_COLOR_SHADER]:
                    matDiffuseText = mat[c4d.MATERIAL_COLOR_SHADER][c4d.BITMAPSHADER_FILENAME]

                if mat[c4d.MATERIAL_ALPHA_SHADER]:
                    matAlphaText = mat[c4d.MATERIAL_ALPHA_SHADER][c4d.BITMAPSHADER_FILENAME]

                return matDiffuseText, matAlphaText

            except:
                print('Skip reduce Mat...')

        def CompareMatTexts(sourceMat):
            docMaterials = doc.GetMaterials()

            textDifuse = getMatTextures(sourceMat)[0]
            textAlpha = getMatTextures(sourceMat)[1]
            similarMats = []
            for mat in docMaterials:
                if textDifuse == getMatTextures(mat)[0] and textAlpha == getMatTextures(mat)[1]:
                    if mat != sourceMat:
                        similarMats.append(mat)

            return similarMats

        skipMatList = ['Sclera', 'Cornea', 'EyeMoisture', 'Irises']
        dontRemoveList = ['Teeth', 'Mouth', 'Lips',
                          'Sclera', 'Cornea', 'EyeMoisture', 'Irises']

        nameSkin = ['Legs', 'Torso', 'Arms', 'Face', 'Fingernails', 'Toenails', 'Lips', 'EyeSocket', 'Ears',
                    'Feet', 'Nipples', 'Forearms', 'Hips', 'Neck', 'Shoulders', 'Hands', 'Head', 'Nostrils']

        doc = c4d.documents.GetActiveDocument()
        docMaterials = doc.GetMaterials()

        for mat in docMaterials:
            try:
                if mat.GetName() not in skipMatList:
                    print(mat.GetName())
                    if getMatTextures(mat)[0] or getMatTextures(mat)[1]:
                        similarMats = CompareMatTexts(mat)
                        if similarMats:
                            for obj in similarMats:
                                objName = obj.GetName()
                                removeit = True
                                for x in dontRemoveList:
                                    if objName in x:
                                        removeit = False
                                        # gui.MessageDialog('DONT Remove: ' + objName, c4d.GEMB_OK)

                                if removeit == True:
                                    # gui.MessageDialog('Remove: ' + objName, c4d.GEMB_OK)

                                    # self.replaceMat(obj, mat)
                                    # obj.Remove()
                                    c4d.EventAdd()
                                # if objName not in dontRemoveList:
                                #     self.replaceMat(obj, mat)
                                #     obj.Remove()
                                #     c4d.EventAdd()
                                skipMatList.append(obj.GetName())
            except:
                print('Skip reduce Mat...')

        # Rename mats based on the texture filename...
        for mat in docMaterials:
            if mat.GetName() not in dontRemoveList:
                if getMatTextures(mat) != None:
                    texDiffuse = getMatTextures(mat)[0]
                    if texDiffuse:
                        head, tail = os.path.split(getMatTextures(mat)[0])
                        newName = tail.split('.')[0]
                        if mat.GetName() in nameSkin:
                            mat.SetName('Skin_' + newName)
                        else:
                            mat.SetName(newName)

        c4d.EventAdd()
    #Not in Use
    

    def protectIKMControls(self):
        doc = documents.GetActiveDocument()

        def protectTag(jointName, protectPreset):
            doc = documents.GetActiveDocument()
            obj = doc.SearchObject(jointName)
            tagProtec = c4d.BaseTag(5629)  # Protection Tag

            if protectPreset == "finger":
                if obj:
                    obj[c4d.ID_BASEOBJECT_ROTATION_ORDER] = 6
                tagProtec[c4d.PROTECTION_P_X] = False
                tagProtec[c4d.PROTECTION_P_Y] = False
                tagProtec[c4d.PROTECTION_P_Z] = False
                tagProtec[c4d.PROTECTION_S_X] = False
                tagProtec[c4d.PROTECTION_S_Y] = False
                tagProtec[c4d.PROTECTION_S_Z] = False
                tagProtec[c4d.PROTECTION_R_X] = True
                tagProtec[c4d.PROTECTION_R_Y] = False
                tagProtec[c4d.PROTECTION_R_Z] = True
            if protectPreset == "position":
                tagProtec[c4d.PROTECTION_P_X] = True
                tagProtec[c4d.PROTECTION_P_Y] = True
                tagProtec[c4d.PROTECTION_P_Z] = True
                tagProtec[c4d.PROTECTION_S_X] = False
                tagProtec[c4d.PROTECTION_S_Y] = False
                tagProtec[c4d.PROTECTION_S_Z] = False
                tagProtec[c4d.PROTECTION_R_X] = False
                tagProtec[c4d.PROTECTION_R_Y] = False
                tagProtec[c4d.PROTECTION_R_Z] = False
            if protectPreset == "twist":
                tagProtec[c4d.PROTECTION_P_X] = True
                tagProtec[c4d.PROTECTION_P_Y] = True
                tagProtec[c4d.PROTECTION_P_Z] = True
                tagProtec[c4d.PROTECTION_S_X] = False
                tagProtec[c4d.PROTECTION_S_Y] = False
                tagProtec[c4d.PROTECTION_S_Z] = False
                tagProtec[c4d.PROTECTION_R_X] = True
                tagProtec[c4d.PROTECTION_R_Y] = False
                tagProtec[c4d.PROTECTION_R_Z] = True
            if obj:
                obj.InsertTag(tagProtec)
                c4d.EventAdd()

        # daz_name = 'Genesis2Male_'  # TEMMPAAAAAAAAAAAAAAAAAAAA
        # LEFT
        protectTag(daz_name + 'jMiddle2', 'finger')
        protectTag(daz_name + 'jMiddle3', 'finger')
        protectTag(daz_name + 'jMiddle4', 'finger')
        protectTag(daz_name + 'jRing2', 'finger')
        protectTag(daz_name + 'jRing3', 'finger')
        protectTag(daz_name + 'jRing4', 'finger')
        protectTag(daz_name + 'jPink2', 'finger')
        protectTag(daz_name + 'jPink3', 'finger')
        protectTag(daz_name + 'jPink4', 'finger')
        protectTag(daz_name + 'jIndex2', 'finger')
        protectTag(daz_name + 'jIndex3', 'finger')
        protectTag(daz_name + 'jIndex4', 'finger')
        # RIGHT
        protectTag(daz_name + 'jMiddle2___R', 'finger')
        protectTag(daz_name + 'jMiddle3___R', 'finger')
        protectTag(daz_name + 'jMiddle4___R', 'finger')
        protectTag(daz_name + 'jRing2___R', 'finger')
        protectTag(daz_name + 'jRing3___R', 'finger')
        protectTag(daz_name + 'jRing4___R', 'finger')
        protectTag(daz_name + 'jPink2___R', 'finger')
        protectTag(daz_name + 'jPink3___R', 'finger')
        protectTag(daz_name + 'jPink4___R', 'finger')
        protectTag(daz_name + 'jIndex2___R', 'finger')
        protectTag(daz_name + 'jIndex3___R', 'finger')
        protectTag(daz_name + 'jIndex4___R', 'finger')

        # MIDDLE
        protectTag(daz_name + 'Spine_ctrl', 'position')
        protectTag(daz_name + 'Chest_ctrl', 'position')
        protectTag(daz_name + 'Neck_ctrl', 'position')
        protectTag(daz_name + 'Head_ctrl', 'position')

        # protectTag(daz_name + 'ForearmTwist_ctrl', 'twist')
        # protectTag(daz_name + 'ForearmTwist_ctrl___R', 'twist')

    

    def unhideProps(self):
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject('hip')
        ObjectIterator(obj)
        for o in ObjectIterator(obj):
            if o.GetType() == 5100 or o.GetType() == 5140:
                o[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 0
                o[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 0
        c4d.EventAdd()

    def fixGenEyes(self):
        dir, file = os.path.split(__file__)  # Gets the plugin's directory
        # Adds the res folder to the path
        folder_DazToC4D_res = os.path.join(dir, 'res')
        # Adds the res folder to the path
        folder_DazToC4D_xtra = os.path.join(folder_DazToC4D_res, 'xtra')
        file_G3_IrisFixMap = os.path.join(
            folder_DazToC4D_xtra, 'G3_Iris_Alpha.psd')

        destination_G3_IrisFixMap = r'C:\TEMP3D\G3_Iris_Alpha.psd'
        destination_G3_IrisFixMapMac = '/users/Shared/temp3d/G3_Iris_Alpha.psd'

        # If detects map in Mac, use the Mac one...
        if os.path.exists(destination_G3_IrisFixMapMac):
            destination_G3_IrisFixMap = destination_G3_IrisFixMapMac

        try:
            copyfile(file_G3_IrisFixMap, destination_G3_IrisFixMap)
        except:
            print('Iris Map transfer...Skipped.')

        # For Mac Missing...

        # gui.MessageDialog(file_G3_IrisFixMap, c4d.GEMB_OK)

        doc = c4d.documents.GetActiveDocument()
        docMaterials = doc.GetMaterials()
        for mat in docMaterials:
            if 'Iris' in mat.GetName():
                matDiffuseMap = ''
                try:
                    matDiffuseMap = mat[c4d.MATERIAL_COLOR_SHADER][c4d.BITMAPSHADER_FILENAME]
                except:
                    pass
                skipThis = False
                if '3duG3FTG2_Eyes' in matDiffuseMap:
                    skipThis = True

                if skipThis == False and os.path.exists(destination_G3_IrisFixMap):
                    mat[c4d.MATERIAL_USE_ALPHA] = True
                    shda = c4d.BaseList2D(c4d.Xbitmap)
                    shda[c4d.BITMAPSHADER_FILENAME] = destination_G3_IrisFixMap
                    mat[c4d.MATERIAL_ALPHA_SHADER] = shda
                    mat.InsertShader(shda)

    def dazManualRotationFixTpose(self):

        # return False #Quit TEMPORAL
        doc = documents.GetActiveDocument()

        def setRotAndMirror(jointName, x, y, z):
            joint = doc.SearchObject(jointName)
            if x != 0.0:
                joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = x
            if y != 0.0:
                joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = y
            if z != 0.0:
                joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = z

        dazType = ''
        if doc.SearchObject('lShldrBend'):
            if doc.SearchObject('lMetatarsals'):
                if doc.SearchObject('rThighTwist'):
                    obj1PosY = ''
                    obj1PosY = ''
                    obj1PosY = doc.SearchObject('lShldrBend').GetMg().off[1]
                    obj2PosY = doc.SearchObject('lForearmBend').GetMg().off[1]
                    distValue = obj1PosY - obj2PosY
                    if distValue < 2.9:
                        dazType = 'Genesis3'  # TODO !!
                    else:
                        dazType = 'Genesis8'

        if doc.SearchObject('lThigh'):
            if doc.SearchObject('lShin'):
                if doc.SearchObject('abdomen2'):
                    dazType = 'Genesis2'
        # dazType = 'Genesis2'
        #gui.MessageDialog(dazType, c4d.GEMB_OK)
        if dazType == 'Genesis8':
            # GENESIS 8 --------------------------------------------
            # Genesis 8 LEFT Side:
            autoAlignArms()
            # setRotAndMirror('lShldrBend', 0.014, 0.034, -0.807)
            # setRotAndMirror('lForearmBend', 0.175, 0.175, 0.0)
            # setRotAndMirror('lHand', -0.142, -0.117, -0.086)

            # Genesis 8 RIGHT Side:
            # setRotAndMirror('rShldrBend', -0.014, 0.034, 0.807)
            # setRotAndMirror('rForearmBend', -0.175, 0.175, 0.0)
            # setRotAndMirror('rHand', 0.142, -0.117, 0.086)

        if dazType == 'Genesis3':
            self.fixGenEyes()  # Apply IRIS alpha fix
            # GENESIS 3 -ZOMBIE WORKS TOO -------------------------------------------
            autoAlignArms()
            # Genesis 3 LEFT Side:
            # setRotAndMirror('lShldrBend', 0.031, 0.0, 0.018)
            # setRotAndMirror('lForearmBend', 0.22, 0.003, 0.014)
            # setRotAndMirror('lHand', -0.165, 0.0, 0.0)

            # Genesis 3 RIGHT Side:
            # setRotAndMirror('rShldrBend', -0.031, 0.0, -0.018)
            # setRotAndMirror('rForearmBend', -0.22, 0.003, -0.014)
            # setRotAndMirror('rHand', 0.165, 0.0, 0.0)

        if dazType == 'Genesis2':
            # GENESIS 2 --------------------------------------------
            # Genesis 2 LEFT Side:
            setRotAndMirror('lShldr', 0.089, 0.0, -0.019)
            setRotAndMirror('lForeArm', 0.334, 0.0, 0.0)
            setRotAndMirror('lHand', 0.083, 0.222, -0.121)
            setRotAndMirror('lThigh', 0.0, 0.0, 0.0)
            # setRotAndMirror('lFoot', -0.23, 0.0, 0.0)

            # Genesis 2 RIGHT Side:
            setRotAndMirror('rShldr', -0.089, 0.0, 0.019)
            setRotAndMirror('rForeArm', -0.334, 0.0, 0.0)
            setRotAndMirror('rHand', -0.083, 0.222, 0.121)
            setRotAndMirror('rThigh', 0.0, 0.0, 0.0)
            # setRotAndMirror('rFoot', 0.23, 0.0, 0.0)
        c4d.EventAdd()
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                      c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        c4d.EventAdd()

    def fixDaz8rot(self, master, mode='', jointToFix='', rotValue=0):
        doc = documents.GetActiveDocument()

        nullObj = c4d.BaseObject(c4d.Onull)  # Create new cube
        doc.InsertObject(nullObj)
        armJoint = doc.SearchObject('lShldrBend')
        handJoint = doc.SearchObject('lForearmBend')

        mg = jointToFix.GetMg()
        nullObj.SetMg(mg)

        nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0
        nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0
        nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0
        c4d.EventAdd()

        slaveObj = nullObj
        masterObj = master

        def addConstraint(slaveObj, masterObj, mode='Parent'):
            if mode == "Parent":
                constraintTAG = c4d.BaseTag(1019364)

                constraintTAG[c4d.EXPRESSION_ENABLE] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR_MAINTAIN] = True
                # constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PARENT_FROZEN] = False
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
                constraintTAG[10005] = True
                constraintTAG[10007] = True
                constraintTAG[10001] = masterObj

                PriorityDataInitial = c4d.PriorityData()
                PriorityDataInitial.SetPriorityValue(
                    c4d.PRIORITYVALUE_MODE, c4d.CYCLE_EXPRESSION)
                PriorityDataInitial.SetPriorityValue(
                    c4d.PRIORITYVALUE_PRIORITY, 0)
                PriorityDataInitial.SetPriorityValue(
                    c4d.PRIORITYVALUE_CAMERADEPENDENT, 0)
                constraintTAG[c4d.EXPRESSION_PRIORITY] = PriorityDataInitial
            slaveObj.InsertTag(constraintTAG)

        mg = slaveObj.GetMg()
        constraintTAG = c4d.BaseTag(1019364)

        if mode == "ROTATION":
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
            constraintTAG[10005] = False
            constraintTAG[10006] = False
            constraintTAG[10001] = masterObj
        if mode == "AIM":
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM] = True
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_MAINTAIN] = False

            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_X] = True
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_Y] = True
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_Z] = True
            constraintTAG[20004] = 0  # Axis X-
            constraintTAG[20001] = masterObj

        slaveObj.InsertTag(constraintTAG)
        # constraintTAG.Remove()

        c4d.EventAdd()
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        constraintTAG.Remove()

        addConstraint(jointToFix, slaveObj)

        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)

        rotZ = nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z]
        # dialogMsg = str(nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
        # gui.MessageDialog(dialogMsg, c4d.GEMB_OK)
        if rotZ > 0.8:
            slaveObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0
            slaveObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0
            slaveObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = rotValue

        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                      c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)

        caca = jointToFix.GetFirstTag()
        caca.Remove()
        slaveObj.Remove()

    def dazGen8fix(self):
        doc = documents.GetActiveDocument()

        mainJoint = doc.SearchObject('lShldrBend')
        goalJoint = doc.SearchObject('lForearmBend')
        if mainJoint:
            self.fixDaz8rot(goalJoint, 'AIM', mainJoint)

            jointOposite = doc.SearchObject('rShldrBend')
            rx = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X]
            ry = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y]
            rz = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z]

            jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION,
                         c4d.VECTOR_X] = rx * -1
            jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = ry
            jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION,
                         c4d.VECTOR_Z] = rz * -1

        # mainJoint = doc.SearchObject('lThighBend')
        # goalJoint = doc.SearchObject('lFoot')
        # rotValue = 1.571
        # fixDaz8rot(goalJoint, 'AIM', mainJoint, rotValue)

        # mainJoint = doc.SearchObject('rThighBend')
        # goalJoint = doc.SearchObject('rFoot')
        # rotValue = 1.571
        # fixDaz8rot(goalJoint, 'AIM', mainJoint, rotValue)

    def importDazFbx(self, filePath):

        file = c4d.documents.LoadDocument(
            filePath, c4d.SCENEFILTER_OBJECTS | c4d.SCENEFILTER_MATERIALS | c4d.SCENEFILTER_MERGESCENE)
        c4d.documents.InsertBaseDocument(file)

    def transpMapFix(self, mat):
        if mat[c4d.MATERIAL_TRANSPARENCY_SHADER] != None:
            mat[c4d.MATERIAL_ALPHA_SHADER] = mat[c4d.MATERIAL_TRANSPARENCY_SHADER]
            mat[c4d.MATERIAL_USE_TRANSPARENCY] = 0
            mat[c4d.MATERIAL_USE_ALPHA] = 1
            mat[c4d.MATERIAL_TRANSPARENCY_SHADER] = None

    def matSetSpec(self, setting, value):
        doc = c4d.documents.GetActiveDocument()

        # Process for all materials of scene
        docMaterials = doc.GetMaterials()
        for mat in docMaterials:
            matName = mat.GetName()
            skinMats = ['MainSkin', 'Legs', 'Torso', 'Arms', 'Face', 'Fingernails', 'Toenails', 'EyeSocket', 'Ears',
                        'Feet', 'Nipples', 'Forearms', 'Hips', 'Neck', 'Shoulders', 'Hands', 'Head', 'Nostrils']
            # if matName in skinMats or 'Skin_' in matName or matname + '_RS' in skinMats:
            #     print('MatType : ',mat.GetType())
            for x in skinMats:
                if x in matName:
                    if mat.GetType() == 1038954:  # Vray
                        if setting == 'Rough':
                            mat[c4d.VRAYSTDMATERIAL_REFLECTGLOSSINESS] = 1.0 - value/100
                        if setting == 'Weight':
                            colorValue = value / 100
                            mat[c4d.VRAYSTDMATERIAL_REFLECTCOLOR] = c4d.Vector(
                                colorValue, colorValue, colorValue)

                    if mat.GetType() == 5703:  # Standard
                        layer = mat.GetReflectionLayerIndex(0)
                        if setting == 'Rough':
                            mat[layer.GetDataID(
                            ) + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS] = value/100
                        if setting == 'Weight':
                            mat[layer.GetDataID(
                            ) + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = value/100
                    if mat.GetType() == 1029501:  # Octane
                        if setting == 'Weight':
                            mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = value/100
                        if setting == 'Rough':
                            mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = value/100
                    if mat.GetType() == 1036224:  # Redshift
                        gvNodeMaster = redshift.GetRSMaterialNodeMaster(mat)
                        rootNode_ShaderGraph = gvNodeMaster.GetRoot()
                        output = rootNode_ShaderGraph.GetDown()
                        RShader = output.GetNext()
                        gvNodeMaster = redshift.GetRSMaterialNodeMaster(mat)
                        nodeRoot = gvNodeMaster.GetRoot()
                        rsMaterial = nodeRoot.GetDown().GetNext()
                        if setting == 'Weight':
                            rsMaterial[c4d.REDSHIFT_SHADER_MATERIAL_REFL_WEIGHT] = value/100
                            rsMaterial[c4d.REDSHIFT_SHADER_MATERIAL_REFL_IOR] = value/10
                        if setting == 'Rough':
                            rsMaterial[c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS] = value/100

    def fixMaterials(self):

        doc = c4d.documents.GetActiveDocument()

        # Process for all materials of scene
        docMaterials = doc.GetMaterials()
        for mat in docMaterials:
            self.transpMapFix(mat)
            matName = mat.GetName()
            eyesMats = ['Eyelashes', 'Cornea', 'EyeMoisture',
                        'EyeMoisture2', 'Sclera', 'Irises']
            layer = mat.GetReflectionLayerIndex(0)

            mat[c4d.MATERIAL_NORMAL_STRENGTH] = 0.25
            mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.05
            try:  # Remove extra layers stuff...
                mat.RemoveReflectionLayerIndex(1)
                mat.RemoveReflectionLayerIndex(2)
                mat.RemoveReflectionLayerIndex(3)
                mat.RemoveReflectionLayerIndex(4)
            except:
                pass

            if matName in eyesMats:
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS] = 0.13
            # if 'Cornea' in matName:
            #     print('CORNEA...')
            #     print(matName)
            #     colorTest = c4d.Vector(int(0), int(0), int(0))
            #     mat[c4d.MATERIAL_COLOR_SHADER] = None
            #     mat[c4d.MATERIAL_USE_ALPHA] = False
            #     mat[c4d.MATERIAL_ALPHA_SHADER] = None
            #     mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION] = 0 #0 = Reflection(legacy)
            #     mat[c4d.MATERIAL_COLOR_COLOR] = colorTest
            #     mat[c4d.MATERIAL_USE_TRANSPARENCY] = True
            #     mat[c4d.MATERIAL_TRANSPARENCY_FRESNEL] = False
            #     mat[c4d.MATERIAL_TRANSPARENCY_EXITREFLECTIONS] = False
            #     mat[c4d.MATERIAL_TRANSPARENCY_COLOR] = c4d.Vector(0.95, 0.95, 0.95)
            #     mat[c4d.MATERIAL_TRANSPARENCY_REFRACTION]=0.33
            #     mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS] = 0.0
            #     mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_REFLECTION] = 0.7
            #     mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.0
            #     mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_BUMP] = 0.0
            if 'Moisture' in matName or 'Cornea' in matName or 'Tear' in matName or 'EyeReflection' in matName:
                # mat[c4d.MATERIAL_BUMP_STRENGTH]=0.01 #To make it diferent than Co..
                mat[c4d.MATERIAL_COLOR_COLOR] = c4d.Vector(0.2, 0.2, 0.2)
                mat[c4d.MATERIAL_USE_TRANSPARENCY] = True
                mat[c4d.MATERIAL_TRANSPARENCY_COLOR] = c4d.Vector(
                    0.9, 0.9, 0.9)
                mat[c4d.MATERIAL_TRANSPARENCY_REFRACTION] = 1.0
                # 0 = Reflection(legacy)
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION] = 0
                mat[c4d.MATERIAL_USE_TRANSPARENCY] = True
                mat[c4d.MATERIAL_TRANSPARENCY_FRESNEL] = False
                mat[c4d.MATERIAL_TRANSPARENCY_EXITREFLECTIONS] = False
                mat[c4d.MATERIAL_TRANSPARENCY_COLOR] = c4d.Vector(
                    0.95, 0.95, 0.95)
                mat[c4d.MATERIAL_TRANSPARENCY_REFRACTION] = 1.33

                mat[layer.GetDataID(
                ) + c4d.REFLECTION_LAYER_COLOR_COLOR] = c4d.Vector(1.0, 1.0, 1.0)
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS] = 0.0
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_REFLECTION] = 0.7
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.0
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_BUMP] = 0.0
            if 'Eyes' in matName:
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.0
            if 'Pupils' in matName:
                mat[c4d.MATERIAL_USE_REFLECTION] = False
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.0
            if 'Teeth' in matName:
                # 0 = Reflection(legacy)
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION] = 0
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS] = 0.07
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_REFLECTION] = 0.09
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.03
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_BUMP] = 0.25
            if 'Mouth' in matName:
                # 0 = Reflection(legacy)
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION] = 0
            if 'Sclera' in matName:
                mat[c4d.MATERIAL_USE_REFLECTION] = False
                mat[c4d.MATERIAL_GLOBALILLUM_RECEIVE_STRENGTH] = 2
                # mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION] = 0 #0 = Reflection(legacy)
                # mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS] = 0.10
                # mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_REFLECTION] = 0.10
                # mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.10
                # mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_BUMP] = 0.5
            if 'Iris' in matName:
                mat[c4d.MATERIAL_USE_REFLECTION] = False
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_REFLECTION] = 0.0
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.0
                # 0 = Reflection(legacy)
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION] = 0
            if 'Eyelash' in matName:
                mat[c4d.MATERIAL_COLOR_SHADER] = None
                mat[c4d.MATERIAL_COLOR_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                try:
                    mat[c4d.MATERIAL_ALPHA_SHADER][c4d.BITMAPSHADER_FILENAME][c4d.BITMAPSHADER_EXPOSURE] = 1.0
                except:
                    print('Exposure Skipped...')

            # mainLayerId = 526336
            # mat[mainLayerId + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION] = c4d.REFLECTION_DISTRIBUTION_GGX
            # mat[mainLayerId + c4d.REFLECTION_LAYER_MAIN_ROUGHNESSREAL] = 0 # sets attenuation to average

        c4d.CallCommand(12253, 12253)  # Render All Materials

        c4d.EventAdd()

    def autoImportDazJustImport(self):
        self.buttonsChangeState(False)

        doc = documents.GetActiveDocument()
        filePath = ''
        filePathPC = 'C:\TEMP3D\DazToC4D.fbx'
        filePathMac = '/users/Shared/temp3d/DazToC4D.fbx'

        if os.path.exists(filePathMac):
            filePath = filePathMac
        else:
            filePath = filePathPC

        if os.path.exists(filePath) == False:
            gui.MessageDialog(
                'Nothing to import.\nYou have to export from DAZ Studio first',
                c4d.GEMB_OK)
            self.buttonsChangeState(True)
            return 0

        self.importDazFbx(filePath)
        # doc = documents.GetActiveDocument()
        #
        # self.fixMaterials()
        #
        # obj = doc.SearchObject('hip')
        # if obj: #Morphs Fixes...
        #     DazToC4D().cleanMorphsGeoRemove()
        #     dazMorphsFix()

        DazToC4DUtils().readExtraMapsFromFile()  # Extra Maps from File...

        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                      c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        c4d.CallCommand(300001026, 300001026)  # Deselect All
        c4d.CallCommand(12168, 12168)  # Remove Unused Materials
        c4d.CallCommand(12113, 12113)  # Deselect All

        screen = c4d.gui.GeGetScreenDimensions(0, 0, True)

        # DazToC4D().unparentObjsFromRig()
        # DazToC4D().hideSomeJoints()
        # DazToC4D().matBumpFix()

        c4d.EventAdd()
        c4d.CallCommand(12148)  # Frame Geometry
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                      c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)

        c4d.CallCommand(300001026, 300001026)  # Deselect All
        c4d.CallCommand(12168, 12168)  # Remove Unused Materials

        DazToC4D().eyeLashAndOtherFixes()
        c4d.EventAdd()
        c4d.EventAdd()

        print('Import Done')
        if dazReduceSimilar == True:
            c4d.CallCommand(12211, 12211)  # Remove Duplicate Materials
            DazToC4D().reduceMatFix()
            DazToC4D().removeDisp()

        DazToC4DUtils().readExtraMapsFromFile()  # Extra Maps from File...

        DazToC4D().addLipsMaterial()  # Add Lips Material
        dazObj = DazToC4DUtils().getDazMesh()

        DazToC4D().morphsFixRemoveAndRename()
        xpressoTag = connectEyeLashesMorphXpresso()
        # morphsGroup = DazToC4D().moveMorphsToGroup(dazObj)
        # DazToC4D().xpressoTagToMorphsGroup(morphsGroup)
        # DazToC4D().morphTagsToGroups()

        c4d.EventAdd()
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                      c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        c4d.EventAdd()
        c4d.CallCommand(300001026, 300001026)  # Deselect All
        c4d.CallCommand(12168, 12168)  # Remove Unused Materials

        DazToC4D().stdMatExtrafixes()
        DazToC4D().specificFiguresFixes()
        self.fixMaterials()

        isPosed = DazToC4D().checkIfPosed()
        if isPosed == False:
            DazToC4D().preAutoIK()  # Only if T pose detected...

        c4d.EventAdd()
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                      c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        c4d.EventAdd()

        self.buttonsChangeState(True)

        self.dialog = guiASKtoSave()
        self.dialog.Open(dlgtype=c4d.DLG_TYPE_MODAL,
                         xpos=screen['sx2']//2-210, ypos=screen['sy2']//2-100, defaultw=200, defaulth=150)

    def checkIfPosed(self):
        doc = documents.GetActiveDocument()

        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        jointsList = ['Collar', 'head', 'ShldrTwist',
                      'Forearm', 'pelvis', 'abdomen', 'Shldr']
        caca = False

        def checkJoint(jointName):
            joint = doc.SearchObject(jointName)
            if joint:
                rotRX = abs(
                    joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                rotRY = abs(
                    joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                rotRZ = abs(
                    joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
                # print(rotRX)
                # print(rotRY)
                # print(rotRZ)
                if rotRX == rotRY == rotRZ == 0.0:
                    return False
                else:
                    return True

        def compareJoints(jointName):
            jointR = doc.SearchObject('r' + jointName)
            jointL = doc.SearchObject('l' + jointName)
            if jointR:
                rotRX = abs(
                    jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                rotRY = abs(
                    jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                rotRZ = abs(
                    jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
                rotLX = abs(
                    jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                rotLY = abs(
                    jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                rotLZ = abs(
                    jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
                rotRX = round(rotRX, 2)
                rotRY = round(rotRY, 2)
                rotRZ = round(rotRZ, 2)
                rotLX = round(rotLX, 2)
                rotLY = round(rotLY, 2)
                rotLZ = round(rotLZ, 2)
                # print(rotRX, rotLX)
                # print(rotRY, rotLY)
                # print(rotRZ, rotLZ)
                if rotRX == rotLX and rotRY == rotLY and rotRZ == rotLZ:
                    return False
                else:
                    return True

        isPosed = False

        if compareJoints('ForeArm'):
            isPosed = True
        if compareJoints('Shldr'):
            isPosed = True
        if compareJoints('ShldrBend'):
            isPosed = True
        if compareJoints('ForearmBend'):
            isPosed = True
        if compareJoints('Hand'):
            isPosed = True
        if compareJoints('ThighBend'):
            isPosed = True
        if checkJoint('chestUpper'):
            isPosed = True
        if checkJoint('chestLower'):
            isPosed = True
        if checkJoint('abdomenLower'):
            isPosed = True
        if checkJoint('abdomenUpper'):
            isPosed = True
        if checkJoint('neckLower'):
            isPosed = True

        return isPosed

    def autoImportDaz(self):

        screen = c4d.gui.GeGetScreenDimensions(0, 0, True)
        # self.dialog = guiPleaseWaitAUTO()
        # self.dialog.Open(dlgtype=c4d.DLG_TYPE_ASYNC, pluginid=103299851, xpos=-2, ypos=-2, defaultw=280, defaulth=50)

        self.buttonsChangeState(False)

        # guiDazToC4dMainLogo.SetImage(guiDazToC4dMain().img_loading, False)  # Add the image to the button
        # guiDazToC4dMainImp.SetImage(guiDazToC4dMain().img_btnManualImportOff, False)  # Add the image to the button
        # guiDazToC4dMainAutoImp.SetImage(guiDazToC4dMain().img_btnAutoImportOff, False)  # Add the image to the button
        # guiDazToC4dMainConvert.SetImage(guiDazToC4dMain().img_btnConvertMaterialsOff, False)  # Add the image to the button
        # guiDazToC4dMainIK.SetImage(guiDazToC4dMain().img_btnAutoIKOff, False)  # Add the image to the button

        doc = documents.GetActiveDocument()
        filePath = ''
        filePathPC = 'C:\TEMP3D\DazToC4D.fbx'
        filePathMac = '/users/Shared/temp3d/DazToC4D.fbx'

        if os.path.exists(filePathMac):
            filePath = filePathMac
        else:
            filePath = filePathPC

        if os.path.exists(filePath) == False:
            gui.MessageDialog(
                'Be sure to export first from DAZ Studio',
                c4d.GEMB_OK)
            return 0

        self.importDazFbx(filePath)
        doc = documents.GetActiveDocument()

        # if dazReduceSimilar == True:
        #     DazToC4D().reduceSimilarMaterials()

        self.fixMaterials()

        # DazToC4DUtils().fixMoisure() #TESTING DISABLE.. ENABLE AGAIN!..

        # ----------- AUTO IK ---------------------------------------
        print('***************************************')
        obj = doc.SearchObject('hip')
        if obj:
            # DazToC4DUtils().sceneToZero()
            # AllSceneToZero().sceneToZero()
            # DazToC4D().dazManualRotationFixTpose()
            # DazToC4D().dazGen8fix()
            if doc.SearchObject('lThighTwist') != True:
                print('***************************************')

                if DazToC4D().checkIfPosedResetPose(False) == False:
                    gui.MessageDialog('AAA')
                    forceTpose().dazFix_All_To_T_Pose()
                    # DazToC4DUtils().sceneToZero()
                    # AllSceneToZero().sceneToZero()
                DazToC4D().cleanMorphsGeoRemove()
                dazMorphsFix()
        #
        #     # DazToC4DUtils().dazFootRotfix() #Foot rotations to Zero Straight Look...
        #
        #     guiDazToC4dMain().applyDazIK()
        #
        #     DazToC4DUtils().ikGoalsZeroRot()
        #     DazToC4DUtils().changeSkinType()
        #     DazToC4D().unhideProps()
        #
        #     c4d.EventAdd()
        #     c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)
        #
        #     #DONE-AUTOIMPORT
        #

        #     DazToC4D().protectIKMControls()
            # ----------- AUTO IK - END --------------------------------------

        DazToC4DUtils().readExtraMapsFromFile()  # Extra Maps from File...

        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                      c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        c4d.CallCommand(300001026, 300001026)  # Deselect All
        c4d.CallCommand(12168, 12168)  # Remove Unused Materials
        c4d.CallCommand(12113, 12113)  # Deselect All

        screen = c4d.gui.GeGetScreenDimensions(0, 0, True)
        obj = doc.SearchObject('hip')
        if obj:
            if DazToC4D().checkIfPosedResetPose(False) == False:

                DazToC4D().dazManualRotationFixTpose()
                # DazToC4DUtils().sceneToZero()
                # AllSceneToZero().sceneToZero()
        DazToC4D().unparentObjsFromRig()
        DazToC4D().hideSomeJoints()
        DazToC4D().matBumpFix()

        c4d.EventAdd()
        c4d.CallCommand(12148)  # Frame Geometry
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                      c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)

        c4d.CallCommand(300001026, 300001026)  # Deselect All
        c4d.CallCommand(12168, 12168)  # Remove Unused Materials

        DazToC4D().eyeLashAndOtherFixes()
        c4d.EventAdd()
        c4d.EventAdd()

        print('--- Import Done ---')
        if dazReduceSimilar == True:
            c4d.CallCommand(12211, 12211)  # Remove Duplicate Materials
            DazToC4D().reduceMatFix()
            DazToC4D().removeDisp()

        DazToC4dUtils().read_extra_maps_from_file()  # Extra Maps from File...

        DazToC4D().addLipsMaterial()  # Add Lips Material
        dazObj = DazToC4dUtils().get_daz_mesh()

        DazToC4D().morphsFixRemoveAndRename()
        xpressoTag = connectEyeLashesMorphXpresso()
        morphsGroup = DazToC4D().moveMorphsToGroup(dazObj)
        DazToC4D().xpressoTagToMorphsGroup(morphsGroup)
        DazToC4D().morphTagsToGroups()
        # morphsGroup.InsertTag(xpressoTag)
        c4d.EventAdd()
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                      c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        c4d.EventAdd()
        c4d.CallCommand(300001026, 300001026)  # Deselect All
        c4d.CallCommand(12168, 12168)  # Remove Unused Materials
        # c4d.CallCommand(12211, 12211)  # Remove Duplicate Materials

        DazToC4D().stdMatExtrafixes()

        c4d.EventAdd()
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                      c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        c4d.EventAdd()
        # if doc.SearchObject('hip'):
        #     AllSceneToZero().sceneToZero()
        #     pass
        self.buttonsChangeState(True)

        self.dialog = guiASKtoSave()
        self.dialog.Open(dlgtype=c4d.DLG_TYPE_MODAL,
                         xpos=screen['sx2']/2-210, ypos=screen['sy2']/2-100, defaultw=200, defaulth=150)
        # AllSceneToZero().sceneToZero()

    def preAutoIK(self):

        doc = documents.GetActiveDocument()
        obj = doc.SearchObject('hip')
        if obj:
            doc = documents.GetActiveDocument()
            if doc.SearchObject('lThighTwist') != True:
                if DazToC4D().checkIfPosedResetPose(False) == False:
                    forceTpose().dazFix_All_To_T_Pose()
            if doc.SearchObject('lThighTwist'):
                if DazToC4D().checkIfPosedResetPose(False) == False:
                    DazToC4D().dazManualRotationFixTpose()
        #
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                      c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        #
        # obj = doc.SearchObject('hip')
        # if obj:
        #     if DazToC4D().checkIfPosedResetPose(False) == False:
        #         DazToC4D().dazManualRotationFixTpose()

        c4d.EventAdd()

    def autoIK(self):
        self.buttonsChangeState(False)
        # DazToC4D().preAutoIK() #DO PRE AUTO IK STUFF!
        doc = c4d.documents.GetActiveDocument()
        DazToC4D().morphsGroupMoveUp()

        obj = doc.SearchObject('hip')
        if obj:
            AllSceneToZero().sceneToZero()

            guiDazToC4dMain().applyDazIK()

            # DazToC4DUtils().ikGoalsZeroRot()

            DazToC4DUtils().changeSkinType()
            DazToC4D().unhideProps()

            c4d.EventAdd()
            c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                          c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)

            # DONE-AUTOIMPORT

            DazToC4D().cleanMorphsGeoRemove()
            dazMorphsFix()
            DazToC4D().protectIKMControls()

        DazToC4D().limitFloorContact()
        DazToC4D().lockAllModels()
        DazToC4D().freezeTwistBones()
        # DazToC4D().limitTwistPosition()
        # DazToC4D().dazEyesLookAtControls()
        DazToC4D().figureFixBrute()

        DazToC4DUtils().protectTwist()

        self.buttonsChangeState(True)
        c4d.CallCommand(12168, 12168)  # Delete Unused Materials
        # quit()  # -------------------------------------------------

        print('Done')

    def manualImportDaz(self):
        filename = c4d.storage.LoadDialog(c4d.FILESELECTTYPE_SCENES)
        if not filename or not os.path.isfile(filename):
            return

        print(filename)
        file = c4d.documents.LoadDocument(
            filename, c4d.SCENEFILTER_OBJECTS | c4d.SCENEFILTER_MATERIALS | c4d.SCENEFILTER_MERGESCENE)
        c4d.documents.InsertBaseDocument(file)
        #doc = c4d.documents.LoadDocument(file)
        # if not doc:
        #    c4d.gui.MessageDialog("The document could not be loaded.")
        #    return

        # DazToC4DUtils().sceneToZero()
        if doc.SearchObject('hip'):
            AllSceneToZero().sceneToZero()
        guiDazToC4dMain().applyDazIK()
        DazToC4DUtils().changeSkinType()
        c4d.EventAdd()


class randowmColors():
    IKMobjList = []

    def selchildren(self, obj, next):  # Scan obj hierarchy and select children

        while obj and obj != next:
            # global IKMobjList
            self.IKMobjList.append(obj)
            self.selchildren(obj.GetDown(), next)
            obj = obj.GetNext()
        return self.IKMobjList

    def get_random_color(self):
        """ Return a random color as c4d.Vector """

        def get_random_value():
            """ Return a random value between 0.0 and 1.0 """
            return randint(0, 255) / 256.0

        return c4d.Vector(get_random_value(), get_random_value(), get_random_value())

    def randomNullsColor(self, parentName, randomCol=1, rigColor1=0, rigColor2=0):
        doc = documents.GetActiveDocument()
        try:
            if randomCol == 1:
                rigColor1 = self.get_random_color()  # c4d.Vector(0,2,0)
                rigColor2 = self.get_random_color()  # c4d.Vector(1,0,0)
            # global IKMobjList
            self.IKMobjList = []
            # parentOb = doc.SearchObject(parentName)
            parentOb = parentName
            for o in self.selchildren(parentOb, parentOb.GetNext()):
                o[c4d.ID_BASEOBJECT_USECOLOR] = 2
                # o[c4d.ID_CA_JOINT_OBJECT_ICONCOL] = 1
                o[c4d.ID_BASEOBJECT_COLOR] = rigColor1
                if 'HAND' in o.GetName() or \
                        'Pelvis' in o.GetName() or \
                        'Platform' in o.GetName() or \
                        'Head' in o.GetName():
                    o[c4d.ID_BASEOBJECT_USECOLOR] = 2
                    # o[c4d.ID_CA_JOINT_OBJECT_ICONCOL] = 1
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
        except:
            pass
        c4d.EventAdd()

    def randomPoleColors(self, parentName, randomCol=1, rigColor1=0, rigColor2=0):
        doc = documents.GetActiveDocument()
        try:
            if randomCol == 1:
                rigColor1 = self.get_random_color()  # c4d.Vector(0,2,0)
                rigColor2 = self.get_random_color()  # c4d.Vector(1,0,0)
            # parentOb = doc.SearchObject(parentName)
            parentOb = parentName

            for o in self.selchildren(parentOb, parentOb.GetNext()):
                try:
                    tag = o.GetFirstTag()
                    tag[c4d.ID_CA_IK_TAG_DRAW_POLE_COLOR] = rigColor2
                except:
                    pass
            c4d.EventAdd()
        except:
            pass

    def randomRigColor(self, parentName, randomCol=1, rigColor1=0, rigColor2=0):
        doc = documents.GetActiveDocument()
        try:
            if randomCol == 1:
                rigColor1 = self.get_random_color()  # c4d.Vector(0,2,0)
                rigColor2 = self.get_random_color()  # c4d.Vector(1,0,0)
            # parentOb = doc.SearchObject(parentName)
            parentOb = parentName
            # global IKMobjList
            self.IKMobjList = []
            for o in self.selchildren(parentOb, parentOb.GetNext()):
                o[c4d.ID_BASEOBJECT_USECOLOR] = 2
                # o[c4d.ID_CA_JOINT_OBJECT_ICONCOL] = 1
                # print o.GetName()

                if "Head" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Neck" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Chest" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = (
                        rigColor2 * 0.9) + (rigColor1 * 0.1)
                if "Spine" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = (
                        rigColor2 * 0.7) + (rigColor1 * 0.3)
                if "Abdomen" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = (
                        rigColor2 * 0.7) + (rigColor1 * 0.3)
                if "Spine2" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = (
                        rigColor2 * 0.7) + (rigColor1 * 0.3)
                if "Collar" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Arm" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "ForeArm" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Hand" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2

                if "Index" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Middle" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Ring" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Pink" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Thumb" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2

                if "Finger" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Thumb" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2

                if "Pelvis" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = (
                        rigColor2 * 0.2) + (rigColor1 * 0.8)

                if "LegUpper" in o.GetName() or "jUpLeg" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor1 * 0.7
                if "LegLower" in o.GetName() or "jLeg" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor1 * 0.6
                if "Foot" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor1 * 0.3
                if "Toes" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor1 * 0.3
                if "ToesEnd" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor1 * 0.2
            c4d.EventAdd()
        except Exception as e:
            print(e)
            # pass


class IKMAXFastAttach(c4d.gui.GeDialog):
    dir, file = os.path.split(__file__)  # Gets the plugin's directory
    # Adds the res folder to the path
    LogoFolder_Path = os.path.join(dir, 'res')
    # Adds the res folder to the path
    LogoFolder_PathImgs = os.path.join(LogoFolder_Path, 'imgs')

    img_fa_head = os.path.join(LogoFolder_PathImgs, 'fa_head.png')
    img_fa_neck = os.path.join(LogoFolder_PathImgs, 'fa_neck.png')
    img_fa_chest = os.path.join(LogoFolder_PathImgs, 'fa_chest.png')
    img_fa_foot = os.path.join(LogoFolder_PathImgs, 'fa_foot.png')
    img_fa_jointV = os.path.join(LogoFolder_PathImgs, 'fa_jointV.png')
    img_fa_pelvis = os.path.join(LogoFolder_PathImgs, 'fa_pelvis.png')
    img_fa_spine = os.path.join(LogoFolder_PathImgs, 'fa_spine.png')
    img_fa_handL = os.path.join(LogoFolder_PathImgs, 'fa_hand_L.png')
    img_fa_handR = os.path.join(LogoFolder_PathImgs, 'fa_hand_R.png')

    jointPelvis = 'naaa'

    PREFFIX = ''
    MODEL = ''

    BUTTON_ATTACH_HEAD = 241798100
    BUTTON_ATTACH_NECK = 241798101
    BUTTON_ATTACH_CHEST = 241798102
    BUTTON_ATTACH_SPINE = 241798103
    BUTTON_ATTACH_PELVIS = 241798104

    BUTTON_ATTACH_ARM_RIGHT = 241798105
    BUTTON_ATTACH_FOREARM_RIGHT = 241798106
    BUTTON_ATTACH_HAND_RIGHT = 241798107

    BUTTON_ATTACH_ARM_LEFT = 241798111
    BUTTON_ATTACH_FOREARM_LEFT = 241798112
    BUTTON_ATTACH_HAND_LEFT = 241798113

    BUTTON_ATTACH_UPLEG_RIGHT = 241798108
    BUTTON_ATTACH_LEG_RIGHT = 241798109
    BUTTON_ATTACH_FOOT_RIGHT = 241798110

    BUTTON_ATTACH_UPLEG_LEFT = 241798114
    BUTTON_ATTACH_LEG_LEFT = 241798115
    BUTTON_ATTACH_FOOT_LEFT = 241798116

    TEXT_ATTACHOBJ = 241798117
    TEXT_ATTACHOBJ2 = 241798118

    def buttonBC(self, tooltipText="", presetLook=""):
        # Logo Image #############################################################
        bc = c4d.BaseContainer()  # Create a new container to store the button image
        bc.SetBool(c4d.BITMAPBUTTON_BUTTON, True)
        bc.SetString(c4d.BITMAPBUTTON_TOOLTIP, tooltipText)

        if presetLook == "":
            # Sets the border to look like a button
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_ROUND)
        if presetLook == "Preset0":
            # Sets the border to look like a button
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE)
        if presetLook == "Preset1":
            # Sets the border to look like a button
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE)
            bc.SetBool(c4d.BITMAPBUTTON_BUTTON, False)

        return bc
        # Logo Image #############################################################

    def CreateLayout(self):
        doc = c4d.documents.GetActiveDocument()

        MU = 0.8
        self.SetTitle("FastAttach")

        objs = doc.GetActiveObjects(1)
        objText = ''
        if len(objs) == 1:
            objText = objs[0].GetName()
        if len(objs) > 1:
            objText = str(len(objs)) + ' objects'

        self.MODEL = objs

        self.GroupBegin(11, c4d.BFV_TOP, 1, 1, title="")  # DIALOG MARGINNNNS
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(0 * MU, 10 * MU, 10 * MU, 5 * MU)

        self.GroupBegin(11, c4d.BFV_TOP, 1, 1, title="")  # DIALOG MARGINNNNS
        self.GroupBorderNoTitle(c4d.BORDER_ACTIVE_4)
        self.GroupBorderSpace(20 * MU, 10 * MU, 20 * MU, 10 * MU)
        self.FA_text = self.AddStaticText(
            self.TEXT_ATTACHOBJ, c4d.BFH_CENTER, 0, 0, name='object')
        self.SetString(self.TEXT_ATTACHOBJ, objText)
        self.GroupEnd()
        self.FA_text2 = self.AddStaticText(
            self.TEXT_ATTACHOBJ2, c4d.BFH_CENTER, 0, 0, name='will be constrainted to...')

        self.GroupEnd()

        self.GroupBegin(11, c4d.BFV_TOP, 1, 2, title="")  # DIALOG MARGINNNNS
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(10 * MU, 10 * MU, 10 * MU, 30 * MU)

        # HEAD ------------------
        self.GroupBegin(11, c4d.BFV_TOP, 1, 2, title="")
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(100 * MU, 0 * MU, 100 * MU, 0 * MU)

        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_HEAD, c4d.CUSTOMGUI_BITMAPBUTTON,
                                            "Bitmap Button", c4d.BFH_CENTER, 60, 70, self.buttonBC("Head", "Preset0"))
        # Add the image to the button
        self.btnFA_head.SetImage(self.img_fa_head, True)

        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_NECK, c4d.CUSTOMGUI_BITMAPBUTTON,
                                            "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        # Add the image to the button
        self.btnFA_head.SetImage(self.img_fa_neck, True)

        self.GroupEnd()

        self.GroupBegin(11, c4d.BFV_TOP, 3, 1, title="")  # MIDDLE ----------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(0, 0, 0, 0)

        # MIDDLE - ARM LEFT --------------
        self.GroupBegin(11, c4d.BFV_TOP, 1, 3, title="")
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(10 * MU, 0 * MU, 10 * MU, 0 * MU)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_ARM_RIGHT, c4d.CUSTOMGUI_BITMAPBUTTON,
                                            "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        # Add the image to the button
        self.btnFA_head.SetImage(self.img_fa_jointV, True)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_FOREARM_RIGHT, c4d.CUSTOMGUI_BITMAPBUTTON,
                                            "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        # Add the image to the button
        self.btnFA_head.SetImage(self.img_fa_jointV, True)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_HAND_RIGHT, c4d.CUSTOMGUI_BITMAPBUTTON,
                                            "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        # Add the image to the button
        self.btnFA_head.SetImage(self.img_fa_handR, True)
        self.GroupEnd()

        # MIDDLE - SPINES AND CHEST --------------
        self.GroupBegin(11, c4d.BFV_TOP, 1, 3, title="")
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(10 * MU, 4 * MU, 10 * MU, 4 * MU)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_CHEST, c4d.CUSTOMGUI_BITMAPBUTTON,
                                            "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        # Add the image to the button
        self.btnFA_head.SetImage(self.img_fa_chest, True)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_SPINE, c4d.CUSTOMGUI_BITMAPBUTTON,
                                            "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        # Add the image to the button
        self.btnFA_head.SetImage(self.img_fa_spine, True)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_PELVIS, c4d.CUSTOMGUI_BITMAPBUTTON,
                                            "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        # Add the image to the button
        self.btnFA_head.SetImage(self.img_fa_pelvis, True)
        self.GroupEnd()

        # MIDDLE - ARM RIGHT --------------
        self.GroupBegin(11, c4d.BFV_TOP, 1, 3, title="")
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(10 * MU, 0 * MU, 10 * MU, 0 * MU)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_ARM_LEFT, c4d.CUSTOMGUI_BITMAPBUTTON,
                                            "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        # Add the image to the button
        self.btnFA_head.SetImage(self.img_fa_jointV, True)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_FOREARM_LEFT, c4d.CUSTOMGUI_BITMAPBUTTON,
                                            "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        # Add the image to the button
        self.btnFA_head.SetImage(self.img_fa_jointV, True)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_HAND_LEFT, c4d.CUSTOMGUI_BITMAPBUTTON,
                                            "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        # Add the image to the button
        self.btnFA_head.SetImage(self.img_fa_handL, True)
        self.GroupEnd()

        self.GroupEnd()

        self.GroupBegin(11, c4d.BFV_TOP, 2, 1, title="")  # LEGS ----------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(0, 0, 0, 0)

        # LEGS - LEFT --------------
        self.GroupBegin(11, c4d.BFV_TOP, 1, 3, title="")
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(0 * MU, 0 * MU, 10 * MU, 0)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_UPLEG_LEFT, c4d.CUSTOMGUI_BITMAPBUTTON,
                                            "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        # Add the image to the button
        self.btnFA_head.SetImage(self.img_fa_jointV, True)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_LEG_LEFT, c4d.CUSTOMGUI_BITMAPBUTTON,
                                            "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        # Add the image to the button
        self.btnFA_head.SetImage(self.img_fa_jointV, True)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_FOOT_LEFT, c4d.CUSTOMGUI_BITMAPBUTTON,
                                            "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        # Add the image to the button
        self.btnFA_head.SetImage(self.img_fa_foot, True)

        self.GroupEnd()

        # LEGS - RIGHT --------------
        self.GroupBegin(11, c4d.BFV_TOP, 1, 3, title="")
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(5 * MU, 0 * MU, 5 * MU, 0 * MU)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_UPLEG_RIGHT, c4d.CUSTOMGUI_BITMAPBUTTON,
                                            "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        # Add the image to the button
        self.btnFA_head.SetImage(self.img_fa_jointV, True)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_LEG_RIGHT, c4d.CUSTOMGUI_BITMAPBUTTON,
                                            "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        # Add the image to the button
        self.btnFA_head.SetImage(self.img_fa_jointV, True)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_FOOT_RIGHT, c4d.CUSTOMGUI_BITMAPBUTTON,
                                            "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        # Add the image to the button
        self.btnFA_head.SetImage(self.img_fa_foot, True)

        self.GroupEnd()

        self.GroupEnd()

        self.GroupEnd()  # DIALOG MARGINSSSSSSS END

        return True

    def removeConstraint(self, obj):
        if obj != None:
            doc = documents.GetActiveDocument()
            tags = TagIterator(obj)
            overwriteConst = 1
            try:
                for tag in tags:

                    if 'Constraint' in tag.GetName():
                        answer = gui.MessageDialog('Object >>>  ' + obj.GetName(
                        ) + '  <<< already constrainted.\nOverwrite constraint?', c4d.GEMB_YESNO)
                        if answer == 6:
                            tag.Remove()
                        else:
                            overwriteConst = 0
            except:
                pass

            c4d.EventAdd()
            return overwriteConst

    def Command(self, id, msg):
        doc = documents.GetActiveDocument()
        jointSelected = ''

        print('asdasd')
        print(self.jointPelvis)
        print('-------')

        if id == self.BUTTON_ATTACH_HEAD:
            jointSelected = 'jHead'
        if id == self.BUTTON_ATTACH_NECK:
            jointSelected = 'jNeck'
        if id == self.BUTTON_ATTACH_CHEST:
            jointSelected = 'jChest'
        if id == self.BUTTON_ATTACH_SPINE:
            jointSelected = 'jSpine'
        if id == self.BUTTON_ATTACH_PELVIS:
            jointSelected = 'jPelvis'

        if id == self.BUTTON_ATTACH_ARM_LEFT:
            jointSelected = 'jArm'
        if id == self.BUTTON_ATTACH_FOREARM_LEFT:
            jointSelected = 'jForeArm'
        if id == self.BUTTON_ATTACH_HAND_LEFT:
            jointSelected = 'jHand'

        if id == self.BUTTON_ATTACH_UPLEG_LEFT:
            jointSelected = 'jUpLeg'
        if id == self.BUTTON_ATTACH_LEG_LEFT:
            jointSelected = 'jLeg'
        if id == self.BUTTON_ATTACH_FOOT_LEFT:
            jointSelected = 'jFoot'

        if id == self.BUTTON_ATTACH_ARM_RIGHT:
            jointSelected = 'jArm___R'
        if id == self.BUTTON_ATTACH_FOREARM_RIGHT:
            jointSelected = 'jForeArm___R'
        if id == self.BUTTON_ATTACH_HAND_RIGHT:
            jointSelected = 'jHand___R'

        if id == self.BUTTON_ATTACH_UPLEG_RIGHT:
            jointSelected = 'jUpLeg___R'
        if id == self.BUTTON_ATTACH_LEG_RIGHT:
            jointSelected = 'jLeg___R'
        if id == self.BUTTON_ATTACH_FOOT_RIGHT:
            jointSelected = 'jFoot___R'

        # objParent = doc.SearchObject(daz_name + jointSelected)
        objParent = ''
        joints = IkMaxUtils().iterateObjChilds(self.jointPelvis)
        if '___R' in jointSelected:
            for j in joints:
                if jointSelected in j.GetName() and '___R' in j.GetName():
                    objParent = j
        else:
            for j in joints:
                if jointSelected in j.GetName() and '___R' not in j.GetName():
                    objParent = j
        objChild = self.MODEL

        if len(objChild) == 1:
            objChild = self.MODEL[0]
            if self.removeConstraint(objChild) == 1:
                IkmGenerator().constraintObj(objChild, objParent, 'PARENT', 0)
                c4d.CallCommand(12113, 12113)  # Deselect All
                c4d.EventAdd()
                self.Close()

        if len(objChild) > 1:
            for obj in objChild:
                if self.removeConstraint(obj) == 1:
                    IkmGenerator().constraintObj(obj, objParent, 'PARENT', 0)
                    c4d.EventAdd()
            c4d.CallCommand(12113, 12113)  # Deselect All
            c4d.EventAdd()
            self.Close()

        c4d.EventAdd()

        return True



