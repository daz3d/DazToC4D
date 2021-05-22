import c4d
import os
import sys
import webbrowser
from c4d import gui, documents

from .Utilities import (
    dazToC4Dutils,
    getJointFromConstraint,
    getJointFromSkin,
    TagIterator,
    ObjectIterator,
)
from .CustomCmd import Cinema4DCommands as dzc4d
from .IkMax import ikmaxUtils, ikmGenerator
from .CustomColors import randomColors
from .DtC4DPosing import Poses
from .Definitions import RES_DIR

dazReduceSimilar = True


class guiLoading(gui.GeDialog):
    dialog = None

    def CreateLayout(self):
        c4d.CallCommand(300001026, 300001026)  # Deselect All
        dzc4d.del_unused_mats()

        self.SetTitle("DazToC4D: Processing...")

        self.GroupBegin(10000, c4d.BFH_CENTER, 1, title="")
        self.GroupBorder(c4d.BORDER_OUT)
        self.GroupBorderSpace(10, 5, 10, 5)

        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0, name=r"Please wait...")

        self.GroupEnd()  # END ///////////////////////////////////////////////
        return True

    def InitValues(self):
        c4d.StatusClear()
        c4d.EventAdd()
        c4d.EventAdd(c4d.EVENT_FORCEREDRAW)
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        c4d.DrawViews()
        return True

    def Command(self, id, msg):
        if id == self.BUTTON_SAVE:
            c4d.CallCommand(12255, 12255)  # Save Project with Assets...

        if id == self.BUTTON_CANCEL:
            self.Close()

        return True


class guiASKtoSave(gui.GeDialog):
    dialog = None

    BUTTON_SAVE = 927123
    BUTTON_CANCEL = 927124

    MY_BITMAP_BUTTON = 927125

    res_dir = RES_DIR  # Adds the res folder to the path
    img_dir = os.path.join(res_dir, "imgs")  # Adds the res folder to the path

    img_btnSave = os.path.join(img_dir, "btnSave.png")
    img_btnLater = os.path.join(img_dir, "btnLater.png")

    def buttonBC(self, tooltipText="", presetLook=""):
        # Logo Image #############################################################
        bc = c4d.BaseContainer()  # Create a new container to store the button image
        bc.SetBool(c4d.BITMAPBUTTON_BUTTON, True)
        bc.SetString(c4d.BITMAPBUTTON_TOOLTIP, tooltipText)

        if presetLook == "":
            bc.SetInt32(
                c4d.BITMAPBUTTON_BORDER, c4d.BORDER_ROUND
            )  # Sets the border to look like a button
        if presetLook == "Preset0":
            bc.SetInt32(
                c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE
            )  # Sets the border to look like a button
        if presetLook == "Preset1":
            bc.SetInt32(
                c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE
            )  # Sets the border to look like a button
            bc.SetBool(c4d.BITMAPBUTTON_BUTTON, False)

        return bc
        # Logo Image #############################################################

    def CreateLayout(self):
        c4d.CallCommand(300001026, 300001026)  # Deselect All
        dzc4d.del_unused_mats()
        self.SetTitle("DazToC4D: Transfer Done!")

        # Import
        self.GroupBegin(10000, c4d.BFH_CENTER, 1, title="Auto-Import Info:")
        self.GroupBorder(c4d.BORDER_OUT)
        self.GroupBorderSpace(10, 5, 10, 5)

        self.AddStaticText(
            99,
            c4d.BFH_CENTER,
            0,
            0,
            name=r"To transfer from DAZ Studio to Cinema 4D you are using a Temp folder.",
        )
        self.AddStaticText(
            99,
            c4d.BFH_CENTER,
            0,
            0,
            name=r"Now is a good time to save the scene+textures to another location.",
        )

        self.GroupEnd()  # END ///////////////////////////////////////////////

        self.GroupBegin(10000, c4d.BFH_CENTER, 2, title="Import:")
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(10, 5, 10, 5)

        self.LogoButton6 = self.AddCustomGui(
            self.BUTTON_SAVE,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("", "Preset0"),
        )
        self.LogoButton6.SetImage(self.img_btnSave, True)  # Add the image to the button

        self.LogoButton6 = self.AddCustomGui(
            self.BUTTON_CANCEL,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("", "Preset0"),
        )
        self.LogoButton6.SetImage(
            self.img_btnLater, True
        )  # Add the image to the button

        self.GroupEnd()  # END ///////////////////////////////////////////////
        self.AddSeparatorH(c4d.BFV_SCALEFIT)  # Separator H
        self.AddStaticText(
            99,
            c4d.BFH_CENTER,
            0,
            0,
            name=r"*If you save later remember to save using File\Save Project with Assets...",
        )
        self.AddSeparatorH(c4d.BFV_SCALEFIT)  # Separator H

        return True

    def Command(self, id, msg):

        if id == self.BUTTON_SAVE:
            c4d.CallCommand(12255, 12255)  # Save Project with Assets...

        if id == self.BUTTON_CANCEL:
            self.Close()

        return True


# Inactive
class guiPleaseWaitAUTO(gui.GeDialog):
    dialog = None

    def CreateLayout(self):
        self.SetTitle("DazToC4D: Importing...")

        self.GroupBegin(10000, c4d.BFH_SCALEFIT, 1, title="")
        self.GroupBorderNoTitle(c4d.BORDER_ACTIVE_3)
        self.GroupBorderSpace(5, 10, 5, 10)

        self.AddSeparatorH(c4d.BFH_SCALEFIT)  # Separator H

        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0, name=r"Importing. Please Wait...")
        self.AddSeparatorH(280, c4d.BFH_SCALEFIT)  # Separator H

        self.GroupEnd()

        return True

    def Command(self, id, msg):

        if id == self.BUTTON_SAVE:
            c4d.CallCommand(12255, 12255)  # Save Project with Assets...

        if id == self.BUTTON_CANCEL:
            self.Close()

        return True


