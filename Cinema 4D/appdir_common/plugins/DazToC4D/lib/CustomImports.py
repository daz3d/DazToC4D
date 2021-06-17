import c4d
import os
import sys
from c4d import documents, gui

from .CustomCmd import Cinema4DCommands as dzc4d
from . import DtuLoader
from . import StandardMaterials
from . import Utilities
from . import Morphs
from . import DazRig
from . import Animations
from .DtC4DWeights import Weights
from .DtC4DPosing import Poses
from .DtC4DDialogs import guiASKtoSave
from .Definitions import EXPORT_DIR

dazReduceSimilar = True


class CustomImports:
    """
    Import Logic for Importing in the DTU File (JSON)
    """

    # Hidden
    def manual_import_genesis(self, path):
        """
        Manually Imports Figure of the Given Path
        """
        dtu = DtuLoader.DtuLoader(path)
        fbx_path = dtu.get_fbx_path()
        self.genesis_import(fbx_path, dtu)

    def manual_import_prop(self, path):
        """
        Manually Import Prop/Environment of the Given Path
        """
        dtu = DtuLoader.DtuLoader(path)
        fbx_path = dtu.get_fbx_path()
        self.prop_import(fbx_path, dtu)

    def auto_import_genesis(self, sss_value, normal_value, bump_value):
        import_list = self.get_genesis_list()
        current_dir = os.getcwd()
        os.chdir(EXPORT_DIR)
        if import_list:
            for imported_dir in import_list:
                dtu = DtuLoader.DtuLoader(imported_dir)
                fbx_path = dtu.get_fbx_path()
                self.genesis_import(fbx_path, dtu, sss_value, normal_value, bump_value)

        os.chdir(current_dir)

    def auto_import_prop(self, sss_value, normal_value, bump_value):
        import_list = self.get_prop_list()
        current_dir = os.getcwd()
        os.chdir(EXPORT_DIR)
        if import_list:
            for imported_dir in import_list:
                dtu = DtuLoader.DtuLoader(imported_dir)
                fbx_path = dtu.get_fbx_path()
                self.prop_import(fbx_path, dtu, sss_value, normal_value, bump_value)
        os.chdir(current_dir)

    def genesis_import(self, file_path, dtu, sss_value, normal_value, bump_value):
        mat = StandardMaterials.StdMaterials()
        morph = Morphs.Morphs()
        var = Utilities.Variables()
        jnt_fixes = DazRig.JointFixes()
        wgt = Weights()
        anim = Animations.Animations()
        pose = Poses()

        if os.path.exists(file_path) == False:
            gui.MessageDialog(
                "Nothing to import.\nYou have to export from DAZ Studio first",
                c4d.GEMB_OK,
            )
            return 0
        print("Import FBX from : {0}".format(os.path.dirname(file_path)))
        c4d.EventAdd()
        self.import_daz_fbx(file_path)
        c4d.EventAdd()
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        dzc4d.deselect_all()  # Deselect All

        screen = c4d.gui.GeGetScreenDimensions(0, 0, True)

        c4d.EventAdd()
        dzc4d.update_viewport()
        c4d.CallCommand(300001026, 300001026)  # Deselect All
        dzc4d.del_unused_mats()
        c4d.EventAdd()

        var.store_dtu(dtu)
        if var.prepare_variables():
            gui.MessageDialog(
                "Import Failed.\nYou can check the console for more info (Shift + F10)",
                c4d.GEMB_OK,
            )
            print("Import Failed")
            return
        print("Import Done")

        print("Starting Material Updates")

        c4d.EventAdd()
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        c4d.EventAdd()
        c4d.CallCommand(300001026, 300001026)  # Deselect All
        dzc4d.del_unused_mats()
        mat.store_materials(dtu)
        mat.store_sliders(sss_value, normal_value, bump_value)
        mat.update_materials()

        print("Material Conversion Done")
        c4d.EventAdd()

        wgt.store_subdivision(dtu)
        if wgt.check_level():
            auto_weight = c4d.gui.QuestionDialog(
                "Subdivisions have been detected\nthis is currently not fully supported.\nWould you like to autoweight the mesh?"
            )
            if auto_weight:
                wgt.auto_calculate_weights(var.body)

        pose.store_pose(dtu)
        is_posed = pose.checkIfPosed()
        is_anim = anim.check_animation_exists(var.c_joints)
        clear_pose = False
        if is_posed:
            clear_pose = gui.QuestionDialog(
                "Importing Posed Figure is currently not fully supported\nWould you like to try to fix bone orientation?",
            )
            if clear_pose:
                pose.clear_pose(var.c_joints)

        if is_anim == False or clear_pose:
            jnt_fixes.store_joint_orientations(dtu)
            jnt_fixes.fix_joints(var.c_skin_data, var.c_joints, var.c_meshes)
            c4d.EventAdd()
            dzc4d.deselect_all()
            if is_posed:
                pose.restore_pose(var.c_joints)
            make_tpose = gui.QuestionDialog(
                "Would you like to Convert\nthe Base Pose to a T-Pose?",
            )
            if make_tpose:
                pose.preAutoIK()
                c4d.EventAdd()

        else:
            gui.MessageDialog(
                "Animation or a Pose was Detected\nJoint Orientation has not been fixed",
                type=c4d.GEMB_ICONEXCLAMATION,
            )
        c4d.EventAdd()

        if var.body.GetTag(c4d.Tposemorph):
            print("Starting Morph Updates")
            morph.store_morph_links(dtu)
            morph.store_variables(
                var.body, var.c_meshes, var.c_joints, var.skeleton, var.c_poses
            )
            morph.morphs_to_delta()
            morph.delete_morphs(var.c_meshes)
            morph.connect_morphs_to_parents(var.body, var.c_meshes)
            morph.add_drivers()
            morph.rename_morphs(var.c_meshes)
            print("Morph Corrections Done")
            c4d.EventAdd()

        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        c4d.EventAdd()

        self.dialog = guiASKtoSave()
        self.dialog.Open(
            dlgtype=c4d.DLG_TYPE_MODAL,
            xpos=screen["sx2"] // 2 - 210,
            ypos=screen["sy2"] // 2 - 100,
            defaultw=200,
            defaulth=150,
        )

    def prop_import(self, file_path, dtu, sss_value, normal_value, bump_value):

        mat = StandardMaterials.StdMaterials()
        if os.path.exists(file_path) == False:
            gui.MessageDialog(
                "Nothing to import.\nYou have to export from DAZ Studio first",
                c4d.GEMB_OK,
            )
            return 0
        print("Import FBX from : {0}".format(os.path.dirname(file_path)))
        self.import_daz_fbx(file_path)
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        dzc4d.deselect_all()  # Deselect All

        screen = c4d.gui.GeGetScreenDimensions(0, 0, True)

        c4d.EventAdd()
        dzc4d.update_viewport()
        c4d.CallCommand(300001026, 300001026)  # Deselect All
        dzc4d.del_unused_mats()
        c4d.EventAdd()
        print("Import Done")

        print("Starting Material Updates")
        c4d.EventAdd()
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        c4d.EventAdd()
        c4d.CallCommand(300001026, 300001026)  # Deselect All
        dzc4d.del_unused_mats()
        mat.store_materials(dtu)
        mat.store_sliders(sss_value, normal_value, bump_value)
        mat.update_materials()

        print("Material Conversion Done")
        c4d.EventAdd()

        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        c4d.EventAdd()

        self.dialog = guiASKtoSave()
        self.dialog.Open(
            dlgtype=c4d.DLG_TYPE_MODAL,
            xpos=screen["sx2"] // 2 - 210,
            ypos=screen["sy2"] // 2 - 100,
            defaultw=200,
            defaulth=150,
        )

    def import_daz_fbx(self, file_path):
        """ """
        flags = (
            c4d.SCENEFILTER_OBJECTS
            | c4d.SCENEFILTER_MATERIALS
            | c4d.SCENEFILTER_MERGESCENE
        )

        file = c4d.documents.LoadDocument(
            str(file_path),
            flags,
        )
        c4d.documents.InsertBaseDocument(file)

    def get_genesis_list(self):
        """
        Returns the Absolute Paths of the Exports from Daz for Figures
        """
        import_list = []
        if os.path.exists(os.path.join(EXPORT_DIR, "FIG")):
            for i in os.listdir(os.path.join(EXPORT_DIR, "FIG")):
                import_list.append(os.path.join(EXPORT_DIR, "FIG", i))
            return import_list
        else:
            gui.MessageDialog(
                "Could Not find Exported File from Daz Studio",
                type=c4d.GEMB_ICONEXCLAMATION,
            )

    def get_prop_list(self):
        """
        Returns the Absolute Paths of the Exports from Daz for Environments and Props
        """
        import_list = []
        if os.path.exists(os.path.join(EXPORT_DIR, "ENV")):
            for i in os.listdir(os.path.join(EXPORT_DIR, "ENV")):
                import_list.append(os.path.join(EXPORT_DIR, "ENV", i))
            return import_list
        else:
            gui.MessageDialog(
                "Could Not find Exported File from Daz Studio",
                type=c4d.GEMB_ICONEXCLAMATION,
            )
