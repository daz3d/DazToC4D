import c4d
import os
import sys
from c4d import documents, gui

folder = os.path.dirname( __file__ )
if folder not in sys.path: 
    sys.path.insert( 0, folder )

from Utilities import dazToC4Dutils
from DazToC4DClasses import DazToC4D
import DtuLoader
import Materials
from DtC4DPosing import Poses
from Morphs import Morphs, connectEyeLashesMorphXpresso
from DtC4DDialogs import guiASKtoSave

dazReduceSimilar = True

class CustomImports:
    home_dir = os.path.expanduser("~")
    root_dir = os.path.join(home_dir, "Documents", "DAZ 3D", "Bridges", "Daz To C4D")
    export_dir = os.path.join(root_dir, "Exports")


    def get_import_list(self, version):
        importList = []
        for export in os.listdir(os.path.join(self.export_dir, version)):
            if os.path.isdir(os.path.join(self.export_dir, version, export)):
                for fbx in os.listdir(os.path.join(self.export_dir, version, export)):
                    if fbx.endswith(".fbx"):
                        importList.append(os.path.join(self.export_dir, version, export, fbx))
        return importList

    
    def auto_import_genesis(self):
        dtu = DtuLoader.DtuLoader()
        mat = Materials.Materials()
        doc = documents.GetActiveDocument()
        import_list = self.get_import_list("FIG")
        for file_path in import_list:
            self.genesis_import(file_path, dtu, mat)

    def genesis_import(self, filePath, dtu, mat):
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
        c4d.CallCommand(12148)  # Frame Geometry
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)

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