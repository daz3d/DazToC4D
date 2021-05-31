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
