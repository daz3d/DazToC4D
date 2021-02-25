from __future__ import division
import os
import sys
import hashlib
import c4d
from c4d import gui, documents
from c4d import utils
from c4d import plugins
from random import randint
from shutil import copyfile
import webbrowser
import json
from xml.etree import ElementTree

folder = os.path.dirname(__file__)
if folder not in sys.path:
    sys.path.insert(0, folder)

from Util import DazToC4dUtils
from Iterators import TagIterator, ObjectIterator
from Globals import *

def cleanMorphsGeoRemove(self):
        doc = documents.GetActiveDocument()

        listObjs = []
        mesh_name = daz_name.replace('_', '')

        caca = doc.GetFirstObject()
        # listObjs.append(caca)

        while caca.GetNext():
            listObjs.append(caca)
            caca = caca.GetNext()

        for x in listObjs:
            if mesh_name not in x.GetName():
                if x.GetDown():
                    if 'Poses:' in x.GetDown().GetName():
                        x.GetDown().Remove()
                        try:
                            objTags = TagIterator(x)
                            for t in objTags:
                                if 'Morph' in t.GetName():
                                    t.Remove()
                        except:
                            pass
        c4d.EventAdd()

def dazMorphsFix():

        doc = documents.GetActiveDocument()

        def tagsIterator(self, obj):
            doc = documents.GetActiveDocument()

            fTag = obj.GetFirstTag()
            if fTag:
                tagsList = []
                tagsList.append(fTag)
                tagNext = fTag.GetNext()
                while tagNext:
                    tagsList.append(tagNext)
                    tagNext = tagNext.GetNext()

                # Clean list in case of empty tags...
                caca = []
                for x in tagsList:
                    if len(x.GetName()) > 2:
                        caca.append(x)

                return caca

        def detectRIGmorph(obj):
            pmTag = obj.GetTag(c4d.Tposemorph)  # Gets the pm tag
            pmTag.ExitEdit(doc, True)
            count = 0
            for x in range(pmTag.GetMorphCount()):
                pmTag.SetActiveMorphIndex(x)
                morphName = pmTag.GetActiveMorph().GetName()
                if 'RIG' in morphName:
                    count = count + 1
            return count

        def morphsRename(obj):
            pmTag = obj.GetTag(c4d.Tposemorph)  # Gets the pm tag
            pmTag.ExitEdit(doc, True)

            # 4000 is the ID# for the sub container in the pm tag
            # The poses saved inside that container have ID#'s 1101,1201,1301,etc...

            # first =  pmTag[4000,1101]= .5         #Sets the value of Pose.0 to 50%
            # second = pmTag[4000,1201]= .5         #Sets the value of Pose.1 to 50%

            for x in range(pmTag.GetMorphCount()):
                try:
                    pmTag.SetActiveMorphIndex(x)
                    morphName = pmTag.GetActiveMorph().GetName()
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
                    if 'RIG' in newMorphName:
                        try:
                            pmTag.RemoveMorph(x)
                        except:
                            print('skip')
                except:
                    pass

            c4d.EventAdd()

        caca = doc.GetFirstObject()
        while caca.GetNext():
            caca = caca.GetNext()
            fTag = None
            if caca.GetFirstTag():

                if tagsIterator(caca):
                    for x in tagsIterator(caca):
                        if 'Pose Morph' in x.GetName():
                            # detectRIGmorph(caca)
                            morphsRename(caca)