from __future__ import division
import os, sys, hashlib, c4d
from c4d import gui, documents
from c4d import utils
from c4d import plugins
from random import randint

import webbrowser
import json

from . import DtuLoader
from . import Materials
from .Utilities import dazToC4Dutils
from .IkMax import applyDazIK, ikmaxUtils, ikmGenerator
from .AllSceneToZero import AllSceneToZero



IDS_AUTH = 40000
IDS_AUTH_DIALOG = 40001
DLG_AUTH = 41000
IDC_SERIAL = 41001
IDC_SUBMIT = 41002
IDC_CANCEL = 41003
IDC_CODEBOX = 41004
IDC_CODEBOX_AUTH = 41005
IDC_PASTESERIAL = 41007

dazName = 'Object_'

authDialogDazToC4D = None
guiDazToC4DLayerLockButton = None

guiDazToC4DExtraDialog = None


class ObjectIterator :
    def __init__(self, baseObject):
        self.baseObject = baseObject
        self.currentObject = baseObject
        self.objectStack = []
        self.depth = 0
        self.nextDepth = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.currentObject == None :
            raise StopIteration

        obj = self.currentObject
        self.depth = self.nextDepth

        child = self.currentObject.GetDown()
        if child :
            self.nextDepth = self.depth + 1
            self.objectStack.append(self.currentObject.GetNext())
            self.currentObject = child
        else :
            self.currentObject = self.currentObject.GetNext()
            while( self.currentObject == None and len(self.objectStack) > 0 ) :
                self.currentObject = self.objectStack.pop()
                self.nextDepth = self.nextDepth - 1
        return obj
    
    next = __next__                 #To Support Python 2.0

class TagIterator:

    def __init__(self, obj):
        currentTag = None
        if obj:
            self.currentTag = obj.GetFirstTag()

    def __iter__(self):
        return self

    def __next__(self):

        tag = self.currentTag
        if tag == None:
            raise StopIteration

        self.currentTag = tag.GetNext()

        return tag
    next = __next__             #To Support Python 2.0



