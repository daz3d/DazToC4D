import c4d

from .CustomIterators import TagIterator


class Morphs:
    morph_links = dict()

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

    def delete_morphs(self, c_meshes):
        """
        Deletes the Morphs that don't have the Bone Controlling it or Alias in Daz
        """
        for obj in c_meshes:
            pm_tag = obj.GetTag(c4d.Tposemorph)
            if pm_tag:
                morphsAmount = len(list(range(pm_tag.GetMorphCount())))
                for x in range(0, morphsAmount):
                    pm_tag.SetActiveMorphIndex(x)
                    morph_name = pm_tag.GetActiveMorph().GetName()
                    morph_link = self.find_morph_link(morph_name)
                    if morph_link == None:
                        continue
                    control_meshes = morph_link["Controlled Meshes"]
                    if obj.GetName().replace(".Shape", "") in control_meshes:
                        continue
                    pm_tag.Remove()

    def find_objects_morph_tag(self, obj):
        obj_tags = TagIterator(obj)
        for t in obj_tags:
            if "Morph" in t.GetName():
                return t

    def find_xpresso_tag(self, obj):
        obj_tags = TagIterator(obj)
        for t in obj_tags:
            if "DazToC4D Morphs Connect" in t.GetName():
                return t

    def connect_morphs_xpresso(self, morph_main, morph_tag_main, morph_tag_slave):
        xtag = self.find_xpresso_tag(morph_main)
        if xtag == None:  # Create Tag
            xtag = c4d.BaseTag(c4d.Texpresso)
            # Set Tag priority to Animation
            pd = xtag[c4d.EXPRESSION_PRIORITY]
            pd.SetPriorityValue(c4d.PRIORITYVALUE_MODE, 1)
            xtag[c4d.EXPRESSION_PRIORITY] = pd
            xtag[c4d.ID_BASELIST_NAME] = "DazToC4D Morphs Connect"
            morph_main.InsertTag(xtag)

        node_master = xtag.GetNodeMaster()

        def connect_morph_nodes(x):
            morph_num = 1001 + x * 100
            par_node = node_master.CreateNode(
                node_master.GetRoot(), c4d.ID_OPERATOR_OBJECT, None, 50, 50 * x
            )
            par_node[c4d.GV_OBJECT_OBJECT_ID] = morph_tag_main
            child_node = node_master.CreateNode(
                node_master.GetRoot(), c4d.ID_OPERATOR_OBJECT, None, 400, 50 * x
            )
            child_node[c4d.GV_OBJECT_OBJECT_ID] = morph_tag_slave

            par_output = par_node.AddPort(
                c4d.GV_PORT_OUTPUT,
                c4d.DescID(c4d.DescLevel(4000), c4d.DescLevel(morph_num)),
            )
            child_input = child_node.AddPort(
                c4d.GV_PORT_INPUT,
                c4d.DescID(c4d.DescLevel(4000), c4d.DescLevel(morph_num)),
            )

            c4d.modules.graphview.RedrawMaster(node_master)
            try:
                par_output.Connect(child_input)
            except:
                return None

        for x in range(1, morph_tag_main.GetMorphCount()):
            connect_morph_nodes(x)
        c4d.EventAdd()

    def connect_morphs_to_parents(self, body, c_meshes):
        parent_morph = self.find_objects_morph_tag(body)
        for obj in c_meshes:
            if obj.GetName() == body.GetName():
                continue
            child_morph = self.find_objects_morph_tag(obj)
            if not child_morph == None:
                self.connect_morphs_xpresso(body, parent_morph, child_morph)
