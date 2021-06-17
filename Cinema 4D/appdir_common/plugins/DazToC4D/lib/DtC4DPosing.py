import math

from c4d import documents, gui
import c4d

from .DazToC4DClasses import DazToC4D
from .CustomIterators import ObjectIterator
from .AllSceneToZero import AllSceneToZero

"""
Switched Daz Characters to a TPose
Z Axis is inverted from Daz to C4D
Genesis 3 To Genesis 8
- Left Shoulder Bend: +45.75 (on Bend) (Z)
- Right Shoulder Bend: -45.75 (on Bend) (Z)
- Left Thigh Bend: -6 (on Side-Side) (Z)
- Right Thigh Bend: +6 (on Side-Side) (Z)

Genesis 8 To Genesis 3
- Left Shoulder Bend: -45.75 (on Bend) (Z)
- Right Shoulder Bend: +45.75 (on Bend) (Z)
- Left Thigh Bend: +6 (on Side-Side) (Z)
- Right Thigh Bend: -6 (on Side-Side) (Z)

ToDo: Refactor the T Pose to Have some type of Standard we can follow.
"""


class autoAlignArms:
    def __init__(self):
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject("lShldrTwist")
        if obj:
            self.alignJoint("l", "ShldrBend", "ForearmBend")
            self.alignJoint("l", "ShldrTwist", "ForearmBend")
            self.alignJoint("l", "ForearmBend", "Hand")
            self.alignJoint("l", "ForearmTwist", "Hand")

            self.alignJoint("l", "Index1", "Index2")
            self.alignJoint("l", "Index2", "Index3")
            self.alignJoint("l", "Mid1", "Mid2")
            self.alignJoint("l", "Mid2", "Mid3")
            self.alignJoint("l", "Ring1", "Ring2")
            self.alignJoint("l", "Ring2", "Ring3")
            self.alignJoint("l", "Pinky1", "Pinky2")
            self.alignJoint("l", "Pinky2", "Pinky3")

            self.alignJoint("r", "ShldrBend", "ForearmBend")
            self.alignJoint("r", "ShldrTwist", "ForearmBend")
            self.alignJoint("r", "ForearmBend", "Hand")
            self.alignJoint("r", "ForearmTwist", "Hand")

            self.alignJoint("r", "Index1", "Index2")
            self.alignJoint("r", "Index2", "Index3")
            self.alignJoint("r", "Mid1", "Mid2")
            self.alignJoint("r", "Mid2", "Mid3")
            self.alignJoint("r", "Ring1", "Ring2")
            self.alignJoint("r", "Ring2", "Ring3")
            self.alignJoint("r", "Pinky1", "Pinky2")
            self.alignJoint("r", "Pinky2", "Pinky3")

        obj = doc.SearchObject("lShldr")
        if obj:
            self.alignJoint("l", "Shldr", "ForeArm")
            self.alignJoint("l", "ForeArm", "Hand")
            self.alignJoint("r", "Shldr", "ForeArm")
            self.alignJoint("r", "ForeArm", "Hand")

    def alignJoint(self, side, jointName, jointTarget):
        doc = documents.GetActiveDocument()
        jointSource = doc.SearchObject(side + jointName)
        objSource = self.newNullfromJoint(side + jointName, "ROTATOR")
        objTarget = self.newNullfromJoint(side + jointTarget, "TARGET")
        if jointSource != None:
            xtag = self.constraintObj(jointSource, objTarget)
            objTarget.SetMg(objSource.GetMg())
            if side == "l":
                xValue = 100
            if side == "r":
                xValue = -100
            objTarget[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X] += xValue
            c4d.DrawViews(
                c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
                | c4d.DRAWFLAGS_NO_THREAD
                | c4d.DRAWFLAGS_STATICBREAK
            )
            c4d.EventAdd()
            xtag.Remove()
            objSource.Remove()
            objTarget.Remove()

    def constraintObj(self, obj, target):
        doc = c4d.documents.GetActiveDocument()

        constraintTAG = c4d.BaseTag(1019364)
        constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM] = True
        constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_MAINTAIN] = True
        constraintTAG[20001] = target

        obj.InsertTag(constraintTAG)

        c4d.EventAdd()
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
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

            c4d.EventAdd()
        return nullTemp


