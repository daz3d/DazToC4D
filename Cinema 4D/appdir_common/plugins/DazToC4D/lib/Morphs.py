from ntpath import join
import c4d
from c4d import utils, documents

from .CustomIterators import TagIterator
from . import ErcExpressions as erc


class Morphs:
    def __init__(self):
        self.morph_links = dict()
        self.stored_outputs = dict()
        self.nodes = dict()

    @staticmethod
    def create_null_for_morphs(body):
        doc = documents.GetActiveDocument()
        null = c4d.BaseObject(c4d.Onull)  # Create new null
        doc.InsertObject(null)
        c4d.EventAdd()
        null.SetName("Daz Morphs Controller")
        morph_tag = body.GetTag(c4d.Tposemorph)
        xpresso_tag = body.GetTag(c4d.Texpresso)
        null.InsertTag(morph_tag)
        null.InsertTag(xpresso_tag)
        c4d.EventAdd()
        return null

    def store_morph_links(self, dtu):
        """
        Pass the Morph Links to be used for the current import
        """
        self.morph_links = dtu.get_morph_links_dict()

    def store_variables(self, body, children, joints):
        self.body = body
        self.body_name = body.GetName()
        self.children = children
        self.joints = joints

    def find_morph_link(self, morph_name):
        split = morph_name.split("__")
        if len(split) != 2:
            if morph_name not in self.morph_links.keys():
                return
            return self.morph_links[morph_name]

        original_morph_name = split[1]
        if original_morph_name not in self.morph_links.keys():
            return
        return self.morph_links[original_morph_name]

    def clean_name(self, morph_name):
        split = morph_name.split("__")
        if len(split) != 2:
            return morph_name
        return split[1]

    def delete_morphs(self, c_meshes, c_morphs):
        """
        Deletes the Morphs that don't have the Bone Controlling it or Alias in Daz
        """
        obj_remove = []
        for obj in c_meshes:
            # Delete Tag
            pm_remove = []
            pm_tag = obj.GetTag(c4d.Tposemorph)
            if pm_tag:
                morph_amount = pm_tag.GetMorphCount()
                for x in range(morph_amount):
                    pm_tag.SetActiveMorphIndex(x)
                    morph_name = pm_tag.GetActiveMorph().GetName()
                    if "Default:" in morph_name:
                        continue
                    morph_link = self.find_morph_link(morph_name)
                    if morph_link == None:
                        continue
                    control_meshes = morph_link["Controlled Meshes"]
                    if obj.GetName() in control_meshes:
                        continue
                    pm_remove.append(x)
                    obj_remove.append(morph_name)
                for i in reversed(pm_remove):
                    pm_tag.RemoveMorph(i)
                if pm_tag.GetMorphCount() == 1:
                    pm_tag.Remove()
        for obj in c_morphs:
            if "Default:" in obj.GetName():
                continue
            morph_name = obj.GetName()
            if morph_name in obj_remove:
                obj.Remove()

    def rename_morphs(self, c_meshes):
        """
        Renames morphs based on the labels in Daz Studio
        """
        for ob in c_meshes:
            pmTag = ob.GetTag(c4d.Tposemorph)  # Gets the pm tag
            if pmTag:
                morphsAmount = len(list(range(pmTag.GetMorphCount())))
                for x in range(0, morphsAmount):
                    pmTag.SetActiveMorphIndex(x)
                    morph_name = pmTag.GetActiveMorph().GetName()
                    morph_link = self.find_morph_link(morph_name)
                    if morph_link == None:
                        continue
                    morph_label = morph_link["Label"]
                    pmTag.GetActiveMorph().SetName(morph_label)

    def store_node(self, obj, value, key):
        if not obj.GetName() in self.nodes.keys():
            self.nodes[obj.GetName()] = {}
        self.nodes[obj.GetName()][key] = value

    def store_morph(self, obj, value, key, morph):
        if isinstance(morph, str):
            morph_name = morph
            morph_name = self.clean_name(morph_name)
        else:
            morph_name = self.clean_name(morph.GetName())
        if not morph_name in self.nodes.keys():
            self.store_node(obj, {}, morph_name)
        self.nodes[obj.GetName()][morph_name][key] = value

    def prepare_pos(self, amount):
        if amount == 1:
            return [100]
        total = (100 * amount) / (100 + amount)
        options = []
        for i in range(amount):
            options.append(i * total)
        return options

    def connect_morphs_to_parents(self, body, c_meshes):
        par_tag = self.find_objects_morph_tag(body)
        xtag = self.find_daz_xpresso_tag(body)
        if xtag == None:
            self.create_daz_xpresso_tag(body)
            xtag = self.find_daz_xpresso_tag(body)
        node_master = xtag.GetNodeMaster()
        self.morph_master_node = self.create_node(node_master, par_tag, 50, 100)
        self.store_node(body, self.morph_master_node, "Node")
        self.store_node(body, par_tag, "Pose Tag")
        options = self.prepare_pos(len(c_meshes) - 1)
        for index, obj in enumerate(c_meshes):
            if obj.GetName() == body.GetName():
                continue
            child_tag = self.find_objects_morph_tag(obj)
            child_node = self.create_node(
                node_master, child_tag, 500, options[index - 1]
            )
            self.store_node(obj, child_node, "Node")
            if not child_tag == None:
                self.connect_morphs_xpresso(
                    par_tag, child_tag, node_master, self.morph_master_node, child_node
                )

    def connect_morphs_xpresso(
        self, par_tag, child_tag, node_master, par_node, child_node
    ):
        for x in range(1, par_tag.GetMorphCount()):
            parent_id, child_id = self.find_morph_id(par_tag, child_tag, x)
            if isinstance(child_id, int):
                continue
            morph_name = par_tag.GetMorph(x).GetName()
            correct_name = self.clean_name(morph_name)
            par_output = par_node.AddPort(c4d.GV_PORT_OUTPUT, parent_id)
            if par_output is None:
                par_output = self.nodes[self.body_name][correct_name]["Output"]
            self.connect_morph_nodes(
                node_master, par_output, child_node, child_id, morph_name
            )
            self.store_morph(self.body, par_output, "Output", correct_name)
        c4d.EventAdd()

    def connect_morph_nodes(
        self, node_master, par_output, child_node, child_id, morph_name
    ):
        child_input = child_node.AddPort(c4d.GV_PORT_INPUT, child_id)
        self.store_morph(self.body, child_input, "Input", morph_name)
        c4d.modules.graphview.RedrawMaster(node_master)
        par_output.Connect(child_input)

    def create_node(self, node_parent, tag, x, y):
        node = node_parent.CreateNode(
            node_parent.GetRoot(), c4d.ID_OPERATOR_OBJECT, None, x, y
        )
        node[c4d.GV_OBJECT_OBJECT_ID] = tag
        return node

    def create_xpresso_node(self, node_parent, type, x, y):
        node = node_parent.CreateNode(node_parent.GetRoot(), type, None, x, y)
        return node

    def add_drivers(self):
        """Creates the drivers that will control all the morphs on the main body."""
        pm_tag = self.body.GetTag(c4d.Tposemorph)
        if pm_tag:
            morph_amount = pm_tag.GetMorphCount()
            xtag = self.find_daz_xpresso_tag(self.body)
            if xtag is None:
                self.create_daz_xpresso_tag(self.body)
                xtag = self.find_daz_xpresso_tag(self.body)
            node_master = xtag.GetNodeMaster()
            self.morph_master_output = self.create_node(node_master, pm_tag, -500, 100)
            pos = self.prepare_pos(morph_amount)
            for x in range(morph_amount):
                pm_tag.SetActiveMorphIndex(x)
                morph = pm_tag.GetActiveMorph()
                morph_name = morph.GetName()
                if "Default:" in morph_name:
                    continue
                morph_link = self.find_morph_link(morph_name)
                links = morph_link["Links"]
                new_links = self.check_links(links)
                if len(new_links) == 0:
                    continue
                python_node = self.create_xpresso_node(
                    node_master,
                    1022471,
                    -100,
                    pos[x],
                )
                clean_name = self.clean_name(morph_name)
                morph_num = pm_tag.GetMorphID(x)
                morph_input = self.morph_master_node.AddPort(
                    c4d.GV_PORT_INPUT, morph_num
                )
                morph_output = self.morph_master_output.AddPort(
                    c4d.GV_PORT_OUTPUT, morph_num
                )
                if morph_input == None:
                    morph_input = self.nodes[self.body_name][clean_name]["Input"]
                if morph_output == None:
                    morph_output = self.nodes[self.body_name][clean_name]["Output2"]
                self.store_morph(self.body, morph_input, "Input", clean_name)
                self.store_morph(self.body, morph_output, "Output2", clean_name)
                for python_output in python_node.GetOutPorts():
                    python_output.Connect(morph_input)

                for i in range(len(new_links) + 1):
                    expression = erc.erc_start()
                    real_id = c4d.DescID(
                        c4d.DescLevel(c4d.IN_REAL, c4d.ID_GV_DATA_TYPE_REAL, 1022471)
                    )
                    python_node.AddPort(c4d.GV_PORT_INPUT, real_id)

                for index, link in enumerate(new_links):
                    driver_output = self.get_driver_output(
                        link, node_master, -300, pos[x], pm_tag
                    )
                    python_inputs = python_node.GetInPorts()
                    python_inputs[0].SetName("current")
                    morph_output.Connect(python_inputs[0])
                    for python_input in python_node.GetInPorts():
                        current_name = python_input.GetName(python_node)
                        if current_name == "current":
                            continue
                        if not current_name.startswith("var"):
                            python_input.SetName("var" + str(index + 1))
                            driver_output.Connect(python_input)
                            break
                    expression += self.get_expression(link, str(index + 1))
                    expression += erc.erc_limits(
                        str(morph_link["Minimum"]), str(morph_link["Maximum"])
                    )
                # Add Expression
                python_node[c4d.GV_PYTHON_CODE] = expression

    def get_expression(self, link, x):
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
        var = erc.erc_var(bone, direction)
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

    def get_driver_output(self, link, node_master, x, y, pm_tag):
        """Check which type of link it is a creates node and Output based on it

        Args:
            link (list): Information for one of the Bones/Morphs that Drives the output
            node_master (c4d.modules.graphview.GvNodeMaster):
                        represents the parent used for the Xpresso Group
            x (int): Horizontal Position of Node
            y (int): Vertical Position of Node

        Returns:
            driver_output (c4d.modules.graphview.GvPort): Output to connect to Python Node
        """
        joint_name = link["Bone"]
        prop = link["Property"]
        if joint_name != "None":
            # Create Joint Driver
            vector = self.find_vector(prop)
            joint = self.find_joint(joint_name)
            descid = c4d.DescID(
                c4d.DescLevel(c4d.ID_BASEOBJECT_ROTATION, 0, 0),
                c4d.DescLevel(vector, 0, 0),
            )
            driver_node = self.create_node(node_master, joint, x, y)
            driver_output = driver_node.AddPort(c4d.GV_PORT_OUTPUT, descid)
        else:
            morph_num = self.find_morph_id_by_name(pm_tag, prop)
            driver_output = self.morph_master_output.AddPort(
                c4d.GV_PORT_OUTPUT, morph_num
            )
            if driver_output is None:
                driver_output = self.nodes[self.body_name][prop]["Output2"]
            self.store_morph(self.body, driver_output, "Output2", prop)
        return driver_output

    def find_vector(self, prop):
        """Finds the Vector needed for Joint
        Args:
            prop (str): Property in Morph_links rotation value that drives the morph
        """
        if "YRotate" == prop:
            return c4d.VECTOR_Y
        if "ZRotate" == prop:
            return c4d.VECTOR_Z
        if "XRotate" == prop:
            return c4d.VECTOR_X

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
        else:
            return 1

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

    def find_joint(self, joint_name):
        """Check if Joint Exists in Scene"""
        for joint in self.joints:
            if joint.GetName() == joint_name:
                return joint

    def find_objects_morph_tag(self, obj):
        """Find Pose Morph Tag"""
        obj_tags = TagIterator(obj)
        for t in obj_tags:
            if "Morph" in t.GetName():
                return t

    def find_daz_xpresso_tag(self, obj):
        """Find Daz Xpresso Tag"""
        obj_tags = TagIterator(obj)
        for t in obj_tags:
            if "DazToC4D Morphs Connect" in t.GetName():
                return t

    def create_daz_xpresso_tag(self, obj):
        """Create the Daz Xpresso Tag"""
        xtag = c4d.BaseTag(c4d.Texpresso)
        # Set Tag priority to Animation
        pd = xtag[c4d.EXPRESSION_PRIORITY]
        pd.SetPriorityValue(c4d.PRIORITYVALUE_MODE, 1)
        xtag[c4d.EXPRESSION_PRIORITY] = pd
        xtag[c4d.ID_BASELIST_NAME] = "DazToC4D Morphs Connect"
        obj.InsertTag(xtag)

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
            split = current_morph.split("__")
            if len(split) > 1:
                original_name = split[1]
            else:
                original_name = current_morph
            if morph_name == original_name:
                return morph_tag.GetMorphID(index)
        return
