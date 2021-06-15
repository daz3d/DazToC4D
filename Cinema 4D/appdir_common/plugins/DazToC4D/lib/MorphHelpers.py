import c4d
from c4d import documents

from . import ErcExpressions as erc
from collections import OrderedDict


class MorphHelpers:
    math_input_desc_id = c4d.DescID(
        c4d.DescLevel(2000, c4d.DTYPE_SUBCONTAINER, 0),
        c4d.DescLevel(1000, c4d.DTYPE_DYNAMIC, 0),
    )
    math_real_input_desc_id = c4d.DescID(
        c4d.DescLevel(c4d.GV_MATH_INPUT, c4d.ID_GV_DATA_TYPE_REAL, 400001121)
    )
    pose_morph_str_desc_id = c4d.DescID(
        c4d.DescLevel(c4d.ID_CA_POSE_ANIMATE_DATA),
        c4d.DescLevel(1101),
    )
    python_real_input_desc_id = c4d.DescID(
        c4d.DescLevel(c4d.IN_REAL, c4d.ID_GV_DATA_TYPE_REAL, 1022471)
    )
    morph_links = dict()
    body_xpresso_tag = None
    morph_controller = None
    ctrl_xpresso_tag = None

    def store_variables(self, body, meshes, joints, skeleton, poses):
        self.body = body
        self.body_name = body.GetName()
        self.meshes = meshes
        self.joints = joints
        self.skeleton = skeleton
        self.skeleton_name = skeleton.GetName()
        self.poses = poses

    def store_morph_links(self, dtu):
        """
        Pass the Morph Links to be used for the current import
        """
        self.morph_links = dtu.get_morph_links_dict()

    def find_morph_link(self, morph_name):
        original_morph_name = self.clean_name(morph_name)
        if original_morph_name not in self.morph_links.keys():
            return
        return self.morph_links[original_morph_name]

    def clean_name(self, morph_name):
        if morph_name.startswith(self.skeleton_name + "__"):
            morph_name = morph_name[len(self.skeleton_name + "__") :]
            return morph_name
        for obj in self.meshes:
            prefix = obj.GetName().replace(".Shape", "") + "__"
            if morph_name.startswith(prefix):
                morph_name = morph_name[len(prefix) :]
                return morph_name
        return morph_name

    def reorder_morph_list(self, pm_tag):
        morph_amount = pm_tag.GetMorphCount()
        morph_keys = {}
        morph_indices = []
        for x in range(morph_amount):
            pm_tag.SetActiveMorphIndex(x)
            morph = pm_tag.GetActiveMorph()
            morph_name = morph.GetName()
            if "Default:" in morph_name:
                continue
            morph_link = self.find_morph_link(morph_name)
            if not morph_link:
                print("{0} Connections Could not be found ...".format(morph_name))
                continue
            morph_keys[morph_link["Label"]] = x
        sorted_morphs = OrderedDict(sorted(morph_keys.items()))
        for i in sorted_morphs:
            morph_indices.append(sorted_morphs[i])
        return morph_indices

    def find_body_xpresso_tag(self, obj):
        """Find Body Xpresso Tag"""
        if not self.body_xpresso_tag:
            self.create_body_xpresso_tag(obj)
        return self.body_xpresso_tag

    def create_body_xpresso_tag(self, obj):
        """Create the Body Xpresso Tag"""
        xtag = c4d.BaseTag(c4d.Texpresso)
        # Set Tag priority to Animation
        pd = xtag[c4d.EXPRESSION_PRIORITY]
        pd.SetPriorityValue(c4d.PRIORITYVALUE_MODE, 1)
        xtag[c4d.EXPRESSION_PRIORITY] = pd
        xtag[c4d.ID_BASELIST_NAME] = "{0} Xpresso Tag".format(self.body_name)
        obj.InsertTag(xtag)
        self.body_xpresso_tag = xtag

    def create_ctrl_null(self):
        doc = documents.GetActiveDocument()
        null = c4d.BaseObject(c4d.Onull)  # Create new null
        doc.InsertObject(null)
        c4d.EventAdd()
        null.SetName("{0} Morph Controller Group".format(self.skeleton_name))
        self.morph_controller = null

    def find_ctrl_null(self):
        if not self.morph_controller:
            self.create_ctrl_null
        return self.morph_controller

    def find_ctrl_xpresso_tag(self):
        """Find Morph Ctrl Xpresso Tag"""
        if not self.morph_controller:
            self.create_ctrl_null()
        if not self.ctrl_xpresso_tag:
            self.create_ctrl_xpresso_tag()
        return self.ctrl_xpresso_tag

    def create_ctrl_xpresso_tag(self):
        """Create the Morph Ctrl Xpresso Tag"""
        xtag = c4d.BaseTag(c4d.Texpresso)
        # Set Tag priority to Animation
        pd = xtag[c4d.EXPRESSION_PRIORITY]
        pd.SetPriorityValue(c4d.PRIORITYVALUE_MODE, 1)
        xtag[c4d.EXPRESSION_PRIORITY] = pd
        xtag[c4d.ID_BASELIST_NAME] = "{0} Xpresso Tag".format(self.skeleton_name)
        self.morph_controller.InsertTag(xtag)
        self.ctrl_xpresso_tag = xtag

    def find_joint(self, joint_name):
        """Check if Joint Exists in Scene"""
        for joint in self.joints:
            if joint.GetName() == joint_name:
                return joint

    def prepare_pos(self, amount):
        if amount == 1:
            return [100]
        total = (100 * amount) / (100 + amount)
        options = []
        for i in range(amount):
            options.append(i * total)
        return options

    def create_node(self, node_parent, tag, x, y):
        node = node_parent.CreateNode(
            node_parent.GetRoot(), c4d.ID_OPERATOR_OBJECT, None, x, y
        )
        node[c4d.GV_OBJECT_OBJECT_ID] = tag
        return node

    def create_xpresso_node(self, node_parent, type, x, y):
        node = node_parent.CreateNode(node_parent.GetRoot(), type, None, x, y)
        return node

    def connect_morph_nodes(
        self, node_master, par_output, child_node, child_id, morph_name
    ):
        child_input = child_node.AddPort(c4d.GV_PORT_INPUT, child_id)
        c4d.modules.graphview.RedrawMaster(node_master)
        par_output.Connect(child_input)

    def find_user_data_by_name(self, obj, name):
        for user_data_id, bc in obj.GetUserDataContainer():
            current_name = bc.GetString(c4d.DESC_NAME)
            if current_name == name:
                return user_data_id

    def find_vector(self, prop):
        """Finds the Vector needed for Joint
        Args:
            prop (str): Property in Morph_links rotation value that drives the morph

        Returns:
            The Attributes for the Rotation/Translation
        """
        if "YRotate" == prop:
            return c4d.VECTOR_Y, c4d.ID_BASEOBJECT_ROTATION
        if "ZRotate" == prop:
            return c4d.VECTOR_Z, c4d.ID_BASEOBJECT_ROTATION
        if "XRotate" == prop:
            return c4d.VECTOR_X, c4d.ID_BASEOBJECT_ROTATION
        if "YTranslate" == prop:
            return c4d.VECTOR_Y, c4d.ID_BASEOBJECT_POSITION
        if "ZTranslate" == prop:
            return c4d.VECTOR_Z, c4d.ID_BASEOBJECT_POSITION
        if "XTranslate" == prop:
            return c4d.VECTOR_X, c4d.ID_BASEOBJECT_POSITION

    def check_conversion(self, prop):
        """Returns the Value to take into account C4D being Right-Handed and Daz Being Left-Handed
        Args:
            prop (str): Property in Morph_links rotation value that drives the morph
        """
        if "YRotate" == prop:
            return 1
        if "ZRotate" == prop:
            return -1
        if "XRotate" == prop:
            return 1
        if "YTranslate" == prop:
            return 1
        if "ZTranslate" == prop:
            return -1
        if "XTranslate" == prop:
            return 1
        else:
            return 1

    def check_sub_links(self, sublinks):
        """Verify which links should be evaluted and have nodes created
        Args:
            sublinks (list): sublinks that move the bone transforms from the morph

        Returns:
            new_links (list):
        """
        new_links = []
        if len(sublinks) == 0:
            return []

        possible_links = [
            "XRotate",
            "YRotate",
            "ZRotate",
            "XTranslate",
            "YTranslate",
            "ZTranslate",
        ]
        for link in sublinks:
            prop = link["Property"]
            joint_name = link["Bone"]
            if not self.find_joint(joint_name):
                continue
            if not prop in possible_links:
                continue
            new_links.append(link)

        return new_links

    def check_links(self, links):
        """Verify which links should be evaluted and have nodes created

        Args:
            links (list): All the morphs that control the morph in Daz

        Returns:
            new_links (list):
        """
        new_links = []
        if len(links) == 0:
            return []
        for link in links:
            prop = link["Property"]
            joint_name = link["Bone"]
            morph_check = self.find_morph_link(prop)
            if morph_check == None:
                if not prop.endswith("Rotate"):
                    continue
                elif joint_name == "None":
                    continue
            new_links.append(link)

        return new_links

    def find_morph_id(self, morph_tag_main, morph_tag_slave, x):
        """Find DescID for parent and child

        Args:
            morph_tag_main (CAPoseMorphTag): Morph Tag for Main Body-
            morph_tag_slave (CAPoseMorphTag): Morph Tag for Children Shapes
            x (int):

        Returns:
            list [DescID, DescID]: DescID Representation for current morph
        """
        morph_main = morph_tag_main.GetMorph(x).GetName()
        clean_main = self.clean_name(morph_main)
        morph_num = morph_tag_main.GetMorphID(x)
        for index in range(morph_tag_slave.GetMorphCount()):
            morph_slave = morph_tag_slave.GetMorph(index).GetName()
            clean_slave = self.clean_name(morph_slave)
            if clean_main == clean_slave:
                return morph_num, morph_tag_slave.GetMorphID(index)
        return 0, 0

    def find_morph_id_by_name(self, morph_tag, morph_name):
        """Find DescID from Morph Name

        Args:
            morph_tag (CAPoseMorphTag)
            morph_name (str)
        """
        for index in range(morph_tag.GetMorphCount()):
            current_morph = morph_tag.GetMorph(index).GetName()
            original_name = self.clean_name(current_morph)
            if morph_name == original_name:
                return morph_tag.GetMorphID(index)
        return

    def get_expression(self, link, x, sublink=False):
        """Selects the expression based on the ErcType
        Args:
            link (list): Information for one of the Bones/Morphs that Drives the output
            x (int): the variable number

        Returns:
            expression (str): the represenation of this link to be added to the python node
        """
        erc_type = link["Type"]
        scalar = link["Scalar"]
        addend = link["Addend"]
        bone = link["Bone"]
        prop = link["Property"]
        expression = ""
        direction = str(self.check_conversion(prop))
        var = erc.erc_var(bone, direction, prop, sublink)
        if erc_type == 0:
            # ERCDeltaAdd
            expression = erc.erc_delta_add(scalar, addend, x, var)
        elif erc_type == 1:
            # ERCDivideInto
            expression = erc.erc_divide_into(addend, x, var)
        elif erc_type == 2:
            # ERCDivideBy
            expression = erc.erc_divide_by(addend, x, var)
        elif erc_type == 3:
            # ERCMultiply
            expression = erc.erc_multiply(addend, x, var)
        elif erc_type == 4:
            # ERCSubtract
            expression - erc.erc_subtract(addend, x, var)
        elif erc_type == 5:
            # ERCAdd
            expression = erc.erc_add(addend, x, var)
        elif erc_type == 6:
            # ERCKeyed
            keyed = link["Keys"]
            # Currently Skip the 3rd Key if Key 0 has two
            for i in range(len(keyed)):
                key = list(keyed)[i]
                if keyed[key]["Value"] == 0:
                    if len(keyed) > (i + 1):
                        next_key = list(keyed)[i + 1]
                        if (
                            (len(keyed) != 2)
                            and (keyed[next_key]["Value"] == 0)
                            and (keyed[next_key]["Rotate"] == 0)
                        ):
                            continue
                    key_0 = str(keyed[key]["Rotate"])
                if keyed[key]["Value"] == 1:
                    key_1 = str(keyed[key]["Rotate"])
            dist = str((float(key_1) - float(key_0)))
            norm_dist = str((1 - 0))
            expression = erc.erc_keyed(dist, key_1, key_0, norm_dist, x, var)

        return expression