class IKMAXFastAttach(c4d.gui.GeDialog):
    LogoFolder_Path = RES_DIR  # Adds the res folder to the path
    LogoFolder_PathImgs = os.path.join(
        LogoFolder_Path, "imgs"
    )  # Adds the res folder to the path

    img_fa_head = os.path.join(LogoFolder_PathImgs, "fa_head.png")
    img_fa_neck = os.path.join(LogoFolder_PathImgs, "fa_neck.png")
    img_fa_chest = os.path.join(LogoFolder_PathImgs, "fa_chest.png")
    img_fa_foot = os.path.join(LogoFolder_PathImgs, "fa_foot.png")
    img_fa_jointV = os.path.join(LogoFolder_PathImgs, "fa_jointV.png")
    img_fa_pelvis = os.path.join(LogoFolder_PathImgs, "fa_pelvis.png")
    img_fa_spine = os.path.join(LogoFolder_PathImgs, "fa_spine.png")
    img_fa_handL = os.path.join(LogoFolder_PathImgs, "fa_hand_L.png")
    img_fa_handR = os.path.join(LogoFolder_PathImgs, "fa_hand_R.png")

    jointPelvis = "naaa"

    PREFFIX = ""
    MODEL = ""

    BUTTON_ATTACH_HEAD = 241798100
    BUTTON_ATTACH_NECK = 241798101
    BUTTON_ATTACH_CHEST = 241798102
    BUTTON_ATTACH_SPINE = 241798103
    BUTTON_ATTACH_PELVIS = 241798104

    BUTTON_ATTACH_ARM_RIGHT = 241798105
    BUTTON_ATTACH_FOREARM_RIGHT = 241798106
    BUTTON_ATTACH_HAND_RIGHT = 241798107

    BUTTON_ATTACH_ARM_LEFT = 241798111
    BUTTON_ATTACH_FOREARM_LEFT = 241798112
    BUTTON_ATTACH_HAND_LEFT = 241798113

    BUTTON_ATTACH_UPLEG_RIGHT = 241798108
    BUTTON_ATTACH_LEG_RIGHT = 241798109
    BUTTON_ATTACH_FOOT_RIGHT = 241798110

    BUTTON_ATTACH_UPLEG_LEFT = 241798114
    BUTTON_ATTACH_LEG_LEFT = 241798115
    BUTTON_ATTACH_FOOT_LEFT = 241798116

    TEXT_ATTACHOBJ = 241798117
    TEXT_ATTACHOBJ2 = 241798118

    def buttonBC(self, tooltipText="", presetLook=""):
        # Logo Image #############################################################
        bc = c4d.BaseContainer()  # Create a new container to store the button image
        bc.SetBool(c4d.BITMAPBUTTON_BUTTON, True)
        bc.SetString(c4d.BITMAPBUTTON_TOOLTIP, tooltipText)

        if presetLook == "":
            bc.SetInt32(
                c4d.BITMAPBUTTON_BORDER, c4d.BORDER_ROUND
            )  # Sets the border to look like a button
        if presetLook == "Preset0":
            bc.SetInt32(
                c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE
            )  # Sets the border to look like a button
        if presetLook == "Preset1":
            bc.SetInt32(
                c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE
            )  # Sets the border to look like a button
            bc.SetBool(c4d.BITMAPBUTTON_BUTTON, False)

        return bc
        # Logo Image #############################################################

    def CreateLayout(self):
        doc = c4d.documents.GetActiveDocument()

        MU = 0.8
        self.SetTitle("FastAttach")

        objs = doc.GetActiveObjects(1)
        objText = ""
        if len(objs) == 1:
            objText = objs[0].GetName()
        if len(objs) > 1:
            objText = str(len(objs)) + " objects"

        self.MODEL = objs

        self.GroupBegin(11, c4d.BFV_TOP, 1, 1, title="")  # DIALOG MARGINNNNS
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(0 * MU, 10 * MU, 10 * MU, 5 * MU)

        self.GroupBegin(11, c4d.BFV_TOP, 1, 1, title="")  # DIALOG MARGINNNNS
        self.GroupBorderNoTitle(c4d.BORDER_ACTIVE_4)
        self.GroupBorderSpace(20 * MU, 10 * MU, 20 * MU, 10 * MU)
        self.FA_text = self.AddStaticText(
            self.TEXT_ATTACHOBJ, c4d.BFH_CENTER, 0, 0, name="object"
        )
        self.SetString(self.TEXT_ATTACHOBJ, objText)
        self.GroupEnd()
        self.FA_text2 = self.AddStaticText(
            self.TEXT_ATTACHOBJ2,
            c4d.BFH_CENTER,
            0,
            0,
            name="will be constrainted to...",
        )

        self.GroupEnd()

        self.GroupBegin(11, c4d.BFV_TOP, 1, 2, title="")  # DIALOG MARGINNNNS
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(10 * MU, 10 * MU, 10 * MU, 30 * MU)

        self.GroupBegin(11, c4d.BFV_TOP, 1, 2, title="")  # HEAD ------------------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(100 * MU, 0 * MU, 100 * MU, 0 * MU)

        self.btnFA_head = self.AddCustomGui(
            self.BUTTON_ATTACH_HEAD,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            60,
            70,
            self.buttonBC("Head", "Preset0"),
        )
        self.btnFA_head.SetImage(self.img_fa_head, True)  # Add the image to the button

        self.btnFA_head = self.AddCustomGui(
            self.BUTTON_ATTACH_NECK,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("Head", "Preset0"),
        )
        self.btnFA_head.SetImage(self.img_fa_neck, True)  # Add the image to the button

        self.GroupEnd()

        self.GroupBegin(11, c4d.BFV_TOP, 3, 1, title="")  # MIDDLE ----------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(0, 0, 0, 0)

        self.GroupBegin(
            11, c4d.BFV_TOP, 1, 3, title=""
        )  # MIDDLE - ARM LEFT --------------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(10 * MU, 0 * MU, 10 * MU, 0 * MU)
        self.btnFA_head = self.AddCustomGui(
            self.BUTTON_ATTACH_ARM_RIGHT,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("Head", "Preset0"),
        )
        self.btnFA_head.SetImage(
            self.img_fa_jointV, True
        )  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(
            self.BUTTON_ATTACH_FOREARM_RIGHT,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("Head", "Preset0"),
        )
        self.btnFA_head.SetImage(
            self.img_fa_jointV, True
        )  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(
            self.BUTTON_ATTACH_HAND_RIGHT,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("Head", "Preset0"),
        )
        self.btnFA_head.SetImage(self.img_fa_handR, True)  # Add the image to the button
        self.GroupEnd()

        self.GroupBegin(
            11, c4d.BFV_TOP, 1, 3, title=""
        )  # MIDDLE - SPINES AND CHEST --------------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(10 * MU, 4 * MU, 10 * MU, 4 * MU)
        self.btnFA_head = self.AddCustomGui(
            self.BUTTON_ATTACH_CHEST,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("Head", "Preset0"),
        )
        self.btnFA_head.SetImage(self.img_fa_chest, True)  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(
            self.BUTTON_ATTACH_SPINE,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("Head", "Preset0"),
        )
        self.btnFA_head.SetImage(self.img_fa_spine, True)  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(
            self.BUTTON_ATTACH_PELVIS,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("Head", "Preset0"),
        )
        self.btnFA_head.SetImage(
            self.img_fa_pelvis, True
        )  # Add the image to the button
        self.GroupEnd()

        self.GroupBegin(
            11, c4d.BFV_TOP, 1, 3, title=""
        )  # MIDDLE - ARM RIGHT --------------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(10 * MU, 0 * MU, 10 * MU, 0 * MU)
        self.btnFA_head = self.AddCustomGui(
            self.BUTTON_ATTACH_ARM_LEFT,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("Head", "Preset0"),
        )
        self.btnFA_head.SetImage(
            self.img_fa_jointV, True
        )  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(
            self.BUTTON_ATTACH_FOREARM_LEFT,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("Head", "Preset0"),
        )
        self.btnFA_head.SetImage(
            self.img_fa_jointV, True
        )  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(
            self.BUTTON_ATTACH_HAND_LEFT,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("Head", "Preset0"),
        )
        self.btnFA_head.SetImage(self.img_fa_handL, True)  # Add the image to the button
        self.GroupEnd()

        self.GroupEnd()

        self.GroupBegin(11, c4d.BFV_TOP, 2, 1, title="")  # LEGS ----------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(0, 0, 0, 0)

        self.GroupBegin(11, c4d.BFV_TOP, 1, 3, title="")  # LEGS - LEFT --------------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(0 * MU, 0 * MU, 10 * MU, 0)
        self.btnFA_head = self.AddCustomGui(
            self.BUTTON_ATTACH_UPLEG_LEFT,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("Head", "Preset0"),
        )
        self.btnFA_head.SetImage(
            self.img_fa_jointV, True
        )  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(
            self.BUTTON_ATTACH_LEG_LEFT,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("Head", "Preset0"),
        )
        self.btnFA_head.SetImage(
            self.img_fa_jointV, True
        )  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(
            self.BUTTON_ATTACH_FOOT_LEFT,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("Head", "Preset0"),
        )
        self.btnFA_head.SetImage(self.img_fa_foot, True)  # Add the image to the button

        self.GroupEnd()

        self.GroupBegin(11, c4d.BFV_TOP, 1, 3, title="")  # LEGS - RIGHT --------------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(5 * MU, 0 * MU, 5 * MU, 0 * MU)
        self.btnFA_head = self.AddCustomGui(
            self.BUTTON_ATTACH_UPLEG_RIGHT,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("Head", "Preset0"),
        )
        self.btnFA_head.SetImage(
            self.img_fa_jointV, True
        )  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(
            self.BUTTON_ATTACH_LEG_RIGHT,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("Head", "Preset0"),
        )
        self.btnFA_head.SetImage(
            self.img_fa_jointV, True
        )  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(
            self.BUTTON_ATTACH_FOOT_RIGHT,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("Head", "Preset0"),
        )
        self.btnFA_head.SetImage(self.img_fa_foot, True)  # Add the image to the button

        self.GroupEnd()

        self.GroupEnd()

        self.GroupEnd()  # DIALOG MARGINSSSSSSS END

        return True

    def removeConstraint(self, obj):
        if obj != None:
            doc = documents.GetActiveDocument()
            tags = TagIterator(obj)
            overwriteConst = 1
            try:
                for tag in tags:

                    if "Constraint" in tag.GetName():
                        answer = gui.MessageDialog(
                            "Object >>>  "
                            + obj.GetName()
                            + "  <<< already constrainted.\nOverwrite constraint?",
                            c4d.GEMB_YESNO,
                        )
                        if answer == 6:
                            tag.Remove()
                        else:
                            overwriteConst = 0
            except:
                pass

            c4d.EventAdd()
            return overwriteConst

    def Command(self, id, msg):
        doc = documents.GetActiveDocument()
        jointSelected = ""

        print("asdasd")
        print(self.jointPelvis)
        print("-------")

        if id == self.BUTTON_ATTACH_HEAD:
            jointSelected = "jHead"
        if id == self.BUTTON_ATTACH_NECK:
            jointSelected = "jNeck"
        if id == self.BUTTON_ATTACH_CHEST:
            jointSelected = "jChest"
        if id == self.BUTTON_ATTACH_SPINE:
            jointSelected = "jSpine"
        if id == self.BUTTON_ATTACH_PELVIS:
            jointSelected = "jPelvis"

        if id == self.BUTTON_ATTACH_ARM_LEFT:
            jointSelected = "jArm"
        if id == self.BUTTON_ATTACH_FOREARM_LEFT:
            jointSelected = "jForeArm"
        if id == self.BUTTON_ATTACH_HAND_LEFT:
            jointSelected = "jHand"

        if id == self.BUTTON_ATTACH_UPLEG_LEFT:
            jointSelected = "jUpLeg"
        if id == self.BUTTON_ATTACH_LEG_LEFT:
            jointSelected = "jLeg"
        if id == self.BUTTON_ATTACH_FOOT_LEFT:
            jointSelected = "jFoot"

        if id == self.BUTTON_ATTACH_ARM_RIGHT:
            jointSelected = "jArm___R"
        if id == self.BUTTON_ATTACH_FOREARM_RIGHT:
            jointSelected = "jForeArm___R"
        if id == self.BUTTON_ATTACH_HAND_RIGHT:
            jointSelected = "jHand___R"

        if id == self.BUTTON_ATTACH_UPLEG_RIGHT:
            jointSelected = "jUpLeg___R"
        if id == self.BUTTON_ATTACH_LEG_RIGHT:
            jointSelected = "jLeg___R"
        if id == self.BUTTON_ATTACH_FOOT_RIGHT:
            jointSelected = "jFoot___R"

        objParent = ""
        joints = ikmaxUtils().iterateObjChilds(self.jointPelvis)
        if "___R" in jointSelected:
            for j in joints:
                if jointSelected in j.GetName() and "___R" in j.GetName():
                    objParent = j
        else:
            for j in joints:
                if jointSelected in j.GetName() and "___R" not in j.GetName():
                    objParent = j
        objChild = self.MODEL

        if len(objChild) == 1:
            objChild = self.MODEL[0]
            if self.removeConstraint(objChild) == 1:
                ikmGenerator().constraintObj(objChild, objParent, "PARENT", 0)
                dzc4d.deselect_all()  # Deselect All
                c4d.EventAdd()
                self.Close()

        if len(objChild) > 1:
            for obj in objChild:
                if self.removeConstraint(obj) == 1:
                    ikmGenerator().constraintObj(obj, objParent, "PARENT", 0)
                    c4d.EventAdd()
            dzc4d.deselect_all()  # Deselect All
            c4d.EventAdd()
            self.Close()

        c4d.EventAdd()

        return True


