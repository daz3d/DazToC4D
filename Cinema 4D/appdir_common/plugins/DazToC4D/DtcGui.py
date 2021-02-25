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
from DazToC4D import *
class EXTRADialog(c4d.gui.GeDialog):
    dialog = None

    dir, file = os.path.split(__file__)  # Gets the plugin's directory

    testStuff = 'asdasdasdasdasd!!!!!!!!!'
    dazMeshObj = ''
    jointPelvis = '---'
    dazIkmControls = ''

    LinkBox = ''
    PREFFIX = ''
    MASTERSIZE = 0
    RIGCOL1 = c4d.Vector(0, 0, 0)
    RIGCOL2 = c4d.Vector(0, 0, 0)

    BUTTON_LOGO = 241798009
    BUTTON_BIGIMG = 241798008

    IDC_LINKBOX_1 = 241798000

    BUTTON_HELP = 241798010
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

    # Adds the res folder to the path
    LogoFolder_Path = os.path.join(dir, 'res')
    # Adds the res folder to the path
    LogoFolder_PathIcons = os.path.join(LogoFolder_Path, 'icons')
    # Adds the res folder to the path
    LogoFolder_PathImgs = os.path.join(LogoFolder_Path, 'imgs')

    img_setColor = os.path.join(LogoFolder_PathIcons, 'r_setcolor.png')
    img_char_mirror = os.path.join(LogoFolder_PathIcons, 'char_mirror.png')
    img_extraQAttach = os.path.join(LogoFolder_PathIcons, 'extraQAttach.png')
    img_r_randomcolor = os.path.join(LogoFolder_PathIcons, 'r_randomcolor.png')
    img_rigUndo = os.path.join(LogoFolder_PathIcons, 'rigUndo.png')
    img_rigMirror = os.path.join(LogoFolder_PathIcons, 'char_mirror.png')
    img_help = os.path.join(LogoFolder_PathIcons, 'ikmax_help_icon.png')
    img_empty = os.path.join(LogoFolder_PathIcons, 'empty.png')
    img_QuickAttach = os.path.join(LogoFolder_PathIcons, 'extraQAttach.png')
    img_extraFWarp = os.path.join(LogoFolder_PathIcons, 'extraFWarp.png')
    img_ani_test = os.path.join(LogoFolder_PathIcons, 'ani_test.png')
    img_ani_clear = os.path.join(LogoFolder_PathIcons, 'ani_clear.png')
    img_ani_mode = os.path.join(LogoFolder_PathIcons, 'ani_mode.png')
    img_r_hideshow = os.path.join(LogoFolder_PathIcons, 'r_hideshow.png')
    img_r_box = os.path.join(LogoFolder_PathIcons, 'r_box.png')
    img_skin_paint = os.path.join(LogoFolder_PathIcons, 'paintSkin.png')
    img_delete = os.path.join(LogoFolder_PathIcons, 'delete.png')
    img_xray = os.path.join(LogoFolder_PathIcons, 'm_xray.png')
    img_lock = os.path.join(LogoFolder_PathIcons, 'm_lock.png')
    img_lockON = os.path.join(LogoFolder_PathIcons, 'm_lockON.png')
    img_extra_eyes = os.path.join(LogoFolder_PathIcons, 'extraFeyes.png')

    img_logo = os.path.join(LogoFolder_PathImgs, 'daztoc4d_hdr.png')  # LOGO
    img_RigStart = os.path.join(LogoFolder_PathImgs, 'GUI_Start.png')
    img_RigStart_NO = os.path.join(LogoFolder_PathImgs, 'GUI_Start_B.png')
    img_guidesNext = os.path.join(LogoFolder_PathImgs, 'GUI_Next.png')
    img_CreateRig = os.path.join(LogoFolder_PathImgs, 'GUI_CreateRig.png')
    img_CreateRig_NO = os.path.join(LogoFolder_PathImgs, 'GUI_CreateRig_B.png')
    img_AutoIK = os.path.join(LogoFolder_PathImgs, 'GUI_AutoIK.png')
    img_AutoIK_NO = os.path.join(LogoFolder_PathImgs, 'GUI_AutoIK_B.png')
    img_AutoSkin = os.path.join(LogoFolder_PathImgs, 'GUI_AutoSkin.png')
    img_AutoSkin_NO = os.path.join(LogoFolder_PathImgs, 'GUI_AutoSkin_B.png')

    img_readyToBegin = os.path.join(LogoFolder_PathImgs, 'ReadyToBegin.jpg')
    img_select = os.path.join(LogoFolder_PathImgs, 'select.jpg')
    img_adjustGuides = os.path.join(
        LogoFolder_PathImgs, 'adjustMainGuides.png')

    img_GUIDE_LArm = os.path.join(LogoFolder_PathImgs, 'LArm.jpg')
    img_GUIDE_Lfoot = os.path.join(LogoFolder_PathImgs, 'Lfoot.jpg')
    img_GUIDE_LForeArm = os.path.join(LogoFolder_PathImgs, 'LForeArm.jpg')
    img_GUIDE_LIndex1 = os.path.join(LogoFolder_PathImgs, 'LIndex1.jpg')
    img_GUIDE_LIndex2 = os.path.join(LogoFolder_PathImgs, 'LIndex2.jpg')
    img_GUIDE_LIndex3 = os.path.join(LogoFolder_PathImgs, 'LIndex3.jpg')
    img_GUIDE_LIndex4 = os.path.join(LogoFolder_PathImgs, 'LIndex4.jpg')
    img_GUIDE_LLeg = os.path.join(LogoFolder_PathImgs, 'LLeg.jpg')
    img_GUIDE_LLegUp = os.path.join(LogoFolder_PathImgs, 'LLegUp.jpg')
    img_GUIDE_LMiddle1 = os.path.join(LogoFolder_PathImgs, 'LMiddle1.jpg')
    img_GUIDE_LMiddle2 = os.path.join(LogoFolder_PathImgs, 'LMiddle2.jpg')
    img_GUIDE_LMiddle3 = os.path.join(LogoFolder_PathImgs, 'LMiddle3.jpg')
    img_GUIDE_LMiddle4 = os.path.join(LogoFolder_PathImgs, 'LMiddle4.jpg')
    img_GUIDE_LPalm = os.path.join(LogoFolder_PathImgs, 'LPalm.jpg')
    img_GUIDE_LPinky1 = os.path.join(LogoFolder_PathImgs, 'LPinky1.jpg')
    img_GUIDE_LPinky2 = os.path.join(LogoFolder_PathImgs, 'LPinky2.jpg')
    img_GUIDE_LPinky3 = os.path.join(LogoFolder_PathImgs, 'LPinky3.jpg')
    img_GUIDE_LPinky4 = os.path.join(LogoFolder_PathImgs, 'LPinky4.jpg')
    img_GUIDE_LRing1 = os.path.join(LogoFolder_PathImgs, 'LRing1.jpg')
    img_GUIDE_LRing2 = os.path.join(LogoFolder_PathImgs, 'LRing2.jpg')
    img_GUIDE_LRing3 = os.path.join(LogoFolder_PathImgs, 'LRing3.jpg')
    img_GUIDE_LRing4 = os.path.join(LogoFolder_PathImgs, 'LRing4.jpg')
    img_GUIDE_LThumb1 = os.path.join(LogoFolder_PathImgs, 'LThumb1.jpg')
    img_GUIDE_LThumb2 = os.path.join(LogoFolder_PathImgs, 'LThumb2.jpg')
    img_GUIDE_LThumb3 = os.path.join(LogoFolder_PathImgs, 'LThumb3.jpg')
    img_GUIDE_Ltoe = os.path.join(LogoFolder_PathImgs, 'Ltoe.jpg')
    img_GUIDE_Ltoe1 = os.path.join(LogoFolder_PathImgs, 'Ltoe1.jpg')

    img_COMPLETE_GUIDES = os.path.join(
        LogoFolder_PathImgs, 'completeGuides.jpg')
    img_COMPLETE_GUIDESADJUST = os.path.join(
        LogoFolder_PathImgs, 'guidesAdjust.jpg')
    img_COMPLETE_RIG = os.path.join(LogoFolder_PathImgs, 'completeRIG.jpg')
    img_COMPLETE_RIG2 = os.path.join(LogoFolder_PathImgs, 'completeRIG2.jpg')
    img_COMPLETE_IK = os.path.join(LogoFolder_PathImgs, 'completeIK.jpg')
    img_COMPLETE_SKIN = os.path.join(LogoFolder_PathImgs, 'completeSKIN.jpg')
    img_COMPLETE_ALL = os.path.join(LogoFolder_PathImgs, 'done.jpg')

    def buttonBC(self, tooltipText="", presetLook=""):
        # Logo Image #############################################################
        bc = c4d.BaseContainer()  # Create a new container to store the button image
        bc.SetBool(c4d.BITMAPBUTTON_BUTTON, True)
        bc.SetString(c4d.BITMAPBUTTON_TOOLTIP, tooltipText)

        if presetLook == "":
            # Sets the border to look like a button
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_ROUND)
        if presetLook == "Preset0":
            # Sets the border to look like a button
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE)
        if presetLook == "Preset1":
            # Sets the border to look like a button
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE)
            bc.SetBool(c4d.BITMAPBUTTON_BUTTON, False)

        return bc
        # Logo Image #############################################################

    def checkVer(self):
        caca = c4d.GetC4DVersion()
        if caca > 23500:
            gui.MessageDialog(
                'Cinema4D version not supported by this DazToC4D version.\nVisit 3DtoAll for update or news.', c4d.GEMB_OK)
            new = 2  # open in a new tab, if possible
            url = "http://www.3dtoall.com"
            webbrowser.open(url, new=new)
            self.Close()
            return 0

    def checkOld(self):
        caca = c4d.GetC4DVersion()
        now = datetime.datetime.now()
        nowY = now.year
        nowM = now.month
        if nowY >= 2019 and nowM >= 1:
            new = 2  # open in a new tab, if possible
            url = "http://www.3dtoall.com"
            webbrowser.open(url, new=new)
            self.Close()
            return 0

    def CreateLayout(self):

        doc = c4d.documents.GetActiveDocument()
        self.checkVer()

        self.SetTitle("DazToC4D: Config")

        # self.LogoButton0 = self.AddCustomGui(self.BUTTON_LOGO, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("", "Preset0"))
        # self.LogoButton0.SetImage(self.img_logo, True)  # Add the image to the button

        # ----------------------------------------------------------
        self.GroupBegin(11, c4d.BFH_SCALEFIT, 1, 1, title="Character Mesh: ")
        self.GroupBorder(c4d.BORDER_GROUP_IN)
        self.GroupBorderSpace(10, 5, 10, 5)

        self.LinkBox = self.AddCustomGui(
            self.IDC_LINKBOX_1, c4d.CUSTOMGUI_LINKBOX, 'Character Mesh', c4d.BFH_SCALEFIT, 350, 0)
        self.LinkBox.SetLink(DazToC4dUtils().get_daz_mesh())

        meshObj = self.LinkBox.GetLink()

        if DazToC4D().findIK() == 1:
            if meshObj:
                dazJoint = getJointFromSkin(meshObj, 'hip')
                self.jointPelvis = getJointFromConstraint(dazJoint)
                self.dazIkmControls = getJointFromConstraint(
                    self.jointPelvis).GetUp()
                IKMAXFastAttach.jointPelvis = self.jointPelvis

        self.GroupEnd()

        # -----------Main Group
        self.GroupBegin(11, c4d.BFH_CENTER, 1, 1, title="AAAAAA")
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(15, 5, 15, 5)

        self.GroupBegin(11, c4d.BFH_SCALEFIT, 1, 1,
                        title="AAAAAA")  # -----------Main Group
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(15, 5, 15, 5)

        self.GroupBegin(11, c4d.BFH_SCALEFIT, 1, 1,
                        title="")  # -----------Main Group
        self.GroupBorderNoTitle(c4d.BORDER_GROUP_OUT)
        self.GroupBorderSpace(15, 5, 15, 5)

        self.AddCheckbox(208, c4d.BFH_LEFT, 0, 0,
                         "Reduce (similar) materials on import")
        if dazReduceSimilar == True:
            self.SetBool(208, True)
        else:
            self.SetBool(208, False)

        self.AddCheckbox(209, c4d.BFH_LEFT, 0, 0, "Keep facial morphs only")

        # self.AddCheckbox(209, c4d.BFH_LEFT, 0, 0, "Lock all geometry after Auto-IK")
        # self.SetBool(209, True)

        # self.AddCheckbox(209,c4d.BFH_LEFT, 0, 0, "Show extra controls")
        # self.SetBool(209, True)

        # self.AddCheckbox(210,c4d.BFH_LEFT, 0, 0, "Don't hide fingers joints")
        # self.SetBool(210, True)

        self.GroupEnd()
        self.GroupEnd()

        # ----------------------------------------------------------
        self.GroupBegin(11, c4d.BFH_CENTER, 8, 1, title="Rig Display: ")
        self.GroupBorder(c4d.BORDER_GROUP_OUT)
        self.GroupBorderSpace(10, 5, 12, 5)

        self.LogoButton10 = self.AddCustomGui(self.BUTTON_RIG_SHOW, c4d.CUSTOMGUI_BITMAPBUTTON,
                                              "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("<b>Show/Hide Rig</b>", "Preset0"))
        # Add the image to the button
        self.LogoButton10.SetImage(self.img_r_hideshow, True)

        self.LogoButton11 = self.AddCustomGui(self.BUTTON_RIG_MODE, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC(
            "<b>Rig Display Mode</b><br>Switch between standard and<br>box lines display style", "Preset0"))
        # Add the image to the button
        self.LogoButton11.SetImage(self.img_r_box, True)

        self.AddColorField(self.BUTTON_COL1, c4d.BFH_CENTER, 20, 20, c4d.DR_COLORFIELD_NO_SCREENPICKER | c4d.DR_COLORFIELD_NO_SWATCHES | c4d.DR_COLORFIELD_NO_MIXER |
                           c4d.DR_COLORFIELD_NO_MODE_BUTTONS | c4d.DR_COLORFIELD_NO_COLORWHEEL | c4d.DR_COLORFIELD_NO_BRIGHTNESS | c4d.DR_COLORFIELD_NO_COLOR)
        self.AddColorField(self.BUTTON_COL2, c4d.BFH_CENTER, 20, 20, c4d.DR_COLORFIELD_NO_SCREENPICKER | c4d.DR_COLORFIELD_NO_SWATCHES | c4d.DR_COLORFIELD_NO_MIXER |
                           c4d.DR_COLORFIELD_NO_MODE_BUTTONS | c4d.DR_COLORFIELD_NO_COLORWHEEL | c4d.DR_COLORFIELD_NO_BRIGHTNESS | c4d.DR_COLORFIELD_NO_COLOR)
        self.AddColorField(self.BUTTON_COL3, c4d.BFH_CENTER, 20, 20, c4d.DR_COLORFIELD_NO_SCREENPICKER | c4d.DR_COLORFIELD_NO_SWATCHES | c4d.DR_COLORFIELD_NO_MIXER |
                           c4d.DR_COLORFIELD_NO_MODE_BUTTONS | c4d.DR_COLORFIELD_NO_COLORWHEEL | c4d.DR_COLORFIELD_NO_BRIGHTNESS | c4d.DR_COLORFIELD_NO_COLOR)
        self.AddColorField(self.BUTTON_COL4, c4d.BFH_CENTER, 20, 20, c4d.DR_COLORFIELD_NO_SCREENPICKER | c4d.DR_COLORFIELD_NO_SWATCHES | c4d.DR_COLORFIELD_NO_MIXER |
                           c4d.DR_COLORFIELD_NO_MODE_BUTTONS | c4d.DR_COLORFIELD_NO_COLORWHEEL | c4d.DR_COLORFIELD_NO_BRIGHTNESS | c4d.DR_COLORFIELD_NO_COLOR)
        # self.AddColorChooser(123123213, c4d.BFH_CENTER, 20, 20, c4d.DR_COLORFIELD_NO_SCREENPICKER | c4d.DR_COLORFIELD_NO_SWATCHES | c4d.DR_COLORFIELD_NO_MIXER | c4d.DR_COLORFIELD_NO_MODE_BUTTONS | c4d.DR_COLORFIELD_NO_COLORWHEEL | c4d.DR_COLORFIELD_NO_BRIGHTNESS | c4d.DR_COLORFIELD_NO_COLOR)
        # self.AddColorChooser(123123213, c4d.BFH_CENTER, 20, 20, c4d.DR_COLORFIELD_NO_SCREENPICKER | c4d.DR_COLORFIELD_NO_SWATCHES | c4d.DR_COLORFIELD_NO_MIXER | c4d.DR_COLORFIELD_NO_MODE_BUTTONS | c4d.DR_COLORFIELD_NO_COLORWHEEL | c4d.DR_COLORFIELD_NO_BRIGHTNESS | c4d.DR_COLORFIELD_NO_COLOR)
        # self.AddColorChooser(123123213, c4d.BFH_CENTER, 20, 20, c4d.DR_COLORFIELD_NO_SCREENPICKER | c4d.DR_COLORFIELD_NO_SWATCHES | c4d.DR_COLORFIELD_NO_MIXER | c4d.DR_COLORFIELD_NO_MODE_BUTTONS | c4d.DR_COLORFIELD_NO_COLORWHEEL | c4d.DR_COLORFIELD_NO_BRIGHTNESS | c4d.DR_COLORFIELD_NO_COLOR)

        self.SetColorField(
            self.BUTTON_COL1, c4d.Vector(1.0, 0.0, 0.4), 1, 1, 1)
        self.SetColorField(
            self.BUTTON_COL2, c4d.Vector(0.4, 0.8, 1.0), 1, 1, 1)
        self.SetColorField(
            self.BUTTON_COL3, c4d.Vector(0.0, 1.0, 0.5), 1, 1, 1)
        self.SetColorField(
            self.BUTTON_COL4, c4d.Vector(1.0, 0.9, 0.0), 1, 1, 1)

        self.LogoButton12 = self.AddCustomGui(self.BUTTON_COL_SET, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC(
            "<b>Set Rig and IK Colors</b><br>Sets specified colors to<br>Rig and IK Controls", "Preset0"))
        # Add the image to the button
        self.LogoButton12.SetImage(self.img_setColor, True)

        self.LogoButton13 = self.AddCustomGui(self.BUTTON_COL_RANDOM, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC(
            "<b>Random Rig Colors</b><br>Assign random colors<br>to the Rig joints", "Preset0"))
        # Add the image to the button
        self.LogoButton13.SetImage(self.img_r_randomcolor, True)

        self.GroupEnd()

        # ----------------------------------------------------------
        self.GroupBegin(11, c4d.BFH_CENTER, 6, 1, title="Extra: ")
        self.GroupBorder(c4d.BORDER_GROUP_OUT)
        self.GroupBorderSpace(13, 5, 14, 5)

        self.LogoButton16 = self.AddCustomGui(self.BUTTON_MODEL_MIRRORPOSE, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button",
                                              c4d.BFH_CENTER, 0, 0, self.buttonBC("<b>Mirror Joints pose before Auto-IK</b>", "Preset0"))
        # Add the image to the button
        self.LogoButton16.SetImage(self.img_char_mirror, True)

        self.LogoButton16 = self.AddCustomGui(self.BUTTON_MODEL_XRAY, c4d.CUSTOMGUI_BITMAPBUTTON,
                                              "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("<b>X-Ray Mode</b>", "Preset0"))
        # Add the image to the button
        self.LogoButton16.SetImage(self.img_xray, True)

        self.LogoButton16 = self.AddCustomGui(self.BUTTON_MODEL_FREEZE, c4d.CUSTOMGUI_BITMAPBUTTON,
                                              "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("<b>Lock/Unlock</b>", "Preset0"))
        # Add the image to the button
        self.LogoButton16.SetImage(self.img_lock, True)

        guiDazToC4DLayerLockButton = self.LogoButton16

        self.LogoButton15 = self.AddCustomGui(self.BUTTON_EXTRA_FIGURE, c4d.CUSTOMGUI_BITMAPBUTTON,
                                              "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("<b>Reset to Orig Pose</b>", "Preset0"))
        # Add the image to the button
        self.LogoButton15.SetImage(self.img_ani_mode, True)

        # self.LogoButton17 = self.AddCustomGui(self.BUTTON_EXTRA_EYES, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("<b>Quick Auto-Eyes</b><br>Generates LookAt controllers<br>for the eyes", "Preset0"))
        # self.LogoButton17.SetImage(self.img_extra_eyes, True)  # Add the image to the button

        self.LogoButton18 = self.AddCustomGui(self.BUTTON_EXTRA_ATTACH, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC(
            "<b>Fast-Attach</b><br>Attach object/s easy and<br>fast to body part", "Preset0"))
        # Add the image to the button
        self.LogoButton18.SetImage(self.img_QuickAttach, True)

        # self.LogoButton19 = self.AddCustomGui(self.BUTTON_EXTRA_CLOTH, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("<b>Quick-Cloth</b><br>Bind joints to object<br>based on presets", "Preset0"))
        # self.LogoButton19.SetImage(self.img_extraFWarp, True)  # Add the image to the button

        self.GroupEnd()

        self.GroupEnd()  # -------------------------------------Main Group

        self.AddSeparatorV(100, c4d.BFH_FIT)

        # self.GroupBegin(11, c4d.BFV_TOP, 1, 1)  # ----------------------------------------------------------
        # self.GroupBorder(c4d.BORDER_NONE)
        # self.GroupBorderSpace(0, -12, 0, 5)
        #
        # self.AddStaticText(99, c4d.BFH_CENTER, 0, 0, name='(c) 2018 3DtoAll. All Rights Reserved.')  # Add the image to the button
        #
        # self.GroupEnd()

        self.GroupEnd()

        layer = IkMaxUtils().getLayer('IKM_Lock')
        if layer != None:
            try:
                layer_data = layer.GetLayerData(doc)
                lockValue = layer_data['locked']
                if lockValue == True:
                    self.LogoButton16.SetImage(self.img_lockON, True)
            except:
                print('Layer test skipped...')

        # doc = c4d.documents.GetActiveDocument()
        # objTemp = doc.SearchObject("MaleChar-Body")  # temporal para debugearrrr...
        # self.LinkBox.SetLink(objTemp)
        # self.checkOld()

        return True

    def Command(self, id, msg):

        EXTRADialog().checkVer()
        # id is the id number of the object the command was issued from, usually a button
        if id == 208:
            # Reduce Materials on Import

            dazReduceSimilar = self.GetBool(208)
            return 0

        if id == self.BUTTON_MODEL_MIRRORPOSE:
            # print('POSE!!!')
            DazToC4D().mirrorPose()
            return 0

        obj = self.LinkBox.GetLink()
        if obj == None and id != self.BUTTON_MODEL_FREEZE:
            gui.MessageDialog(
                'Select your Character object first', c4d.GEMB_OK)

            return 0

        # MESH SELECT
        if id == self.IDC_LINKBOX_1:
            doc = c4d.documents.GetActiveDocument()
            meshObj = self.LinkBox.GetLink()
            dazJoint = getJointFromSkin(meshObj, 'hip')
            self.jointPelvis = getJointFromConstraint(dazJoint)
            self.dazIkmControls = getJointFromConstraint(
                self.jointPelvis).GetUp()
            IKMAXFastAttach.jointPelvis = self.jointPelvis

            # obj = self.LinkBox.GetLink()
            # daz_name = obj.GetName().replace('.Shape','') + '_'
            # print(daz_name)

        # GUIDES
        if DazToC4D().findIK() == 1:

            if id == self.BUTTON_RESET:
                caca = IkMaxUtils().removeStuff()
                if caca is 1:
                    # Add the image to the button
                    self.imgSelect.SetImage(self.img_select, True)
                    # Add the image to the button
                    self.LogoButton3.SetImage(self.img_RigStart, True)
                    self.LogoButton6.SetImage(self.img_CreateRig_NO, True)
                    c4d.CallCommand(12113, 12113)  # Deselect All
                    c4d.CallCommand(12298)  # Model

            if id == self.BUTTON_START:
                obj = self.LinkBox.GetLink()
                if obj == None:
                    gui.MessageDialog('No object selected', c4d.GEMB_OK)
                else:
                    objRots = obj.GetRelRot()
                    # If rotated or anim, reset all
                    if objRots != c4d.Vector(0, 0, 0):
                        answer = gui.MessageDialog(
                            'Object rotations needs to be reseted. Do you want to proceed?', c4d.GEMB_YESNO)
                        if answer == 6:
                            objFixed = IkMaxUtils().resetObj(obj)
                            self.LinkBox.SetLink(objFixed)
                            EXTRADialog.MASTERSIZE = objHeight = (
                                objFixed.GetRad()[1] * objFixed[c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_Y]) * 2
                            # Start main guides and placement...
                            self.startGuides(objFixed)
                    else:
                        self.startGuides(obj)

            if id == self.BUTTON_HELP:
                dialog = IKMAXhelp()
                dialog.Open(dlgtype=c4d.DLG_TYPE_MODAL,
                            defaultw=200, defaulth=150, xpos=-1, ypos=-1)

            # AUTO-RIG
            if id == self.BUTTON_REMOVE_RIG:
                answer = gui.MessageDialog('Remove RIG?', c4d.GEMB_YESNO)
                if answer == 6:
                    IkMaxUtils().removeRIGandMirrorsandGuides()

                    self.LogoButton9.SetImage(self.img_AutoIK_NO, True)
                    self.LogoButton14.SetImage(self.img_AutoSkin_NO, True)
                    self.imgSelect.SetImage(self.img_adjustGuides, True)

            if id == self.BUTTON_MIRROR:
                doc = documents.GetActiveDocument()
                ikControls = doc.SearchObject(
                    EXTRADialog.PREFFIX + 'IKM_Controls')
                jointsRoot = doc.SearchObject(EXTRADialog.PREFFIX + 'jPelvis')
                answer = 0
                if ikControls:
                    answer = gui.MessageDialog(
                        'Remove IK to make rig changes/mirror rig, etc.\nWhen happy generate Auto-IK again.\n\nRemove IK now and mirror RIG?', c4d.GEMB_YESNO)
                    if answer == 6:
                        IkMaxUtils().removeIK()
                        print('Removing IK...')

                if ikControls == None or answer == 6:
                    suffix = "___R"
                    objArm = doc.SearchObject(EXTRADialog.PREFFIX + 'jCollar')
                    objLeg = doc.SearchObject(EXTRADialog.PREFFIX + 'jUpLeg')
                    IkMaxUtils().mirrorObjects(objArm, suffix)
                    IkMaxUtils().mirrorObjects(objLeg, suffix)
                doc.FlushUndoBuffer()

            if id == self.BUTTON_IK_COL_RANDOM:
                obj = self.LinkBox.GetLink()
                objName = obj.GetName().replace('.Shape', '') + '_'
                # obj = doc.SearchObject(objName + 'jPelvis')

                randomColors().randomNullsColor(objName + "IKM_Controls")
                randomColors().randomPoleColors(self.jointPelvis)

            # RIG-DISPLAY
            if id == self.BUTTON_RIG_SHOW:
                doc = c4d.documents.GetActiveDocument()

                # for x in IkMaxUtils().iterateObjChilds(self.jointPelvis):
                #     displayValue = x[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR]
                #     x[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = not x[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR]
                # self.jointPelvis[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = not self.jointPelvis[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR]

                boneDisplay = self.jointPelvis[c4d.ID_CA_JOINT_OBJECT_BONE_DISPLAY]
                if boneDisplay != 0:
                    boneDisplay = 0
                else:
                    boneDisplay = 2
                for x in IkMaxUtils().iterateObjChilds(self.jointPelvis):
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
                                if 'Display' in tag.GetName():
                                    displayReady = 1
                        except:
                            pass

                    if displayReady == 0:
                        addDisplayTAG(obj)

                    if displayReady == 1:
                        tags = TagIterator(obj)
                        try:
                            for tag in tags:
                                if 'Display' in tag.GetName():
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

                # obj = self.LinkBox.GetLink()
                # objName = obj.GetName().replace('.Shape','') + '_'
                # obj = doc.SearchObject(objName + 'jPelvis')
                obj = self.jointPelvis

                getDisplayTAG(obj)
                c4d.EventAdd()

            if id == self.BUTTON_COL_RANDOM:
                print('random colors')
                # obj = self.LinkBox.GetLink()
                # objName = obj.GetName().replace('.Shape', '') + '_'

                randomColors().randomRigColor(self.jointPelvis)
                print(self.dazIkmControls.GetName())
                randomColors().randomNullsColor(self.dazIkmControls)
                randomColors().randomPoleColors(self.jointPelvis)

            if id == self.BUTTON_COL_SET:
                obj = self.LinkBox.GetLink()
                objName = obj.GetName().replace('.Shape', '') + '_'
                # obj = doc.SearchObject(objName + 'jPelvis')

                RIGCOL1 = self.GetColorField(self.BUTTON_COL1)['color']
                RIGCOL2 = self.GetColorField(self.BUTTON_COL2)['color']
                RIGCOL3 = self.GetColorField(self.BUTTON_COL3)['color']
                RIGCOL4 = self.GetColorField(self.BUTTON_COL4)['color']

                randomColors().randomRigColor(self.jointPelvis, 0, RIGCOL2, RIGCOL1)
                randomColors().randomNullsColor(self.dazIkmControls, 0, RIGCOL3, RIGCOL4)
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
                DazToC4D().lockLayerOnOff()
                # meshToBind = self.LinkBox.GetLink()
                # lockLayer = IkMaxUtils().layerSettings(meshToBind)
                # if lockLayer == True:
                #     self.LogoButton16.SetImage(self.img_lock, True)
                # else:
                #     self.LogoButton16.SetImage(self.img_lockON, True)

            if id == self.BUTTON_EXTRA_FIGURE:
                obj = self.LinkBox.GetLink()
                # objName = obj.GetName().replace('.Shape','') + '_'

                IkMaxUtils().setProtectionChildren(self.dazIkmControls, 0)

                IkMaxUtils().resetPRS(self.dazIkmControls)
                IkMaxUtils().resetPRS(self.jointPelvis)
                # IkMaxUtils().resetPRS(objName + "Eyes-LookAt")

                IkMaxUtils().setProtectionChildren(self.dazIkmControls, 1)

            if id == self.BUTTON_EXTRA_EYES:
                doc = documents.GetActiveDocument()
                characterMesh = self.LinkBox.GetLink()
                allOk = 1

                answer = gui.MessageDialog(
                    'This is an experimental feature, you may want to save your scene first. Do you want to proceed?', c4d.GEMB_YESNO)
                if answer != 6:
                    return 0

                selected = doc.GetActiveObjects(0)

                if len(selected) != 2:
                    gui.MessageDialog(
                        'You need to select 2 eyes/objects o.O!', c4d.GEMB_OK)
                    allOk = 0
                if IkMaxUtils().checkIfExist('jHead') != 1:
                    gui.MessageDialog(
                        'No rig detected, first you need to\ngenerate a rig for your Character', c4d.GEMB_OK)
                    allOk = 0

                if allOk == 1:
                    ojo1 = selected[0]
                    ojo2 = selected[1]

                    headJoint = doc.SearchObject(EXTRADialog.PREFFIX + 'jHead')
                    joints = doc.SearchObject(EXTRADialog.PREFFIX + 'jPelvis')

                    obj1 = IkMaxUtils().makeNull('lEye_ctrl', ojo1)
                    obj2 = IkMaxUtils().makeNull('rEye_ctrl', ojo2)

                    objParent = ojo1.GetUp()
                    eyesParentNull = IkMaxUtils().makeNull('EyesParent', headJoint)
                    eyesGroup = IkMaxUtils().makeNull('EyesParent', headJoint)
                    eyesGroup2 = IkMaxUtils().makeNull('EyesParent', headJoint)

                    #obj1.SetName(EXTRADialog.PREFFIX + 'Eye1')
                    #obj2.SetName(EXTRADialog.PREFFIX + 'Eye2')
                    obj1.SetAbsScale(c4d.Vector(1, 1, 1))
                    obj2.SetAbsScale(c4d.Vector(1, 1, 1))

                    eyesParentNull.SetName(EXTRADialog.PREFFIX + 'Eyes-LookAt')
                    eyesGroup.SetName(EXTRADialog.PREFFIX + 'EyesGroup')

                    masterSize = EXTRADialog.MASTERSIZE  # IkMaxUtils().getObjHeight(characterMesh)

                    obj1[c4d.ID_BASEOBJECT_REL_POSITION,
                         c4d.VECTOR_Z] -= masterSize / 4
                    obj2[c4d.ID_BASEOBJECT_REL_POSITION,
                         c4d.VECTOR_Z] -= masterSize / 4

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
                        obj[c4d.NULLOBJECT_RADIUS] = (masterSize / 25)

                    def makeChild(child, parent):
                        mg = child.GetMg()
                        child.InsertUnder(parent)
                        child.SetMg(mg)

                    c4d.CallCommand(12113, 12113)  # Deselect All
                    doc.SetActiveObject(obj1, c4d.SELECTION_NEW)
                    doc.SetActiveObject(obj2, c4d.SELECTION_ADD)
                    c4d.CallCommand(100004772, 100004772)  # Group Objects
                    c4d.CallCommand(100004773, 100004773)  # Expand Object

                    objMasterEyes = doc.GetActiveObjects(0)[0]
                    objMasterEyes.SetName(
                        EXTRADialog.PREFFIX + 'EyesLookAtGroup')
                    objMasterEyes.SetAbsScale(c4d.Vector(1, 1, 1))

                    nullStyle(obj1)
                    nullStyle(obj2)
                    nullStyleMaster(objMasterEyes)

                    IkmGenerator().constraintObj(ojo1, obj1, 'AIM', 0)
                    IkmGenerator().constraintObj(ojo2, obj2, 'AIM', 0)

                    makeChild(obj1, objMasterEyes)
                    makeChild(obj2, objMasterEyes)
                    makeChild(objMasterEyes, eyesParentNull)

                    obj1.SetAbsRot(c4d.Vector(0))
                    obj2.SetAbsRot(c4d.Vector(0))

                    #IkmGenerator().constraintObj(eyesGroup, headJoint, '', 0)
                    IkmGenerator().constraintObj(eyesParentNull, headJoint, '', 0)

                    #makeChild(ojo1, eyesGroup)
                    #makeChild(ojo2, eyesGroup)

                    # if objParent != None:
                    #     makeChild(eyesGroup, objParent)

                    # eyesGroup.InsertAfter(joints)
                    eyesParentNull.InsertAfter(joints)

                    IkMaxUtils().freezeChilds(EXTRADialog.PREFFIX + "Eyes-LookAt")
                    IkMaxUtils().freezeChilds(EXTRADialog.PREFFIX + "EyesLookAtGroup")

                    #IkMaxUtils().freezeChilds(EXTRADialog.PREFFIX + "EyesGroup")

                    c4d.EventAdd()
                    c4d.CallCommand(12288, 12288)  # Frame All

            if id == self.BUTTON_EXTRA_ATTACH:
                doc = documents.GetActiveDocument()

                if len(doc.GetActiveObjects(1)) == 0:
                    gui.MessageDialog(
                        'Select object(s) that you want to attach to joints')
                    return 0
                else:
                    # if IkMaxUtils().checkIfExist('jHead') != 1:
                    #     gui.MessageDialog('Generate a RIG first', c4d.GEMB_OK)
                    #     return 0
                    dialog = IKMAXFastAttach()
                    dialog.Open(dlgtype=c4d.DLG_TYPE_MODAL,
                                defaultw=200, defaulth=150, xpos=-1, ypos=-1)

        return True


class guiLoading(gui.GeDialog):
    dialog = None

    def CreateLayout(self):
        c4d.CallCommand(300001026, 300001026)  # Deselect All
        c4d.CallCommand(12168, 12168)  # Remove Unused Materials

        self.SetTitle('DazToC4D: Processing...')

        self.GroupBegin(10000, c4d.BFH_CENTER, 1, title='')
        self.GroupBorder(c4d.BORDER_OUT)
        self.GroupBorderSpace(10, 5, 10, 5)

        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0, name=r'Please wait...')

        self.GroupEnd()  # END ///////////////////////////////////////////////
        # gui.MessageDialog('Popup')
        return True

    # def Message(self, msg, result):
    #     print('asdasd')
    #     if guiDazToC4Dloading:
    #         self.Close()
    #         global guiDazToC4Dloading
    #         guiDazToC4Dloading = None
    #         return True
    #
    #     return gui.GeDialog.Message(self, msg, result)

    # def __init__(self):
    #     print('cascascaaaaaaaaaaaaaaaaaaaaaaaaaa')
    #     # guiDazToC4Dloading.Close()
    #     # gui.MessageDialog('Popup')
    #     self.Close()
    #     # guiDazToC4Dloading.Close()

    def InitValues(self):
        c4d.StatusClear()
        c4d.EventAdd()
        c4d.EventAdd(c4d.EVENT_FORCEREDRAW)
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW |
                      c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        c4d.DrawViews()
        # gui.MessageDialog('Popup')
        # guiDazToC4Dloading.Close()
        # guiDazToC4Dloading.KillEvents()
        # print(guiDazToC4Dloading)
        return True

    def Command(self, id, msg):
        print('OOOOOOOOOOOOOOOOOOOOO')
        print(id)
        print(msg)

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

    dir, file = os.path.split(__file__)  # Gets the plugin's directory
    # Adds the res folder to the path
    daztoC4D_Folder = os.path.join(dir, 'res')
    # Adds the res folder to the path
    daztoC4D_FolderImgs = os.path.join(daztoC4D_Folder, 'imgs')

    # img_d2c4dLogo = os.path.join(daztoC4D_Folder, 'd2c4d_logo.png')

    img_btnSave = os.path.join(daztoC4D_FolderImgs, 'btnSave.png')
    img_btnLater = os.path.join(daztoC4D_FolderImgs, 'btnLater.png')
    # img_btnConvertMaterials = os.path.join(daztoC4D_Folder, 'btnConvertMaterials.png')
    # img_btnConfig = os.path.join(daztoC4D_Folder, 'btnConfig.png')

    def buttonBC(self, tooltipText="", presetLook=""):
        # Logo Image #############################################################
        bc = c4d.BaseContainer()  # Create a new container to store the button image
        bc.SetBool(c4d.BITMAPBUTTON_BUTTON, True)
        bc.SetString(c4d.BITMAPBUTTON_TOOLTIP, tooltipText)

        if presetLook == "":
            # Sets the border to look like a button
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_ROUND)
        if presetLook == "Preset0":
            # Sets the border to look like a button
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE)
        if presetLook == "Preset1":
            # Sets the border to look like a button
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE)
            bc.SetBool(c4d.BITMAPBUTTON_BUTTON, False)

        return bc
        # Logo Image #############################################################

    def CreateLayout(self):
        # doc = documents.GetActiveDocument()
        # if doc.SearchObject('hip'):
        #     AllSceneToZero().sceneToZero()
        #     pass
        c4d.CallCommand(300001026, 300001026)  # Deselect All
        c4d.CallCommand(12168, 12168)  # Remove Unused Materials
        # c4d.CallCommand(12211, 12211)  # Remove Duplicate Materials
        self.SetTitle('DazToC4D: Transfer Done!')

        # Logo Image #############################################################
        # bc = c4d.BaseContainer()  # Create a new container to store the button image
        # bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_ROUND)  # Sets the border to look like a button
        # self.LogoButton = self.AddCustomGui(self.MY_BITMAP_BUTTON, c4d.CUSTOMGUI_BITMAPBUTTON, "Logo", c4d.BFH_CENTER, 0, 0, bc)
        # self.LogoButton.SetImage(self.img_d2c4dLogo, False)  # Add the image to the button
        # Logo Image #############################################################

        # Import
        self.GroupBegin(10000, c4d.BFH_CENTER, 1, title='Auto-Import Info:')
        self.GroupBorder(c4d.BORDER_OUT)
        self.GroupBorderSpace(10, 5, 10, 5)

        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0,
                           name=r'To transfer from DAZ Studio to Cinema 4D you are using a Temp folder.')
        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0,
                           name=r'Now is a good time to save the scene+textures to another location.')

        self.GroupEnd()  # END ///////////////////////////////////////////////

        self.GroupBegin(10000, c4d.BFH_CENTER, 2, title='Import:')
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(10, 5, 10, 5)

        self.LogoButton6 = self.AddCustomGui(
            self.BUTTON_SAVE, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("", "Preset0"))
        # Add the image to the button
        self.LogoButton6.SetImage(self.img_btnSave, True)

        self.LogoButton6 = self.AddCustomGui(
            self.BUTTON_CANCEL, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("", "Preset0"))
        # Add the image to the button
        self.LogoButton6.SetImage(self.img_btnLater, True)

        # self.AddButton(self.BUTTON_SAVE, c4d.BFV_MASK, initw=150, inith=35, name="Save Now!")
        # self.AddButton(self.BUTTON_CANCEL, c4d.BFV_MASK, initw=150, inith=35, name="*Later")
        self.GroupEnd()  # END ///////////////////////////////////////////////

        self.AddSeparatorH(c4d.BFV_SCALEFIT)  # Separator H

        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0,
                           name=r'*If you save later remember to save using File\Save Project with Assets...')
        self.AddSeparatorH(c4d.BFV_SCALEFIT)  # Separator H

        return True

    def Command(self, id, msg):

        if id == self.BUTTON_SAVE:
            c4d.CallCommand(12255, 12255)  # Save Project with Assets...

        if id == self.BUTTON_CANCEL:
            self.Close()

        return True


