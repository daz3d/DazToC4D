import os
import sys
import c4d
from c4d import documents

from .CustomIterators import ObjectIterator, TagIterator
from .Utilities import dazToC4Dutils


class Morphs:
    morph_links = dict()

    def store_morph_links(self, dtu):
        """
        Pass the Morph Links to be used for the current import
        """
        self.morph_links = dtu.get_morph_links_dict()

    def rename_morphs(self, skeleton):
        """
        Renames morphs based on the labels in Daz Studio
        """
        scene = ObjectIterator(skeleton)
        for ob in scene:
            pmTag = ob.GetTag(c4d.Tposemorph)  # Gets the pm tag
            if pmTag:
                morphsAmount = len(list(range(pmTag.GetMorphCount())))
                for x in range(0, morphsAmount):
                    pmTag.SetActiveMorphIndex(x)
                    morph_name = pmTag.GetActiveMorph().GetName()
                    split = morph_name.split("__")
                    if len(split) != 2:
                        continue
                    original_morph_name = split[1]
                    if original_morph_name not in self.morph_links.keys():
                        continue
                    morph_label = self.morph_links[original_morph_name]["Label"]
                    pmTag.GetActiveMorph().SetName(morph_label)

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

    # TODO: Refactor and Understand Logic
    def connectMorphsXpresso(self, morphMain, morphTagMain, morphTagSlave):
        xtag = self.find_xpresso_tag(morphMain)
        if xtag == None:  # Create Tag
            xtag = c4d.BaseTag(c4d.Texpresso)
            # Set Tag priority to Animation
            pd = xtag[c4d.EXPRESSION_PRIORITY]
            pd.SetPriorityValue(c4d.PRIORITYVALUE_MODE, 1)
            xtag[c4d.EXPRESSION_PRIORITY] = pd
            xtag[c4d.ID_BASELIST_NAME] = "DazToC4D Morphs Connect"
            morphMain.InsertTag(xtag)

        nodemaster = xtag.GetNodeMaster()

        def connectMorphNodes(x):
            morphNumber = 1001 + x * 100
            node1 = nodemaster.CreateNode(
                nodemaster.GetRoot(), c4d.ID_OPERATOR_OBJECT, None, 50, 50 * x
            )
            node1[c4d.GV_OBJECT_OBJECT_ID] = morphTagMain
            node2 = nodemaster.CreateNode(
                nodemaster.GetRoot(), c4d.ID_OPERATOR_OBJECT, None, 400, 50 * x
            )
            node2[c4d.GV_OBJECT_OBJECT_ID] = morphTagSlave

            node1out = node1.AddPort(
                c4d.GV_PORT_OUTPUT,
                c4d.DescID(c4d.DescLevel(4000), c4d.DescLevel(morphNumber)),
            )
            node2in = node2.AddPort(
                c4d.GV_PORT_INPUT,
                c4d.DescID(c4d.DescLevel(4000), c4d.DescLevel(morphNumber)),
            )

            c4d.modules.graphview.RedrawMaster(nodemaster)
            try:
                node1out.Connect(node2in)
            except:
                return None

        for x in range(1, morphTagMain.GetMorphCount()):
            connectMorphNodes(x)
        c4d.EventAdd()

    def connect_morphs_to_parents(self, body, children):
        parent_morph = self.find_objects_morph_tag(body)
        for obj in children:
            if obj.GetName() == body.GetName():
                continue
            child_morph = self.find_objects_morph_tag(obj)
            if not child_morph == None:
                self.connectMorphsXpresso(body, parent_morph, child_morph)
