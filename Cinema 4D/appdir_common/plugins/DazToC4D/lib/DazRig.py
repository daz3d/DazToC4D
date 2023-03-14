from ntpath import join
import c4d
from c4d import documents
import sys

from .CustomCmd import Cinema4DCommands as dzc4d
from .CustomIterators import TagIterator
from . import Database
from . import Utilities


class JointFixes:
    joint_orient_dict = dict()

    @staticmethod
    def update_rotation_order(ctrl_name, rig_name):
        doc = documents.GetActiveDocument()
        ctrl = doc.SearchObject(ctrl_name)
        rig = doc.SearchObject(rig_name)
        ctrl[c4d.ID_BASEOBJECT_ROTATION_ORDER] = rig[c4d.ID_BASEOBJECT_ROTATION_ORDER]

    def store_joint_orientations(self, dtu):
        self.joint_orient_dict = dtu.get_joint_orientation_dict()
        self.head_tail_dict = dtu.get_bone_head_tail_dict()

    def disable_skin_data(self, c_skin_data):
        for obj in c_skin_data:
            obj[c4d.ID_BASEOBJECT_GENERATOR_FLAG] = False
        c4d.EventAdd()

    def enable_skin_data(self, c_skin_data):
        for obj in c_skin_data:
            obj[c4d.ID_BASEOBJECT_GENERATOR_FLAG] = True
        c4d.EventAdd()

    def get_orientation(self, joint):
        joint_name = joint.GetName()
        if joint_name in self.joint_orient_dict.keys():
            return self.joint_orient_dict[joint_name]
        return []

    def find_order(self, rotation_order):
        if rotation_order == "XYZ":
            return 5
        if rotation_order == "XZY":
            return 4
        if rotation_order == "YXZ":
            return 0
        if rotation_order == "YZX":
            return 1
        if rotation_order == "ZXY":
            return 3
        if rotation_order == "ZYX":
            return 2

    def move_axis(self, obj, new_axis):
        matrix = ~new_axis * obj.GetMl()
        children = obj.GetChildren()
        for child in children:
            child.SetMl(matrix * child.GetMl())
        obj.SetMl(new_axis)

    def update_rig_axis(self, joint, rig_joint):
        joint_data = self.get_orientation(joint)
        if len(joint_data) == 0:
            return
        rotation_order = joint_data[0]
        index = self.find_order(rotation_order)
        rig_joint[c4d.ID_BASEOBJECT_ROTATION_ORDER] = index
        rig_joint.SetMg(joint.GetMg())
        c4d.CallButton(rig_joint, c4d.ID_BASEOBJECT_FREEZE_R)

    def store_incorrect_orientations(self, joint):
        current_m = joint.GetMl()
        v1 = c4d.GetCustomDataTypeDefault(c4d.DTYPE_VECTOR)
        v1[c4d.DESC_NAME] = "V1 at Import"
        descId = joint.AddUserData(v1)
        joint[descId] = current_m.v1
        v2 = c4d.GetCustomDataTypeDefault(c4d.DTYPE_VECTOR)
        v2[c4d.DESC_NAME] = "V2 at Import"
        descId = joint.AddUserData(v2)
        joint[descId] = current_m.v2
        v3 = c4d.GetCustomDataTypeDefault(c4d.DTYPE_VECTOR)
        v3[c4d.DESC_NAME] = "V3 at Import"
        descId = joint.AddUserData(v3)
        joint[descId] = current_m.v3

    def update_axis(self, joint):
        joint_data = self.get_orientation(joint)
        if len(joint_data) == 0:
            return
        rotation_order = joint_data[0]
        index = self.find_order(rotation_order)
        x = joint_data[1]
        y = joint_data[2]
        z = joint_data[3]
        joint[c4d.ID_BASEOBJECT_ROTATION_ORDER] = index
        self.store_incorrect_orientations(joint)
        matrix = joint.GetMl() * c4d.utils.MatrixRotX(c4d.utils.Rad(x))
        matrix = matrix * c4d.utils.MatrixRotY(c4d.utils.Rad(y))
        matrix = matrix * c4d.utils.MatrixRotZ(c4d.utils.Rad(-1 * z))
        self.move_axis(joint, matrix)
        c4d.CallButton(joint, c4d.ID_BASEOBJECT_FREEZE_R)

    def reset_bind_pose(self, c_meshes):
        for obj in c_meshes:
            tags = TagIterator(obj)
            for tag in tags:
                tag_type = tag.GetType()
                if tag_type == c4d.Tweights:
                    if c4d.GetC4DVersion() <= 22123:
                        tag[c4d.ID_CA_WEIGHT_TAG_SET] = 2005
                        c4d.CallButton(tag, c4d.ID_CA_WEIGHT_TAG_SET)
                        c4d.EventAdd()
                        break
                    else:
                        tag[c4d.ID_CA_WEIGHT_TAG_SET_BUTTON] = 2005
                        c4d.CallButton(tag, c4d.ID_CA_WEIGHT_TAG_SET_BUTTON)
                        c4d.EventAdd()
                        break

    def fix_joints(self, c_skin_data, c_joints, c_meshes):
        self.disable_skin_data(c_skin_data)
        doc = documents.GetActiveDocument()
        c4d.CallCommand(12102)
        c4d.EventAdd()

        for joint in c_joints:
            doc.SetActiveObject(joint, c4d.SELECTION_NEW)
            doc.AddUndo(c4d.UNDOTYPE_CHANGE, joint)
            self.update_axis(joint)
            c4d.EventAdd()

        self.reset_bind_pose(c_meshes)
        self.enable_skin_data(c_skin_data)
        c4d.CallCommand(12102)
        c4d.EventAdd()

    def find_matching_joint(self, joint):
        doc = documents.GetActiveDocument()
        dz_jnt_name = joint.GetName()
        prefix = dz_jnt_name[0:1]
        post_prefix = dz_jnt_name[1:2]
        if prefix == "l" and post_prefix.isupper():
            dz_jnt_name = dz_jnt_name[1:]
            suffix = ""
        elif prefix == "r" and post_prefix.isupper():
            dz_jnt_name = dz_jnt_name[1:]
            suffix = "___R"
        else:
            suffix = ""

        mesh_name = Utilities.get_daz_name() + "_"
        ## TODO: REPLACE WITH TRUE GENERATION TEST
        if doc.SearchObject("l_thightwist1"):
            constraints = Database.rig_joints_g9
        else:
            constraints = Database.rig_joints
        for joints in constraints:
            if dz_jnt_name == joints[0]:
                return doc.SearchObject(mesh_name + joints[1] + suffix)

    def fix_rig_joints(self, c_joints):
        doc = documents.GetActiveDocument()
        c4d.CallCommand(12102)
        c4d.EventAdd()

        for joint in c_joints:
            doc.SetActiveObject(joint, c4d.SELECTION_NEW)
            doc.AddUndo(c4d.UNDOTYPE_CHANGE, joint)
            rig_joint = self.find_matching_joint(joint)
            if rig_joint:
                self.update_rig_axis(joint, rig_joint)
            c4d.EventAdd()

        c4d.CallCommand(12102)
        c4d.EventAdd()