class guiPleaseWaitAUTO(gui.GeDialog):
    dialog = None

    def CreateLayout(self):
        self.SetTitle('DazToC4D: Importing...')

        self.GroupBegin(10000, c4d.BFH_SCALEFIT, 1, title='')
        self.GroupBorderNoTitle(c4d.BORDER_ACTIVE_3)
        self.GroupBorderSpace(5, 10, 5, 10)

        self.AddSeparatorH(c4d.BFH_SCALEFIT)  # Separator H

        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0,
                           name=r'Importing. Please Wait...')
        self.AddSeparatorH(280, c4d.BFH_SCALEFIT)  # Separator H

        self.GroupEnd()

        return True

    def Command(self, id, msg):

        if id == self.BUTTON_SAVE:
            c4d.CallCommand(12255, 12255)  # Save Project with Assets...

        if id == self.BUTTON_CANCEL:
            self.Close()

        return True

# Creates the Main Window
class guiDazToC4dMain(gui.GeDialog):
    dialog = None
    extraDialog = None

    BUTTON_CONFIG = 923123
    BUTTON_AUTO_IMPORT = 923124
    BUTTON_MANUAL_IMPORT = 923125
    BUTTON_CONVERT_MATERIALS = 923126
    BUTTON_CONFIG = 923127
    BUTTON_TEMP = 923128
    BUTTON_HELP = 923129
    BUTTON_AUTO_IK = 923130

    MY_BITMAP_BUTTON = 9353535

    logo_button = ''

    dir, file = os.path.split(__file__)  # Gets the plugin's directory
    # Adds the res folder to the path
    daz_to_c4d_folder = os.path.join(folder, 'res')
    
    img_d2c4d_logo = os.path.join(daz_to_c4d_folder, 'd2c4d_logo.png')
    img_d2c4d_loading = os.path.join(daz_to_c4d_folder, 'd2c4d_loading.png')

    img_d2c4d_help = os.path.join(daz_to_c4d_folder, 'd2c4d_help.png')

    img_btn_auto_import = os.path.join(daz_to_c4d_folder, 'btnAutoImport.png')
    img_btn_auto_import_off = os.path.join(
        daz_to_c4d_folder, 'btnAutoImport0.png')
    img_btn_manual_import = os.path.join(daz_to_c4d_folder, 'btnImport.png')
    img_btn_manual_import_off = os.path.join(
        daz_to_c4d_folder, 'btnImport0.png')
    img_btn_convert_materials = os.path.join(
        daz_to_c4d_folder, 'btnConvertMaterials.png')
    img_btn_convert_materials_off = os.path.join(
        daz_to_c4d_folder, 'btnConvertMaterials0.png')
    img_btn_auto_ik = os.path.join(daz_to_c4d_folder, 'btnAutoIK.png')
    img_btn_auto_ik_off = os.path.join(daz_to_c4d_folder, 'btnAutoIK0.png')

    img_btn_config = os.path.join(daz_to_c4d_folder, 'btnConfig.png')

    def __init__(self):
        try:
            self.AddGadget(c4d.DIALOG_NOMENUBAR, 0)  # disable menubar
        except:
            pass

    def buttonBC(self, tooltipText="", presetLook=""):
        # Logo Image #############################################################
        bc = c4d.BaseContainer()  # Create a new container to store the button image
        bc.SetBool(c4d.BITMAPBUTTON_BUTTON, True)
        bc.SetString(c4d.BITMAPBUTTON_TOOLTIP, tooltipText)

        if presetLook == "":
            # Sets the border to look like a button
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_ROUND)
        if presetLook == "Preset0":
            # Sets the border to look like a button
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE)
        if presetLook == "Preset1":
            # Sets the border to look like a button
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE)
            bc.SetBool(c4d.BITMAPBUTTON_BUTTON, False)

        return bc
        # Logo Image #############################################################

    def CreateLayout(self):

        self.SetTitle('DazToC4D v1.1')
        self.AddSeparatorH(c4d.BFV_SCALEFIT)  # Separator H

        # Logo Image #############################################################
        bc = c4d.BaseContainer()  # Create a new container to store the button image
        # Sets the border to look like a button
        bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_ROUND)
        self.logo_button = self.AddCustomGui(
            self.MY_BITMAP_BUTTON, c4d.CUSTOMGUI_BITMAPBUTTON, "Logo", c4d.BFH_CENTER, 0, 0, bc)
        # Add the image to the button
        self.logo_button.SetImage(self.img_d2c4d_logo, False)

        guiDazToC4dMainLogo = self.logo_button
        print('**********************')
        print(self.logo_button)
        print('**********************')

        # Logo Image #############################################################

        # Import
        self.GroupBegin(10000, c4d.BFH_CENTER, 1, title='')
        self.GroupBorderNoTitle(c4d.BORDER_OUT)
        self.GroupBorderSpace(0, 0, 0, 0)

        # BEGIN ----------------------
        self.GroupBegin(10000, c4d.BFH_SCALEFIT, 5)
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(12, 5, 10, 5)

        self.LogoButton6 = self.AddCustomGui(
            self.BUTTON_CONFIG, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.button_bc("", "Preset0"))
        # Add the image to the button
        self.LogoButton6.SetImage(self.img_btn_config, True)

        self.AddSeparatorV(0, c4d.BFV_SCALEFIT)  # Separator V

        self.LogoButton6 = self.AddCustomGui(
            self.BUTTON_AUTO_IMPORT, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.button_bc("", "Preset0"))
        # Add the image to the button
        self.LogoButton6.SetImage(self.img_btn_auto_import, True)

        guiDazToC4dMainAutoImp = self.LogoButton6

        self.AddSeparatorV(0, c4d.BFV_SCALEFIT)  # Separator V

        self.LogoButton6 = self.AddCustomGui(
            self.BUTTON_AUTO_IK, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.button_bc("", "Preset0"))
        # Add the image to the button
        self.LogoButton6.SetImage(self.img_btn_auto_ik, True)

        guiDazToC4dMainIK = self.LogoButton6

        self.GroupEnd()  # END ///////////////////////////////////////////////
        self.GroupEnd()  # END ///////////////////////////////////////////////

        # Rig
        # self.GroupBegin(10000, c4d.BFH_CENTER, 1, title='Rig:')
        # self.GroupBorder(c4d.BORDER_OUT)
        # self.GroupBorderSpace(0, 0, 0, 0)
        #
        # self.GroupBegin(10000, c4d.BFH_SCALEFIT, 5)  # BEGIN ----------------------
        # self.GroupBorderNoTitle(c4d.BORDER_NONE)
        # self.GroupBorderSpace(12, 5, 10, 5)
        #
        # self.LogoButton6 = self.AddCustomGui(self.BUTTON_CONFIG, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("", "Preset0"))
        # self.LogoButton6.SetImage(self.img_btnConfig, True)  # Add the image to the button
        #
        # self.AddSeparatorV(0, c4d.BFV_SCALEFIT)  # Separator V
        #
        # self.LogoButton6 = self.AddCustomGui(self.BUTTON_AUTO_IK, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("", "Preset0"))
        # self.LogoButton6.SetImage(self.img_btnAutoIK, True)  # Add the image to the button
        # global guiDazToC4dMainIK
        # guiDazToC4dMainIK = self.LogoButton6
        #
        # self.GroupEnd()  # END ///////////////////////////////////////////////
        self.GroupEnd()  # END ///////////////////////////////////////////////

        # self.GroupBegin(10000, c4d.BFH_SCALEFIT, 2)
        # self.GroupBorderNoTitle(c4d.BORDER_THIN_OUT)
        # self.GroupBorderSpace(80, 10, 10, 10)
        #
        # self.AddStaticText(99, c4d.BFH_CENTER, 70, 0, name='Scale: ')
        # self.AddComboBox(1000, c4d.BFH_CENTER, 150, 15, False)
        # self.AddChild(1000, 0, 'Automatic')
        # self.GroupEnd()
        #
        # self.GroupEnd()

        self.AddSeparatorH(c4d.BFV_SCALEFIT)  # Separator H

        # MATERIALS BEGIN -----------------------------------------------------
        self.GroupBegin(10000, c4d.BFH_SCALEFIT, 1, title='Materials:')
        self.GroupBorder(c4d.BORDER_OUT)
        self.GroupBorderSpace(10, 0, 10, 10)

        # BEGIN ----------------------
        self.GroupBegin(10000, c4d.BFH_SCALEFIT, 3)
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(20, 5, 20, 5)

        self.LogoButton6 = self.AddCustomGui(self.BUTTON_CONVERT_MATERIALS, c4d.CUSTOMGUI_BITMAPBUTTON,
                                             "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.button_bc("", "Preset0"))
        # Add the image to the button
        self.LogoButton6.SetImage(self.img_btn_convert_materials, True)

        guiDazToC4dMainConvert = self.LogoButton6
        self.AddSeparatorV(0, c4d.BFV_SCALEFIT)  # Separator V
        self.AddComboBox(2001, c4d.BFH_SCALEFIT, 100, 15, False)
        self.AddChild(2001, 0, ' - Select -')
        self.AddChild(2001, 1, 'V-Ray')
        self.AddChild(2001, 2, 'Redshift')
        self.AddChild(2001, 3, 'Octane')

        self.GroupEnd()  # END ///////////////////////////////////////////////

        # BEGIN ----------------------
        self.GroupBegin(10000, c4d.BFH_SCALEFIT, 2,
                        title='Global Skin Parameters:')
        self.GroupBorder(c4d.BORDER_THIN_OUT)
        self.GroupBorderSpace(20, 5, 20, 5)

        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0, name='Specular Weight:')
        self.AddEditSlider(17524, c4d.BFH_SCALEFIT, initw=40, inith=0)
        self.SetInt32(17524, value=20, min=0, max=100)

        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0,
                           name='Specular Roughtness:')
        self.AddEditSlider(17525, c4d.BFH_SCALEFIT, initw=40, inith=0)
        self.SetInt32(17525, value=57, min=0, max=100)

        self.GroupEnd()  # END ///////////////////////////////////////////////

        self.GroupEnd()  # MATERIALS END ///////////////////////////////////////////////

        # self.AddButton(BUTTON_TEMP, name='cacca')
        # self.AddButton(self.BUTTON_TEMP, c4d.BFV_MASK, initw=150, inith=35, name="TEST")

        self.AddSeparatorH(c4d.BFV_SCALEFIT)  # Separator H

        # BEGIN ----------------------
        self.GroupBegin(10000, c4d.BFH_CENTER, 2,
                        title='Global Skin Parameters:')
        self.AddStaticText(99, c4d.BFH_SCALEFIT, 0, 0,
                           name='Copyright(c) 2020. All Rights Reserved.')

        self.LogoButtonHelp = self.AddCustomGui(
            self.BUTTON_HELP, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.button_bc("Help", "Preset0"))
        # Add the image to the button
        self.LogoButtonHelp.SetImage(self.img_d2c4d_help, True)

        self.GroupEnd()
        self.AddSeparatorH(c4d.BFV_SCALEFIT)  # Separator H

        return True

    def Command(self, id, msg):
        if id == 17524:
            slider_value = self.GetFloat(17524)
            DazToC4D().matSetSpec('Weight', slider_value)
            c4d.EventAdd()

        if id == 17525:
            slider_value = self.GetFloat(17525)
            print(slider_value/100)
            DazToC4D().matSetSpec('Rough', slider_value)
            c4d.EventAdd()

        if id == self.BUTTON_MANUAL_IMPORT:
            # gui.MessageDialog('Not in beta', c4d.GEMB_OK)
            new = 2  # open in a new tab, if possible
            url = "http://www.daz3d.com"
            webbrowser.open(url, new=new)

        if id == self.BUTTON_AUTO_IMPORT:
            DazToC4D().autoImportDazJustImport()
            # DazToC4D().autoImportDaz()

        if id == self.BUTTON_AUTO_IK:

            try:
                guiDazToC4DExtraDialog.Close()
            except:
                print('Extra Dialog Close Error...')
            doc = documents.GetActiveDocument()
            obj = doc.GetFirstObject()
            scene = ObjectIterator(obj)
            hipFound = False
            IKFound = False

            for obj in scene:
                if 'hip' in obj.GetName():
                    hipFound = True
                if 'Foot_PlatformBase' in obj.GetName():
                    IKFound = True

            if hipFound == False:
                gui.MessageDialog(
                    'No rig found to apply IK, Auto-Import a Figure and try again.', c4d.GEMB_OK)
                return 0
            else:
                if IKFound == True:
                    gui.MessageDialog(
                        'IK Already Found, Auto-Import and try again.', c4d.GEMB_OK)
                    return 0
                else:
                    if DazToC4D().findMesh() == False:
                        gui.MessageDialog(
                            'No Figure found, Auto-Import a Figure and try again.', c4d.GEMB_OK)
                    else:
                        DazToC4D().checkIfPosedResetPose()  # THIS RUNS AUTO-IK !

            DazToC4D().buttonsChangeState(True)

        if id == self.BUTTON_CONFIG:
            if self.extraDialog != None:
                self.extraDialog.Close()
            if self.extraDialog == None:
                self.extraDialog = EXTRADialog()
                # global guiDazToC4DExtraDialog
                guiDazToC4DExtraDialog = self.extraDialog
            self.extraDialog = EXTRADialog()
            # global guiDazToC4DExtraDialog
            guiDazToC4DExtraDialog = self.extraDialog
            self.extraDialog.Open(dlgtype=c4d.DLG_TYPE_ASYNC,
                                  xpos=-1, ypos=-1, defaultw=200, defaulth=150)

        if id == self.BUTTON_CONVERT_MATERIALS:
            # CONVERT MATERIAL
            doc = c4d.documents.GetActiveDocument()
            comboRender = self.GetInt32(2001)

            if comboRender == 0:
                gui.MessageDialog('Please select renderer from the list')

            else:
                if DazToC4D().checkStdMats() == True:
                    return
                else:
                    answer = gui.MessageDialog(
                        '::: WARNING :::\n\nNo Undo for this.\nSave your scene first, in case you want to revert changes.\n\nProceed and Convert Materials now?', c4d.GEMB_YESNO)
                    if answer is 6:
                        if comboRender == 1:
                            ConvertToVray()
                            c4d.CallCommand(1026375)  # Reload Python Plugins

                        if comboRender == 2:
                            ConvertToRedshift()
                            DazToC4D().hideEyePolys()
                            c4d.CallCommand(100004766, 100004766)  # Select All
                            # Deselect All
                            c4d.CallCommand(100004767, 100004767)

                        if comboRender == 3:
                            ConvertToOctane()
                            DazToC4D().hideEyePolys()
                            c4d.CallCommand(100004766, 100004766)  # Select All
                            # Deselect All
                            c4d.CallCommand(100004767, 100004767)

        if id == self.BUTTON_TEMP:
            if self.dialog == None:
                self.dialog = EXTRADialog()
            self.dialog = EXTRADialog()
            self.dialog.Open(dlgtype=c4d.DLG_TYPE_ASYNC, xpos=-1,
                             ypos=-1, pluginid=103299851, defaultw=200, defaulth=150)

        if id == self.BUTTON_HELP:
            new = 2  # open in a new tab, if possible
            url = "http://www.daz3d.com"
            webbrowser.open(url, new=new)

        return True


