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

from Globals import *

class DazToC4dUtils():

    mesh_name = daz_name

    def find_text_in_file(self, matName, propertyName):
        dazExtraMapsFile = r'C:\\TEMP3D\\DazToC4D.xml'
        dazExtraMapsFileMac = '/users/Shared/temp3d/DazToC4D.xml'

        if os.path.exists(dazExtraMapsFileMac):
            dazExtraMapsFile = dazExtraMapsFileMac

        if os.path.exists(dazExtraMapsFile) == False:
            print('...')
            return
        xmlFilePath = dazExtraMapsFile
        xmlFile = ElementTree.parse(xmlFilePath)
        xmlMaterials = xmlFile.getroot()
        xmlMaterial = xmlMaterials.find('material')
        texturePath = None
        for node in xmlMaterials:
            if node.attrib['name'] == matName:
                #xmlValue = node.attrib[xmlMatProperty]
                try:
                    texturePath = node.attrib[propertyName]
                except:
                    pass

        if texturePath == '':
            return None

        if texturePath:
            texturePath = os.path.abspath(texturePath)  # OS Path Fix...

        return texturePath

    def read_extra_maps_from_file(self):
        doc = c4d.documents.GetActiveDocument()
        docMaterials = doc.GetMaterials()
        for mat in docMaterials:
            matName = mat.GetName()
            extraMapBump = self.find_text_in_file(matName, 'bump')
            extraMapBump2 = self.find_text_in_file(matName, 'bump2')
            if extraMapBump == None and extraMapBump2 != None:
                extraMapBump = extraMapBump2
            extraMapNormal = self.find_text_in_file(matName, 'Normal_Map_Map')
            if extraMapNormal != None and extraMapBump == None:
                extraMapBump = extraMapNormal
            if extraMapBump != None:
                mat[c4d.MATERIAL_USE_BUMP] = True
                shda = c4d.BaseList2D(c4d.Xbitmap)
                shda[c4d.BITMAPSHADER_FILENAME] = extraMapBump
                mat[c4d.MATERIAL_BUMP_SHADER] = shda
                mat.InsertShader(shda)

            extraMapNormal = self.find_text_in_file(matName, 'Normal_Map_Map')
            if extraMapNormal != None:
                mat[c4d.MATERIAL_USE_NORMAL] = True
                shda = c4d.BaseList2D(c4d.Xbitmap)
                shda[c4d.BITMAPSHADER_FILENAME] = extraMapNormal
                mat[c4d.MATERIAL_NORMAL_SHADER] = shda
                mat.InsertShader(shda)

            extraMapSpec = self.find_text_in_file(
                matName, 'Glossy_Layered_Weight_Map')
            extraMapSpec2 = self.find_text_in_file(matName, 'spec')
            extraMapGlossy = self.find_text_in_file(matName, 'Metallicity_Map')
            if extraMapSpec2 != None and extraMapSpec == None:
                extraMapSpec = extraMapSpec2
            if extraMapGlossy != None and extraMapSpec == None:
                extraMapSpec = extraMapGlossy
            if extraMapSpec != None:
                mat[c4d.MATERIAL_USE_REFLECTION] = True
                shda = c4d.BaseList2D(c4d.Xbitmap)
                shda[c4d.BITMAPSHADER_FILENAME] = extraMapSpec
                layer = mat.GetReflectionLayerIndex(0)
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_TRANS_TEXTURE] = shda
                # mat[c4d.MATERIAL_BUMP_SHADER]=shda
                mat.InsertShader(shda)
                try:
                    mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION] = 4
                except:
                    pass

            extraMapGlossyRough = self.find_text_in_file(
                matName, 'Glossy_Roughness_Map')
            if extraMapGlossyRough != None:
                mat[c4d.MATERIAL_USE_REFLECTION] = True
                shda = c4d.BaseList2D(c4d.Xbitmap)
                shda[c4d.BITMAPSHADER_FILENAME] = extraMapGlossyRough
                layer = mat.GetReflectionLayerIndex(0)
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_SHADER_ROUGHNESS] = shda
                try:
                    mat.InsertShader(shda)
                    mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION] = 4
                except:
                    pass

    def zero_twist_rotation_fix(self, twistName, jointName):
        doc = c4d.documents.GetActiveDocument()

        objTarget = doc.SearchObject(twistName)
        joint = doc.SearchObject(jointName)
        xtag = None
        objTags = TagIterator(joint)
        for t in objTags:
            if 'Constraint' in t.GetName():
                xtag = t
        xtag[10001] = None

        mgTarget = objTarget.GetMg()
        newNull = c4d.BaseObject(c4d.Onull)
        newNull.SetName('TARGET')
        newNull.SetMg(mgTarget)
        doc.InsertObject(newNull)
        newNull[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0.0

        c4d.EventAdd()
        objTarget.SetMg(newNull.GetMg())
        c4d.EventAdd()
        xtag[10001] = objTarget

        objTarget[c4d.ID_BASEOBJECT_ROTATION_ORDER] = 6
        c4d.EventAdd()

    def protect_twist(self):
        doc = c4d.documents.GetActiveDocument()

        def addProtTag(obj):
            xtag = c4d.BaseTag(c4d.Tprotection)
            xtag[c4d.PROTECTION_P] = 1
            xtag[c4d.PROTECTION_S] = False
            xtag[c4d.PROTECTION_R] = 1
            xtag[c4d.PROTECTION_R_X] = True
            xtag[c4d.PROTECTION_R_Y] = False
            xtag[c4d.PROTECTION_R_Z] = True

            obj.InsertTag(xtag)
            c4d.EventAdd()

        nullForeArm = doc.SearchObject(daz_name + 'ForearmTwist_ctrl')
        nullForeArmR = doc.SearchObject(daz_name + 'ForearmTwist_ctrl___R')
        addProtTag(nullForeArm)
        addProtTag(nullForeArmR)

    def fix_moisure(self):
        def removeMoisureTag(obj):
            # validate object and selectiontag
            if not obj:
                return
            if not obj.IsInstanceOf(c4d.Opolygon):
                return
            tags = obj.GetTags()

            # deselect current polygonselection and store a backup to reselect
            polyselection = obj.GetPolygonS()

            # define the name to search for
            name = "EyeMoisture"

            # loop through the tags and check if name and type fits
            # if so split
            t = obj.GetFirstTag()
            while t:
                if t.GetType() == c4d.Tpolygonselection:
                    if name in t.GetName():

                        # select polygons from selectiontag
                        tagselection = t.GetBaseSelect()
                        tagselection.CopyTo(polyselection)

                        # split: polygonselection to a new object
                        sec = utils.SendModelingCommand(command=c4d.MCOMMAND_DELETE,
                                                        list=[obj],
                                                        mode=c4d.MODELINGCOMMANDMODE_POLYGONSELECTION,
                                                        doc=doc)

                        if not sec:
                            print(sec)
                            return

                        # sec[0].InsertAfter(op)

                t = t.GetNext()

            c4d.EventAdd()

        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for obj in scene:
            if obj.GetType() == 5100:
                removeMoisureTag(obj)

    def fix_daz_foot_rot(self, master, mode='', jointToFix='', rotValue=0):
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
                PriorityDataInitial.SetPriorityValue(
                    c4d.PRIORITYVALUE_MODE, c4d.CYCLE_EXPRESSION)
                PriorityDataInitial.SetPriorityValue(
                    c4d.PRIORITYVALUE_PRIORITY, 0)
                PriorityDataInitial.SetPriorityValue(
                    c4d.PRIORITYVALUE_CAMERADEPENDENT, 0)
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
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_Y] = False
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_Z] = False
            constraintTAG[20004] = 0  # Axis X-
            constraintTAG[20001] = masterObj

        slaveObj.InsertTag(constraintTAG)
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        c4d.EventAdd()
        caca = slaveObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X]

        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)

        addConstraint(jointToFix, slaveObj)
        constraintTAG.Remove()

        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)

        slaveObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = -1.571
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)

        caca = jointToFix.GetFirstTag()
        caca.Remove()
        slaveObj.Remove()

    def daz_foot_rot_fix(self):
        doc = documents.GetActiveDocument()

        mainJoint = doc.SearchObject('lFoot')
        goalJoint = doc.SearchObject('lToe')
        self.fix_daz_foot_rot(goalJoint, 'AIM', mainJoint)

        jointOposite = doc.SearchObject('rFoot')
        rx = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X]
        ry = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y]
        rz = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z]

        jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = rx * -1
        jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0
        jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0

    def ik_goals_zero_rot(self):
        def ikZeroRot(jointObj):
            tag = jointObj.GetFirstTag()
            goalObj = tag[10001]

            ry = jointObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y]

            tag[10001] = None

            jointObj[c4d.ID_BASEOBJECT_FROZEN_ROTATION, c4d.VECTOR_Y] = ry
            jointObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0

            c4d.EventAdd()
            c4d.DrawViews(
                c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)

            c4d.EventAdd()

            goalObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0
            goalObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0
            goalObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0
            goalObj[c4d.ID_BASEOBJECT_FROZEN_ROTATION, c4d.VECTOR_X] = 0
            goalObj[c4d.ID_BASEOBJECT_FROZEN_ROTATION, c4d.VECTOR_Y] = 0
            goalObj[c4d.ID_BASEOBJECT_FROZEN_ROTATION, c4d.VECTOR_Z] = 0

            tag[c4d.ID_CA_CONSTRAINT_TAG_PSR_MAINTAIN] = True

            c4d.EventAdd()
            tag[10001] = goalObj

            c4d.EventAdd()
            c4d.DrawViews(
                c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
            c4d.EventAdd()

        doc = documents.GetActiveDocument()

        jointObj = doc.SearchObject(daz_name + 'jHand')
        ikZeroRot(jointObj)

        jointObj = doc.SearchObject(daz_name + 'jHand___R')
        ikZeroRot(jointObj)

        jointObj = doc.SearchObject(daz_name + 'jUpLeg.Pole___R')
        jointObj[c4d.ID_BASEOBJECT_FROZEN_ROTATION, c4d.VECTOR_X] = 0
        jointObj = doc.SearchObject(daz_name + 'jArm.Pole___R')
        jointObj[c4d.ID_BASEOBJECT_FROZEN_ROTATION, c4d.VECTOR_X] = 0
        c4d.EventAdd()

    def get_daz_mesh(self):
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject('hip')
        if obj:
            dazRigName = obj.GetUp().GetName()
            dazMeshObj = doc.SearchObject(dazRigName + '.Shape')
            return dazMeshObj
        return None

    def initial_display_settings(self):
        doc = documents.GetActiveDocument()
        daz_name = self.get_daz_mesh()
        if daz_name:
            daz_name = daz_name.GetName().replace('.Shape', '')
            daz_name = daz_name + '_'

            def hideJoint(obj, value):
                obj[c4d.ID_CA_JOINT_OBJECT_BONE_DISPLAY] = value
                obj[c4d.ID_CA_JOINT_OBJECT_JOINT_DISPLAY] = value

            def hideJoints(jName, value):
                jointParent = doc.SearchObject(daz_name + jName)
                if jointParent:
                    listObjs = ObjectIterator(jointParent)
                    for obj in listObjs:
                        hideJoint(obj, value)

            objPelvis = doc.SearchObject(daz_name + 'jPelvis')
            hideJoint(objPelvis, 0)
            hideJoints('jSpine', 0)
            hideJoints('jUpLeg', 0)
            hideJoints('jUpLeg___R', 0)

            hideJoints('jHand', 2)  # Show
            hideJoints('jHand___R', 2)  # Show

            c4d.EventAdd()

    def joint_display_initial_settings(self):

        [c4d.ID_CA_JOINT_OBJECT_JOINT_DISPLAY] = 0
        self.get_daz_mesh()

        boneDisplay = self.jointPelvis[c4d.ID_CA_JOINT_OBJECT_BONE_DISPLAY]
        if boneDisplay != 0:
            boneDisplay = 0
        else:
            boneDisplay = 2
        for x in IkMaxUtils().iterateObjChilds(self.jointPelvis):
            x[c4d.ID_CA_JOINT_OBJECT_BONE_DISPLAY] = boneDisplay
        self.jointPelvis[c4d.ID_CA_JOINT_OBJECT_BONE_DISPLAY] = boneDisplay

        c4d.EventAdd()

    def change_skin_type(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()

        scene = ObjectIterator(obj)
        baseObjs = []

        for obj in scene:
            # print obj.GetName(), obj.GetType()

            if obj.GetType() == 1019363:
                obj[c4d.ID_CA_SKIN_OBJECT_TYPE] = 1

        c4d.EventAdd()

    def twist_bone_setup(self):
        doc = documents.GetActiveDocument()

        def aimObj(slave, master, mode="", searchObj=1):
            doc = documents.GetActiveDocument()
            if searchObj == 1:
                slaveObj = doc.SearchObject(slave)
                masterObj = doc.SearchObject(master)
            else:
                slaveObj = slave
                masterObj = master
            mg = slaveObj.GetMg()

            constraintTAG = c4d.BaseTag(1019364)

            if mode == "ROTATION":
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
                constraintTAG[10005] = False
                constraintTAG[10006] = False
                constraintTAG[10001] = masterObj
            if mode == "AIM":
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_MAINTAIN] = False
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_X] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_Y] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_Z] = True
                constraintTAG[20004] = 0  # Axis X-
                constraintTAG[20001] = masterObj

            slaveObj.InsertTag(constraintTAG)

            # constraintTAG.Remove()

            c4d.EventAdd()
            c4d.DrawViews(
                c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
            constraintTAG.Remove()

        twistJoint = doc.SearchObject(daz_name + 'ForearmTwist_ctrl')
        handJoint = doc.SearchObject('lHand')
        aimObj(twistJoint, handJoint, 'AIM', 0)
        twistJoint = doc.SearchObject(daz_name + 'ForearmTwist_ctrl___R')
        handJoint = doc.SearchObject('rHand')
        aimObj(twistJoint, handJoint, 'AIM', 0)

    def fix_constraints(self):
        def fixConstraint(jointName):
            doc = documents.GetActiveDocument()
            obj = doc.SearchObject(jointName)
            if obj:
                tag = obj.GetFirstTag()
                tag[c4d.ID_CA_CONSTRAINT_TAG_PSR_MAINTAIN] = True
                c4d.EventAdd()

        fixConstraint('lForearmTwist')
        fixConstraint('rForearmTwist')

    def hide_rig(self):
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject('hip')
        dazRig = obj.GetUp()
        guideNulls = IkMaxUtils().iterateObjChilds(dazRig)
        for obj in guideNulls:
            obj()[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 1
            obj()[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 1
        dazRig()[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 1
        dazRig()[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 1

        c4d.EventAdd()

    def add_protection(self):

        def protectObj(objName, lock='Position'):
            doc = documents.GetActiveDocument()
            obj = doc.SearchObject(objName)
            protectionTAG = c4d.BaseTag(c4d.Tprotection)
            if lock == 'Position':
                protectionTAG[c4d.PROTECTION_P_X] = True
                protectionTAG[c4d.PROTECTION_P_Y] = True
                protectionTAG[c4d.PROTECTION_P_Z] = True
                protectionTAG[c4d.PROTECTION_R_X] = False
                protectionTAG[c4d.PROTECTION_R_Y] = False
                protectionTAG[c4d.PROTECTION_R_Z] = False
                protectionTAG[c4d.PROTECTION_S_Z] = False
                protectionTAG[c4d.PROTECTION_S_Y] = False
                protectionTAG[c4d.PROTECTION_S_X] = False
            obj.InsertTag(protectionTAG)
            c4d.EventAdd()

        protectObj(daz_name + 'Toe_Rot')
        protectObj(daz_name + 'Toe_Rot___R')
        protectObj(daz_name + 'Foot_Roll')
        protectObj(daz_name + 'Foot_Roll___R')

    def ungroup_daz_geo(self):
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject('hip')
        children = obj.GetUp().GetChildren()
        c4d.CallCommand(12113, 12113)  # Deselect All
        geoDetected = False
        for c in children:
            if c.GetType() == 5100:
                geoDetected = True
                c.SetBit(c4d.BIT_ACTIVE)
        if geoDetected == True:
            c4d.CallCommand(12106, 12106)  # Cut
            c4d.CallCommand(12108, 12108)  # Paste
        c4d.CallCommand(12113, 12113)  # Deselect All
        c4d.EventAdd()

    def add_head_end_bone(self):
        doc = documents.GetActiveDocument()
        # meshName = dazName + '_'
        jointHeadEnd = doc.SearchObject('head_end')
        if jointHeadEnd == None:
            jointCollar = doc.SearchObject('lCollar')

            jointHead = doc.SearchObject('head')
            newJoint = c4d.BaseObject(c4d.Ojoint)
            newJoint.SetName('head_end')
            doc.InsertObject(newJoint)
            newJoint.InsertUnder(jointHead)
            newJoint.SetMg(jointHead.GetMg())

            headHeight = 9
            if jointCollar:
                headHeight = jointCollar[c4d.ID_CA_JOINT_OBJECT_LENGTH]

            newJoint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y] = headHeight
            c4d.EventAdd()

    def remove_constraint_tags(self, obj):

        doc = c4d.documents.GetActiveDocument()
        # obj = doc.SearchObject('pelvis')
        tags = TagIterator(obj)
        try:
            for t in tags:
                if 'Constraint' in t.GetName():
                    t.Remove()
        except:
            pass
        c4d.EventAdd()

    def add_constraint(self, slave, master, mode='Parent'):
        doc = documents.GetActiveDocument()
        slaveObj = doc.SearchObject(slave)
        masterObj = doc.SearchObject(master)
        self.remove_constraint_tags(slaveObj)
        # removeConstraintTags(masterObj)

        if mode == "Parent":
            constraintTAG = c4d.BaseTag(1019364)

            constraintTAG[c4d.EXPRESSION_ENABLE] = True
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR_MAINTAIN] = True
            # constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PARENT_FROZEN] = False
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
            constraintTAG[10005] = True
            constraintTAG[10007] = True
            constraintTAG[10001] = masterObj
            # constraintTAG[30009, 1000] = c4d.Vector(nullSlave.GetRelPos()[0], nullSlave.GetRelPos()[1], nullSlave.GetRelPos()[2])
            # constraintTAG[30009, 1002] = c4d.Vector(nullSlave.GetRelRot()[0], nullSlave.GetRelRot()[1], nullSlave.GetRelRot()[2])

            PriorityDataInitial = c4d.PriorityData()
            PriorityDataInitial.SetPriorityValue(
                c4d.PRIORITYVALUE_MODE, c4d.CYCLE_EXPRESSION)
            PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_PRIORITY, 0)
            PriorityDataInitial.SetPriorityValue(
                c4d.PRIORITYVALUE_CAMERADEPENDENT, 0)
            constraintTAG[c4d.EXPRESSION_PRIORITY] = PriorityDataInitial
        try:
            slaveObj.InsertTag(constraintTAG)
        except:
            print('constr skip')
            pass

    def parentTo(self, childName, parentName):
        doc = documents.GetActiveDocument()
        child = doc.SearchObject(childName)
        parent = doc.SearchObject(parentName)
        mg = child.GetMg()
        child.InsertUnder(parent)
        child.SetMg(mg)

    def extend_3d_line(self, nameA, nameB, actObjName, offset=1):
        doc = documents.GetActiveDocument()
        actObj = doc.SearchObject(meshName + actObjName)
        # Aobj = doc.SearchObject('A') #Direction line Start
        # Bobj = doc.SearchObject('B') #Direction line End
        Aobj = doc.SearchObject(meshName + nameA)  # Direction line Start
        Bobj = doc.SearchObject(meshName + nameB)  # Direction line End

        targetObj = c4d.BaseObject(c4d.Onull)
        targetObj.SetName('TARGET')
        doc.InsertObject(targetObj)

        targetObjExtend = c4d.BaseObject(c4d.Onull)
        targetObjExtend.SetName('TARGET_Extend')
        doc.InsertObject(targetObjExtend)
        targetObj.SetMg(Aobj.GetMg())

        targetObjExtend.InsertUnder(targetObj)

        constraintTAG = c4d.BaseTag(1019364)
        constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM] = True
        constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_MAINTAIN] = False
        constraintTAG[20004] = 2
        constraintTAG[20001] = Bobj
        targetObj.InsertTag(constraintTAG)

        caca = targetObj.GetFirstTag()
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        caca.Remove()
        targetMg = None
        try:
            targetObjExtend.SetMg(Bobj.GetMg())
            objDistance = targetObjExtend[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z]
            targetObj.SetAbsPos(Bobj.GetAbsPos())
            targetObjExtend[c4d.ID_BASEOBJECT_REL_POSITION,
                            c4d.VECTOR_Z] = objDistance * offset
            targetObjExtend[c4d.NULLOBJECT_DISPLAY] = 9

            targetMg = targetObjExtend.GetMg()
            actObj.SetMg(targetObjExtend.GetMg())
        except:
            print('skip extend')

        targetObj.Remove()

        c4d.EventAdd()
        return targetMg

    def move_to_obj(self, source, target):
        doc = documents.GetActiveDocument()
        parentGuidesName = daz_name + '__IKM-Guides'

        if doc.SearchObject(parentGuidesName) == None:
            newNull = c4d.BaseObject(c4d.Onull)
            newNull.SetName(parentGuidesName)
            doc.InsertObject(newNull)

        guidesParent = doc.SearchObject(parentGuidesName)

        newNull = c4d.BaseObject(c4d.Onull)
        newNull.SetName(source)
        doc.InsertObject(newNull)
        newNull[c4d.NULLOBJECT_DISPLAY] = 11
        newNull[c4d.NULLOBJECT_RADIUS] = 1
        newNull[c4d.NULLOBJECT_ORIENTATION] = 1

        # sourceObj = doc.SearchObject(source)
        sourceObj = newNull
        targetObj = doc.SearchObject(target)
        sourceObj.SetMg(targetObj.GetMg())

        mg = sourceObj.GetMg()
        sourceObj.InsertUnder(guidesParent)
        sourceObj.SetMg(mg)

        c4d.EventAdd()

    def guides_to_daz(self):
        doc = documents.GetActiveDocument()
        self.add_head_end_bone()

        if doc.SearchObject('lCollar'):
            self.move_to_obj(meshName + 'Collar', 'lCollar')
            self.move_to_obj(meshName + 'Collar___R', 'rCollar')
        else:
            self.move_to_obj(meshName + 'Collar', 'chest')
            self.move_to_obj(meshName + 'Collar___R', 'chest')

        if doc.SearchObject('abdomenUpper'):
            self.move_to_obj(meshName + 'AbdomenUpper', 'abdomenUpper')
            self.move_to_obj(meshName + 'ChestUpper', 'chestUpper')

        if doc.SearchObject('lShldr'):
            self.move_to_obj(meshName + 'Shoulder', 'lShldr')
            self.move_to_obj(meshName + 'Elbow', 'lForeArm')

        if doc.SearchObject('lShldrBend'):
            self.move_to_obj(meshName + 'Shoulder', 'lShldrBend')
            self.move_to_obj(meshName + 'Elbow', 'lForearmBend')

        self.move_to_obj(meshName + 'Hand', 'lHand')
        self.move_to_obj(meshName + 'Index1', 'lIndex1')
        self.move_to_obj(meshName + 'Index2', 'lIndex2')
        if doc.SearchObject('lIndex3'):
            self.move_to_obj(meshName + 'Index3', 'lIndex3')
            self.move_to_obj(meshName + 'Index_end', 'lIndex3')
        self.move_to_obj(meshName + 'Middle1', 'lMid1')
        self.move_to_obj(meshName + 'Middle2', 'lMid2')
        if doc.SearchObject('lMid3'):
            self.move_to_obj(meshName + 'Middle3', 'lMid3')
            self.move_to_obj(meshName + 'Middle_end', 'lMid3')
        self.move_to_obj(meshName + 'Ring1', 'lRing1')
        self.move_to_obj(meshName + 'Ring2', 'lRing2')
        if doc.SearchObject('lRing3'):
            self.move_to_obj(meshName + 'Ring3', 'lRing3')
            self.move_to_obj(meshName + 'Ring_end', 'lRing3')
        self.move_to_obj(meshName + 'Pinky1', 'lPinky1')
        self.move_to_obj(meshName + 'Pinky2', 'lPinky2')
        if doc.SearchObject('lPinky3'):
            self.move_to_obj(meshName + 'Pinky3', 'lPinky3')
            self.move_to_obj(meshName + 'Pinky_end', 'lPinky3')
        self.move_to_obj(meshName + 'Thumb1', 'lThumb1')
        self.move_to_obj(meshName + 'Thumb2', 'lThumb2')
        if doc.SearchObject('lThumb3'):
            self.move_to_obj(meshName + 'Thumb3', 'lThumb3')
            self.move_to_obj(meshName + 'Thumb_end', 'lThumb3')

        if doc.SearchObject('lThighBend'):
            self.move_to_obj(meshName + 'LegUpper', 'lThighBend')

        if doc.SearchObject('lThigh'):
            self.move_to_obj(meshName + 'LegUpper', 'lThigh')

        self.move_to_obj(meshName + 'Knee', 'lShin')
        self.move_to_obj(meshName + 'Foot', 'lFoot')
        self.move_to_obj(meshName + 'Toes', 'lToe')

        if doc.SearchObject('lSmallToe2_2'):
            self.move_to_obj(meshName + 'Toes_end', 'lSmallToe2_2')
        else:
            if doc.SearchObject('lSmallToe2'):
                self.move_to_obj(meshName + 'Toes_end', 'lSmallToe2')

        self.move_to_obj(meshName + 'Pelvis', 'hip')

        if doc.SearchObject('abdomenLower'):
            self.move_to_obj(meshName + 'Spine_Start', 'abdomenLower')
            self.move_to_obj(meshName + 'Chest_Start', 'chestLower')
            self.move_to_obj(meshName + 'Neck_Start', 'neckLower')
            self.move_to_obj(meshName + 'Neck_End', 'head')

        if doc.SearchObject('abdomen'):
            self.move_to_obj(meshName + 'Spine_Start', 'abdomen')
            self.move_to_obj(meshName + 'Chest_Start', 'chest')
            self.move_to_obj(meshName + 'Neck_Start', 'neck')
            self.move_to_obj(meshName + 'Neck_End', 'head')

        self.move_to_obj(meshName + 'Head_End', 'head_end')  # TEMPPP

        # actObj = doc.SearchObject('Object_Index_end')

        self.extend_3d_line('Index2', 'Index3', 'Index_end')
        self.extend_3d_line('Middle2', 'Middle3', 'Middle_end')
        self.extend_3d_line('Ring2', 'Ring3', 'Ring_end')
        self.extend_3d_line('Pinky2', 'Pinky3', 'Pinky_end')
        self.extend_3d_line('Thumb2', 'Thumb3', 'Thumb_end')

    def clean_joints_daz(self, side='Left'):
        doc = documents.GetActiveDocument()
        prefix = 'l'
        suffix = ''
        if side == 'Right':
            prefix = 'r'
            suffix = '___R'
        # self.parentTo('lShin','lThighBend')
        # self.parentTo('lHand','lForearmBend')
        # self.parentTo('lForearmBend','lShldrBend')
        if doc.SearchObject(prefix + 'SmallToe4'):
            self.parentTo(prefix + 'SmallToe4', prefix + 'Toe')
        if doc.SearchObject(prefix + 'SmallToe3'):
            self.parentTo(prefix + 'SmallToe3', prefix + 'Toe')
        if doc.SearchObject(prefix + 'SmallToe2'):
            self.parentTo(prefix + 'SmallToe2', prefix + 'Toe')
        if doc.SearchObject(prefix + 'SmallToe1'):
            self.parentTo(prefix + 'SmallToe1', prefix + 'Toe')
        if doc.SearchObject(prefix + 'BigToe'):
            self.parentTo(prefix + 'BigToe', prefix + 'Toe')
        c4d.EventAdd()

    def constraint_joints_to_daz(self, side='Left'):
        doc = documents.GetActiveDocument()

        prefix = 'l'
        suffix = ''
        if side == 'Right':
            prefix = 'r'
            suffix = '___R'
        # Constraints
        self.add_constraint(prefix + 'Collar', meshName + 'jCollar' + suffix)

        if doc.SearchObject(prefix + 'ShldrBend'):
            self.add_constraint(prefix + 'ShldrBend',
                                meshName + 'jArm' + suffix)
            self.add_constraint(prefix + 'ForearmBend',
                                meshName + 'jForeArm' + suffix)
        if doc.SearchObject(prefix + 'Shldr'):
            self.add_constraint(prefix + 'Shldr', meshName + 'jArm' + suffix)
            self.add_constraint(prefix + 'ForeArm',
                                meshName + 'jForeArm' + suffix)

        self.add_constraint(prefix + 'Hand', meshName + 'jHand' + suffix)
        self.add_constraint('hip', meshName + 'jPelvis')
        if doc.SearchObject('pelvis'):
            self.add_constraint('pelvis', meshName + 'jPelvis')
        if doc.SearchObject('abdomenLower'):
            self.add_constraint('abdomenLower', meshName + 'jSpine')
            self.add_constraint('abdomenUpper', meshName + 'jAbdomenUpper')
            self.add_constraint('chestLower', meshName + 'jChest')
            self.add_constraint('chestUpper', meshName + 'jChestUpper')
            self.add_constraint('neckLower', meshName + 'jNeck')
        if doc.SearchObject('abdomen'):
            self.add_constraint('abdomen', meshName + 'jSpine')
            # self.addConstraint('abdomenUpper', meshName + 'jAbdomenUpper')
            self.add_constraint('chest', meshName + 'jChest')
            # self.addConstraint('chestUpper', meshName + 'jChestUpper')
            self.add_constraint('neck', meshName + 'jNeck')

        self.add_constraint('head', meshName + 'jHead')

        if doc.SearchObject(prefix + 'ThighBend'):
            self.add_constraint(prefix + 'ThighBend',
                                meshName + 'jUpLeg' + suffix)
        if doc.SearchObject(prefix + 'Thigh'):
            self.add_constraint(prefix + 'Thigh', meshName + 'jUpLeg' + suffix)

        self.add_constraint(prefix + 'Shin', meshName + 'jLeg' + suffix)
        self.add_constraint(prefix + 'Foot', meshName + 'jFoot' + suffix)
        self.add_constraint(prefix + 'Toe', meshName + 'jToes' + suffix)
        self.add_constraint(prefix + 'Index1', meshName + 'jIndex1' + suffix)
        self.add_constraint(prefix + 'Index2', meshName + 'jIndex2' + suffix)
        self.add_constraint(prefix + 'Index3', meshName + 'jIndex3' + suffix)
        self.add_constraint(prefix + 'Mid1', meshName + 'jMiddle1' + suffix)
        self.add_constraint(prefix + 'Mid2', meshName + 'jMiddle2' + suffix)
        self.add_constraint(prefix + 'Mid3', meshName + 'jMiddle3' + suffix)
        self.add_constraint(prefix + 'Ring1', meshName + 'jRing1' + suffix)
        self.add_constraint(prefix + 'Ring2', meshName + 'jRing2' + suffix)
        self.add_constraint(prefix + 'Ring3', meshName + 'jRing3' + suffix)
        self.add_constraint(prefix + 'Pinky1', meshName + 'jPink1' + suffix)
        self.add_constraint(prefix + 'Pinky2', meshName + 'jPink2' + suffix)
        self.add_constraint(prefix + 'Pinky3', meshName + 'jPink3' + suffix)

        self.add_constraint(prefix + 'Thumb1', meshName + 'jThumb1' + suffix)
        self.add_constraint(prefix + 'Thumb2', meshName + 'jThumb2' + suffix)
        self.add_constraint(prefix + 'Thumb3', meshName + 'jThumb3' + suffix)