class DazRig:
    def __init__(self, add):
        self.dazName = add

    def dazEyesLookAtControls(self):
        def constraintObj(slave, master, mode="", searchObj=1):
            doc = documents.GetActiveDocument()
            if searchObj == 1:
                slaveObj = doc.SearchObject(slave)
                masterObj = doc.SearchObject(master)
            else:
                slaveObj = slave
                masterObj = master
            mg = slaveObj.GetMg()

            constraintTAG = c4d.BaseTag(1019364)
            if mode == "":
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
                constraintTAG[10001] = masterObj
            if mode == "UPVECTOR":
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_UP] = True
                constraintTAG[40004] = 4
                constraintTAG[40005] = 3
                constraintTAG[40001] = masterObj
            if mode == "ROTATION":
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
                constraintTAG[10005] = False
                constraintTAG[10006] = False
                constraintTAG[10001] = masterObj
            if mode == "AIM":
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_MAINTAIN] = True
                constraintTAG[20004] = 5
                constraintTAG[20001] = masterObj
            if mode == "PARENT":
                nullSlave = c4d.BaseObject(c4d.Onull)
                nullSlave.SetName("nullSlave")
                nullSlave.SetMg(slaveObj.GetMg())
                doc.InsertObject(nullSlave)
                nullParent = c4d.BaseObject(c4d.Onull)
                nullParent.SetName("nullParent")
                nullParent.SetMg(masterObj.GetMg())
                slaveMg = nullSlave.GetMg()
                doc.InsertObject(nullParent)
                nullSlave.InsertUnder(nullParent)
                nullSlave.SetMg(slaveMg)
                constraintTAG[c4d.EXPRESSION_ENABLE] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PARENT_MAINTAIN] = False
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PARENT_FROZEN] = False
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PARENT] = True
                constraintTAG[30001] = masterObj
                constraintTAG[30009, 1000] = c4d.Vector(
                    nullSlave.GetRelPos()[0],
                    nullSlave.GetRelPos()[1],
                    nullSlave.GetRelPos()[2],
                )
                constraintTAG[30009, 1002] = c4d.Vector(
                    nullSlave.GetRelRot()[0],
                    nullSlave.GetRelRot()[1],
                    nullSlave.GetRelRot()[2],
                )

                PriorityDataInitial = c4d.PriorityData()
                PriorityDataInitial.SetPriorityValue(
                    c4d.PRIORITYVALUE_MODE, c4d.CYCLE_GENERATORS
                )
                PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_PRIORITY, 0)
                PriorityDataInitial.SetPriorityValue(
                    c4d.PRIORITYVALUE_CAMERADEPENDENT, 0
                )
                constraintTAG[c4d.EXPRESSION_PRIORITY] = PriorityDataInitial
                try:
                    nullParent.Remove()
                except:
                    pass
            slaveObj.InsertTag(constraintTAG)

            c4d.EventAdd()

        def makeNull(nullName, target):
            doc = c4d.documents.GetActiveDocument()
            objNull = c4d.BaseObject(c4d.Onull)
            objNull.SetName(nullName + "_IKM-StartGuides")
            objNull.SetMg(target.GetMg())
            doc.InsertObject(objNull)
            c4d.EventAdd()

            return objNull

        def freezeChilds(parentObj=""):
            doc = c4d.documents.GetActiveDocument()
            obj = doc.SearchObject(parentObj)
            if obj:
                for x in obj.GetChildren():
                    c4d.CallButton(x, c4d.ID_BASEOBJECT_FREEZE_R)
                    c4d.CallButton(x, c4d.ID_BASEOBJECT_FREEZE_P)

                c4d.EventAdd()

        def nullStyle(obj):
            obj[c4d.ID_BASEOBJECT_USECOLOR] = True
            obj[c4d.ID_BASEOBJECT_COLOR] = c4d.Vector(0, 0.9, 0)
            obj[c4d.NULLOBJECT_DISPLAY] = 2
            obj[c4d.NULLOBJECT_ORIENTATION] = 1
            obj[c4d.NULLOBJECT_RADIUS] = 0.5
            try:
                obj[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 2
                obj[c4d.ID_BASELIST_ICON_COLOR] = obj[c4d.ID_BASEOBJECT_COLOR]
            except:
                obj[c4d.NULLOBJECT_ICONCOL] = True

        def nullStyleMaster(obj):
            obj[c4d.ID_BASEOBJECT_USECOLOR] = True
            obj[c4d.ID_BASEOBJECT_COLOR] = c4d.Vector(0, 1, 0)
            obj[c4d.NULLOBJECT_DISPLAY] = 7
            obj[c4d.NULLOBJECT_ASPECTRATIO] = 0.3
            obj[c4d.NULLOBJECT_ORIENTATION] = 1
            obj[c4d.NULLOBJECT_RADIUS] = masterSize / 25
            try:
                obj[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 2
                obj[c4d.ID_BASELIST_ICON_COLOR] = obj[c4d.ID_BASEOBJECT_COLOR]
            except:
                obj[c4d.NULLOBJECT_ICONCOL] = True

        def makeChild(child, parent):
            mg = child.GetMg()
            child.InsertUnder(parent)
            child.SetMg(mg)

        def protectTag(obj, protectPreset):
            doc = documents.GetActiveDocument()
            tagProtec = c4d.BaseTag(5629)  # Protection Tag
            if protectPreset == "Rotation":
                tagProtec[c4d.PROTECTION_P_X] = False
                tagProtec[c4d.PROTECTION_P_Y] = False
                tagProtec[c4d.PROTECTION_P_Z] = False
                tagProtec[c4d.PROTECTION_S_X] = True
                tagProtec[c4d.PROTECTION_S_Y] = True
                tagProtec[c4d.PROTECTION_S_Z] = True
                tagProtec[c4d.PROTECTION_R_X] = True
                tagProtec[c4d.PROTECTION_R_Y] = True
                tagProtec[c4d.PROTECTION_R_Z] = True
            obj.InsertTag(tagProtec)
            c4d.EventAdd()

        doc = c4d.documents.GetActiveDocument()
        r_eye = doc.SearchObject("rEye")  # Genesis2
        l_eye = doc.SearchObject("lEye")  # Genesis2

        if r_eye is None or l_eye is None:
            r_eye = doc.SearchObject("r_eye")  # Genesis9
            l_eye = doc.SearchObject("l_eye")  # Genesis9

        if r_eye is None or l_eye is None:
            return
        headJoint = doc.SearchObject("head")  # Genesis2
        joints = doc.SearchObject("pelvis")  # Genesis2
        ikControls = doc.SearchObject(self.dazName + "IKM_Controls")
        ikHeadCtrl = doc.SearchObject(self.dazName + "Head_ctrl")

        eye_r_ctrl = makeNull("Eye_R", r_eye)
        eye_l_ctrl = makeNull("Eye_L", l_eye)
        objParent = doc.SearchObject("head")
        eyesParentNull = makeNull("EyesParent", headJoint)

        eye_r_ctrl.SetName(self.dazName + "rEye_ctrl")
        eye_l_ctrl.SetName(self.dazName + "lEye_ctrl")
        eye_r_ctrl.SetAbsScale(c4d.Vector(1, 1, 1))
        eye_l_ctrl.SetAbsScale(c4d.Vector(1, 1, 1))

        eyesParentNull.SetName(self.dazName + "Eyes-LookAt")
        masterSize = 100  # ??????

        eye_r_ctrl[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z] -= masterSize / 4
        eye_l_ctrl[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z] -= masterSize / 4

        dzc4d.deselect_all()  # Deselect All
        doc.SetActiveObject(eye_r_ctrl, c4d.SELECTION_NEW)
        doc.SetActiveObject(eye_l_ctrl, c4d.SELECTION_ADD)
        c4d.CallCommand(100004772, 100004772)  # Group Objects
        c4d.CallCommand(100004773, 100004773)  # Expand Object

        objMasterEyes = doc.GetActiveObjects(0)[0]
        objMasterEyes.SetName(self.dazName + "EyesLookAtGroup")
        objMasterEyes.SetAbsScale(c4d.Vector(1, 1, 1))

        nullStyle(eye_r_ctrl)
        nullStyle(eye_l_ctrl)
        nullStyleMaster(objMasterEyes)

        constraintObj(r_eye, eye_r_ctrl, "AIM", 0)
        constraintObj(l_eye, eye_l_ctrl, "AIM", 0)

        makeChild(eye_r_ctrl, objMasterEyes)
        makeChild(eye_l_ctrl, objMasterEyes)
        makeChild(objMasterEyes, ikHeadCtrl)

        eye_r_ctrl.SetAbsRot(c4d.Vector(0))
        eye_l_ctrl.SetAbsRot(c4d.Vector(0))

        constraintObj(eyesParentNull, headJoint, "", 0)
        eyesParentNull.InsertAfter(joints)

        freezeChilds(self.dazName + "Eyes-LookAt")
        freezeChilds(self.dazName + "EyesLookAtGroup")
        # protectTag(objMasterEyes, "Rotation")
        c4d.EventAdd()
