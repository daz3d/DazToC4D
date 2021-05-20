import c4d
from c4d import utils

from .CustomIterators import TagIterator
from . import ErcExpressions as erc


class Morphs:
    morph_links = dict()
    stored_outputs = dict()

    def store_morph_links(self, dtu):
        """
        Pass the Morph Links to be used for the current import
        """
        self.morph_links = dtu.get_morph_links_dict()

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

    def connect_morphs_to_parents(self, body, c_meshes):
        par_tag = self.find_objects_morph_tag(body)
        xtag = self.find_daz_xpresso_tag(body)
        if xtag == None:
            self.create_daz_xpresso_tag(body)
            xtag = self.find_daz_xpresso_tag(body)
        node_master = xtag.GetNodeMaster()
        self.morph_master_node = self.create_node(node_master, par_tag, 50, 50)

        options = self.prepare_pos(len(c_meshes) - 1)
        self.stored_outputs = {}
        for index, obj in enumerate(c_meshes):
            if obj.GetName() == body.GetName():
                continue
            child_tag = self.find_objects_morph_tag(obj)
            child_node = self.create_node(
                node_master, child_tag, 400, options[index - 1]
            )
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
            par_output = par_node.AddPort(c4d.GV_PORT_OUTPUT, parent_id)
            if par_output is None:
                par_output = self.stored_outputs[x]
            self.connect_morph_nodes(node_master, par_output, child_node, child_id)
            self.stored_outputs[x] = par_output
        c4d.EventAdd()

    def find_objects_morph_tag(self, obj):
        obj_tags = TagIterator(obj)
        for t in obj_tags:
            if "Morph" in t.GetName():
                return t

    def find_daz_xpresso_tag(self, obj):
        obj_tags = TagIterator(obj)
        for t in obj_tags:
            if "DazToC4D Morphs Connect" in t.GetName():
                return t

    def create_daz_xpresso_tag(self, obj):
        xtag = c4d.BaseTag(c4d.Texpresso)
        # Set Tag priority to Animation
        pd = xtag[c4d.EXPRESSION_PRIORITY]
        pd.SetPriorityValue(c4d.PRIORITYVALUE_MODE, 1)
        xtag[c4d.EXPRESSION_PRIORITY] = pd
        xtag[c4d.ID_BASELIST_NAME] = "DazToC4D Morphs Connect"
        obj.InsertTag(xtag)

    def prepare_pos(self, amount):
        if amount == 1:
            return [50]
        total = amount * 50
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

    def create_xpresso_node(self, node_parent, type, x, y, exp):
        node = node_parent.CreateNode(node_parent.GetRoot(), type, None, x, y)
        node[c4d.GV_PYTHON_CODE] = exp
        return node

    def find_morph_id(self, morph_tag_main, morph_tag_slave, x):
        morph_main = morph_tag_main.GetMorph(x).GetName()
        morph_num = morph_tag_main.GetMorphID(x)
        for index in range(morph_tag_slave.GetMorphCount()):
            morph_slave = morph_tag_slave.GetMorph(index).GetName()
            if morph_main == morph_slave:
                return morph_num, morph_tag_slave.GetMorphID(index)
        return 0, 0

    def connect_morph_nodes(self, node_master, par_output, child_node, child_id):
        child_input = child_node.AddPort(c4d.GV_PORT_INPUT, child_id)
        c4d.modules.graphview.RedrawMaster(node_master)
        par_output.Connect(child_input)

    def add_drivers(self, body, joints):
        pm_tag = body.GetTag(c4d.Tposemorph)
        if pm_tag:
            morph_amount = pm_tag.GetMorphCount()
            xtag = self.find_daz_xpresso_tag(body)
            node_master = xtag.GetNodeMaster()

            for x in range(morph_amount):
                pm_tag.SetActiveMorphIndex(x)
                morph = pm_tag.GetActiveMorph()
                morph_name = morph.GetName()
                if "Default:" in morph_name:
                    continue
                morph_link = self.find_morph_link(morph_name)
                links = morph_link["Links"]
                for link in links:
                    joint_name = link["Bone"]
                    erc_type = link["Type"]
                    prop = link["Property"]
                    if erc_type == 6:
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
                        expression = erc.erc_keyed(dist, key_1, key_0, norm_dist)

                        if joint_name != "None":
                            # Create Joint
                            vector = self.find_vector(prop)
                            joint = self.find_joint(joint_name, joints)
                            descid = c4d.DescID(
                                c4d.DescLevel(c4d.ID_BASEOBJECT_ROTATION, 0, 0),
                                c4d.DescLevel(vector, 0, 0),
                            )
                            joint_node = self.create_node(node_master, joint, -150, 50)
                            joint_input = joint_node.AddPort(c4d.GV_PORT_OUTPUT, descid)

                            python_node = self.create_xpresso_node(
                                node_master,
                                1022471,
                                -100,
                                50,
                                expression,
                            )

                            morph_num = pm_tag.GetMorphID(x)
                            morph_input = self.morph_master_node.AddPort(
                                c4d.GV_PORT_INPUT, morph_num
                            )
                            for form_input in python_node.GetInPorts():
                                form_input.SetName("var")
                                joint_input.Connect(form_input)
                                break
                            for form_output in python_node.GetOutPorts():
                                form_output.Connect(morph_input)

    def find_vector(self, prop):
        if "YRotate" == prop:
            return c4d.VECTOR_Y
        if "ZRotate" == prop:
            return c4d.VECTOR_Z
        if "XRotate" == prop:
            return c4d.VECTOR_X

    def check_conversion(self, prop):
        if "YRotate" == prop:
            return 1
        if "ZRotate" == prop:
            return -1
        if "XRotate" == prop:
            return 1

    def find_joint(self, name, joints):
        for joint in joints:
            if joint.GetName() == name:
                return joint