class DazToC4D():
    dialog = None

    def figureFixBrute(self):
        doc = c4d.documents.GetActiveDocument()
        def checkIfBrute():
            isBrute = False
            docMaterials = doc.GetMaterials()
            for mat in docMaterials:
                mapDiffuse = ''
                try:
                    mapDiffuse = mat[c4d.MATERIAL_COLOR_SHADER][c4d.BITMAPSHADER_FILENAME]
                except:
                    pass
                if 'Brute8' in mapDiffuse:
                    isBrute = True
            return isBrute

        def nullSize(nullName, rad=1, ratio=1):
            dazName = 'Genesis8Male_'  # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            obj = doc.SearchObject(dazName + nullName)
            if obj:
                obj[c4d.NULLOBJECT_RADIUS] = rad
                obj[c4d.NULLOBJECT_ASPECTRATIO] = ratio
                c4d.EventAdd()

        if checkIfBrute():  # If BRUTE8! Change Null Sizes!
            nullSize('Pelvis_ctrl', 40, 0.8)
            nullSize('Spine_ctrl', 30, 0.8)
            nullSize('Chest_ctrl', 30, 0.8)
            nullSize('Foot_PlatformBase', 9.3, 1.52)
            nullSize('Foot_PlatformBase___R', 9.3, 1.52)
            nullSize('Collar_ctrl', 20, 0.3)
            nullSize('Collar_ctrl___R', 20, 0.3)

            nullSize('ForearmTwist_ctrl', 11, 1.0)
            nullSize('ForearmTwist_ctrl___R', 11, 1.0)

            nullSize('IK_Hand', 7, 1.4)
            nullSize('IK_Hand___R', 7, 1.4)



    def hidePolyTagByName(self, op, tagName):
        doc = documents.GetActiveDocument()
        tags = op.GetTags()
        polyselection = None
        try:
            polyselection = op.GetPolygonS()
        except:
            pass
        if polyselection:
            store = c4d.BaseSelect()
            polyselection.CopyTo(store)

            t = op.GetFirstTag()
            while t:
                if t.GetType() == c4d.Tpolygonselection:
                    if tagName in t.GetName():
                        tagselection = t.GetBaseSelect()
                        tagselection.CopyTo(polyselection)
                        sec = utils.SendModelingCommand(command=c4d.MCOMMAND_HIDESELECTED,
                                                        list=[op],
                                                        mode=c4d.MODELINGCOMMANDMODE_POLYGONSELECTION,
                                                        doc=doc)
                        if not sec: return
                        # sec[0].InsertAfter(op)
                t = t.GetNext()

            store.CopyTo(polyselection)
            c4d.EventAdd()


    def moveMorphsToGroup(self, figureObj):
        doc = documents.GetActiveDocument()
        newNull = None
        groupNull = None

        def makeGroup():
            newNull = c4d.BaseObject(c4d.Onull)  # Create new null
            doc.InsertObject(newNull)
            c4d.EventAdd()
            newNull.SetName('Morphs')
            return newNull

        def moveMorphTag(sourceObj, targetObj):
            doc = documents.GetActiveDocument()
            morphTag = None
            tags = TagIterator(sourceObj)
            for tag in tags:
                if 'Pose Morph' in tag.GetName():
                    morphTag = tag

            if morphTag:
                print(morphTag)
                targetObj.InsertTag(morphTag)

            c4d.EventAdd()

        firstObj = doc.GetFirstObject()
        scene = ObjectIterator(firstObj)
        morphGroups = []
        for obj in scene:
            objName = obj.GetName()
            if 'Poses' in objName:
                morphGroups.append(obj)

        print(len(morphGroups))
        if len(morphGroups) > 0:
            groupNull = makeGroup()
            for x in morphGroups:
                print(x)
                x.InsertUnder(groupNull)
            moveMorphTag(figureObj, groupNull)

        c4d.EventAdd()
        return groupNull

    def xpressoTagToMorphsGroup(self, morphsGroup):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()

        scene = ObjectIterator(obj)
        objTags = TagIterator(obj)
        xtag = None

        for ob in scene:
            objTags = TagIterator(ob)
            if objTags:
                for tag in objTags:
                    if tag.GetName() == 'DazToC4D Morphs Connect':
                        morphsGroup.InsertTag(tag)
                        mtag = morphsGroup.GetLastTag()
                        morphsGroup.InsertTag(mtag)

        c4d.EventAdd()

    def morphsGroupMoveUp(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        objTags = TagIterator(obj)

        for ob in scene:
            if ob.GetUp() == None and ob.GetType() == 5140:
                objTags = TagIterator(ob)
                if objTags:
                    for tag in objTags:
                        if tag.GetType() == 1024237:  # Morph Tag Type
                            c4d.CallCommand(100004767, 100004767)  # Deselect All
                            ob.SetBit(c4d.BIT_ACTIVE)
                            c4d.CallCommand(100004819)  # Cut
                            c4d.CallCommand(100004821)  # Paste
                            c4d.CallCommand(100004767, 100004767)  # Deselect All

        c4d.EventAdd()

    def morphTagsToGroups(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()

        scene = ObjectIterator(obj)
        objTags = TagIterator(obj)
        xtag = None

        for ob in scene:
            objTags = TagIterator(ob)
            if objTags:
                for tag in objTags:
                    if tag.GetType() == 1024237:
                        print(ob.GetName(), tag.GetName())
                        mGroup = doc.SearchObject('Poses: ' + ob.GetName())
                        if mGroup:
                            mGroup.InsertTag(tag)

        c4d.EventAdd()


    def findMesh(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)

        foundMesh = False

        for obj in scene:
            if obj.GetType() == 5100:
                foundMesh = True

        return foundMesh

    

    def limitTwistPosition(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()

        def addProtTag(obj):
            xtag = c4d.BaseTag(c4d.Tprotection)
            xtag[c4d.PROTECTION_P] = 1
            xtag[c4d.PROTECTION_S] = False
            xtag[c4d.PROTECTION_R] = 1
            xtag[c4d.PROTECTION_R_X] = True
            xtag[c4d.PROTECTION_R_Y] = False
            xtag[c4d.PROTECTION_R_Z] = True

            obj.InsertTag(xtag)

        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for obj in scene:
            if 'ForearmTwist' in obj.GetName():
                addProtTag(obj)

    def freezeTwistBones(self):
        doc = c4d.documents.GetActiveDocument()

        nullForeArm = doc.SearchObject(dazName + 'ForearmTwist_ctrl')
        nullForeArmR = doc.SearchObject(dazName + 'ForearmTwist_ctrl___R')
        if nullForeArm:
            nullForeArm.SetFrozenPos(nullForeArm.GetAbsPos())
            nullForeArm.SetFrozenRot(nullForeArm.GetAbsRot())
            nullForeArmR.SetFrozenPos(nullForeArmR.GetAbsPos())
            nullForeArmR.SetFrozenRot(nullForeArmR.GetAbsRot())

            nullForeArm.SetRelPos(c4d.Vector(0, 0, 0))
            nullForeArm.SetRelRot(c4d.Vector(0, 0, 0))
            nullForeArmR.SetRelPos(c4d.Vector(0, 0, 0))
            nullForeArmR.SetRelRot(c4d.Vector(0, 0, 0))

    def lockAllModels(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for obj in scene:
            if obj.GetType() == 5100:
                lockLayer = ikmaxUtils().layerSettings(obj, 1, 1)

    def limitFloorContact(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()

        def addProtTag(obj):
            xtag = c4d.BaseTag(c4d.Tprotection)
            xtag[c4d.PROTECTION_P] = 2
            xtag[c4d.PROTECTION_S] = False
            xtag[c4d.PROTECTION_R] = False
            xtag[c4d.PROTECTION_P_X] = False
            xtag[c4d.PROTECTION_P_Y] = True
            xtag[c4d.PROTECTION_P_Z] = False
            xtag[c4d.PROTECTION_P_MIN_Y] = 0
            xtag[c4d.PROTECTION_P_MAX_Y] = 1000000
            obj.InsertTag(xtag)

        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for obj in scene:
            if 'Foot_PlatformBase' in obj.GetName():
                addProtTag(obj)

        c4d.EventAdd()

    def matBumpFix(self):
        doc = c4d.documents.GetActiveDocument()
        docMaterials = doc.GetMaterials()
        for mat in docMaterials:
            try:
                mat[c4d.MATERIAL_BUMP_STRENGTH] = 0.2
            except:
                pass
            try:
                mat[c4d.MATERIAL_DISPLAY_USE_BUMP] = False
            except:
                pass
            try:
                mat[c4d.MATERIAL_PREVIEWSIZE] = 9
            except:
                pass

    def unparentObjsFromRig(self):
        doc = documents.GetActiveDocument()
        jointHip = doc.SearchObject('hip')
        if jointHip:
            dazRig = jointHip.GetUp()
            rigChildren = ikmaxUtils().iterateObjChilds(dazRig)
            for obj in rigChildren:
                if obj.GetUp() == dazRig:
                    if obj.GetType() == 5100:
                        geoDetected = True
                        obj.SetBit(c4d.BIT_ACTIVE)
                        c4d.CallCommand(12106, 12106)  # Cut
                        c4d.CallCommand(12108, 12108)  # Paste
                        c4d.CallCommand(12113, 12113)  # Deselect All
            c4d.EventAdd()

    def hideSomeJoints(self):
        doc = documents.GetActiveDocument()
        jointHip = doc.SearchObject('hip')
        jointHead = doc.SearchObject('head')
        if not jointHip:
            return 0
        dazRig = jointHip.GetUp()
        facialRig = jointHead.GetUp()
        rigJoints = ikmaxUtils().iterateObjChilds(jointHip)
        facialJoints = ikmaxUtils().iterateObjChilds(facialRig)
        for obj in rigJoints:
            obj()[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 0
            obj()[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 0
        jointHip()[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 0
        jointHip()[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 0
        for obj in facialJoints:
            obj()[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 1
            obj()[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 1
        dazRig()[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 1
        dazRig()[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 1

        c4d.EventAdd()


    def getAllObjs(self):  # Return All OBJS from Scene! Works!
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()

        def GetAllChildren(topObj, childList):  # Get all objects down the hierarchy
            childList.extend(topObj.GetChildren())

            for each in topObj.GetChildren():
                if each.GetDown() != None:
                    GetAllChildren(each, childList)

            return childList

        objList = []
        while obj:
            allChildren = GetAllChildren(obj, [])
            if allChildren:
                for o in allChildren:
                    objList.append(o)
            objList.append(obj)
            obj = obj.GetNext()

        return objList

    def replaceMat(self, oldMat, newMat):
        doc = documents.GetActiveDocument()

        def tagsIterator(obj):
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

        # Script starts here:
        for o in self.getAllObjs():
            objTags = tagsIterator(o)
            if objTags:
                for t in objTags:
                    if t.GetType() == 5616:
                        if t[c4d.TEXTURETAG_MATERIAL] == oldMat:
                            t[c4d.TEXTURETAG_MATERIAL] = newMat

        c4d.EventAdd()

    def reduceSimilarMaterials(self):
        doc = c4d.documents.GetActiveDocument()

        # Process for all materials of scene
        docMaterials = doc.GetMaterials()

        def getMatTextures(mat):
            try:
                doc = c4d.documents.GetActiveDocument()
                matName = mat.GetName()
                matDiffuseText = ''
                matAlphaText = ''
                if mat[c4d.MATERIAL_COLOR_SHADER]:
                    matDiffuseText = mat[c4d.MATERIAL_COLOR_SHADER][c4d.BITMAPSHADER_FILENAME]

                if mat[c4d.MATERIAL_ALPHA_SHADER]:
                    matAlphaText = mat[c4d.MATERIAL_ALPHA_SHADER][c4d.BITMAPSHADER_FILENAME]

                return matDiffuseText, matAlphaText

            except:
                print('Skip reduce Mat...')

        def CompareMatTexts(sourceMat):
            docMaterials = doc.GetMaterials()

            textDifuse = getMatTextures(sourceMat)[0]
            textAlpha = getMatTextures(sourceMat)[1]
            similarMats = []
            for mat in docMaterials:
                if textDifuse == getMatTextures(mat)[0] and textAlpha == getMatTextures(mat)[1]:
                    if mat != sourceMat:
                        similarMats.append(mat)

            return similarMats

        skipMatList = ['Sclera','Cornea','EyeMoisture','Irises']
        dontRemoveList = ['Teeth', 'Mouth', 'Lips', 'Sclera','Cornea','EyeMoisture','Irises']

        nameSkin = ['Legs', 'Torso', 'Arms', 'Face', 'Fingernails', 'Toenails', 'Lips', 'EyeSocket', 'Ears',
                    'Feet', 'Nipples', 'Forearms', 'Hips', 'Neck', 'Shoulders', 'Hands', 'Head', 'Nostrils']

        doc = c4d.documents.GetActiveDocument()
        docMaterials = doc.GetMaterials()

        for mat in docMaterials:
            try:
                if mat.GetName() not in skipMatList:
                    print(mat.GetName())
                    if getMatTextures(mat)[0] or getMatTextures(mat)[1]:
                        similarMats = CompareMatTexts(mat)
                        if similarMats:
                            for obj in similarMats:
                                objName = obj.GetName()
                                removeit = True
                                for x in dontRemoveList:
                                    if objName in x:
                                        removeit = False

                                if removeit == True:
                                    c4d.EventAdd()
                         
                                skipMatList.append(obj.GetName())
            except:
                print('Skip reduce Mat...')

        # Rename mats based on the texture filename...
        for mat in docMaterials:
            if mat.GetName() not in dontRemoveList:
                if getMatTextures(mat) != None:
                    texDiffuse = getMatTextures(mat)[0]
                    if texDiffuse:
                        head, tail = os.path.split(getMatTextures(mat)[0])
                        newName = tail.split('.')[0]
                        if mat.GetName() in nameSkin:
                            mat.SetName('Skin_' + newName)
                        else:
                            mat.SetName(newName)

        c4d.EventAdd()

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

    def cleanMorphsGeoRemove(self):
        doc = documents.GetActiveDocument()

        listObjs = []
        meshName = dazName.replace('_', '')

        caca = doc.GetFirstObject()
        # listObjs.append(caca)

        while caca.GetNext():
            listObjs.append(caca)
            caca = caca.GetNext()

        for x in listObjs:
            if meshName not in x.GetName():
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

    def protectIKMControls(self):
        doc = documents.GetActiveDocument()

        def protectTag(jointName, protectPreset):
            doc = documents.GetActiveDocument()
            obj = doc.SearchObject(jointName)
            tagProtec = c4d.BaseTag(5629)  # Protection Tag

            if protectPreset == "finger":
                if obj:
                    obj[c4d.ID_BASEOBJECT_ROTATION_ORDER] = 6
                tagProtec[c4d.PROTECTION_P_X] = False
                tagProtec[c4d.PROTECTION_P_Y] = False
                tagProtec[c4d.PROTECTION_P_Z] = False
                tagProtec[c4d.PROTECTION_S_X] = False
                tagProtec[c4d.PROTECTION_S_Y] = False
                tagProtec[c4d.PROTECTION_S_Z] = False
                tagProtec[c4d.PROTECTION_R_X] = True
                tagProtec[c4d.PROTECTION_R_Y] = False
                tagProtec[c4d.PROTECTION_R_Z] = True
            if protectPreset == "position":
                tagProtec[c4d.PROTECTION_P_X] = True
                tagProtec[c4d.PROTECTION_P_Y] = True
                tagProtec[c4d.PROTECTION_P_Z] = True
                tagProtec[c4d.PROTECTION_S_X] = False
                tagProtec[c4d.PROTECTION_S_Y] = False
                tagProtec[c4d.PROTECTION_S_Z] = False
                tagProtec[c4d.PROTECTION_R_X] = False
                tagProtec[c4d.PROTECTION_R_Y] = False
                tagProtec[c4d.PROTECTION_R_Z] = False
            if protectPreset == "twist":
                tagProtec[c4d.PROTECTION_P_X] = True
                tagProtec[c4d.PROTECTION_P_Y] = True
                tagProtec[c4d.PROTECTION_P_Z] = True
                tagProtec[c4d.PROTECTION_S_X] = False
                tagProtec[c4d.PROTECTION_S_Y] = False
                tagProtec[c4d.PROTECTION_S_Z] = False
                tagProtec[c4d.PROTECTION_R_X] = True
                tagProtec[c4d.PROTECTION_R_Y] = False
                tagProtec[c4d.PROTECTION_R_Z] = True
            if obj:
                obj.InsertTag(tagProtec)
                c4d.EventAdd()

        # LEFT
        protectTag(dazName + 'jMiddle2', 'finger')
        protectTag(dazName + 'jMiddle3', 'finger')
        protectTag(dazName + 'jMiddle4', 'finger')
        protectTag(dazName + 'jRing2', 'finger')
        protectTag(dazName + 'jRing3', 'finger')
        protectTag(dazName + 'jRing4', 'finger')
        protectTag(dazName + 'jPink2', 'finger')
        protectTag(dazName + 'jPink3', 'finger')
        protectTag(dazName + 'jPink4', 'finger')
        protectTag(dazName + 'jIndex2', 'finger')
        protectTag(dazName + 'jIndex3', 'finger')
        protectTag(dazName + 'jIndex4', 'finger')
        # RIGHT
        protectTag(dazName + 'jMiddle2___R', 'finger')
        protectTag(dazName + 'jMiddle3___R', 'finger')
        protectTag(dazName + 'jMiddle4___R', 'finger')
        protectTag(dazName + 'jRing2___R', 'finger')
        protectTag(dazName + 'jRing3___R', 'finger')
        protectTag(dazName + 'jRing4___R', 'finger')
        protectTag(dazName + 'jPink2___R', 'finger')
        protectTag(dazName + 'jPink3___R', 'finger')
        protectTag(dazName + 'jPink4___R', 'finger')
        protectTag(dazName + 'jIndex2___R', 'finger')
        protectTag(dazName + 'jIndex3___R', 'finger')
        protectTag(dazName + 'jIndex4___R', 'finger')

        # MIDDLE
        protectTag(dazName + 'Spine_ctrl', 'position')
        protectTag(dazName + 'Chest_ctrl', 'position')
        protectTag(dazName + 'Neck_ctrl', 'position')
        protectTag(dazName + 'Head_ctrl', 'position')


    def unhideProps(self):
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject('hip')
        ObjectIterator(obj)
        for o in ObjectIterator(obj):
            if o.GetType() == 5100 or o.GetType() == 5140:
                o[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 0
                o[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 0
        c4d.EventAdd()


    def fixDaz8rot(self, master, mode='', jointToFix='', rotValue=0):
        doc = documents.GetActiveDocument()

        nullObj = c4d.BaseObject(c4d.Onull)  # Create new cube
        doc.InsertObject(nullObj)
        armJoint = doc.SearchObject('lShldrBend')
        handJoint = doc.SearchObject('lForearmBend')

        mg = jointToFix.GetMg()
        nullObj.SetMg(mg)

        nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0
        nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0
        nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0
        c4d.EventAdd()

        slaveObj = nullObj
        masterObj = master

        def addConstraint(slaveObj, masterObj, mode='Parent'):
            if mode == "Parent":
                constraintTAG = c4d.BaseTag(1019364)

                constraintTAG[c4d.EXPRESSION_ENABLE] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR_MAINTAIN] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
                constraintTAG[10005] = True
                constraintTAG[10007] = True
                constraintTAG[10001] = masterObj

                PriorityDataInitial = c4d.PriorityData()
                PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_MODE, c4d.CYCLE_EXPRESSION)
                PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_PRIORITY, 0)
                PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_CAMERADEPENDENT, 0)
                constraintTAG[c4d.EXPRESSION_PRIORITY] = PriorityDataInitial
            slaveObj.InsertTag(constraintTAG)

        mg = slaveObj.GetMg()
        constraintTAG = c4d.BaseTag(1019364)

        if mode == "ROTATION":
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
            constraintTAG[10005] = False
            constraintTAG[10006] = False
            constraintTAG[10001] = masterObj
        if mode == "AIM":
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM] = True
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_MAINTAIN] = False

            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_X] = True
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_Y] = True
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_Z] = True
            constraintTAG[20004] = 0  # Axis X-
            constraintTAG[20001] = masterObj

        slaveObj.InsertTag(constraintTAG)

        c4d.EventAdd()
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        constraintTAG.Remove()

        addConstraint(jointToFix, slaveObj)

        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)

        rotZ = nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z]
        if rotZ > 0.8:
            slaveObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0
            slaveObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0
            slaveObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = rotValue

        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)

        caca = jointToFix.GetFirstTag()
        caca.Remove()
        slaveObj.Remove()

    def dazGen8fix(self):
        doc = documents.GetActiveDocument()

        mainJoint = doc.SearchObject('lShldrBend')
        goalJoint = doc.SearchObject('lForearmBend')
        if mainJoint:
            self.fixDaz8rot(goalJoint, 'AIM', mainJoint)

            jointOposite = doc.SearchObject('rShldrBend')
            rx = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X]
            ry = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y]
            rz = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z]

            jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = rx * -1
            jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = ry
            jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = rz * -1


    


    def autoIK(self):
        #self.buttonsChangeState(False)
        doc = c4d.documents.GetActiveDocument()
        DazToC4D().morphsGroupMoveUp()

        obj = doc.SearchObject('hip')
        if obj:
            AllSceneToZero().sceneToZero()

            applyDazIK()

            dazToC4Dutils().changeSkinType()
            DazToC4D().unhideProps()

            c4d.EventAdd()
            c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD   | c4d.DRAWFLAGS_STATICBREAK)

            #DONE-AUTOIMPORT

            # DazToC4D().cleanMorphsGeoRemove()
            DazToC4D().protectIKMControls()


        DazToC4D().limitFloorContact()
        DazToC4D().lockAllModels()
        DazToC4D().freezeTwistBones()
        DazToC4D().figureFixBrute()

        dazToC4Dutils().protectTwist()


        #self.buttonsChangeState(True)
        c4d.CallCommand(12168, 12168)  # Delete Unused Materials
        # quit()  # -------------------------------------------------

        print('Done')


