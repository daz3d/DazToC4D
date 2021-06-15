import c4d
from . import Utilities
from .MorphHelpers import MorphHelpers


class Tracking(MorphHelpers):
    @staticmethod
    def add_head_tracking(face_capture):
        """Need to removed Hardcoding of Neck_Ctrl"""
        neck_name = Utilities.get_daz_name() + "_Neck_ctrl"
        doc = c4d.documents.GetActiveDocument()
        neck_ctrl = doc.SearchObject(neck_name)
        if neck_ctrl:
            xpresso_tag = c4d.BaseTag(c4d.Texpresso)
            # Set Tag priority to Animation
            pd = xpresso_tag[c4d.EXPRESSION_PRIORITY]
            pd.SetPriorityValue(c4d.PRIORITYVALUE_MODE, 1)
            xpresso_tag[c4d.EXPRESSION_PRIORITY] = pd
            xpresso_tag[c4d.ID_BASELIST_NAME] = "Movement Tracking"
            neck_ctrl.InsertTag(xpresso_tag)
            node_master = xpresso_tag.GetNodeMaster()
            neck_node = Tracking.create_node(node_master, neck_ctrl, 600, 0)
            face_node = Tracking.create_node(node_master, face_capture, 0, 0)
            vect_real = Tracking.create_xpresso_node(
                node_master, c4d.GV_VECT2REAL_, 100, 0
            )
            degrees_to_rad = Tracking.create_xpresso_node(
                node_master, c4d.GV_DEGREE_, 200, 0
            )
            degrees_to_rad[c4d.GV_DEGREE_FUNCTION_ID] = c4d.GV_DEGREE2RAD_NODE_FUNCTION
            math_node = Tracking.create_xpresso_node(node_master, c4d.GV_MATH_, 300, 0)
            rad_to_degrees = Tracking.create_xpresso_node(
                node_master, c4d.GV_DEGREE_, 400, 0
            )
            degrees_to_rad[c4d.GV_DEGREE_FUNCTION_ID] = c4d.GV_RAD2DEGREE_NODE_FUNCTION

    def find_facial_morph(self, face_capture, morph_name):
        description = face_capture.GetDescription(c4d.DESCFLAGS_DESC_0)
        for bc, paramid, groupid in description:
            name = bc[c4d.DESC_NAME]
            print(name, paramid, morph_name)
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