class Poses:
    pose_data = dict()

    def store_pose(self, dtu):
        self.pose_data = dtu.get_pose_data_dict()

    def get_pose_data(self, joint):
        jnt_name = joint.GetName()
        if jnt_name in self.pose_data.keys():
            return self.pose_data[jnt_name]

    def clear_pose(self, joints):
        for joint in joints:
            jnt_data = self.get_pose_data(joint)
            if jnt_data:
                pos_x = joint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X]
                pos_y = joint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y]
                pos_z = joint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z]
                joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0
                joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0
                joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0
                joint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X] = (
                    pos_x - jnt_data["Position"][0]
                )
                joint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y] = (
                    pos_y - jnt_data["Position"][1]
                )
                joint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z] = (
                    pos_z + jnt_data["Position"][2]
                )
            c4d.EventAdd()

    def restore_pose(self, joints):
        for joint in joints:
            jnt_data = self.get_pose_data(joint)
            if jnt_data:
                pos_x = joint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X]
                pos_y = joint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y]
                pos_z = joint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z]
                joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = math.radians(
                    jnt_data["Rotation"][0]
                )
                joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = math.radians(
                    jnt_data["Rotation"][1]
                )
                joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = -1 * math.radians(
                    jnt_data["Rotation"][2]
                )
                joint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X] = (
                    pos_x + jnt_data["Position"][0]
                )
                joint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y] = (
                    pos_y + jnt_data["Position"][1]
                )
                joint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z] = (
                    pos_z - jnt_data["Position"][2]
                )
            c4d.EventAdd()

    def preAutoIK(self):
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject("hip")
        if obj:
            doc = documents.GetActiveDocument()
            if not doc.SearchObject("lThighTwist"):
                if self.checkIfPosedResetPose(False) == False:
                    forceTpose().dazFix_All_To_T_Pose()
            if doc.SearchObject("lThighTwist"):
                if self.checkIfPosedResetPose(False) == False:
                    self.dazManualRotationFixTpose()

        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        c4d.EventAdd()

    def checkIfPosedResetPose(self, checkAndReset=True):
        def checkIfPosed():
            obj = doc.GetFirstObject()
            scene = ObjectIterator(obj)
            jointsList = [
                "Collar",
                "head",
                "ShldrTwist",
                "Forearm",
                "pelvis",
                "abdomen",
                "Shldr",
            ]
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
                jointR = doc.SearchObject("r" + jointName)
                jointL = doc.SearchObject("l" + jointName)
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

            if compareJoints("ForeArm"):
                isPosed = True
            if compareJoints("Shldr"):
                isPosed = True
            if compareJoints("ShldrBend"):
                isPosed = True
            if compareJoints("ForearmBend"):
                isPosed = True
            if compareJoints("Hand"):
                isPosed = True
            if compareJoints("ThighBend"):
                isPosed = True
            if checkJoint("chestUpper"):
                isPosed = True
            if checkJoint("chestLower"):
                isPosed = True
            if checkJoint("abdomenLower"):
                isPosed = True
            if checkJoint("abdomenUpper"):
                isPosed = True
            if checkJoint("neckLower"):
                isPosed = True

            return isPosed

        doc = documents.GetActiveDocument()
        if checkAndReset == False:
            return checkIfPosed()
        jointHip = doc.SearchObject("hip")
        jointRig = ObjectIterator(jointHip)
        if checkIfPosed():
            answer = gui.QuestionDialog(
                "Reset Pose first before Auto-Ik.\nReset Pose now?\n\nWarning: No Undo"
            )
            if answer:
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
                    mainJoint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z] = 0.0
                except:
                    pass

                self.dazManualRotationFixTpose()

                c4d.EventAdd()
                c4d.DrawViews(
                    c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
                    | c4d.DRAWFLAGS_NO_THREAD
                    | c4d.DRAWFLAGS_STATICBREAK
                )
                c4d.EventAdd()

                AllSceneToZero().sceneToZero()
                answer = gui.QuestionDialog("Would You Like to Run\nAUTO-IK")
                if answer:
                    return True
                else:
                    return False

        else:
            return True

    def checkIfPosed(self):
        doc = documents.GetActiveDocument()

        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        jointsList = [
            "Collar",
            "head",
            "ShldrTwist",
            "Forearm",
            "pelvis",
            "abdomen",
            "Shldr",
        ]
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
            jointR = doc.SearchObject("r" + jointName)
            jointL = doc.SearchObject("l" + jointName)
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

        if compareJoints("ForeArm"):
            isPosed = True
        if compareJoints("Shldr"):
            isPosed = True
        if compareJoints("ShldrBend"):
            isPosed = True
        if compareJoints("ForearmBend"):
            isPosed = True
        if compareJoints("Hand"):
            isPosed = True
        if compareJoints("ThighBend"):
            isPosed = True
        if checkJoint("chestUpper"):
            isPosed = True
        if checkJoint("chestLower"):
            isPosed = True
        if checkJoint("abdomenLower"):
            isPosed = True
        if checkJoint("abdomenUpper"):
            isPosed = True
        if checkJoint("neckLower"):
            isPosed = True

        return isPosed

    def find_genesis(self):
        doc = documents.GetActiveDocument()

        if doc.SearchObject("lThigh"):
            if doc.SearchObject("lShin"):
                if doc.SearchObject("abdomen2"):
                    return "Genesis2"

        if doc.SearchObject("lShldrBend"):
            if doc.SearchObject("lMetatarsals"):
                if doc.SearchObject("rThighTwist"):
                    obj1PosY = ""
                    obj1PosY = ""
                    obj1PosY = doc.SearchObject("lShldrBend").GetMg().off[1]
                    obj2PosY = doc.SearchObject("lForearmBend").GetMg().off[1]
                    distValue = obj1PosY - obj2PosY
                    if distValue < 2.9:
                        return "Genesis3"  # TODO !!
                    else:
                        return "Genesis8"

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

        dazType = self.find_genesis()

        if dazType == "Genesis8":
            autoAlignArms()

        if dazType == "Genesis3":
            autoAlignArms()

        if dazType == "Genesis2":
            # Genesis 2 LEFT Side:
            setRotAndMirror("lShldr", 0.089, 0.0, -0.019)
            setRotAndMirror("lForeArm", 0.334, 0.0, 0.0)
            setRotAndMirror("lHand", 0.083, 0.222, -0.121)
            setRotAndMirror("lThigh", 0.0, 0.0, 0.0)

            # Genesis 2 RIGHT Side:
            setRotAndMirror("rShldr", -0.089, 0.0, 0.019)
            setRotAndMirror("rForeArm", -0.334, 0.0, 0.0)
            setRotAndMirror("rHand", -0.083, 0.222, 0.121)
            setRotAndMirror("rThigh", 0.0, 0.0, 0.0)

        c4d.EventAdd()
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        c4d.EventAdd()


