import os
import sys
import c4d
from c4d import documents

folder = os.path.dirname( __file__ )
if folder not in sys.path: 
    sys.path.insert( 0, folder )

from CustomIterators import ObjectIterator, TagIterator
from Utilities import dazToC4Dutils

class connectEyeLashesMorphXpresso:
    xtag = None
    def __repr__(self):
        return self.xtag

    def __init__(self):
        morphMain = dazToC4Dutils().getDazMesh()
        morphSlave = ''

        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for obj in scene:
            if 'Eyelashes' in obj.GetName():
                if obj.GetType() == 5100:
                    if self.findMorphTag(obj):
                        morphSlave = obj
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for obj in scene: #TOON GENERATION FIX
            if 'ToonBrows' in obj.GetName():
                if obj.GetType() == 5100:
                    if self.findMorphTag(obj):
                        morphSlave = obj


        if morphSlave != '':
            morphTagMain = self.findMorphTag(morphMain)  #GET FIGURE MESH OBJ!
            morphTagSlave = self.findMorphTag(morphSlave)
            self.connectMorphsXpresso(morphMain, morphTagMain, morphTagSlave)

    def connectMorphsXpresso(self, morphMain, morphTagMain, morphTagSlave):
        xtag = c4d.BaseTag(c4d.Texpresso)

        #Set Tag priority to Animation
        pd = xtag[c4d.EXPRESSION_PRIORITY]
        pd.SetPriorityValue(c4d.PRIORITYVALUE_MODE, 1)
        # pd.SetPriorityValue(c4d.PRIORITYVALUE_PRIORITY, Value)
        xtag[c4d.EXPRESSION_PRIORITY] = pd
        xtag[c4d.ID_BASELIST_NAME] = 'DazToC4D Morphs Connect'
        morphMain.InsertTag(xtag)

        nodemaster = xtag.GetNodeMaster()
        # print nodemaster.GetOwner().GetName()
        def connectMorphNodes(x):
            morphNumber = 1001 + x*100
            node1 = nodemaster.CreateNode(nodemaster.GetRoot(),c4d.ID_OPERATOR_OBJECT,None,50, 50 * x)
            node1[c4d.GV_OBJECT_OBJECT_ID] = morphTagMain
            node2 = nodemaster.CreateNode(nodemaster.GetRoot(),c4d.ID_OPERATOR_OBJECT,None,400, 50 * x)
            node2[c4d.GV_OBJECT_OBJECT_ID] = morphTagSlave

            node1out = node1.AddPort(c4d.GV_PORT_OUTPUT,c4d.DescID(c4d.DescLevel(4000), c4d.DescLevel(morphNumber)))
            node2in = node2.AddPort(c4d.GV_PORT_INPUT,c4d.DescID(c4d.DescLevel(4000), c4d.DescLevel(morphNumber)))

            c4d.modules.graphview.RedrawMaster(nodemaster)
            try:
                node1out.Connect(node2in)
            except:
                return None

        for x in range(1, morphTagMain.GetMorphCount()):
            connectMorphNodes(x)
        c4d.EventAdd()

    def findMorphTag(self, obj):
        objTags =  TagIterator(obj)
        for t in objTags:
            if 'Morph' in t.GetName():
                return t



class Morphs:
    def morphsFixRemoveAndRename(self):
        def morphsRemoveAndRename(obj):
            
            def morphRemove():
                listMorphsToRemove = ['RIG',
                                    'HDLv2',
                                    'HDLv3',
                                    'pNeckHead',
                                    'Genesis8Male_',
                                    'Genesis8MaleEyelashes_',
                                    'Genesis8Female_',
                                    'Genesis8FemaleEyelashes_'
                                    ]
                    
                morphsAmount = len(list(range(pmTag.GetMorphCount())))
                for x in range(0, morphsAmount):
                    try:
                        pmTag.SetActiveMorphIndex(x)
                        morphName = pmTag.GetActiveMorph().GetName()
                        for morphToRemove in listMorphsToRemove:
                            try:
                                if morphToRemove in morphName:
                                    pmTag.RemoveMorph(x)
                                    try:
                                        obj = doc.SearchObject(morphName)
                                        obj.Remove()
                                    except:
                                        pass
                                    return
                            except:
                                print('skip remove')
                    except:
                        pass
                c4d.EventAdd()

            def morphRename():
                morphsAmount = len(list(range(pmTag.GetMorphCount())))
                for x in range(0, morphsAmount):
                    try:
                        pmTag.SetActiveMorphIndex(x)
                        morphName = pmTag.GetActiveMorph().GetName()
                        try:
                            newMorphName = morphName.replace('head__', '')
                            newMorphName = newMorphName.replace('eCTRLM7', '')
                            newMorphName = newMorphName.replace('eCTRL', '')
                            newMorphName = newMorphName.replace('3duTG2_10yo_', '')
                            newMorphName = newMorphName.replace('PBMSTEDIM7', '')
                            newMorphName = newMorphName.replace('PHM', '')
                            newMorphName = newMorphName.replace('CTRLB', '')
                            newMorphName = newMorphName.replace('CTRL', '')
                            newMorphName = newMorphName.replace('_', '')
                            pmTag.GetActiveMorph().SetName(newMorphName)
                        except Exception as e:
                            pass
                    except Exception as e:
                        pass
                c4d.EventAdd()

            pmTag = obj.GetTag(c4d.Tposemorph)  # Gets the pm tag
            pmTag.ExitEdit(doc, True)
            morphsAmount = len(list(range(pmTag.GetMorphCount())))
                
            for x in range(0, morphsAmount):
                morphRename()
            for x in range(0, morphsAmount):
                morphRemove()  # REMOVE
                
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for ob in scene:
            pmTag = ob.GetTag(c4d.Tposemorph)  # Gets the pm tag
            if pmTag:
                morphsRemoveAndRename(ob)
