import os
import sys
from c4d import documents, gui
import c4d

from .Materials import Materials
from .CustomIterators import ObjectIterator, TagIterator
from .DazToC4DClasses import DazToC4D
from .AllSceneToZero import AllSceneToZero

class autoAlignArms():
    def constraintObj(self, obj, target):
        doc = c4d.documents.GetActiveDocument()

        constraintTAG = c4d.BaseTag(1019364)
        constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM] = True
        constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_MAINTAIN] = True
        constraintTAG[20001] = target

        obj.InsertTag(constraintTAG)

        c4d.EventAdd()
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)
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
            c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)
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


class Poses:
    
    def preAutoIK(self):
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject('hip')
        if obj:
            doc = documents.GetActiveDocument()
            if doc.SearchObject('lThighTwist') != True:
                if self.checkIfPosedResetPose(False) == False:
                    forceTpose().dazFix_All_To_T_Pose()
            if doc.SearchObject('lThighTwist'):
                if self.checkIfPosedResetPose(False) == False:
                    self.dazManualRotationFixTpose()
        
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD   | c4d.DRAWFLAGS_STATICBREAK)
        c4d.EventAdd()

    def checkIfPosedResetPose(self, checkAndReset=True):
        doc = documents.GetActiveDocument()
        # isPosed = False

        def checkIfPosed():
            obj = doc.GetFirstObject()
            scene = ObjectIterator(obj)
            jointsList = ['Collar', 'head', 'ShldrTwist', 'Forearm', 'pelvis', 'abdomen', 'Shldr']
            caca = False

            def checkJoint(jointName):
                joint = doc.SearchObject(jointName)
                if joint:
                    rotRX = abs(joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                    rotRY = abs(joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                    rotRZ = abs(joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
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
                    rotRX = abs(jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                    rotRY = abs(jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                    rotRZ = abs(jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
                    rotLX = abs(jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                    rotLY = abs(jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                    rotLZ = abs(jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
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
            answer = gui.MessageDialog('Reset Pose first before Auto-Ik.\nReset Pose now?\n\nWarning: No Undo', c4d.GEMB_YESNO)
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
                    mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0.0
                    mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0.0
                    mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0.0
                    mainJoint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X] = 0.0
                    # mainJoint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y] = 0.0
                    mainJoint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z] = 0.0
                except:
                    pass

                self.dazManualRotationFixTpose()
                # dazToC4Dutils().sceneToZero()

                c4d.EventAdd()
                c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
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


    def checkIfPosed(self):
        doc = documents.GetActiveDocument()

        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        jointsList = ['Collar', 'head', 'ShldrTwist', 'Forearm', 'pelvis', 'abdomen', 'Shldr']
        caca = False

        def checkJoint(jointName):
            joint = doc.SearchObject(jointName)
            if joint:
                rotRX = abs(joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                rotRY = abs(joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                rotRZ = abs(joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
                if rotRX == rotRY == rotRZ == 0.0:
                    return False
                else:
                    return True

        def compareJoints(jointName):
            jointR = doc.SearchObject('r' + jointName)
            jointL = doc.SearchObject('l' + jointName)
            if jointR:
                rotRX = abs(jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                rotRY = abs(jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                rotRZ = abs(jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
                rotLX = abs(jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                rotLY = abs(jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                rotLZ = abs(jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
                rotRX = round(rotRX, 2)
                rotRY = round(rotRY, 2)
                rotRZ = round(rotRZ, 2)
                rotLX = round(rotLX, 2)
                rotLY = round(rotLY, 2)
                rotLZ = round(rotLZ, 2)
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
                        dazType = 'Genesis3' # TODO !!
                    else:
                        dazType = 'Genesis8'

        if doc.SearchObject('lThigh'):
            if doc.SearchObject('lShin'):
                if doc.SearchObject('abdomen2'):
                    dazType = 'Genesis2'
   
        if dazType == 'Genesis8':
            # GENESIS 8 --------------------------------------------
            # Genesis 8 LEFT Side:
            autoAlignArms()


        if dazType == 'Genesis3':
            # TODO: Why Material updates here?
            # Materials().fixGenEyes() # Apply IRIS alpha fix
            # GENESIS 3 -ZOMBIE WORKS TOO -------------------------------------------
            autoAlignArms()

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
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        c4d.EventAdd()


    def mirrorPose(self):
        doc = documents.GetActiveDocument()

        def mirrorPose(jointName):
            # jointName = 'lShldrBend'
            jointNameR = 'r' + jointName[1:100]
            jointObjL = doc.SearchObject(jointName)
            jointObjR = doc.SearchObject(jointNameR)
            if jointObjL:
                objLRot = jointObjL[c4d.ID_BASEOBJECT_REL_ROTATION]
                jointObjR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = -objLRot[0]
                jointObjR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = objLRot[1]
                jointObjR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = -objLRot[2]

        mirrorPose('lCollar')
        mirrorPose('lShldr') # ----Genesis 2
        mirrorPose('lForeArm') # ----Genesis 2
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

        mirrorPose('lThigh') # ----Genesis 2
        mirrorPose('lShin') # ----Genesis 2
        mirrorPose('lToe') # ----Genesis 2

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
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
                constraintTAG[10005] = True
                constraintTAG[10007] = True
                constraintTAG[10001] = masterObj

                PriorityDataInitial = c4d.PriorityData()
                PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_MODE, c4d.CYCLE_EXPRESSION)
                PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_PRIORITY, 0)
                PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_CAMERADEPENDENT, 0)
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
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)
        c4d.EventAdd()

        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)
        constraintTAG.Remove()

        addConstraint(jointToFix, slaveObj)

        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        slaveObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = rotValue

    def dazRotationsFix(self, jointToFix, jointToAim, oppositeJoint, rotValue=0, allToZero=False):
        doc = documents.GetActiveDocument()

        mainJoint = doc.SearchObject(jointToFix)
        goalJoint = doc.SearchObject(jointToAim)
        self.dazRotFix(goalJoint, 'AIM', mainJoint, rotValue)

        jointOposite = doc.SearchObject(oppositeJoint)
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)

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

        # All Genesis..Maybe...
        if doc.SearchObject('lFoot'):
            self.dazRotationsFix('lFoot', 'lToe', 'rFoot')