class forceTpose:
    def dazRotFix(self, master, mode="", jointToFix="", rotValue=0):
        doc = documents.GetActiveDocument()

        nullObj = c4d.BaseObject(c4d.Onull)
        nullObj.SetName("TempNull")
        doc.InsertObject(nullObj)
        armJoint = doc.SearchObject("lShldrBend")
        handJoint = doc.SearchObject("lForearmBend")

        mg = jointToFix.GetMg()
        nullObj.SetMg(mg)

        nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0
        nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0
        nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0
        c4d.EventAdd()

        slaveObj = nullObj
        masterObj = master

        def addConstraint(slaveObj, masterObj, mode="Parent"):
            if mode == "Parent":
                constraintTAG = c4d.BaseTag(1019364)

                constraintTAG[c4d.EXPRESSION_ENABLE] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR_MAINTAIN] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
                constraintTAG[10005] = True
                constraintTAG[10007] = True
                constraintTAG[10001] = masterObj

                PriorityDataInitial = c4d.PriorityData()
                PriorityDataInitial.SetPriorityValue(
                    c4d.PRIORITYVALUE_MODE, c4d.CYCLE_EXPRESSION
                )
                PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_PRIORITY, 0)
                PriorityDataInitial.SetPriorityValue(
                    c4d.PRIORITYVALUE_CAMERADEPENDENT, 0
                )
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
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        c4d.EventAdd()

        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        constraintTAG.Remove()

        addConstraint(jointToFix, slaveObj)

        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        slaveObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = rotValue

    def dazRotationsFix(
        self, jointToFix, jointToAim, oppositeJoint, rotValue=0, allToZero=False
    ):
        doc = documents.GetActiveDocument()

        mainJoint = doc.SearchObject(jointToFix)
        goalJoint = doc.SearchObject(jointToAim)
        self.dazRotFix(goalJoint, "AIM", mainJoint, rotValue)

        jointOposite = doc.SearchObject(oppositeJoint)
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )

        rx = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X]
        ry = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y]
        rz = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z]

        jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = rx * -1
        if allToZero == True:
            jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0
            jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0

        tempNull = doc.SearchObject("TempNull")
        tempNull.Remove()
        caca = mainJoint.GetFirstTag()
        caca.Remove()

        c4d.EventAdd()

    def dazFix_All_To_T_Pose(self):
        # Genesis2
        doc = documents.GetActiveDocument()
        if doc.SearchObject("lShldr"):
            self.dazRotationsFix("lShldr", "lForeArm", "rShldr", 1.571)
        if doc.SearchObject("lForeArm"):
            self.dazRotationsFix("lForeArm", "lHand", "rForeArm", 1.571)

        # All Genesis..Maybe...
        if doc.SearchObject("lFoot"):
            self.dazRotationsFix("lFoot", "lToe", "rFoot")
