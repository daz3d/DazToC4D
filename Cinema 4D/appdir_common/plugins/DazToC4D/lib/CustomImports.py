import c4d
import os
import sys
from c4d import documents, gui

from .Utilities import dazToC4Dutils, Utils
from .DazToC4DClasses import DazToC4D
from . import DtuLoader
from . import Materials
from .DtC4DPosing import Poses
from .Morphs import Morphs, connectEyeLashesMorphXpresso
from .DtC4DDialogs import guiASKtoSave
from .Definitions import EXPORT_DIR

dazReduceSimilar = True

class CustomImports:
    


    def get_genesis_list(self):
        """
        Returns the Absolute Paths of the Exports from Daz for Figures
        """
        import_list = []
        for i in os.listdir(os.path.join(EXPORT_DIR, "FIG")):
            import_list.append(os.path.join(EXPORT_DIR, "FIG", i))
        return import_list


    # Hidden
    def manual_import_genesis(self, path):
        """
        Manually Imports Figure of the Given Path
        """
        dtu = DtuLoader.DtuLoader(path)
        mat = Materials.Materials()
        fbx_path = dtu.get_fbx_path()
        self.genesis_import(fbx_path, dtu, mat)


    def auto_import_genesis(self):
        doc = documents.GetActiveDocument()
        import_list = self.get_genesis_list()
        for imported_dir in import_list:
            dtu = DtuLoader.DtuLoader(imported_dir)
            fbx_path = dtu.get_fbx_path()
            self.genesis_import(fbx_path, dtu)


    def genesis_import(self, filePath, dtu):
        mat = Materials.Materials()
        util = Utils()
        if os.path.exists(filePath) == False:
            gui.MessageDialog(
                'Nothing to import.\nYou have to export from DAZ Studio first',
                c4d.GEMB_OK)
            return 0
        print("Import FBX from : {0}".format(os.path.dirname(filePath)))
        self.import_daz_fbx(filePath)
        dazToC4Dutils().readExtraMapsFromFile() #Extra Maps from File...

        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)
        c4d.CallCommand(300001026, 300001026)  # Deselect All
        c4d.CallCommand(12168, 12168)  # Remove Unused Materials
        c4d.CallCommand(12113, 12113)  # Deselect All

        screen = c4d.gui.GeGetScreenDimensions(0, 0, True)

        c4d.EventAdd()
        util.update_viewport()       

        c4d.CallCommand(300001026, 300001026)  # Deselect All
        c4d.CallCommand(12168, 12168)  # Remove Unused Materials

        mat.eyeLashAndOtherFixes()
        c4d.EventAdd()
        c4d.EventAdd()

        print('Import Done')
        if dazReduceSimilar == True:
            c4d.CallCommand(12211, 12211)  # Remove Duplicate Materials
            mat.reduceMatFix()
            mat.disableDisplace()

        dazToC4Dutils().readExtraMapsFromFile() #Extra Maps from File...

        mat.addLipsMaterial() # Add Lips Material # Needs to have iterators removed to be pull
        dazObj = dazToC4Dutils().getDazMesh() 

        Morphs().morphsFixRemoveAndRename()
        xpressoTag = connectEyeLashesMorphXpresso()

        c4d.EventAdd()
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)
        c4d.EventAdd()
        c4d.CallCommand(300001026, 300001026)  # Deselect All
        c4d.CallCommand(12168, 12168)  # Remove Unused Materials

        mat.stdMatExtrafixes()
        mat.specificFiguresFixes()
        mat.fixMaterials()

        isPosed = Poses().checkIfPosed()
        if isPosed == False:
            Poses().preAutoIK() #Only if T pose detected...


        c4d.EventAdd()
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        c4d.EventAdd()

        #self.buttonsChangeState(True)

        self.dialog = guiASKtoSave()
        self.dialog.Open(dlgtype=c4d.DLG_TYPE_MODAL, xpos=screen['sx2']//2-210, ypos=screen['sy2']//2-100, defaultw=200, defaulth=150)

    
    def import_daz_fbx(self, filePath):
        file = c4d.documents.LoadDocument(filePath, c4d.SCENEFILTER_OBJECTS | c4d.SCENEFILTER_MATERIALS | c4d.SCENEFILTER_MERGESCENE)
        c4d.documents.InsertBaseDocument(file)