class EXTRADialog(c4d.gui.GeDialog):
    dialog = None
    testStuff = "asdasdasdasdasd!!!!!!!!!"
    dazMeshObj = ""
    jointPelvis = "---"
    dazIkmControls = ""

    LinkBox = ""
    PREFFIX = ""
    MASTERSIZE = 0
    RIGCOL1 = c4d.Vector(0, 0, 0)
    RIGCOL2 = c4d.Vector(0, 0, 0)

    BUTTON_LOGO = 241798009
    BUTTON_BIGIMG = 241798008

    IDC_LINKBOX_1 = 241798000

    BUTTON_START = 241798011

    BUTTON_UNDO = 241798012
    BUTTON_RIG_CREATE = 241798013
    BUTTON_MIRROR = 241798014

    BUTTON_RIG_SHOW = 241798015
    BUTTON_RIG_MODE = 241798016
    BUTTON_COL1 = 241798017
    BUTTON_COL2 = 241798018
    BUTTON_COL3 = 241798019
    BUTTON_COL4 = 241798020
    BUTTON_COL_RANDOM = 241798021
    BUTTON_COL_SET = 241798022

    BUTTON_SKIN_AUTO = 241798023

    BUTTON_EXTRA_FIGURE = 241798024
    BUTTON_EXTRA_TEST = 241798025
    BUTTON_EXTRA_REMOVE = 241798026
    BUTTON_EXTRA_ATTACH = 241798027
    BUTTON_EXTRA_CLOTH = 241798028

    BUTTON_IK_AUTO = 241798029
    BUTTON_IK_UNDO = 241798030
    BUTTON_IK_COL_RANDOM = 241798039

    BUTTON_SKIN_PAINT = 241798031
    BUTTON_RESET = 241798032
    BUTTON_MODEL_XRAY = 241798033
    BUTTON_MODEL_FREEZE = 241798034

    BUTTON_EXTRA_EYES = 241798035

    BUTTON_REMOVE_RIG = 241798036
    BUTTON_REMOVE_IK = 241798037
    BUTTON_REMOVE_SKIN = 241798038

    BUTTON_MODEL_MIRRORPOSE = 241798039

    LogoFolder_Path = RES_DIR  # Adds the res folder to the path
    LogoFolder_PathIcons = os.path.join(
        LogoFolder_Path, "icons"
    )  # Adds the res folder to the path
    LogoFolder_PathImgs = os.path.join(
        LogoFolder_Path, "imgs"
    )  # Adds the res folder to the path

    img_setColor = os.path.join(LogoFolder_PathIcons, "r_setcolor.png")
    img_char_mirror = os.path.join(LogoFolder_PathIcons, "char_mirror.png")
    img_extraQAttach = os.path.join(LogoFolder_PathIcons, "extraQAttach.png")
    img_r_randomcolor = os.path.join(LogoFolder_PathIcons, "r_randomcolor.png")
    img_rigUndo = os.path.join(LogoFolder_PathIcons, "rigUndo.png")
    img_rigMirror = os.path.join(LogoFolder_PathIcons, "char_mirror.png")
    img_help = os.path.join(LogoFolder_PathIcons, "ikmax_help_icon.png")
    img_empty = os.path.join(LogoFolder_PathIcons, "empty.png")
    img_QuickAttach = os.path.join(LogoFolder_PathIcons, "extraQAttach.png")
    img_extraFWarp = os.path.join(LogoFolder_PathIcons, "extraFWarp.png")
    img_ani_test = os.path.join(LogoFolder_PathIcons, "ani_test.png")
    img_ani_clear = os.path.join(LogoFolder_PathIcons, "ani_clear.png")
    img_ani_mode = os.path.join(LogoFolder_PathIcons, "ani_mode.png")
    img_r_hideshow = os.path.join(LogoFolder_PathIcons, "r_hideshow.png")
    img_r_box = os.path.join(LogoFolder_PathIcons, "r_box.png")
    img_skin_paint = os.path.join(LogoFolder_PathIcons, "paintSkin.png")
    img_delete = os.path.join(LogoFolder_PathIcons, "delete.png")
    img_xray = os.path.join(LogoFolder_PathIcons, "m_xray.png")
    img_lock = os.path.join(LogoFolder_PathIcons, "m_lock.png")
    img_lockON = os.path.join(LogoFolder_PathIcons, "m_lockON.png")
    img_extra_eyes = os.path.join(LogoFolder_PathIcons, "extraFeyes.png")

    img_logo = os.path.join(LogoFolder_PathImgs, "daztoc4d_hdr.png")  # LOGO
    img_RigStart = os.path.join(LogoFolder_PathImgs, "GUI_Start.png")
    img_RigStart_NO = os.path.join(LogoFolder_PathImgs, "GUI_Start_B.png")
    img_guidesNext = os.path.join(LogoFolder_PathImgs, "GUI_Next.png")
    img_CreateRig = os.path.join(LogoFolder_PathImgs, "GUI_CreateRig.png")
    img_CreateRig_NO = os.path.join(LogoFolder_PathImgs, "GUI_CreateRig_B.png")
    img_AutoIK = os.path.join(LogoFolder_PathImgs, "GUI_AutoIK.png")
    img_AutoIK_NO = os.path.join(LogoFolder_PathImgs, "GUI_AutoIK_B.png")
    img_AutoSkin = os.path.join(LogoFolder_PathImgs, "GUI_AutoSkin.png")
    img_AutoSkin_NO = os.path.join(LogoFolder_PathImgs, "GUI_AutoSkin_B.png")

    img_readyToBegin = os.path.join(LogoFolder_PathImgs, "ReadyToBegin.jpg")
    img_select = os.path.join(LogoFolder_PathImgs, "select.jpg")
    img_adjustGuides = os.path.join(LogoFolder_PathImgs, "adjustMainGuides.png")

    img_GUIDE_LArm = os.path.join(LogoFolder_PathImgs, "LArm.jpg")
    img_GUIDE_Lfoot = os.path.join(LogoFolder_PathImgs, "Lfoot.jpg")
    img_GUIDE_LForeArm = os.path.join(LogoFolder_PathImgs, "LForeArm.jpg")
    img_GUIDE_LIndex1 = os.path.join(LogoFolder_PathImgs, "LIndex1.jpg")
    img_GUIDE_LIndex2 = os.path.join(LogoFolder_PathImgs, "LIndex2.jpg")
    img_GUIDE_LIndex3 = os.path.join(LogoFolder_PathImgs, "LIndex3.jpg")
    img_GUIDE_LIndex4 = os.path.join(LogoFolder_PathImgs, "LIndex4.jpg")
    img_GUIDE_LLeg = os.path.join(LogoFolder_PathImgs, "LLeg.jpg")
    img_GUIDE_LLegUp = os.path.join(LogoFolder_PathImgs, "LLegUp.jpg")
    img_GUIDE_LMiddle1 = os.path.join(LogoFolder_PathImgs, "LMiddle1.jpg")
    img_GUIDE_LMiddle2 = os.path.join(LogoFolder_PathImgs, "LMiddle2.jpg")
    img_GUIDE_LMiddle3 = os.path.join(LogoFolder_PathImgs, "LMiddle3.jpg")
    img_GUIDE_LMiddle4 = os.path.join(LogoFolder_PathImgs, "LMiddle4.jpg")
    img_GUIDE_LPalm = os.path.join(LogoFolder_PathImgs, "LPalm.jpg")
    img_GUIDE_LPinky1 = os.path.join(LogoFolder_PathImgs, "LPinky1.jpg")
    img_GUIDE_LPinky2 = os.path.join(LogoFolder_PathImgs, "LPinky2.jpg")
    img_GUIDE_LPinky3 = os.path.join(LogoFolder_PathImgs, "LPinky3.jpg")
    img_GUIDE_LPinky4 = os.path.join(LogoFolder_PathImgs, "LPinky4.jpg")
    img_GUIDE_LRing1 = os.path.join(LogoFolder_PathImgs, "LRing1.jpg")
    img_GUIDE_LRing2 = os.path.join(LogoFolder_PathImgs, "LRing2.jpg")
    img_GUIDE_LRing3 = os.path.join(LogoFolder_PathImgs, "LRing3.jpg")
    img_GUIDE_LRing4 = os.path.join(LogoFolder_PathImgs, "LRing4.jpg")
    img_GUIDE_LThumb1 = os.path.join(LogoFolder_PathImgs, "LThumb1.jpg")
    img_GUIDE_LThumb2 = os.path.join(LogoFolder_PathImgs, "LThumb2.jpg")
    img_GUIDE_LThumb3 = os.path.join(LogoFolder_PathImgs, "LThumb3.jpg")
    img_GUIDE_Ltoe = os.path.join(LogoFolder_PathImgs, "Ltoe.jpg")
    img_GUIDE_Ltoe1 = os.path.join(LogoFolder_PathImgs, "Ltoe1.jpg")

    img_COMPLETE_GUIDES = os.path.join(LogoFolder_PathImgs, "completeGuides.jpg")
    img_COMPLETE_GUIDESADJUST = os.path.join(LogoFolder_PathImgs, "guidesAdjust.jpg")
    img_COMPLETE_RIG = os.path.join(LogoFolder_PathImgs, "completeRIG.jpg")
    img_COMPLETE_RIG2 = os.path.join(LogoFolder_PathImgs, "completeRIG2.jpg")
    img_COMPLETE_IK = os.path.join(LogoFolder_PathImgs, "completeIK.jpg")
    img_COMPLETE_SKIN = os.path.join(LogoFolder_PathImgs, "completeSKIN.jpg")
    img_COMPLETE_ALL = os.path.join(LogoFolder_PathImgs, "done.jpg")

    def lockLayerOnOff(self):
        doc = documents.GetActiveDocument()
        root = doc.GetLayerObjectRoot()  # Gets the layer manager
        layer = ""
        LayersList = root.GetChildren()
        for layers in LayersList:
            name = layers.GetName()
            if name == "IKM_Lock":
                layer = layers
        if layer:
            if layer.GetName() == "IKM_Lock":
                layer_data = layer.GetLayerData(doc)
                lockValue = layer_data["locked"]
                LogoFolder_Path = RES_DIR  # Adds the res folder to the path
                LogoFolder_PathIcons = os.path.join(
                    LogoFolder_Path, "icons"
                )  # Adds the res folder to the path
                img_lock = os.path.join(LogoFolder_PathIcons, "m_lock.png")
                img_lockON = os.path.join(LogoFolder_PathIcons, "m_lockON.png")

                print(lockValue)
                if lockValue == True:
                    layer_data["locked"] = False
                    guiDazToC4DLayerLockButton.SetImage(img_lock, True)
                else:
                    layer_data["locked"] = True
                    guiDazToC4DLayerLockButton.SetImage(img_lockON, True)

                layer.SetLayerData(doc, layer_data)

        c4d.EventAdd()

    def buttonBC(self, tooltipText="", presetLook=""):
        # Logo Image #############################################################
        bc = c4d.BaseContainer()  # Create a new container to store the button image
        bc.SetBool(c4d.BITMAPBUTTON_BUTTON, True)
        bc.SetString(c4d.BITMAPBUTTON_TOOLTIP, tooltipText)

        if presetLook == "":
            bc.SetInt32(
                c4d.BITMAPBUTTON_BORDER, c4d.BORDER_ROUND
            )  # Sets the border to look like a button
        if presetLook == "Preset0":
            bc.SetInt32(
                c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE
            )  # Sets the border to look like a button
        if presetLook == "Preset1":
            bc.SetInt32(
                c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE
            )  # Sets the border to look like a button
            bc.SetBool(c4d.BITMAPBUTTON_BUTTON, False)

        return bc
        # Logo Image #############################################################

    def open_support(self, message):
        gui.MessageDialog(message, c4d.GEMB_OK)
        new = 2  # open in a new tab, if possible
        url = "https://helpdaz.zendesk.com/hc/en-us/sections/360009575931-Cinema-4D"
        webbrowser.open(url, new=new)
        self.Close()

    def checkVer(self):
        caca = c4d.GetC4DVersion()
        if caca > 24035:  # Cinema4D R24
            message = "Cinema4D version not supported by this DazToC4D version.\nVisit Daz3D.com for updates or news."
            self.open_support(message)
            return 0

    def CreateLayout(self):
        doc = c4d.documents.GetActiveDocument()
        self.checkVer()

        self.SetTitle("DazToC4D: Config")

        # self.LogoButton0 = self.AddCustomGui(self.BUTTON_LOGO, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("", "Preset0"))
        # self.LogoButton0.SetImage(self.img_logo, True)  # Add the image to the button

        self.GroupBegin(
            11, c4d.BFH_SCALEFIT, 1, 1, title="Character Mesh: "
        )  # ----------------------------------------------------------
        self.GroupBorder(c4d.BORDER_GROUP_IN)
        self.GroupBorderSpace(10, 5, 10, 5)

        self.LinkBox = self.AddCustomGui(
            self.IDC_LINKBOX_1,
            c4d.CUSTOMGUI_LINKBOX,
            "Character Mesh",
            c4d.BFH_SCALEFIT,
            350,
            0,
        )
        self.LinkBox.SetLink(dazToC4Dutils().getDazMesh())

        meshObj = self.LinkBox.GetLink()

        if dzc4d.findIK() == 1:
            if meshObj:
                dazJoint = getJointFromSkin(meshObj, "hip")
                self.jointPelvis = getJointFromConstraint(dazJoint)
                self.dazIkmControls = getJointFromConstraint(self.jointPelvis).GetUp()
                IKMAXFastAttach.jointPelvis = self.jointPelvis

        self.GroupEnd()

        self.GroupBegin(
            11, c4d.BFH_CENTER, 1, 1, title="AAAAAA"
        )  # -----------Main Group
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(15, 5, 15, 5)

        self.GroupBegin(
            11, c4d.BFH_SCALEFIT, 1, 1, title="AAAAAA"
        )  # -----------Main Group
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(15, 5, 15, 5)

        self.GroupBegin(11, c4d.BFH_SCALEFIT, 1, 1, title="")  # -----------Main Group
        self.GroupBorderNoTitle(c4d.BORDER_GROUP_OUT)
        self.GroupBorderSpace(15, 5, 15, 5)

        self.AddCheckbox(
            208, c4d.BFH_LEFT, 0, 0, "Reduce (similar) materials on import"
        )
        if dazReduceSimilar == True:
            self.SetBool(208, True)
        else:
            self.SetBool(208, False)

        self.AddCheckbox(209, c4d.BFH_LEFT, 0, 0, "Keep facial morphs only")

        self.GroupEnd()
        self.GroupEnd()

        self.GroupBegin(
            11, c4d.BFH_CENTER, 8, 1, title="Rig Display: "
        )  # ----------------------------------------------------------
        self.GroupBorder(c4d.BORDER_GROUP_OUT)
        self.GroupBorderSpace(10, 5, 12, 5)

        self.LogoButton10 = self.AddCustomGui(
            self.BUTTON_RIG_SHOW,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("<b>Show/Hide Rig</b>", "Preset0"),
        )
        self.LogoButton10.SetImage(
            self.img_r_hideshow, True
        )  # Add the image to the button

        self.LogoButton11 = self.AddCustomGui(
            self.BUTTON_RIG_MODE,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC(
                "<b>Rig Display Mode</b><br>Switch between standard and<br>box lines display style",
                "Preset0",
            ),
        )
        self.LogoButton11.SetImage(self.img_r_box, True)  # Add the image to the button

        self.AddColorField(
            self.BUTTON_COL1,
            c4d.BFH_CENTER,
            20,
            20,
            c4d.DR_COLORFIELD_NO_SCREENPICKER
            | c4d.DR_COLORFIELD_NO_SWATCHES
            | c4d.DR_COLORFIELD_NO_MIXER
            | c4d.DR_COLORFIELD_NO_MODE_BUTTONS
            | c4d.DR_COLORFIELD_NO_COLORWHEEL
            | c4d.DR_COLORFIELD_NO_BRIGHTNESS
            | c4d.DR_COLORFIELD_NO_COLOR,
        )
        self.AddColorField(
            self.BUTTON_COL2,
            c4d.BFH_CENTER,
            20,
            20,
            c4d.DR_COLORFIELD_NO_SCREENPICKER
            | c4d.DR_COLORFIELD_NO_SWATCHES
            | c4d.DR_COLORFIELD_NO_MIXER
            | c4d.DR_COLORFIELD_NO_MODE_BUTTONS
            | c4d.DR_COLORFIELD_NO_COLORWHEEL
            | c4d.DR_COLORFIELD_NO_BRIGHTNESS
            | c4d.DR_COLORFIELD_NO_COLOR,
        )
        self.AddColorField(
            self.BUTTON_COL3,
            c4d.BFH_CENTER,
            20,
            20,
            c4d.DR_COLORFIELD_NO_SCREENPICKER
            | c4d.DR_COLORFIELD_NO_SWATCHES
            | c4d.DR_COLORFIELD_NO_MIXER
            | c4d.DR_COLORFIELD_NO_MODE_BUTTONS
            | c4d.DR_COLORFIELD_NO_COLORWHEEL
            | c4d.DR_COLORFIELD_NO_BRIGHTNESS
            | c4d.DR_COLORFIELD_NO_COLOR,
        )
        self.AddColorField(
            self.BUTTON_COL4,
            c4d.BFH_CENTER,
            20,
            20,
            c4d.DR_COLORFIELD_NO_SCREENPICKER
            | c4d.DR_COLORFIELD_NO_SWATCHES
            | c4d.DR_COLORFIELD_NO_MIXER
            | c4d.DR_COLORFIELD_NO_MODE_BUTTONS
            | c4d.DR_COLORFIELD_NO_COLORWHEEL
            | c4d.DR_COLORFIELD_NO_BRIGHTNESS
            | c4d.DR_COLORFIELD_NO_COLOR,
        )

        self.SetColorField(self.BUTTON_COL1, c4d.Vector(1.0, 0.0, 0.4), 1, 1, 1)
        self.SetColorField(self.BUTTON_COL2, c4d.Vector(0.4, 0.8, 1.0), 1, 1, 1)
        self.SetColorField(self.BUTTON_COL3, c4d.Vector(0.0, 1.0, 0.5), 1, 1, 1)
        self.SetColorField(self.BUTTON_COL4, c4d.Vector(1.0, 0.9, 0.0), 1, 1, 1)

        self.LogoButton12 = self.AddCustomGui(
            self.BUTTON_COL_SET,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC(
                "<b>Set Rig and IK Colors</b><br>Sets specified colors to<br>Rig and IK Controls",
                "Preset0",
            ),
        )
        self.LogoButton12.SetImage(
            self.img_setColor, True
        )  # Add the image to the button

        self.LogoButton13 = self.AddCustomGui(
            self.BUTTON_COL_RANDOM,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC(
                "<b>Random Rig Colors</b><br>Assign random colors<br>to the Rig joints",
                "Preset0",
            ),
        )
        self.LogoButton13.SetImage(
            self.img_r_randomcolor, True
        )  # Add the image to the button

        self.GroupEnd()

        self.GroupBegin(
            11, c4d.BFH_CENTER, 6, 1, title="Extra: "
        )  # ----------------------------------------------------------
        self.GroupBorder(c4d.BORDER_GROUP_OUT)
        self.GroupBorderSpace(13, 5, 14, 5)

        self.LogoButton16 = self.AddCustomGui(
            self.BUTTON_MODEL_MIRRORPOSE,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("<b>Mirror Joints pose before Auto-IK</b>", "Preset0"),
        )
        self.LogoButton16.SetImage(
            self.img_char_mirror, True
        )  # Add the image to the button

        self.LogoButton16 = self.AddCustomGui(
            self.BUTTON_MODEL_XRAY,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("<b>X-Ray Mode</b>", "Preset0"),
        )
        self.LogoButton16.SetImage(self.img_xray, True)  # Add the image to the button

        self.LogoButton16 = self.AddCustomGui(
            self.BUTTON_MODEL_FREEZE,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("<b>Lock/Unlock</b>", "Preset0"),
        )
        self.LogoButton16.SetImage(self.img_lock, True)  # Add the image to the button
        global guiDazToC4DLayerLockButton
        guiDazToC4DLayerLockButton = self.LogoButton16

        self.LogoButton15 = self.AddCustomGui(
            self.BUTTON_EXTRA_FIGURE,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("<b>Reset to Orig Pose</b>", "Preset0"),
        )
        self.LogoButton15.SetImage(
            self.img_ani_mode, True
        )  # Add the image to the button

        self.LogoButton18 = self.AddCustomGui(
            self.BUTTON_EXTRA_ATTACH,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC(
                "<b>Fast-Attach</b><br>Attach object/s easy and<br>fast to body part",
                "Preset0",
            ),
        )
        self.LogoButton18.SetImage(
            self.img_QuickAttach, True
        )  # Add the image to the button

        self.GroupEnd()

        self.GroupEnd()  # -------------------------------------Main Group

        self.AddSeparatorV(100, c4d.BFH_FIT)

        self.GroupEnd()

        layer = ikmaxUtils().getLayer("IKM_Lock")
        if layer != None:
            try:
                layer_data = layer.GetLayerData(doc)
                lockValue = layer_data["locked"]
                if lockValue == True:
                    self.LogoButton16.SetImage(self.img_lockON, True)
            except:
                print("Layer test skipped...")

        return True

    def Command(self, id, msg):

        EXTRADialog().checkVer()
        # id is the id number of the object the command was issued from, usually a button
        if id == 208:
            # Reduce Materials on Import
            global dazReduceSimilar
            dazReduceSimilar = self.GetBool(208)
            return 0

        if id == self.BUTTON_MODEL_MIRRORPOSE:
            Poses().mirrorPose()
            return 0

        obj = self.LinkBox.GetLink()
        if obj == None and id != self.BUTTON_MODEL_FREEZE:
            gui.MessageDialog("Select your Character object first", c4d.GEMB_OK)

            return 0

        # MESH SELECT
        if id == self.IDC_LINKBOX_1:
            doc = c4d.documents.GetActiveDocument()
            meshObj = self.LinkBox.GetLink()
            dazJoint = getJointFromSkin(meshObj, "hip")
            self.jointPelvis = getJointFromConstraint(dazJoint)
            self.dazIkmControls = getJointFromConstraint(self.jointPelvis).GetUp()
            IKMAXFastAttach.jointPelvis = self.jointPelvis

        # GUIDES
        if dzc4d.findIK() == 1:

            if id == self.BUTTON_RESET:
                caca = ikmaxUtils().removeStuff()
                if caca == 1:
                    self.imgSelect.SetImage(
                        self.img_select, True
                    )  # Add the image to the button
                    self.LogoButton3.SetImage(
                        self.img_RigStart, True
                    )  # Add the image to the button
                    self.LogoButton6.SetImage(self.img_CreateRig_NO, True)
                    dzc4d.deselect_all()  # Deselect All
                    dzc4d.object_mode()  # Model

            if id == self.BUTTON_START:
                obj = self.LinkBox.GetLink()
                if obj == None:
                    gui.MessageDialog("No object selected", c4d.GEMB_OK)
                else:
                    objRots = obj.GetRelRot()
                    # If rotated or anim, reset all
                    if objRots != c4d.Vector(0, 0, 0):
                        answer = gui.MessageDialog(
                            "Object rotations needs to be reseted. Do you want to proceed?",
                            c4d.GEMB_YESNO,
                        )
                        if answer == 6:
                            objFixed = ikmaxUtils().resetObj(obj)
                            self.LinkBox.SetLink(objFixed)
                            EXTRADialog.MASTERSIZE = objHeight = (
                                objFixed.GetRad()[1]
                                * objFixed[c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_Y]
                            ) * 2
                            # Start main guides and placement...
                            self.startGuides(objFixed)
                    else:
                        self.startGuides(obj)

            # AUTO-RIG
            if id == self.BUTTON_REMOVE_RIG:
                answer = gui.MessageDialog("Remove RIG?", c4d.GEMB_YESNO)
                if answer == 6:
                    ikmaxUtils().removeRIGandMirrorsandGuides()

                    self.LogoButton9.SetImage(self.img_AutoIK_NO, True)
                    self.LogoButton14.SetImage(self.img_AutoSkin_NO, True)
                    self.imgSelect.SetImage(self.img_adjustGuides, True)

            if id == self.BUTTON_MIRROR:
                doc = documents.GetActiveDocument()
                ikControls = doc.SearchObject(EXTRADialog.PREFFIX + "IKM_Controls")
                jointsRoot = doc.SearchObject(EXTRADialog.PREFFIX + "jPelvis")
                answer = 0
                if ikControls:
                    answer = gui.MessageDialog(
                        "Remove IK to make rig changes/mirror rig, etc.\nWhen happy generate Auto-IK again.\n\nRemove IK now and mirror RIG?",
                        c4d.GEMB_YESNO,
                    )
                    if answer == 6:
                        ikmaxUtils().removeIK()
                        print("Removing IK...")

                if ikControls == None or answer == 6:
                    suffix = "___R"
                    objArm = doc.SearchObject(EXTRADialog.PREFFIX + "jCollar")
                    objLeg = doc.SearchObject(EXTRADialog.PREFFIX + "jUpLeg")
                    ikmaxUtils().mirrorObjects(objArm, suffix)
                    ikmaxUtils().mirrorObjects(objLeg, suffix)
                doc.FlushUndoBuffer()

            if id == self.BUTTON_IK_COL_RANDOM:
                obj = self.LinkBox.GetLink()
                objName = obj.GetName().replace(".Shape", "") + "_"
                # obj = doc.SearchObject(objName + 'jPelvis')

                randomColors().randomNullsColor(objName + "IKM_Controls")
                randomColors().randomPoleColors(self.jointPelvis)

            # RIG-DISPLAY
            if id == self.BUTTON_RIG_SHOW:
                doc = c4d.documents.GetActiveDocument()

                boneDisplay = self.jointPelvis[c4d.ID_CA_JOINT_OBJECT_BONE_DISPLAY]
                if boneDisplay != 0:
                    boneDisplay = 0
                else:
                    boneDisplay = 2
                for x in ikmaxUtils().iterateObjChilds(self.jointPelvis):
                    x[c4d.ID_CA_JOINT_OBJECT_BONE_DISPLAY] = boneDisplay
                self.jointPelvis[c4d.ID_CA_JOINT_OBJECT_BONE_DISPLAY] = boneDisplay

                c4d.EventAdd()

            if id == self.BUTTON_RIG_MODE:
                doc = documents.GetActiveDocument()
                displayMode = False
                wDisplay = 2
                sDispley = 6

                def addDisplayTAG(obj, boxMode=0):
                    displayTag = c4d.BaseTag(c4d.Tdisplay)
                    displayTag[c4d.DISPLAYTAG_AFFECT_DISPLAYMODE] = 1
                    displayTag[c4d.DISPLAYTAG_WDISPLAYMODE] = 2
                    displayTag[c4d.DISPLAYTAG_SDISPLAYMODE] = 6
                    obj.InsertTag(displayTag)

                def getDisplayTAG(obj):
                    tags = TagIterator(obj)
                    displayReady = 0
                    firstTAG = obj.GetFirstTag()
                    if firstTAG == None:
                        addDisplayTAG(obj)
                        return 0
                    else:
                        try:
                            for tag in tags:
                                if "Display" in tag.GetName():
                                    displayReady = 1
                        except:
                            pass

                    if displayReady == 0:
                        addDisplayTAG(obj)

                    if displayReady == 1:
                        tags = TagIterator(obj)
                        try:
                            for tag in tags:
                                if "Display" in tag.GetName():
                                    displayMode = tag[c4d.DISPLAYTAG_AFFECT_DISPLAYMODE]
                                    if displayMode == 1:
                                        tag[c4d.DISPLAYTAG_AFFECT_DISPLAYMODE] = 0
                                        c4d.EventAdd()
                                    else:
                                        tag[c4d.DISPLAYTAG_AFFECT_DISPLAYMODE] = 1
                                        tag[c4d.DISPLAYTAG_WDISPLAYMODE] = 2
                                        tag[c4d.DISPLAYTAG_SDISPLAYMODE] = 6
                        except:
                            pass

                obj = self.jointPelvis

                getDisplayTAG(obj)
                c4d.EventAdd()

            if id == self.BUTTON_COL_RANDOM:
                print("random colors")

                randomColors().randomRigColor(self.jointPelvis)
                print(self.dazIkmControls.GetName())
                randomColors().randomNullsColor(self.dazIkmControls)
                randomColors().randomPoleColors(self.jointPelvis)

            if id == self.BUTTON_COL_SET:
                obj = self.LinkBox.GetLink()
                objName = obj.GetName().replace(".Shape", "") + "_"

                RIGCOL1 = self.GetColorField(self.BUTTON_COL1)["color"]
                RIGCOL2 = self.GetColorField(self.BUTTON_COL2)["color"]
                RIGCOL3 = self.GetColorField(self.BUTTON_COL3)["color"]
                RIGCOL4 = self.GetColorField(self.BUTTON_COL4)["color"]

                randomColors().randomRigColor(self.jointPelvis, 0, RIGCOL2, RIGCOL1)
                randomColors().randomNullsColor(
                    self.dazIkmControls, 0, RIGCOL3, RIGCOL4
                )
                randomColors().randomPoleColors(self.jointPelvis, 0, RIGCOL3, RIGCOL4)

            # MODE/TEST/EXTRA

            if id == self.BUTTON_MODEL_XRAY:
                obj = self.LinkBox.GetLink()
                objXrayValue = obj[c4d.ID_BASEOBJECT_XRAY]
                # invert value
                if objXrayValue == 1:
                    objXrayValue = 0
                else:
                    objXrayValue = 1
                # get parent if present...
                objParent = obj.GetUp()

                # assign ivnerted value
                obj[c4d.ID_BASEOBJECT_XRAY] = objXrayValue
                try:
                    objParent[c4d.ID_BASEOBJECT_XRAY] = objXrayValue
                except:
                    pass

                c4d.EventAdd()

            if id == self.BUTTON_MODEL_FREEZE:
                self.lockLayerOnOff()

            if id == self.BUTTON_EXTRA_FIGURE:
                obj = self.LinkBox.GetLink()

                ikmaxUtils().setProtectionChildren(self.dazIkmControls, 0)

                ikmaxUtils().resetPRS(self.dazIkmControls)
                ikmaxUtils().resetPRS(self.jointPelvis)

                ikmaxUtils().setProtectionChildren(self.dazIkmControls, 1)

            if id == self.BUTTON_EXTRA_EYES:
                doc = documents.GetActiveDocument()
                characterMesh = self.LinkBox.GetLink()
                allOk = 1

                answer = gui.MessageDialog(
                    "This is an experimental feature, you may want to save your scene first. Do you want to proceed?",
                    c4d.GEMB_YESNO,
                )
                if answer != 6:
                    return 0

                selected = doc.GetActiveObjects(0)

                if len(selected) != 2:
                    gui.MessageDialog(
                        "You need to select 2 eyes/objects o.O!", c4d.GEMB_OK
                    )
                    allOk = 0
                if ikmaxUtils().checkIfExist("jHead") != 1:
                    gui.MessageDialog(
                        "No rig detected, first you need to\ngenerate a rig for your Character",
                        c4d.GEMB_OK,
                    )
                    allOk = 0

                if allOk == 1:
                    ojo1 = selected[0]
                    ojo2 = selected[1]

                    headJoint = doc.SearchObject(EXTRADialog.PREFFIX + "jHead")
                    joints = doc.SearchObject(EXTRADialog.PREFFIX + "jPelvis")

                    obj1 = ikmaxUtils().makeNull("lEye_ctrl", ojo1)
                    obj2 = ikmaxUtils().makeNull("rEye_ctrl", ojo2)

                    objParent = ojo1.GetUp()
                    eyesParentNull = ikmaxUtils().makeNull("EyesParent", headJoint)
                    eyesGroup = ikmaxUtils().makeNull("EyesParent", headJoint)
                    eyesGroup2 = ikmaxUtils().makeNull("EyesParent", headJoint)

                    obj1.SetAbsScale(c4d.Vector(1, 1, 1))
                    obj2.SetAbsScale(c4d.Vector(1, 1, 1))

                    eyesParentNull.SetName(EXTRADialog.PREFFIX + "Eyes-LookAt")
                    eyesGroup.SetName(EXTRADialog.PREFFIX + "EyesGroup")

                    masterSize = EXTRADialog.MASTERSIZE

                    obj1[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z] -= masterSize / 4
                    obj2[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z] -= masterSize / 4

                    def nullStyle(obj):
                        obj[c4d.ID_BASEOBJECT_USECOLOR] = True
                        obj[c4d.ID_BASEOBJECT_COLOR] = c4d.Vector(0, 0.9, 0)
                        # obj[c4d.NULLOBJECT_ICONCOL] = True
                        obj[c4d.NULLOBJECT_DISPLAY] = 2
                        obj[c4d.NULLOBJECT_ORIENTATION] = 1
                        obj[c4d.NULLOBJECT_RADIUS] = masterSize / 160

                    def nullStyleMaster(obj):
                        obj[c4d.ID_BASEOBJECT_USECOLOR] = True
                        obj[c4d.ID_BASEOBJECT_COLOR] = c4d.Vector(0, 1, 0)
                        # obj[c4d.NULLOBJECT_ICONCOL] = True
                        obj[c4d.NULLOBJECT_DISPLAY] = 7
                        obj[c4d.NULLOBJECT_ASPECTRATIO] = 0.3
                        obj[c4d.NULLOBJECT_ORIENTATION] = 1
                        obj[c4d.NULLOBJECT_RADIUS] = masterSize / 25

                    def makeChild(child, parent):
                        mg = child.GetMg()
                        child.InsertUnder(parent)
                        child.SetMg(mg)

                    dzc4d.deselect_all()  # Deselect All
                    doc.SetActiveObject(obj1, c4d.SELECTION_NEW)
                    doc.SetActiveObject(obj2, c4d.SELECTION_ADD)
                    c4d.CallCommand(100004772, 100004772)  # Group Objects
                    c4d.CallCommand(100004773, 100004773)  # Expand Object

                    objMasterEyes = doc.GetActiveObjects(0)[0]
                    objMasterEyes.SetName(EXTRADialog.PREFFIX + "EyesLookAtGroup")
                    objMasterEyes.SetAbsScale(c4d.Vector(1, 1, 1))

                    nullStyle(obj1)
                    nullStyle(obj2)
                    nullStyleMaster(objMasterEyes)

                    ikmGenerator().constraintObj(ojo1, obj1, "AIM", 0)
                    ikmGenerator().constraintObj(ojo2, obj2, "AIM", 0)

                    makeChild(obj1, objMasterEyes)
                    makeChild(obj2, objMasterEyes)
                    makeChild(objMasterEyes, eyesParentNull)

                    obj1.SetAbsRot(c4d.Vector(0))
                    obj2.SetAbsRot(c4d.Vector(0))

                    ikmGenerator().constraintObj(eyesParentNull, headJoint, "", 0)

                    eyesParentNull.InsertAfter(joints)

                    ikmaxUtils().freezeChilds(EXTRADialog.PREFFIX + "Eyes-LookAt")
                    ikmaxUtils().freezeChilds(EXTRADialog.PREFFIX + "EyesLookAtGroup")

                    c4d.EventAdd()
                    c4d.CallCommand(12288, 12288)  # Frame All

            if id == self.BUTTON_EXTRA_ATTACH:
                doc = documents.GetActiveDocument()

                if len(doc.GetActiveObjects(1)) == 0:
                    gui.MessageDialog(
                        "Select object(s) that you want to attach to joints"
                    )
                    return 0
                else:
                    dialog = IKMAXFastAttach()
                    dialog.Open(
                        dlgtype=c4d.DLG_TYPE_MODAL,
                        defaultw=200,
                        defaulth=150,
                        xpos=-1,
                        ypos=-1,
                    )

        return True
