import os
import webbrowser

import c4d
from c4d import gui

from .Materials import Materials, convertMaterials
from .RedshfitMaterials import RedshiftMaterials
from .CustomImports import CustomImports
from .DtC4DDialogs import EXTRADialog
from .DtC4DPosing import Poses
from .Definitions import RES_DIR, EXPORT_DIR
from .Morphs import Morphs
from .DazToC4DClasses import DazToC4D
from .CustomCmd import Cinema4DCommands as dzc4d
from .Utilities import Variables


class GuiImportDaz(gui.GeDialog):
    daz_to_c4d_bridge_title = None

    dialog = None
    import_vars = []

    BUTTON_CONFIG = 923123
    BUTTON_MORPHS = 923113
    BUTTON_AUTO_IMPORT_FIG = 923124
    BUTTON_AUTO_IMPORT_PROP = 923131
    BUTTON_CONVERT_MATERIALS = 923126
    BUTTON_CONFIG = 923127
    BUTTON_HELP = 923129
    BUTTON_AUTO_IK = 923130
    SLIDER_BUMP_MULTIPLIER = 17550
    SLIDER_NORMAL_MULTIPLIER = 17551
    SLIDER_SSS_MULTIPLIER = 17552
    MY_BITMAP_BUTTON = 9353535

    res_dir = RES_DIR  # Adds the res folder to the path

    # Set Images for UI
    img_d2c4dLogo = os.path.join(res_dir, "d2c4d_logo.png")
    img_loading = os.path.join(res_dir, "d2c4d_loading.png")
    img_d2c4dHelp = os.path.join(res_dir, "d2c4d_help.png")
    img_btnAutoImport_FIG = os.path.join(res_dir, "btnGenesisImport.png")
    img_btnAutoImportOff_FIG = os.path.join(res_dir, "btnGenesisImport_off.png")
    img_btnAutoImport_PROP = os.path.join(res_dir, "btnPropImport.png")
    img_btnAutoImportOff_PROP = os.path.join(res_dir, "btnPropImport_off.png")
    img_btnConvertMaterials = os.path.join(res_dir, "btnConvertMaterials.png")
    img_btnConvertMaterialsOff = os.path.join(res_dir, "btnConvertMaterials0.png")
    img_btnAutoIK = os.path.join(res_dir, "btnAutoIK.png")
    img_btnAutoIKOff = os.path.join(res_dir, "btnAutoIK0.png")
    img_btnConfig = os.path.join(res_dir, "btnConfig.png")

    def __init__(self):
        try:
            self.AddGadget(c4d.DIALOG_PIN, 0)
            self.config_dialog = EXTRADialog()
        except:
            pass

    def buttonsChangeState(self, btnState):
        """
        Changes the Images when Given a Boolean
        Used to Allow the User to know when the command is still loading
        """
        c4d.StatusClear()
        c4d.EventAdd(c4d.EVENT_FORCEREDRAW)
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        c4d.DrawViews(c4d.EVMSG_CHANGEDSCRIPTMODE)
        c4d.EventAdd(c4d.EVENT_ANIMATE)
        c4d.StatusClear()
        if btnState == False:
            self.main_logo.SetImage(self.img_loading, False)
            self.auto_import_fig_but.SetImage(self.img_btnAutoImportOff_FIG, True)
            self.auto_import_prop_but.SetImage(self.img_btnAutoImportOff_PROP, True)
            self.convert_mat_but.SetImage(self.img_btnConvertMaterialsOff, True)
            self.auto_ik_but.SetImage(self.img_btnAutoIKOff, True)

        if btnState == True:
            self.main_logo.SetImage(self.img_d2c4dLogo, True)
            self.auto_import_fig_but.SetImage(self.img_btnAutoImport_FIG, True)
            self.auto_import_prop_but.SetImage(self.img_btnAutoImport_PROP, True)
            self.convert_mat_but.SetImage(self.img_btnConvertMaterials, True)
            self.auto_ik_but.SetImage(self.img_btnAutoIK, True)

        try:
            self.main_logo.LayoutChanged()
            self.main_logo.Redraw()
        except:
            print("DazToC4D: LayoutChanged skip...")
        c4d.StatusClear()
        c4d.EventAdd()
        c4d.EventAdd(c4d.EVENT_FORCEREDRAW)
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        c4d.DrawViews()
        c4d.EventAdd(c4d.EVENT_FORCEREDRAW)
        c4d.DrawViews(c4d.DRAWFLAGS_FORCEFULLREDRAW)
        bc = c4d.BaseContainer()
        c4d.gui.GetInputState(c4d.BFM_INPUT_MOUSE, c4d.BFM_INPUT_CHANNEL, bc)
        return True

    def buttonBC(self, tooltipText="", presetLook=""):
        """
        Preset Options
        """
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

    def CreateLayout(self):
        if self.daz_to_c4d_bridge_title is not None:
            self.SetTitle(self.daz_to_c4d_bridge_title)
        else:
            self.SetTitle("DazToC4D private beta build")
        self.AddSeparatorH(c4d.BFV_SCALEFIT)  # Separator H

        bc = c4d.BaseContainer()  # Create a new container to store the button image
        bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_ROUND)
        self.main_logo = self.AddCustomGui(
            self.MY_BITMAP_BUTTON,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Logo",
            c4d.BFH_CENTER,
            0,
            0,
            bc,
        )
        self.main_logo.SetImage(self.img_d2c4dLogo, False)

        # Import
        self.GroupBegin(10000, c4d.BFH_CENTER, 1)
        self.GroupBorderNoTitle(c4d.BORDER_OUT)
        self.GroupBorderSpace(0, 0, 0, 0)

        self.GroupBegin(10000, c4d.BFH_SCALEFIT, 5)  # BEGIN ----------------------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(12, 5, 10, 5)

        self.LogoButton6 = self.AddCustomGui(
            self.BUTTON_CONFIG,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("", "Preset0"),
        )
        self.LogoButton6.SetImage(self.img_btnConfig, True)

        self.AddSeparatorV(0, c4d.BFV_SCALEFIT)  # Separator V

        self.GroupBegin(10000, c4d.BFH_CENTER, 1)
        self.GroupBorderSpace(0, 0, 0, 0)

        self.auto_import_fig_but = self.AddCustomGui(
            self.BUTTON_AUTO_IMPORT_FIG,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("", "Preset0"),
        )
        self.auto_import_fig_but.SetImage(self.img_btnAutoImport_FIG, True)

        self.auto_import_prop_but = self.AddCustomGui(
            self.BUTTON_AUTO_IMPORT_PROP,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("", "Preset0"),
        )
        self.auto_import_prop_but.SetImage(self.img_btnAutoImport_PROP, True)

        self.GroupEnd()  # END ///////////////////////////////////////////////
        self.AddSeparatorV(0, c4d.BFV_SCALEFIT)  # Separator V

        self.auto_ik_but = self.AddCustomGui(
            self.BUTTON_AUTO_IK,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("", "Preset0"),
        )
        self.auto_ik_but.SetImage(
            self.img_btnAutoIK, True
        )  # Add the image to the button

        self.GroupEnd()  # END ///////////////////////////////////////////////
        self.GroupEnd()  # END ///////////////////////////////////////////////

        self.GroupEnd()  # END ///////////////////////////////////////////////

        self.AddSeparatorH(c4d.BFV_SCALEFIT)  # Separator H

        self.GroupBegin(
            10000, c4d.BFH_SCALEFIT, 1, title="Materials:"
        )  # MATERIALS BEGIN -----------------------------------------------------
        self.GroupBorder(c4d.BORDER_OUT)
        self.GroupBorderSpace(10, 0, 10, 10)

        self.GroupBegin(10000, c4d.BFH_SCALEFIT, 3)  # BEGIN ----------------------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(20, 5, 20, 5)

        self.convert_mat_but = self.AddCustomGui(
            self.BUTTON_CONVERT_MATERIALS,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("", "Preset0"),
        )
        self.convert_mat_but.SetImage(self.img_btnConvertMaterials, True)
        self.AddSeparatorV(0, c4d.BFV_SCALEFIT)  # Separator V
        self.AddComboBox(2001, c4d.BFH_SCALEFIT, 100, 15, False)
        self.AddChild(2001, 0, " - Select -")
        self.AddChild(2001, 1, "V-Ray")
        self.AddChild(2001, 2, "Redshift")
        self.AddChild(2001, 3, "Octane")

        self.GroupEnd()  # END ///////////////////////////////////////////////

        self.GroupBegin(
            10000, c4d.BFH_SCALEFIT, 2, title="Global Material Multipliers:"
        )  # BEGIN ----------------------
        self.GroupBorder(c4d.BORDER_THIN_OUT)
        self.GroupBorderSpace(20, 5, 20, 5)

        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0, name="Bump Multiplier:")
        self.AddEditSlider(
            self.SLIDER_BUMP_MULTIPLIER, c4d.BFH_SCALEFIT, initw=40, inith=0
        )
        self.SetInt32(self.SLIDER_BUMP_MULTIPLIER, value=10, min=1, max=100)

        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0, name="Normal Multiplier:")
        self.AddEditSlider(
            self.SLIDER_NORMAL_MULTIPLIER, c4d.BFH_SCALEFIT, initw=40, inith=0
        )
        self.SetInt32(self.SLIDER_NORMAL_MULTIPLIER, value=50, min=1, max=100)

        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0, name="Subsurface Multiplier:")
        self.AddEditSlider(
            self.SLIDER_SSS_MULTIPLIER, c4d.BFH_SCALEFIT, initw=40, inith=0
        )
        self.SetInt32(self.SLIDER_SSS_MULTIPLIER, value=5, min=1, max=100)

        self.GroupEnd()  # END ///////////////////////////////////////////////
        self.GroupEnd()  # MATERIALS END ///////////////////////////////////////////////

        self.AddSeparatorH(c4d.BFV_SCALEFIT)  # Separator H

        self.GroupBegin(
            10000, c4d.BFH_CENTER, 2, title="Global Skin Parameters:"
        )  # BEGIN ----------------------
        self.GroupBegin(10001, c4d.BFH_CENTER, 2, title="Redshift Settings: ")
        self.AddStaticText(
            99, c4d.BFH_SCALEFIT, 0, 0, name="Copyright(c) 2020. All Rights Reserved."
        )

        self.LogoButtonHelp = self.AddCustomGui(
            self.BUTTON_HELP,
            c4d.CUSTOMGUI_BITMAPBUTTON,
            "Bitmap Button",
            c4d.BFH_CENTER,
            0,
            0,
            self.buttonBC("Help", "Preset0"),
        )
        self.LogoButtonHelp.SetImage(
            self.img_d2c4dHelp, True
        )  # Add the image to the button

        self.GroupEnd()
        self.AddSeparatorH(c4d.BFV_SCALEFIT)  # Separator H

        return True

    def Command(self, id, msg):
        if id == self.BUTTON_AUTO_IMPORT_FIG:
            print("DEBUG: Auto Import Fig button pressed...")
            self.buttonsChangeState(False)
            sss_value = self.GetFloat(self.SLIDER_SSS_MULTIPLIER)
            normal_value = self.GetFloat(self.SLIDER_NORMAL_MULTIPLIER)
            bump_value = self.GetFloat(self.SLIDER_BUMP_MULTIPLIER)
            CustomImports().auto_import_genesis(sss_value, normal_value, bump_value)
            self.buttonsChangeState(True)

        if id == self.BUTTON_AUTO_IMPORT_PROP:
            print("DEBUG: Auto Import Prop button pressed...")
            self.buttonsChangeState(False)
            sss_value = self.GetFloat(self.SLIDER_SSS_MULTIPLIER)
            normal_value = self.GetFloat(self.SLIDER_NORMAL_MULTIPLIER)
            bump_value = self.GetFloat(self.SLIDER_BUMP_MULTIPLIER)
            CustomImports().auto_import_prop(sss_value, normal_value, bump_value)
            self.buttonsChangeState(True)

        if id == self.BUTTON_AUTO_IK:
            self.buttonsChangeState(False)
            c4d.EventAdd()
            if self.config_dialog.IsOpen():
                self.config_dialog.Close()
            var = Variables()
            var.restore_variables()
            if not var.skeleton:
                error = gui.MessageDialog(
                    "Error has occured\n please re-import Character",
                    c4d.GEMB_RETRYCANCEL,
                )
                if error == c4d.GEMB_R_RETRY:
                    CustomImports().auto_import_genesis()

            if "Genesis" in var.skeleton.GetName():
                if Poses().checkIfPosedResetPose():  # Removes Pose if Needed
                    daz_geo = dzc4d.add_obj_to_new_group(var.c_meshes)
                    DazToC4D().autoIK(var)
                    dzc4d.add_sub_div(daz_geo)
                    DazToC4D().lockAllModels()
            else:
                gui.MessageDialog(
                    "No Character found, Auto-Import a Character and try again.",
                    c4d.GEMB_OK,
                )
            self.buttonsChangeState(True)

        if id == self.BUTTON_CONFIG:
            if self.config_dialog.IsOpen():
                self.config_dialog.Close()
            self.config_dialog.Open(
                dlgtype=c4d.DLG_TYPE_ASYNC, xpos=-1, ypos=-1, defaultw=200, defaulth=150
            )

        if id == self.BUTTON_CONVERT_MATERIALS:
            # CONVERT MATERIAL
            gui.MessageDialog(
                "Material Rework is in Progress\nYour results may vary...",
                type=c4d.GEMB_ICONEXCLAMATION,
            )
            doc = c4d.documents.GetActiveDocument()
            comboRender = self.GetInt32(2001)
            redshiftBumpType = self.GetInt32(2002)
            mat = Materials()
            sss_value = self.GetFloat(self.SLIDER_SSS_MULTIPLIER)
            normal_value = self.GetFloat(self.SLIDER_NORMAL_MULTIPLIER)
            bump_value = self.GetFloat(self.SLIDER_BUMP_MULTIPLIER)
            if comboRender == 0:
                gui.MessageDialog("Please select renderer from the list")

            else:
                if Materials().checkStdMats() == True:
                    return
                else:
                    answer = gui.MessageDialog(
                        "::: WARNING :::\n\nNo Undo for this.\nSave your scene first, in case you want to revert changes.\n\nProceed and Convert Materials now?",
                        c4d.GEMB_YESNO,
                    )
                    if answer == c4d.GEMB_R_YES:
                        current_dir = os.getcwd()
                        os.chdir(EXPORT_DIR)
                        if comboRender == 1:
                            convertMaterials().convertTo("Vray")
                            c4d.CallCommand(1026375)  # Reload Python Plugins

                        if comboRender == 2:
                            var = Variables()
                            var.restore_variables()
                            rs_mat = RedshiftMaterials()
                            if rs_mat.check_for_redshift():
                                rs_mat.store_materials(var.dtu)
                                rs_mat.store_sliders(
                                    sss_value, normal_value, bump_value
                                )
                                rs_mat.execute()
                                c4d.CallCommand(100004766, 100004766)  # Select All
                                c4d.CallCommand(100004767, 100004767)  # Deselect All
                            else:
                                gui.MessageDialog("Redshift is Not Installed...")

                        if comboRender == 3:
                            mat.convertToOctane()
                            c4d.CallCommand(100004766, 100004766)  # Select All
                            c4d.CallCommand(100004767, 100004767)  # Deselect All
                        os.chdir(current_dir)

        if id == self.BUTTON_HELP:
            new = 2  # open in a new tab, if possible
            url = "http://www.daz3d.com"
            webbrowser.open(url, new=new)

        return True
