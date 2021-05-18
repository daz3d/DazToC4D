import c4d
import os
import sys
from c4d import documents, gui

from .Utilities import dazToC4Dutils, Utils
from .DazToC4DClasses import DazToC4D
from . import DtuLoader
from . import Materials
from . import Utilities
from . import Morphs
from .DtC4DPosing import Poses
from .DtC4DDialogs import guiASKtoSave
from .Definitions import EXPORT_DIR

dazReduceSimilar = True


class CustomImports:
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

    def auto_import_genesis(self):
        import_list = self.get_genesis_list()
        for imported_dir in import_list:
            dtu = DtuLoader.DtuLoader(imported_dir)
            fbx_path = dtu.get_fbx_path()
            self.genesis_import(fbx_path, dtu)

    def auto_import_prop(self):
        import_list = self.get_prop_list()
        for imported_dir in import_list:
            dtu = DtuLoader.DtuLoader(imported_dir)
            fbx_path = dtu.get_fbx_path()
            self.prop_import(fbx_path, dtu)

    def genesis_import(self, filePath, dtu):
        mat = Materials.Materials()
        util = Utils()
        morph = Morphs.Morphs()
        var = Utilities.Variables()
        if os.path.exists(filePath) == False:
            gui.MessageDialog(
                "Nothing to import.\nYou have to export from DAZ Studio first",
                c4d.GEMB_OK,
            )
            return 0
        print("Import FBX from : {0}".format(os.path.dirname(filePath)))
        self.import_daz_fbx(filePath)
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        c4d.CallCommand(12113, 12113)  # Deselect All

        screen = c4d.gui.GeGetScreenDimensions(0, 0, True)

        c4d.EventAdd()
        util.update_viewport()
        c4d.CallCommand(300001026, 300001026)  # Deselect All
        c4d.CallCommand(12168, 12168)  # Remove Unused Materials
        c4d.EventAdd()

        var.store_asset_name(dtu)
        if var.prepare_variables():
            print("Import Failed")
            return
        print("Import Done")

        print("Starting Material Updates")

        mat.eyeLashAndOtherFixes()
        c4d.EventAdd()
        mat.addLipsMaterial()  # Add Lips Material

        c4d.EventAdd()
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        c4d.EventAdd()
        c4d.CallCommand(300001026, 300001026)  # Deselect All
        c4d.CallCommand(12168, 12168)  # Remove Unused Materials

        mat.stdMatExtrafixes()
        mat.specificFiguresFixes()
        mat.fixMaterials()

        print("Material Conversion Done")

        print("Starting Morph Updates")

        morph.store_morph_links(dtu)
        morph.rename_morphs(var.skeleton)
        morph.connect_morphs_to_parents(var.body, var.children)

        print("Morph Corrections Done")

        isPosed = Poses().checkIfPosed()
        if isPosed == False:
            Poses().preAutoIK()  # Only if T pose detected...

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

    def prop_import(self, file_path, dtu):
        if os.path.exists(filePath) == False:
            gui.MessageDialog(
                "Nothing to import.\nYou have to export from DAZ Studio first",
                c4d.GEMB_OK,
            )
            return 0
        print("Import FBX from : {0}".format(os.path.dirname(filePath)))
        self.import_daz_fbx(filePath)
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        c4d.CallCommand(12113, 12113)  # Deselect All

        screen = c4d.gui.GeGetScreenDimensions(0, 0, True)

        c4d.EventAdd()
        util.update_viewport()
        c4d.CallCommand(300001026, 300001026)  # Deselect All
        c4d.CallCommand(12168, 12168)  # Remove Unused Materials
        c4d.EventAdd()
        print("Import Done")

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
        """
        """
        flags = (
            c4d.SCENEFILTER_OBJECTS
            | c4d.SCENEFILTER_MATERIALS
            | c4d.SCENEFILTER_MERGESCENE
        )

        file = c4d.documents.LoadDocument(
            file_path,
            flags,
        )
        c4d.documents.InsertBaseDocument(file)

    def get_genesis_list(self):
        """
        Returns the Absolute Paths of the Exports from Daz for Figures
        """
        import_list = []
        for i in os.listdir(os.path.join(EXPORT_DIR, "FIG")):
            import_list.append(os.path.join(EXPORT_DIR, "FIG", i))
        return import_list
    
    def get_prop_list(self):
        """
        Returns the Absolute Paths of the Exports from Daz for Environments and Props
        """
        import_list = []
        for i in os.listdir(os.path.join(EXPORT_DIR, "ENV")):
            import_list.append(os.path.join(EXPORT_DIR, "ENV", i))
        return import_list