class authDialogDazToC4D(c4d.gui.GeDialog):
    dialog = None
    _serList = []
    MY_BITMAP_BUTTON = 9353535
    IDS_AUTH = 40000
    IDS_AUTH_DIALOG = 40001
    DLG_AUTH = 41000
    IDC_SERIAL = 41001
    IDC_SERIAL_COPY = 41008
    IDC_SUBMIT = 41002
    IDC_CANCEL = 41003
    IDC_CODEBOX = 41004
    IDC_CODEBOX_AUTH = 41005
    IDC_PASTESERIAL = 41007

    def CreateLayout(self):

        # print("CreateLayout")
        dir, file = os.path.split(__file__)  # Gets the plugin's directory
        # Adds the res folder to the path
        LogoFolder_Path = os.path.join(dir, 'res')
        LogoImage_Path = os.path.join(LogoFolder_Path, 'm2c4d_serialh.jpg')

        self.SetTitle('DazToC4D - Activation')

        self.GroupBegin(11, c4d.BFH_SCALEFIT, 1, title='Registration')

        # Logo Image #############################################################
        bc = c4d.BaseContainer()  # Create a new container to store the button image
        # Sets the border to look like a button
        bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_ROUND)
        self.LogoButton = self.AddCustomGui(
            self.MY_BITMAP_BUTTON, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, bc)
        # Add the image to the button
        self.LogoButton.SetImage(guiDazToC4dMain().img_d2c4dLogo, False)
        # Logo Image #############################################################

        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(5, 0, 5, 5)

        self.GroupBegin(11, c4d.BFH_CENTER, 1, title='')
        self.GroupBorderSpace(0, 0, 0, 0)
        self.AddStaticText(11, c4d.BFH_CENTER, name="Your DazToC4D Code:")

        self.GroupBegin(11, c4d.BFH_CENTER, 2, title='')
        self.GroupBorderNoTitle(c4d.BORDER_THIN_OUT)
        self.GroupBorderSpace(20, 5, 20, 5)
        self.AddStaticText(IDC_CODEBOX_AUTH, c4d.BFH_CENTER,
                           borderstyle=c4d.BORDER_IN)
        self.AddButton(self.IDC_SERIAL_COPY,
                       c4d.BFH_CENTER, 60, 15, name="Copy")
        self.GroupEnd()

        self.AddButton(IDC_SERIAL, c4d.BFH_CENTER, 250,
                       20, name="Get Activation Serial")

        self.GroupBegin(11, c4d.BFV_TOP, 200, 2)
        self.GroupBorderSpace(0, 10, 0, 0)
        self.AddSeparatorV(100, c4d.BFH_FIT)
        self.AddStaticText(11, c4d.BFH_CENTER,
                           name="DazToC4D Activation Serial:")
        self.AddSeparatorV(100, c4d.BFH_FIT)
        self.GroupEnd()

        self.GroupBegin(11, c4d.BFV_TOP, 200, 2)
        self.GroupBorderNoTitle(c4d.BORDER_ACTIVE_4)
        self.GroupBorderSpace(5, 5, 3, 5)

        # self.AddStaticText(11, c4d.BFH_CENTER, name = "Enter your Activation Serial here     " )

        self.AddButton(IDC_PASTESERIAL, c4d.BFH_CENTER, 40, 60, name="Paste")
        self.AddMultiLineEditText(
            IDC_CODEBOX, c4d.BFH_CENTER, initw=410, inith=60)
        self.SetString(IDC_CODEBOX, "Enter your Activation Serial here.")

        self.GroupEnd()

        self.SetString(IDC_CODEBOX_AUTH, self.GetAC())

        self.AddButton(IDC_SUBMIT, c4d.BFH_CENTER, 150, 30, name="SUBMIT")
        self.GroupEnd()
        self.GroupEnd()

        self.GroupBegin(11, c4d.BFV_TOP, 200, 2)
        self.GroupBorder(c4d.BORDER_WITH_TITLE_MONO)
        self.GroupBorderSpace(0, 0, 0, 10)
        # self.AddButton(IDC_CANCEL, c4d.BFH_CENTER, 100, 20, name="Cancel")

        self.GroupEnd()

        self.AddSeparatorV(100, c4d.BFH_FIT)

        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0,
                           name='CopyRight (c) 2020. 3DtoAll. All Rights Reserved.')

        return True

    def Command(self, id, msg):

        if id == self.IDC_PASTESERIAL:
            pasteText = c4d.GetStringFromClipboard()
            if pasteText != None:
                self.SetString(IDC_CODEBOX, pasteText.replace(' ', ''))

        if id == self.IDC_SERIAL_COPY:
            c4d.CopyStringToClipboard(self.GetString(IDC_CODEBOX_AUTH))

        if id == self.IDC_SERIAL:
            new = 2  # open in a new tab, if possible
            url = "http://www.3dtoall.com/register"
            webbrowser.open(url, new=new)

        if id == self.IDC_SUBMIT:

            ReturnSuccess = False

            srl = self.GetString(IDC_CODEBOX)
            print(srl)
            if self.checkSrlDAZ(srl) == True:

                bc = c4d.BaseContainer()
                # bc.SetBool(101, True)
                srl = srl.replace(' ', '')
                bc.SetString(101, srl)
                c4d.plugins.SetWorldPluginData(PLUGIN_ID, bc, False)

                ReturnSuccess = True

            if ReturnSuccess:
                gui.MessageDialog("DazToC4D: Plugin Authorization successful!")
                # print("3DToAll Plugin Authorization successful.")
                self.Close()
            else:
                gui.MessageDialog(
                    "DazToC4D: Please enter a valid serial number.")
                # print("Please enter a valid serial number.")

        if id == self.IDC_CANCEL:
            self.Close()

        return True

    def VerSC(self, srl):
        activcode = srl.replace(' ', '')
        if activcode == "912205626U59":
            return True
        serialError = False
        siNr = ''
        try:
            c4d.GeGetSerialInfo(c4d.SERIALINFO_MULTILICENSE)
        except:
            serialError = True

        if serialError == True:  # CINEMA R21 or UP <<<<<<<<<<<<
            try:
                print('R21 or Up...')
                data = json.loads(c4d.ExportLicenses())
                # c4dversion = float(data["version"])
                sysID = data["systemid"]
                c4dserial = sysID[0:11]
            except:
                gui.MessageDialog(
                    'Activation Error.\nContact 3DtoAll Support using email or website contact form', c4d.GEMB_OK)

        if serialError == False:
            si = c4d.GeGetSerialInfo(c4d.SERIALINFO_MULTILICENSE)
            siNr = ''
            if len(si['nr']) > 0:
                # Multi-license, do something
                siNr = si['nr']
            else:
                si = c4d.GeGetSerialInfo(c4d.SERIALINFO_CINEMA4D)
                # Single-license, do something
                siNr = si['nr']

        c4dserial = siNr
        activcode = srl.replace(' ', '')

        specialkey = '912'
        activPart1 = activcode[3:5]
        activPart2 = activcode[7:9]
        serialPart1 = c4dserial[2:4]
        serialPart2 = c4dserial[6:8]

        if specialkey in activcode and activPart1 == serialPart1 and activPart2 == serialPart2:
            print('Activated')
            return True
        else:
            print("Invalid Activation Code")
            return False

        # -------------------------------------------------

        # si = self.GetAC()
        # siNr = si[-5:]

        # self._serList = [
        #         "2cc87350c0f0aae58bc33b04598d4",
        #         "3ed0b1fe4d9ec6a3b41a77b177a6d",
        #         "45546dfb44141872e66d647986caa",
        #         "2f306c3548dcbeb6081388114a273",
        #         "6be2e3440a2a7dce1be600763e39f",
        #         "1b3d37e95d83730d873f5eb6802ed",
        #         "548a9d63762c82e5acb8ff1124b2e",
        #         "199bd44d3a4a8500d54a4600673ad",
        #         "cb402f0b3e7257a2333f2048a53bf",
        #         "92fa866910987894fa71396291600",
        #         "40333deb6e8ef12147294461f2e45",
        #         "d8fde7d7cb730a3c2959910b9f85a",
        #         "6be2e3440a2a7dce1be600763e39f",
        #                 ]

        # digAuth = hashlib.sha224(siNr+"891df377116ee3bb6dae89d51d7a432729d6ca2e2c50d967af906fbd").hexdigest()
        # digSer = hashlib.sha224(digAuth+"c1a3ccbc85a37d4c01e89f24245176e75cd0b5efc8d6e2d3219f84e5").hexdigest()

        # hcValid = False
        # for hc in self._serList:
        #     if hc==srl:
        #         hcValid = True
        # if hcValid:
        #     return True
        # elif digSer==srl:
        #     return True
        # else:
        #     return False

    def GetAC(self):
        serialError = False
        siNr = ''
        try:
            c4d.GeGetSerialInfo(c4d.SERIALINFO_MULTILICENSE)
        except:
            serialError = True

        if serialError == True:  # CINEMA R21 or UP <<<<<<<<<<<<
            try:
                data = json.loads(c4d.ExportLicenses())
                # c4dversion = float(data["version"])
                sysID = data["systemid"]
                siNr = sysID[0:11]
            except:
                siNr = '87201726154'

        if serialError == False:
            si = c4d.GeGetSerialInfo(c4d.SERIALINFO_MULTILICENSE)
            siNr = ''
            if len(si['nr']) > 0:
                # Multi-license, do something
                siNr = si['nr']
            else:
                si = c4d.GeGetSerialInfo(c4d.SERIALINFO_CINEMA4D)
                # Single-license, do something
                siNr = si['nr']

        daztoc4dCode = 'DZ2C4D' + siNr[2:10]
        return daztoc4dCode

    def getPluginDataAndCheck(self):

        data = plugins.GetWorldPluginData(PLUGIN_ID)
        dataString = ''

        if data:
            dataString = data.GetString(101)

        checkResult = False
        if self.VerSC(dataString):
            # gui.MessageDialog("DazToC4D: Plugin Authorization successful!")
            checkResult = True
        else:
            # gui.MessageDialog("Invalid Serial")
            checkResult = False

        return checkResult

    def checkSrlDAZ(self, srl):
        # D2C4DFk7HuJG19UJLyoZ
        mustHave = [
            'F', 'k', '7', 'H', 'u', 'J', 'G',
            '1', '9', 'U', 'J', 'L', 'y', 'o', 'Z',
            'D2C4D'
        ]
        allFound = True
        for x in mustHave:
            if x not in srl:
                allFound = False

        return allFound

    def getPluginDataAndCheckDAZ(self):

        data = plugins.GetWorldPluginData(PLUGIN_ID)
        checkResult = False
        if data:
            dataString = data.GetString(101)
            if self.checkSrlDAZ(dataString) == True:
                checkResult = True
            else:
                checkResult = False

        return checkResult

    def VersionCheck_C4D(self, maxVerAllowed):
        c4dVersionNum = int(str(c4d.GetC4DVersion())[0:2])
        print(c4dVersionNum)
        allowed = True
        if c4dVersionNum > maxVerAllowed:
            gui.MessageDialog(
                "This version of DazToC4D plugin \ndoes not officially support this version of C4D.\n\nCheck 3DtoAll.com for updates")
            allowed = False
        return allowed
