import c4d

from . import ErcExpressions as erc
from .MorphHelpers import MorphHelpers


class Morphs(MorphHelpers):
    def __init__(self):
        self.stored_outputs = dict()
        self.nodes = dict()
        self.morph_ctrl_user_data = dict()
        self.ctrl_sliders_output = dict()
        self.ctrl_sliders_input = dict()
        self.morph_to_joints_nodes = dict()
        self.math_to_joints_nodes = dict()

    def morphs_to_delta(self):
        """
        Convert Morphs to Delta Morphs
        """
        doc = c4d.documents.GetActiveDocument()
        for obj in self.meshes:
            morph_names = []
            pm_remove = []
            pm_tag = obj.GetTag(c4d.Tposemorph)
            pm_tag.ExitEdit(doc, True)
            if pm_tag:
                morph_amount = pm_tag.GetMorphCount()
                for x in range(morph_amount):
                    pm_tag.SetActiveMorphIndex(x)
                    morph_name = pm_tag.GetActiveMorph().GetName()
                    if "Default:" in morph_name:
                        continue
                    morph_names.append(morph_name)
                    pm_remove.append(x)
                for i in reversed(pm_remove):
                    pm_tag.RemoveMorph(i)
                pm_tag[c4d.ID_CA_POSE_POINTS] = True
                for pose in self.poses:
                    for morph_obj in pose.GetChildren():
                        if morph_obj.GetName() in morph_names:
                            morph = pm_tag.AddMorph()
                            morph.SetName(morph_obj.GetName())
                            count = pm_tag.GetMorphCount()
                            pm_tag.SetActiveMorphIndex(count - 1)
                            # Set Data to Absolute and link to our obj
                            pm_tag[c4d.ID_CA_POSE_MIXING] = c4d.ID_CA_POSE_MIXING_ABS
                            pm_tag[c4d.ID_CA_POSE_TARGET] = morph_obj

                            # Store the point data in the morph node
                            morph.Store(doc, pm_tag, c4d.CAMORPH_DATA_FLAGS_POINTS)
                            morph.Apply(doc, pm_tag, c4d.CAMORPH_DATA_FLAGS_POINTS)

                            # Set data to Relative and remove the link
                            pm_tag[c4d.ID_CA_POSE_MIXING] = c4d.ID_CA_POSE_MIXING_REL
                            pm_tag[c4d.ID_CA_POSE_TARGET] = None

                            pm_tag.UpdateMorphs()
                            desc_id = pm_tag.GetMorphID(count - 1)
                            pm_tag.SetParameter(
                                desc_id,
                                0,
                                c4d.DESCFLAGS_SET_USERINTERACTION,
                            )
                            morph_obj.Remove()
                            c4d.EventAdd()

        for obj in self.meshes:
            pm_tag = obj.GetTag(c4d.Tposemorph)
            pm_tag[c4d.ID_CA_POSE_MODE] = c4d.ID_CA_POSE_MODE_ANIMATE

    def delete_morphs(self, c_meshes):
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

    def add_drivers(self):
        """Creates the drivers that will control all the morphs on the main body."""

        pm_tag = self.body.GetTag(c4d.Tposemorph)
        if pm_tag:
            morph_amount = pm_tag.GetMorphCount()
            ctrl_xtag = self.find_ctrl_xpresso_tag()
            ctrl_node_master = ctrl_xtag.GetNodeMaster()
            self.create_xpresso_nodes()
            pos = self.prepare_pos(morph_amount)
            morph_indices = self.reorder_morph_list(pm_tag)
            for x in morph_indices:
                pm_tag.SetActiveMorphIndex(x)
                morph = pm_tag.GetActiveMorph()
                morph_name = morph.GetName()
                if "Default:" in morph_name:
                    continue
                morph_link = self.find_morph_link(morph_name)
                if not morph_link:
                    print("{0} Connections Could not be found ...".format(morph_name))
                    continue

                self.create_morph_connection(
                    ctrl_node_master, morph_link, x, morph_name, pm_tag, pos
                )
                self.connect_morph_to_bones(
                    ctrl_node_master, pm_tag, morph_link, x, morph_name, pos
                )
                # self.create_ctrl_connections(
                #     morph_link, morph_name, x, ctrl_node_master, pos
                # )
            self.remove_empty_nodes()

    def create_morph_connection(
        self, node_master, morph_link, x, morph_name, pm_tag, pos
    ):
        links = morph_link["Links"]
        clean_name = self.clean_name(morph_name)
        new_links = self.check_links(links)
        if len(new_links) == 0:
            self.create_custom_controller(morph_link, clean_name)
            return
        if not morph_link["isHidden"]:
            self.create_custom_controller(morph_link, clean_name)
        python_node = self.create_xpresso_node(
            node_master,
            1022471,
            -100,
            pos[x],
        )
        morph_num = pm_tag.GetMorphID(x)
        morph_input, morph_output, driver_node, input_tier = self.check_morph_hierarchy(
            new_links, morph_num
        )

        if morph_input == None:
            morph_input = self.nodes[self.body_name][clean_name][input_tier]
        if morph_output == None:
            morph_output = self.nodes[self.body_name][clean_name]["Output2"]

        self.store_morph(self.body, morph_input, input_tier, clean_name)
        self.store_morph(self.body, morph_output, "Output2", clean_name)
        for python_output in python_node.GetOutPorts():
            python_output.Connect(morph_input)
        for i in range(len(new_links) + 1):
            python_node.AddPort(c4d.GV_PORT_INPUT, self.python_real_input_desc_id)
        expression = erc.erc_start()
        for index, link in enumerate(new_links):
            driver_output = self.get_driver_output(
                link, node_master, -300, pos[x], pm_tag, driver_node
            )
            python_inputs = python_node.GetInPorts()
            python_inputs[0].SetName("current")
            if not morph_link["isHidden"]:
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

    def connect_morph_to_bones(
        self, node_master, pm_tag, morph_link, x, morph_name, pos
    ):
        sub_links = morph_link["SubLinks"]
        clean_name = self.clean_name(morph_name)
        new_sub_links = self.check_sub_links(sub_links)
        if len(new_sub_links) == 0:
            return
        self.morph_to_joints_nodes = {}

        morph_num = pm_tag.GetMorphID(x)
        morph_output = self.morph_to_bone.AddPort(c4d.GV_PORT_OUTPUT, morph_num)
        for link in new_sub_links:
            joint_name = link["Bone"]
            prop = link["Property"]
            python_node = self.create_xpresso_node(
                node_master,
                1022471,
                -600,
                pos[x],
            )
            joint = self.find_joint(joint_name)
            vector, transform = self.find_vector(prop)
            descid = c4d.DescID(
                c4d.DescLevel(transform, 0, 0),
                c4d.DescLevel(vector, 0, 0),
            )
            if not joint_name + prop in self.math_to_joints_nodes.keys():
                math_node = self.create_xpresso_node(
                    node_master,
                    c4d.ID_OPERATOR_MATH,
                    -400,
                    pos[x],
                )
                self.math_to_joints_nodes[joint_name + prop] = math_node

            if joint_name + prop not in self.morph_to_joints_nodes.keys():
                driver_node = self.create_node(node_master, joint, x, -300)
                driver_input = driver_node.AddPort(c4d.GV_PORT_INPUT, descid)
                self.morph_to_joints_nodes[joint_name + prop] = driver_node

            math_node = self.math_to_joints_nodes[joint_name + prop]
            driver_node = self.morph_to_joints_nodes[joint_name + prop]

            current_port = python_node.GetInPorts()[0]
            current_port.SetName("current")
            ctrl_python_port = python_node.GetInPorts()[1]
            ctrl_python_port.SetName("var1")
            morph_output.Connect(ctrl_python_port)
            connected = False
            math_node.SetParameter(
                self.math_input_desc_id, joint[descid], c4d.DESCFLAGS_SET_0
            )
            for index, math_input in enumerate(math_node.GetInPorts()):
                if index == 0:
                    continue
                elif not math_input.IsIncomingConnected():
                    python_node.GetOutPorts()[0].Connect(math_input)
                    connected = True
                    break
            if not connected:
                math_node.AddPort(c4d.GV_PORT_INPUT, self.math_real_input_desc_id)
                for index, math_input in enumerate(math_node.GetInPorts()):
                    if index == 0:
                        continue
                    elif not math_input.IsIncomingConnected():
                        python_node.GetOutPorts()[0].Connect(math_input)
                        break

            math_node.GetOutPorts()[0].Connect(driver_input)

            expression = erc.erc_start()
            expression += self.get_expression(link, str(1), True)
            if prop.endswith("Rotate"):
                expression += erc.erc_to_degrees()
            expression += erc.erc_translate()
            python_node[c4d.GV_PYTHON_CODE] = expression

    def rename_morphs(self, c_meshes):
        """
        Renames morphs based on the labels in Daz Studio
        """
        for ob in c_meshes:
            pmTag = ob.GetTag(c4d.Tposemorph)
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
            try:
                morph_name = self.clean_name(morph.GetName())

            except AttributeError:  # To deal with string bug in R22
                morph_name = str(morph)
                morph_name = self.clean_name(morph_name)

        if not morph_name in self.nodes[obj.GetName()].keys():
            self.store_node(obj, {}, morph_name)
        self.nodes[obj.GetName()][morph_name][key] = value

    def connect_morphs_to_parents(self, body, c_meshes):
        par_tag = body.GetTag(c4d.Tposemorph)
        xtag = self.find_body_xpresso_tag(body)
        node_master = xtag.GetNodeMaster()
        self.morph_master_node = self.create_node(node_master, par_tag, 50, 100)
        self.store_node(body, self.morph_master_node, "Node")
        self.store_node(body, par_tag, "Pose Tag")
        options = self.prepare_pos(len(c_meshes) - 1)
        for index, obj in enumerate(c_meshes):
            if obj.GetName() == body.GetName():
                continue
            child_tag = obj.GetTag(c4d.Tposemorph)
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

    def create_xpresso_nodes(self):
        pm_tag = self.body.GetTag(c4d.Tposemorph)
        ctrl_xtag = self.find_ctrl_xpresso_tag()
        ctrl_null = self.find_ctrl_null()
        ctrl_node_master = ctrl_xtag.GetNodeMaster()
        self.ctrl_null_node = self.create_node(
            ctrl_node_master,
            ctrl_null,
            -1000,
            100,
        )
        self.ctrl_null_node_input = self.create_node(
            ctrl_node_master,
            ctrl_null,
            -600,
            100,
        )
        self.morph_ctrl_node = self.create_node(
            ctrl_node_master,
            pm_tag,
            -200,
            100,
        )
        self.morph_master_input = self.create_node(
            ctrl_node_master,
            pm_tag,
            200,
            100,
        )
        self.morph_master_input_2 = self.create_node(
            ctrl_node_master,
            pm_tag,
            600,
            100,
        )
        self.morph_master_input_3 = self.create_node(
            ctrl_node_master,
            pm_tag,
            1000,
            100,
        )
        self.morph_to_bone = self.create_node(
            ctrl_node_master,
            pm_tag,
            -1200,
            100,
        )

    def remove_empty_nodes(self):
        """Check if any nodes can be removed"""
        nodes = [
            self.morph_ctrl_node,
            self.ctrl_null_node,
            self.ctrl_null_node_input,
            self.morph_master_input,
            self.morph_master_input_2,
            self.morph_master_input_3,
        ]
        for node in nodes:
            if len(node.GetInPorts()) == 0 and len(node.GetOutPorts()) == 0:
                node.Remove()

    def check_morph_hierarchy(self, new_links, morph_num):
        for link in new_links:
            tmp_morph = link["Property"]
            if tmp_morph in self.nodes[self.body_name].keys():
                if "Input1" in self.nodes[self.body_name][tmp_morph].keys():
                    morph_input = self.morph_master_input_2.AddPort(
                        c4d.GV_PORT_INPUT, morph_num
                    )
                    morph_output = self.morph_master_input.AddPort(
                        c4d.GV_PORT_OUTPUT, morph_num
                    )
                    driver_node = self.morph_master_input
                    return morph_input, morph_output, driver_node, "Input2"
                if "Input2" in self.nodes[self.body_name][tmp_morph].keys():
                    morph_input = self.morph_master_input_3.AddPort(
                        c4d.GV_PORT_INPUT, morph_num
                    )
                    morph_output = self.morph_master_input_2.AddPort(
                        c4d.GV_PORT_OUTPUT, morph_num
                    )
                    driver_node = self.morph_master_input_2
                    return morph_input, morph_output, driver_node, "Input3"

        morph_input = self.morph_master_input.AddPort(c4d.GV_PORT_INPUT, morph_num)
        morph_output = self.morph_ctrl_node.AddPort(c4d.GV_PORT_OUTPUT, morph_num)
        driver_node = self.morph_ctrl_node
        return morph_input, morph_output, driver_node, "Input1"

    def get_driver_output(self, link, node_master, x, y, pm_tag, driver_node):
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
            vector, rotation = self.find_vector(prop)
            joint = self.find_joint(joint_name)
            descid = c4d.DescID(
                c4d.DescLevel(rotation, 0, 0),
                c4d.DescLevel(vector, 0, 0),
            )
            driver_node = self.create_node(node_master, joint, x, y)
            driver_output = driver_node.AddPort(c4d.GV_PORT_OUTPUT, descid)
        else:
            morph_num = self.find_morph_id_by_name(pm_tag, prop)
            driver_output = driver_node.AddPort(c4d.GV_PORT_OUTPUT, morph_num)
            if driver_output is None:
                driver_output = self.nodes[self.body_name][prop]["Output2"]
            self.store_morph(self.body, driver_output, "Output2", prop)
        return driver_output

    def add_path_group(self, morph_ctrl, morph_link):
        path = str(morph_link["Path"])
        path = path.replace("//", "/")
        group_names = path.split("/")
        parent = None
        for grp_name in group_names:
            grp_name = str(grp_name)
            user_id = self.find_user_data_by_name(morph_ctrl, grp_name)
            if not user_id:
                group = c4d.GetCustomDatatypeDefault(c4d.DTYPE_GROUP)
                group[c4d.DESC_NAME] = grp_name
                group[c4d.DESC_PARENTGROUP] = parent
                group[c4d.DESC_DEFAULT] = c4d.DESC_GUIOPEN

                parent = morph_ctrl.AddUserData(group)
            else:
                parent = user_id
        return parent

    def create_custom_controller(self, morph_link, morph_name):
        morph_ctrl = self.find_ctrl_null()
        parent = self.add_path_group(morph_ctrl, morph_link)
        label_name = str(morph_link["Label"])
        min_morph = morph_link["Minimum"]
        max_morph = morph_link["Maximum"]
        real_data = c4d.GetCustomDataTypeDefault(c4d.DTYPE_REAL)
        real_data[c4d.DESC_NAME] = label_name
        real_data[c4d.DESC_CUSTOMGUI] = c4d.CUSTOMGUI_REALSLIDER
        real_data[c4d.DESC_UNIT] = c4d.DESC_UNIT_PERCENT
        real_data[c4d.DESC_MIN] = min_morph
        real_data[c4d.DESC_MAX] = max_morph
        real_data[c4d.DESC_MINSLIDER] = min_morph
        real_data[c4d.DESC_MAXSLIDER] = max_morph
        real_data[c4d.DESC_STEP] = 0.01
        real_data[c4d.DESC_PARENTGROUP] = parent
        slider_id = morph_ctrl.AddUserData(real_data)
        c4d.EventAdd()
        self.morph_ctrl_user_data[morph_name] = slider_id
        self.connect_morph_to_controller(slider_id, morph_name)

    def create_ctrl_connections(self, morph_link, morph_name, x, node_master, pos):
        morph_name = self.clean_name(morph_name)
        if morph_link["isHidden"]:
            return
        slider_id = self.morph_ctrl_user_data[morph_name]
        new_links = self.check_links(morph_link["Links"])
        if len(new_links) > 0:
            python_node = self.create_xpresso_node(
                node_master,
                1022471,
                -100,
                pos[x],
            )
            if len(new_links) - 1 > 0:
                for i in range(len(new_links) - 2):
                    python_node.AddPort(
                        c4d.GV_PORT_INPUT, self.python_real_input_desc_id
                    )
            python_inputs = python_node.GetInPorts()
            for index, link in enumerate(new_links):
                morph_prop_name = link["Property"]
                if link["Bone"] != "None":
                    continue
                if not morph_prop_name in self.ctrl_sliders_output.keys():
                    continue
                self.connect_ctrl_to_python(python_inputs[index], morph_prop_name)
            self.connect_ctrl_to_python(python_inputs[-1], morph_name)
            python_output = python_node.GetOutPorts()[0]
            self.connect_python_to_ctrl(slider_id, python_output, morph_name)
            python_node[c4d.GV_PYTHON_CODE] = erc.erc_controls()

    def connect_ctrl_to_python(self, python_input, parent_morph_name):
        ctrl_null_output = self.ctrl_sliders_output[parent_morph_name]
        ctrl_null_output.Connect(python_input)

    def connect_python_to_ctrl(self, slider_id, python_output, morph_name):
        ctrl_null_input = self.ctrl_null_node_input.AddPort(
            c4d.GV_PORT_INPUT, slider_id
        )
        if not ctrl_null_input:
            ctrl_null_input = self.ctrl_sliders_input[morph_name]
        python_output.Connect(ctrl_null_input)
        self.ctrl_sliders_input[morph_name] = ctrl_null_input

    def connect_morph_to_controller(self, slider_id, morph_name):
        pm_tag = self.body.GetTag(c4d.Tposemorph)
        morph_num = self.find_morph_id_by_name(pm_tag, morph_name)
        morph_input = self.morph_ctrl_node.AddPort(c4d.GV_PORT_INPUT, morph_num)
        ctrl_null_output = self.ctrl_null_node.AddPort(c4d.GV_PORT_OUTPUT, slider_id)
        self.ctrl_sliders_output[morph_name] = ctrl_null_output
        ctrl_null_output.Connect(morph_input)
