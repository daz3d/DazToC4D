import math

import c4d
from . import Utilities
from .MorphHelpers import MorphHelpers
from .Utilities import Variables


class Tracking(MorphHelpers):
    def find_which_neck(self, joints):
        """Will return the head bone or IK Control"""
        for joint in joints:
            if "neckUpper" in joint.GetName():
                return joint

    def find_eyes(self, joints):
        joint_to_use = ["r", "l"]
        for joint in joints:
            if "rEye" == joint.GetName():
                joint_to_use[0] = joint
            if "lEye" == joint.GetName():
                joint_to_use[1] = joint
        return joint_to_use

    def add_eye_tracking(self, face_capture):
        var = Variables()
        var.restore_variables()
        r_eye, l_eye = self.find_eyes(var.c_joints)
        xpresso_tag = self.get_tracking_xpresso(var.skeleton)
        node_master = xpresso_tag.GetNodeMaster()
        face_node = self.create_node(node_master, face_capture, 0, -200)
        r_eye_node = self.create_node(node_master, r_eye, 600, -100)
        l_eye_node = self.create_node(node_master, l_eye, 600, -300)
        face_r_eye = face_node.AddPort(
            c4d.GV_PORT_OUTPUT,
            c4d.DescID(c4d.DescLevel(c4d.FACECAPTURE_EYETRACKING_RIGHTEYE_ROTATION)),
        )
        face_l_eye = face_node.AddPort(
            c4d.GV_PORT_OUTPUT,
            c4d.DescID(c4d.DescLevel(c4d.FACECAPTURE_EYETRACKING_LEFTEYE_ROTATION)),
        )
        r_eye_rot = r_eye_node.AddPort(
            c4d.GV_PORT_INPUT,
            c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_REL_ROTATION)),
        )
        l_eye_rot = l_eye_node.AddPort(
            c4d.GV_PORT_INPUT,
            c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_REL_ROTATION)),
        )
        r_vec_to_real = self.create_xpresso_node(
            node_master,
            c4d.ID_OPERATOR_VECT2REAL,
            200,
            -100,
        )
        r_real_to_vect = self.create_xpresso_node(
            node_master,
            c4d.ID_OPERATOR_REAL2VECT,
            400,
            -100,
        )
        l_vec_to_real = self.create_xpresso_node(
            node_master,
            c4d.ID_OPERATOR_VECT2REAL,
            200,
            -300,
        )
        l_real_to_vect = self.create_xpresso_node(
            node_master,
            c4d.ID_OPERATOR_REAL2VECT,
            400,
            -300,
        )
        r_negate_x_node = self.create_xpresso_node(
            node_master,
            c4d.ID_OPERATOR_NEG,
            300,
            -100,
        )
        r_negate_y_node = self.create_xpresso_node(
            node_master,
            c4d.ID_OPERATOR_NEG,
            300,
            -100,
        )
        r_negate_z_node = self.create_xpresso_node(
            node_master,
            c4d.ID_OPERATOR_NEG,
            300,
            -100,
        )
        l_negate_x_node = self.create_xpresso_node(
            node_master,
            c4d.ID_OPERATOR_NEG,
            300,
            -200,
        )
        l_negate_y_node = self.create_xpresso_node(
            node_master,
            c4d.ID_OPERATOR_NEG,
            300,
            -200,
        )
        l_negate_z_node = self.create_xpresso_node(
            node_master,
            c4d.ID_OPERATOR_NEG,
            300,
            -200,
        )
        face_r_eye.Connect(r_vec_to_real.GetInPorts()[0])
        face_l_eye.Connect(l_vec_to_real.GetInPorts()[0])

        r_vec_to_real.GetOutPorts()[0].Connect(r_negate_x_node.GetInPorts()[0])
        r_negate_x_node.GetOutPorts()[0].Connect(r_real_to_vect.GetInPorts()[1])
        r_vec_to_real.GetOutPorts()[1].Connect(r_negate_y_node.GetInPorts()[0])
        r_negate_y_node.GetOutPorts()[0].Connect(r_real_to_vect.GetInPorts()[0])
        r_vec_to_real.GetOutPorts()[2].Connect(r_negate_z_node.GetInPorts()[0])
        r_negate_z_node.GetOutPorts()[0].Connect(r_real_to_vect.GetInPorts()[2])

        l_vec_to_real.GetOutPorts()[0].Connect(l_negate_x_node.GetInPorts()[0])
        l_negate_x_node.GetOutPorts()[0].Connect(l_real_to_vect.GetInPorts()[1])
        l_vec_to_real.GetOutPorts()[1].Connect(l_negate_y_node.GetInPorts()[0])
        l_negate_y_node.GetOutPorts()[0].Connect(l_real_to_vect.GetInPorts()[0])
        l_vec_to_real.GetOutPorts()[2].Connect(l_negate_z_node.GetInPorts()[0])
        l_negate_z_node.GetOutPorts()[0].Connect(l_real_to_vect.GetInPorts()[2])

        r_real_to_vect.GetOutPorts()[0].Connect(r_eye_rot)
        l_real_to_vect.GetOutPorts()[0].Connect(l_eye_rot)

    def create_tracking_xpresso(self, skeleton):
        xpresso_tag = c4d.BaseTag(c4d.Texpresso)
        # Set Tag priority to Animation
        pd = xpresso_tag[c4d.EXPRESSION_PRIORITY]
        pd.SetPriorityValue(c4d.PRIORITYVALUE_MODE, 1)
        xpresso_tag[c4d.EXPRESSION_PRIORITY] = pd
        xpresso_tag[c4d.ID_BASELIST_NAME] = "Movement Tracking"
        skeleton.InsertTag(xpresso_tag)
        return xpresso_tag

    def get_tracking_xpresso(self, skeleton):
        xpresso_tag = skeleton.GetTag(c4d.Texpresso)
        if xpresso_tag:
            return xpresso_tag
        else:
            xpresso_tag = self.create_tracking_xpresso(skeleton)
            return xpresso_tag

    def add_head_tracking(self, face_capture):
        var = Variables()
        var.restore_variables()
        doc = c4d.documents.GetActiveDocument()
        ctrl = self.find_which_neck(var.c_joints)

        if ctrl:
            xpresso_tag = self.get_tracking_xpresso(var.skeleton)
            node_master = xpresso_tag.GetNodeMaster()
            head_node = self.create_node(node_master, ctrl, 600, 0)
            face_node = self.create_node(node_master, face_capture, 0, 0)
            vec_to_real = self.create_xpresso_node(
                node_master,
                c4d.ID_OPERATOR_VECT2REAL,
                200,
                0,
            )
            real_to_vect = self.create_xpresso_node(
                node_master,
                c4d.ID_OPERATOR_REAL2VECT,
                400,
                0,
            )
            math_x_node = self.create_xpresso_node(
                node_master,
                c4d.ID_OPERATOR_MATH,
                300,
                0,
            )
            negate_y_node = self.create_xpresso_node(
                node_master,
                c4d.ID_OPERATOR_NEG,
                300,
                0,
            )
            negate_z_node = self.create_xpresso_node(
                node_master,
                c4d.ID_OPERATOR_NEG,
                300,
                0,
            )
            face_pos = face_node.AddPort(
                c4d.GV_PORT_OUTPUT,
                c4d.DescID(c4d.DescLevel(c4d.FACECAPTURE_MATRIX_FACE_POSITION)),
            )
            face_rot = face_node.AddPort(
                c4d.GV_PORT_OUTPUT,
                c4d.DescID(c4d.DescLevel(c4d.FACECAPTURE_MATRIX_FACE_ROTATION)),
            )
            head_pos = head_node.AddPort(
                c4d.GV_PORT_INPUT,
                c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_REL_POSITION)),
            )

            head_rot = head_node.AddPort(
                c4d.GV_PORT_INPUT,
                c4d.DescID(c4d.DescLevel(c4d.ID_BASEOBJECT_REL_ROTATION)),
            )
            face_rot.Connect(vec_to_real.GetInPorts()[0])
            math_x_node.SetParameter(
                self.math_input_desc_id, -1 * math.pi, c4d.DESCFLAGS_SET_0
            )
            vec_to_real.GetOutPorts()[0].Connect(math_x_node.GetInPorts()[1])
            math_x_node.GetOutPorts()[0].Connect(real_to_vect.GetInPorts()[1])
            vec_to_real.GetOutPorts()[1].Connect(negate_y_node.GetInPorts()[0])
            negate_y_node.GetOutPorts()[0].Connect(real_to_vect.GetInPorts()[0])
            vec_to_real.GetOutPorts()[2].Connect(negate_z_node.GetInPorts()[0])
            negate_z_node.GetOutPorts()[0].Connect(real_to_vect.GetInPorts()[2])

            real_to_vect.GetOutPorts()[0].Connect(head_rot)
            # face_pos.Connect(head_pos)

    def find_facial_morph(self, face_capture, morph_name):
        description = face_capture.GetDescription(c4d.DESCFLAGS_DESC_0)
        for bc, paramid, groupid in description:
            name = bc[c4d.DESC_NAME]
            if set(name.split(" ")) == set(morph_name.split(" ")):
                return paramid

    def connect_face_morphs(self, morphs, face_capture):
        """Connects to the Move By Maxon Animation"""
        doc = c4d.documents.GetActiveDocument()
        xpresso_tag = morphs.GetTag(c4d.Texpresso)
        node_master = xpresso_tag.GetNodeMaster()
        morph_node = self.create_node(node_master, morphs, -1000, 100)
        facial_node = self.create_node(node_master, face_capture, -1200, 100)
        for desc_id, bc in morphs.GetUserDataContainer():
            morph_name = bc.GetString(c4d.DESC_NAME)
            face_capture_id = self.find_facial_morph(face_capture, morph_name)
            if not face_capture_id:
                continue
            facial_output = facial_node.AddPort(c4d.GV_PORT_OUTPUT, face_capture_id)
            morph_input = morph_node.AddPort(c4d.GV_PORT_INPUT, desc_id)
            facial_output.Connect(morph_input)

    @staticmethod
    def disconnect_face_morphs(face_node, morph_node):
        """Remove the Connection to the Move By Maxon Animation"""
        face_node.Remove()
        morph_node.Remove()
        c4d.gui.MessageDialog(
            "Face Capture Has been Successfully Removed!", type=c4d.GEMB_OK
        )
