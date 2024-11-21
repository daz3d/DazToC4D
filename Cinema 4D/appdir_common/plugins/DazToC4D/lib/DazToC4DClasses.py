import traceback
import c4d
from c4d import documents, gui

from . import Utilities as util
from .CustomIterators import ObjectIterator
from .Utilities import dazToC4Dutils, is_genesis9
from .IkMax import applyDazIK, ikmaxUtils
from .AllSceneToZero import AllSceneToZero


dazName = "Object_"


class DazToC4D:
    def figureFixBrute(self):
        """Hard Coded Fixes to Rig to Deal with Larger Character"""
        doc = c4d.documents.GetActiveDocument()

        def checkIfBrute():
            isBrute = False
            docMaterials = doc.GetMaterials()
            for mat in docMaterials:
                mapDiffuse = ""
                try:
                    mapDiffuse = mat[c4d.MATERIAL_COLOR_SHADER][
                        c4d.BITMAPSHADER_FILENAME
                    ]
                except:
                    pass
                if "Brute8" in mapDiffuse:
                    isBrute = True
            return isBrute

        def nullSize(nullName, rad=1, ratio=1):
            dazName = "Genesis8Male_"
            obj = doc.SearchObject(dazName + nullName)
            if obj:
                obj[c4d.NULLOBJECT_RADIUS] = rad
                obj[c4d.NULLOBJECT_ASPECTRATIO] = ratio
                c4d.EventAdd()

        if checkIfBrute():  # If BRUTE8! Change Null Sizes!
            nullSize("Pelvis_ctrl", 40, 0.8)
            nullSize("Spine_ctrl", 30, 0.8)
            nullSize("Chest_ctrl", 30, 0.8)
            nullSize("Foot_PlatformBase", 9.3, 1.52)
            nullSize("Foot_PlatformBase___R", 9.3, 1.52)
            nullSize("Collar_ctrl", 20, 0.3)
            nullSize("Collar_ctrl___R", 20, 0.3)

            nullSize("ForearmTwist_ctrl", 11, 1.0)
            nullSize("ForearmTwist_ctrl___R", 11, 1.0)

            nullSize("IK_Hand", 7, 1.4)
            nullSize("IK_Hand___R", 7, 1.4)

    def freezeTwistBones(self):
        doc = c4d.documents.GetActiveDocument()

        nullForeArm = doc.SearchObject(dazName + "ForearmTwist_ctrl")
        nullForeArmR = doc.SearchObject(dazName + "ForearmTwist_ctrl___R")
        if nullForeArm:
            nullForeArm.SetFrozenPos(nullForeArm.GetAbsPos())
            nullForeArm.SetFrozenRot(nullForeArm.GetAbsRot())
            nullForeArmR.SetFrozenPos(nullForeArmR.GetAbsPos())
            nullForeArmR.SetFrozenRot(nullForeArmR.GetAbsRot())

            nullForeArm.SetRelPos(c4d.Vector(0, 0, 0))
            nullForeArm.SetRelRot(c4d.Vector(0, 0, 0))
            nullForeArmR.SetRelPos(c4d.Vector(0, 0, 0))
            nullForeArmR.SetRelRot(c4d.Vector(0, 0, 0))

        nullForeArm = doc.SearchObject(dazName + "ForearmTwist2_ctrl")
        nullForeArmR = doc.SearchObject(dazName + "ForearmTwist2_ctrl___R")
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
            if (obj.GetType() == 5100) or (obj.GetType() == 1007455):
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
            if "Foot_PlatformBase" in obj.GetName():
                addProtTag(obj)

        c4d.EventAdd()

    def protectTwist(self):
        doc = c4d.documents.GetActiveDocument()
        dazName = util.get_daz_name() + "_"

        def addProtTag(obj):
            if obj is None:
                print("DEBUG: addProtTag: unsupported figure crashfix")
                return
            xtag = c4d.BaseTag(c4d.Tprotection)
            xtag[c4d.PROTECTION_P] = 1
            xtag[c4d.PROTECTION_S] = False
            xtag[c4d.PROTECTION_R] = 1
            xtag[c4d.PROTECTION_R_X] = True
            xtag[c4d.PROTECTION_R_Y] = False
            xtag[c4d.PROTECTION_R_Z] = True

            obj.InsertTag(xtag)
            c4d.EventAdd()

        nullForeArm = doc.SearchObject(dazName + "ForearmTwist_ctrl")
        nullForeArmR = doc.SearchObject(dazName + "ForearmTwist_ctrl___R")
        addProtTag(nullForeArm)
        addProtTag(nullForeArmR)
        if is_genesis9():
            nullForeArm = doc.SearchObject(dazName + "ForearmTwist2_ctrl")
            nullForeArmR = doc.SearchObject(dazName + "ForearmTwist2_ctrl___R")
            addProtTag(nullForeArm)
            addProtTag(nullForeArmR)

    def protectIKMControls(self):
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

        dazName = util.get_daz_name() + "_"
        # LEFT
        # protectTag(dazName + "jMiddle2", "finger")
        # protectTag(dazName + "jMiddle3", "finger")
        # protectTag(dazName + "jMiddle4", "finger")
        # protectTag(dazName + "jRing2", "finger")
        # protectTag(dazName + "jRing3", "finger")
        # protectTag(dazName + "jRing4", "finger")
        # protectTag(dazName + "jPink2", "finger")
        # protectTag(dazName + "jPink3", "finger")
        # protectTag(dazName + "jPink4", "finger")
        # protectTag(dazName + "jIndex2", "finger")
        # protectTag(dazName + "jIndex3", "finger")
        # protectTag(dazName + "jIndex4", "finger")
        # # RIGHT
        # protectTag(dazName + "jMiddle2___R", "finger")
        # protectTag(dazName + "jMiddle3___R", "finger")
        # protectTag(dazName + "jMiddle4___R", "finger")
        # protectTag(dazName + "jRing2___R", "finger")
        # protectTag(dazName + "jRing3___R", "finger")
        # protectTag(dazName + "jRing4___R", "finger")
        # protectTag(dazName + "jPink2___R", "finger")
        # protectTag(dazName + "jPink3___R", "finger")
        # protectTag(dazName + "jPink4___R", "finger")
        # protectTag(dazName + "jIndex2___R", "finger")
        # protectTag(dazName + "jIndex3___R", "finger")
        # protectTag(dazName + "jIndex4___R", "finger")

        # MIDDLE
        # protectTag(dazName + "Spine_ctrl", "position")
        # protectTag(dazName + "Chest_ctrl", "position")
        # protectTag(dazName + "Neck_ctrl", "position")
        # protectTag(dazName + "Head_ctrl", "position")

    def unhideProps(self):
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject("hip")
        ObjectIterator(obj)
        for o in ObjectIterator(obj):
            if o.GetType() == 5100 or o.GetType() == 5140:
                o[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 0
                o[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 0
        c4d.EventAdd()

    def autoIK(self, var):
        doc = c4d.documents.GetActiveDocument()
        obj = doc.SearchObject("hip")
        if obj:
            try:
                AllSceneToZero().sceneToZero()
                applyDazIK(var)
                dazToC4Dutils().changeSkinType()
                self.unhideProps()
                c4d.EventAdd()
                c4d.DrawViews(
                    c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
                    | c4d.DRAWFLAGS_NO_THREAD
                    | c4d.DRAWFLAGS_STATICBREAK
                )
                self.protectIKMControls()
                self.limitFloorContact()
                self.freezeTwistBones()
                self.figureFixBrute()
                self.protectTwist()
            except Exception as e:
                gui.MessageDialog(
                    "Auto IK Failed.\n" + 
                    "\nException: " + str(e) + "\n\n" +
                    "You can check the console for more info (Shift + F10)",
                    c4d.GEMB_OK,
                )
                print("Auto IK Failed with Exception: " + str(e))
                traceback.print_exc()
