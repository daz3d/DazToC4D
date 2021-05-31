import c4d
from . import Utilities


class Tracking:
    @staticmethod
    def create_node(node_parent, obj, x, y):
        node = node_parent.CreateNode(
            node_parent.GetRoot(), c4d.ID_OPERATOR_OBJECT, None, x, y
        )
        node[c4d.GV_OBJECT_OBJECT_ID] = obj
        return node

    @staticmethod
    def create_xpresso_node(node_parent, type, x, y):
        node = node_parent.CreateNode(node_parent.GetRoot(), type, None, x, y)
        return node

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

    @staticmethod
    def find_facial_morph(face_morph_tag, morph_name):
        morph_amount = face_morph_tag.GetMorphCount()
        for x in range(morph_amount):
            face_morph_tag.SetActiveMorphIndex(x)
            morph = face_morph_tag.GetActiveMorph()
            face_morph_name = morph.GetName()
            if set(face_morph_name.split(" ")) == set(morph_name.split(" ")):
                return face_morph_tag.GetMorphID(x)

    @staticmethod
    def connect_face_morphs(face_capture):
        """Connects to the Move By Maxon Animation"""
        doc = c4d.documents.GetActiveDocument()
        morph_obj = doc.SearchObject("Daz Morphs Controller")
        morph_tag = morph_obj.GetTag(c4d.Tposemorph)
        face_morph_tag = face_capture.GetTag(c4d.Tposemorph)
        xpresso_tag = morph_obj.GetTag(c4d.Texpresso)
        node_master = xpresso_tag.GetNodeMaster()
        morph_master_output = Tracking.create_node(node_master, morph_tag, -1000, 100)
        facial_node = Tracking.create_node(node_master, face_morph_tag, -1200, 100)
        if morph_tag:
            morph_amount = morph_tag.GetMorphCount()
            for x in range(morph_amount):
                morph_tag.SetActiveMorphIndex(x)
                morph = morph_tag.GetActiveMorph()
                morph_name = morph.GetName()
                blend_shape = Tracking.find_facial_morph(face_morph_tag, morph_name)
                if blend_shape:
                    morph_num = morph_tag.GetMorphID(x)
                    morph_input = morph_master_output.AddPort(
                        c4d.GV_PORT_INPUT, morph_num
                    )
                    facial_output = facial_node.AddPort(c4d.GV_PORT_OUTPUT, blend_shape)
                    facial_output.Connect(morph_input)

            return morph_master_output, facial_node

    @staticmethod
    def disconnect_face_morphs(face_node, morph_node):
        """Remove the Connection to the Move By Maxon Animation"""
        face_node.Remove()
        morph_node.Remove()
        c4d.gui.MessageDialog(
            "Face Capture Has been Successfully Removed!", type=c4d.GEMB_OK
        )
