from __future__ import division
import os, sys, hashlib, c4d
from c4d import gui, documents
from c4d import utils
from c4d import plugins
from random import randint
from shutil import copyfile
import webbrowser
import json

"""
Converted to Python 3 to deal with changes in Cinema 4D R23
Manual Changes to the code:
Removed  c4d.DRAWFLAGS_NO_REDUCTION as it was removed from the Python SDK
Changes for Division from / to // to achieve an integer instead of a float
Added Backwards Support for __next__ for Python 2 Versions
"""
try:
    import redshift
except:
    print('Redshift not found')

folder = os.path.dirname( __file__ )
if folder not in sys.path: 
    sys.path.insert( 0, folder )

import DtuLoader
import Materials
from Utilities import dazToC4Dutils

HOME_DIR = os.path.expanduser("~")
ROOT_DIR = os.path.join(HOME_DIR, "Documents", "DAZ 3D", "Bridges", "Daz To C4D")
EXPORT_DIR = os.path.join(ROOT_DIR, "Exports")

print(ROOT_DIR)


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
dazReduceSimilar = True

authDialogDazToC4D = None
guiDazToC4DLayerLockButton = None

guiDazToC4DExtraDialog = None


def applyDazIK():
        doc = documents.GetActiveDocument()

        dazToC4Dutils().ungroupDazGeo()

        meshName = dazToC4Dutils().getDazMesh().GetName()
        meshName = meshName.replace('.Shape', '')
        global dazName
        dazName = meshName + '_'

        dazToC4Dutils().guidesToDaz()  # Auto Generate Guides
        dazToC4Dutils().cleanJointsDaz()  # Some adjustments to Daz Rig...
        # Ikmax stuff...----------------------
        ikmGenerator().makeRig()
        suffix = "___R"
        objArm = doc.SearchObject(dazName + 'jCollar')
        objLeg = doc.SearchObject(dazName + 'jUpLeg')

        ikmGenerator().makeIKcontrols()
        ikmaxUtils().mirrorObjects(objArm, suffix)
        ikmaxUtils().mirrorObjects(objLeg, suffix)
        ikmGenerator().makeChildKeepPos(dazName + "Foot_Platform___R", dazName + "Foot_PlatformBase___R")
        ikmGenerator().makeChildKeepPos(dazName + "Foot_PlatformBase___R", dazName + "IKM_Controls")

        DazToC4D().dazEyesLookAtControls()

        # ------------------------------------

        dazToC4Dutils().cleanJointsDaz('Right')
        dazToC4Dutils().constraintJointsToDaz()
        dazToC4Dutils().constraintJointsToDaz('Right')
        if doc.SearchObject(dazName + 'ForearmTwist_ctrl'):
            dazToC4Dutils().twistBoneSetup() #TwistBone Setup
            obj = doc.SearchObject(dazName + "ForearmTwist_ctrl")
            obj[c4d.ID_BASEOBJECT_REL_ROTATION,c4d.VECTOR_X] = 0
            obj = doc.SearchObject(dazName + "ForearmTwist_ctrl___R")
            obj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0
            ikmGenerator().constraintObj("lForearmTwist", dazName + "ForearmTwist_ctrl")
            ikmGenerator().constraintObj("rForearmTwist", dazName + "ForearmTwist_ctrl___R")
            dazToC4Dutils().fixConstraints()
            dazToC4Dutils().zeroTwistRotationFix(dazName + "ForearmTwist_ctrl", "lForearmTwist")
            dazToC4Dutils().zeroTwistRotationFix(dazName + "ForearmTwist_ctrl___R", "rForearmTwist")

        ikmaxUtils().freezeChilds(dazName + "IKM_Controls")
        ikmaxUtils().freezeChilds(dazName + "jPelvis")

        dazToC4Dutils().addProtection()  # Foot controls lock position, allow rotations.
        ikmaxUtils().hideGuides(1)
        dazToC4Dutils().hideRig()
        c4d.CallCommand(12113, 12113)  # Deselect All
        guides = doc.SearchObject(dazName + '__IKM-Guides')
        if guides:
            guides.Remove() #REMOVE GUIDES
        c4d.EventAdd()



def _GetNextHierarchyObject(op):
    """Return the next object in hieararchy.
    """
    if op is None:
        return None
    down = op.GetDown()
    if down:
        return down
    next = op.GetNext()
    if next:
        return next
    prev = op.GetUp()
    while prev:
        next = prev.GetNext()
        if next:
            return next
        prev = prev.GetUp()
    return None


class convertMaterials:

    def _GetNextHierarchyObject(self, op):
        """Return the next object in hieararchy.
        """
        if op is None:
            return None
        down = op.GetDown()
        if down:
            return down
        next = op.GetNext()
        if next:
            return next
        prev = op.GetUp()
        while prev:
            next = prev.GetNext()
            if next:
                return next
            prev = prev.GetUp()
        return None

    def convertShader(self, sourceMat, mat):

        def makeVrayShader(slotName, bmpPath):
            # With Bitmap found:
            bmpShader = c4d.BaseShader(1026701)
            bmpShader[c4d.VRAY_SHADERS_LIST] = 10 # Set as Bitmap Shader
            bc = bmpShader.GetData()
            #bc[89981968] = 2 # Sets to sRGB but no - leave as default.
            bc.SetFilename(4999,bmpPath)
            bmpShader.SetData(bc)
            mat.InsertShader( bmpShader )
            if slotName == 'diffuse':
                mat[c4d.VRAYSTDMATERIAL_DIFFUSECOLOR_TEX] = bmpShader
            if slotName == 'mapRough':
                mat[c4d.VRAYSTDMATERIAL_REFLECTGLOSSINESS_TEX] = bmpShader
            if slotName == 'bump':
                mat[c4d.VRAYSTDMATERIAL_BUMP_BUMPMAP] = bmpShader
                try:
                    mat[c4d.VRAYSTDMATERIAL_BUMP_BUMPMAP_MULT] = 0.2
                except:
                    pass
            if slotName == 'mapAlpha':
                mat[c4d.VRAYSTDMATERIAL_OPACITY_TEX] = bmpShader
            if slotName == 'mapSpec':
                mat[c4d.VRAYSTDMATERIAL_REFLECTCOLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.VRAYSTDMATERIAL_REFLECTGLOSSINESS] = 0.7
                mat[c4d.VRAYSTDMATERIAL_REFLECTFRESNELIOR_LOCK] = False
                mat[c4d.VRAYSTDMATERIAL_REFLECTCOLOR_TEX] = bmpShader
                try:
                    mat[c4d.VRAYSTDMATERIAL_REFLECTCOLOR_TEX][107820085] = True #ALPHA_FROM_INTENSITY
                except:
                    pass


        bmpPath = r''

        #To all Octane mats... With or without Bitmap:
        if self.matType == 'Octane':          
            mat[c4d.OCT_MATERIAL_TYPE] = 2511  # Glossy
            mat[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = sourceMat[c4d.MATERIAL_COLOR_COLOR]
            mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.3
            if 'LENS' in mat.GetName():
                mat[c4d.OCT_MATERIAL_OPACITY_FLOAT] = 0.0
            if 'Moisture' in mat.GetName():
                mat[c4d.OCT_MATERIAL_TYPE] = 2513 # Specular
                mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.0
            if 'Cornea' in mat.GetName():
                mat[c4d.OCT_MATERIAL_TYPE] = 2513 # Specular
                mat[c4d.OCT_MATERIAL_INDEX] = 2.8
                mat[c4d.OCT_MATERIAL_OPACITY_FLOAT] = 0.2
                mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.0
            if 'Mouth' in mat.GetName():
                mat[c4d.OCT_MATERIAL_INDEX] = 4.8
                mat[c4d.OCT_MATERIAL_SPECULAR_COLOR] = c4d.Vector(0.4, 0.2, 0.1)
                mat[c4d.OCT_MATERIAL_ROUGHNESS_COLOR] = c4d.Vector(0.08, 0.06, 0.0)

        # Check if maps found...
        diffuseMap = None
        mapBump = None
        mapSpec = None
        mapAlpha = None

        # DIFFUSE ---------------------------
        try:
            diffuseMap = sourceMat[c4d.MATERIAL_COLOR_SHADER][c4d.BITMAPSHADER_FILENAME]
        except:
            diffuseMap = None
        # BUMP ---------------------------
        try:
            mapBump = sourceMat[c4d.MATERIAL_BUMP_SHADER][c4d.BITMAPSHADER_FILENAME]
        except:
            mapBump = None
        # ALPHA ---------------------------
        try:
            mapAlpha = sourceMat[c4d.MATERIAL_ALPHA_SHADER][c4d.BITMAPSHADER_FILENAME]
        except:
            mapAlpha = None
        # SPEC ---------------------------
        try:
            layer = sourceMat.GetReflectionLayerIndex(0)
            caca = sourceMat[layer.GetDataID() + c4d.REFLECTION_LAYER_TRANS_TEXTURE]
            if caca:
                if caca.GetType() == 5833:
                    mapSpec = caca[c4d.BITMAPSHADER_FILENAME]
        except:
            mapSpec = None
        # ----------------------

        bmpShader = None

        if self.matType == 'Std':
            bmpShader = c4d.BaseList2D(c4d.Xbitmap) # create a bitmap shader for the material
            bmpShader[c4d.BITMAPSHADER_FILENAME] = bmpPath
            mat.InsertShader( bmpShader )
            mat[dstSlotID]  = bmpShader
        elif self.matType == 'Vray':
            mat[c4d.VRAYSTDMATERIAL_DIFFUSECOLOR] = sourceMat[c4d.MATERIAL_COLOR_COLOR]
            mat[c4d.VRAYSTDMATERIAL_REFRACTCOLOR] = sourceMat[c4d.MATERIAL_TRANSPARENCY_COLOR]
            mat[c4d.VRAYSTDMATERIAL_REFRACTIOR] = sourceMat[c4d.MATERIAL_TRANSPARENCY_REFRACTION]

            extraMapGlossyRough = dazToC4Dutils().findTextInFile(sourceMat.GetName(), 'Glossy_Roughness_Map')

            # If Bitmap found:
            if diffuseMap != None:
                makeVrayShader('diffuse', diffuseMap)
            if mapBump != None:
                makeVrayShader('bump', mapBump)
            if mapSpec != None:
                makeVrayShader('mapSpec', mapSpec)
            if mapAlpha != None:
                makeVrayShader('mapAlpha', mapAlpha)
            if extraMapGlossyRough != None:
                makeVrayShader('mapRough', extraMapGlossyRough)

            #Extra adjust.. specular and stuff..
            matName = mat.GetName()
            if 'Cornea' in matName or 'Sclera' in matName or 'Pupil' in matName:
                mat[c4d.VRAYSTDMATERIAL_REFLECTCOLOR] = c4d.Vector(1,1,1)
                mat[c4d.VRAYSTDMATERIAL_REFLECTFRESNELIOR_LOCK] = False
                mat[c4d.VRAYSTDMATERIAL_REFLECTFRESNELIOR] = 1.6
            if 'Mouth' in matName or 'Teeth' in matName:
                mat[c4d.VRAYSTDMATERIAL_REFLECTCOLOR] = c4d.Vector(0.8, 0.8, 0.8)
                mat[c4d.VRAYSTDMATERIAL_REFLECTFRESNELIOR_LOCK] = False
                mat[c4d.VRAYSTDMATERIAL_REFLECTFRESNELIOR] = 1.6
           

        elif self.matType == 'Redshift':
            bmpShader = mat.CreateShader(dstSlotID, "TextureSampler")
            bmpShader[c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0, c4d.REDSHIFT_FILE_PATH] = bmpPath.encode('utf-8')
        elif self.matType == 'Octane':
            bmpShader = c4d.BaseList2D(1029508)

            if isinstance(bmpPath,str):
                bmpShader[c4d.IMAGETEXTURE_FILE] = bmpPath
                bmpShader[c4d.IMAGETEXTURE_MODE] = 0
                bmpShader[c4d.IMAGETEXTURE_GAMMA] = 2.2
                bmpShader[c4d.IMAGETEX_BORDER_MODE] = 0
                if slotName == 'diffuse':
                    mat[c4d.OCT_MATERIAL_DIFFUSE_LINK] = bmpShader
                    mat[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = sourceMat[c4d.MATERIAL_COLOR_COLOR]
                if slotName == 'alpha':
                    mat[c4d.OCT_MATERIAL_OPACITY_LINK] = bmpShader
                    mat[c4d.OCT_MATERIAL_OPACITY_LINK][c4d.IMAGETEXTURE_GAMMA] = 0.5
                    # mat[c4d.OCT_MATERIAL_OPACITY_LINK][c4d.IMAGETEXTURE_INVERT] = True
                if slotName == 'glossy':
                    mat[c4d.OCT_MATERIAL_ROUGHNESS_LINK] = bmpShader
                mat[c4d.OCT_MATERIAL_TYPE]=2511 #Glossy
                mat.InsertShader(bmpShader)
                mat.Message(c4d.MSG_UPDATE)

                c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)
                mat.Message( c4d.MSG_UPDATE )
                mat.Update( True, True )
                c4d.EventAdd()

        elif self.matType == 'Corona':
            bmpShader = c4d.BaseList2D(c4d.Xbitmap) # create a bitmap shader for the material
            bmpShader[1036473] = bmpPath
            mat.InsertShader( bmpShader )
            mat[dstSlotID]  = bmpShader

        return True

    def convertMat(self, sourceMat, matType='Std'):

        self.matType = matType

        print("----- Converting : " + sourceMat.GetName() + ' -----')

        matName = sourceMat.GetName()
        mat = None

        if matType == 'Std':
            mat = c4d.BaseMaterial(5703)
            self.MatNameAdd = '_STD'
        elif matType == 'Vray':
            mat = c4d.BaseMaterial(1038954)
            self.MatNameAdd = '_VR'
        elif matType == 'Redshift':
            mat = RedshiftMaterial()
            self.MatNameAdd = '_RS'
        elif matType == 'Octane':
            mat = c4d.BaseMaterial(1029501)
            self.MatNameAdd = '_OCT'
        elif matType == 'Corona':
            mat = c4d.BaseMaterial(1032100)
            self.MatNameAdd = '_CRNA'

        mat.SetName( matName + self.MatNameAdd)
        self.NewMatList.append([sourceMat,mat])

        self.convertShader(sourceMat, mat)


        if mat == None: return False

        mat.Message( c4d.MSG_UPDATE )
        mat.Update( True, True )

        doc = c4d.documents.GetActiveDocument()
        doc.InsertMaterial( mat )
        c4d.EventAdd()

        print("----- Converted : "+matName+" : "+mat.GetName()+' -----')
        bc = c4d.BaseContainer()
        c4d.gui.GetInputState(c4d.BFM_INPUT_MOUSE, c4d.BFM_INPUT_CHANNEL, bc)
        return True

    def ApplyMaterials(self):
        doc = c4d.documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        while obj:
            for tag in obj.GetTags():
                if tag.GetType() == c4d.Ttexture:
                    oMat = tag.GetMaterial()
                    for mat in self.NewMatList:
                        if oMat == mat[0]:
                            tag.SetMaterial(mat[1])
            obj = self._GetNextHierarchyObject(obj)

        for mat in self.NewMatList:
            mat[0].Remove()

        c4d.EventAdd()

    def convertTo(self, matType='Std'):
        doc = c4d.documents.GetActiveDocument()

        success = False

        self.NewMatList = []

        myMaterials = doc.GetMaterials()
        for mat in myMaterials:
            success = self.convertMat(mat, matType)

        self.ApplyMaterials()

        if success:
            print("Done Material Conversion.")
        else:
            c4d.gui.MessageDialog("A problem has occurred or no mats to convert.")

        if matType == 'Octane':
            c4d.CallCommand(12168, 12168)  # Remove Unused Materials
            c4d.CallCommand(100004766, 100004766) # Select All
            c4d.CallCommand(100004819, 100004819) # Cut
            c4d.CallCommand(100004821, 100004821) # Paste

        return True


class convertToRedshift:

    def __init__(self):
        try:
            import redshift
        except:
            print('No Redshift found')

        self.bump_input_type = 1 # Tangent-Space Normals
        self.NewMatList = [] 

    def execute(self):
        # Execute main()
        doc = c4d.documents.GetActiveDocument()

        # Process for all materials of scene
        docMaterials = doc.GetMaterials()
        if DazToC4D().checkStdMats() == True:
            return

        for mat in docMaterials:
            matName = mat.GetName()
            if mat.GetType() == 5703:
                self.makeRSmat(mat)

        self.applyMaterials()

        c4d.EventAdd()
        bc = c4d.BaseContainer()
        c4d.gui.GetInputState(c4d.BFM_INPUT_MOUSE, c4d.BFM_INPUT_CHANNEL, bc)

    def getBumpType(self,index):
        if index == 0:
            self.bump_input_type = 1
        elif index == 1:
            self.bump_input_type = 0
        elif index == 2:
            self.bump_input_type = 2


    def applyMaterials(self):
        doc = c4d.documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        while obj:
            for tag in obj.GetTags():
                if tag.GetType() == c4d.Ttexture:
                    oMat = tag.GetMaterial()
                    for mat in self.NewMatList:
                        if oMat == mat[0]:
                            tag.SetMaterial(mat[1])
            obj = _GetNextHierarchyObject(obj)

        for mat in self.NewMatList:
            mat[0].Remove()

        c4d.EventAdd()


    def makeRSmat(self, mat):
        doc = c4d.documents.GetActiveDocument()
        skinMats = ['Legs', 'Torso', 'Body', 'Arms', 'Face', 'Fingernails', 'Toenails', 'Lips', 'EyeSocket', 'Ears',
                    'Feet', 'Nipples', 'Forearms', 'Hips', 'Neck', 'Shoulders', 'Hands', 'Head', 'Nostrils']
        matName = mat.GetName()
        matDiffuseColor = mat[c4d.MATERIAL_COLOR_COLOR]
        
        INPORT = 0

        def getRSnode(mat):
            gvNodeMaster = redshift.GetRSMaterialNodeMaster(mat)
            rootNode_ShaderGraph = gvNodeMaster.GetRoot()
            output = rootNode_ShaderGraph.GetDown()
            RShader = output.GetNext()
            return RShader

        c4d.CallCommand(1036759, 1000)  # Create RS Mat...

        newMat = c4d.documents.GetActiveDocument().GetActiveMaterial()
        newMat.SetName(matName + '_RS')

        self.NewMatList.append([mat, newMat])  # Add Original and New

        RShader = getRSnode(newMat)
        gvNodeMaster = redshift.GetRSMaterialNodeMaster(newMat)
        nodeRoot = gvNodeMaster.GetRoot()

        RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_WEIGHT] = 0.7
        RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS] = 0.35

        try:
            rsMaterial = nodeRoot.GetDown().GetNext()
            rsMaterial[c4d.REDSHIFT_SHADER_MATERIAL_DIFFUSE_COLOR] = matDiffuseColor
        except:
            print('RootNode color skip...')

        if mat[c4d.MATERIAL_USE_COLOR]:
            if mat[c4d.MATERIAL_COLOR_SHADER]:
                if mat[c4d.MATERIAL_COLOR_SHADER].GetType() == 5833:
                    # Texture Node:
                    Node = gvNodeMaster.CreateNode(nodeRoot, 1036227, None, 10, 200)
                    Node[c4d.GV_REDSHIFT_SHADER_META_CLASSNAME] = 'TextureSampler'
                    fileName = mat[c4d.MATERIAL_COLOR_SHADER][c4d.BITMAPSHADER_FILENAME]
                    Node[(c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0, c4d.REDSHIFT_FILE_PATH)] = fileName

                    if 'Sclera' in mat.GetName():
                        Node[c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0_GAMMAOVERRIDE] = True
                        Node[c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0_GAMMA] = 1.0

                    nodeShaderDiffuseColInput = RShader.AddPort(c4d.GV_PORT_INPUT,
                                                    c4d.DescID(c4d.DescLevel(c4d.REDSHIFT_SHADER_MATERIAL_DIFFUSE_COLOR)),
                                                    message=True)

                    Node.GetOutPort(0).Connect(nodeShaderDiffuseColInput)

        if mat[c4d.MATERIAL_USE_ALPHA]:
            if mat[c4d.MATERIAL_ALPHA_SHADER]:
                if mat[c4d.MATERIAL_ALPHA_SHADER].GetType() == 5833:
                    # Texture Node:
                    Node = gvNodeMaster.CreateNode(nodeRoot, 1036227, None, 10, 400)
                    Node[c4d.GV_REDSHIFT_SHADER_META_CLASSNAME] = 'TextureSampler'
                    fileName = mat[c4d.MATERIAL_ALPHA_SHADER][c4d.BITMAPSHADER_FILENAME]
                    Node[(c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0, c4d.REDSHIFT_FILE_PATH)] = fileName
                    Node[c4d.REDSHIFT_SHADER_TEXTURESAMPLER_ALPHA_IS_LUMINANCE] = True
                    Node[c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0_GAMMAOVERRIDE] = True
                    Node[c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0_GAMMA] = 0.1
                    if 'Eyelash' in mat.GetName():
                        Node[c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0_GAMMAOVERRIDE] = True
                        Node[c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0_GAMMA] = 1.0

                    nodeShaderOpacityColInput = RShader.AddPort(c4d.GV_PORT_INPUT,
                                                    c4d.DescID(c4d.DescLevel(c4d.REDSHIFT_SHADER_MATERIAL_OPACITY_COLOR)),
                                                    message=True)

                    Node.GetOutPort(0).Connect(nodeShaderOpacityColInput)

        if mat[c4d.MATERIAL_USE_BUMP]:
            if mat[c4d.MATERIAL_BUMP_SHADER]:
                if mat[c4d.MATERIAL_BUMP_SHADER].GetType() == 5833:
                    # Bump Node:
                    NodeBump = gvNodeMaster.CreateNode(nodeRoot, 1036227, None, 200, 150)  # Always use this to create any nodeee!!!
                    NodeBump[c4d.GV_REDSHIFT_SHADER_META_CLASSNAME] = 'BumpMap'  # This defines the node!!!
                    NodeBump[c4d.REDSHIFT_SHADER_BUMPMAP_INPUTTYPE] = self.bump_input_type
                    NodeBump[c4d.REDSHIFT_SHADER_BUMPMAP_SCALE] = 0.5
                    # Texture Node:
                    NodeTexture = gvNodeMaster.CreateNode(nodeRoot, 1036227, None, 80, 150)  # Always use this to create any nodeee!!!
                    NodeTexture[c4d.GV_REDSHIFT_SHADER_META_CLASSNAME] = 'TextureSampler'  # This defines the node!!!
                    fileName = mat[c4d.MATERIAL_BUMP_SHADER][c4d.BITMAPSHADER_FILENAME]
                    NodeTexture[(c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0, c4d.REDSHIFT_FILE_PATH)] = fileName

                    nodeShaderBumpInput = RShader.AddPort(c4d.GV_PORT_INPUT,
                                                    c4d.DescID(c4d.DescLevel(c4d.REDSHIFT_SHADER_MATERIAL_BUMP_INPUT)),
                                                    message=True)
                    nodeBumpMapInput = NodeBump.AddPort(c4d.GV_PORT_INPUT,
                                                     c4d.DescID(c4d.DescLevel(c4d.REDSHIFT_SHADER_BUMPMAP_INPUT)),
                                                     message=True)

                    NodeTexture.GetOutPort(0).Connect(nodeBumpMapInput)
                    NodeBump.GetOutPort(0).Connect(nodeShaderBumpInput)

        extraMapGlossyRough = dazToC4Dutils().findTextInFile(mat.GetName(), 'Glossy_Roughness_Map')
        if extraMapGlossyRough != None:
            Node = gvNodeMaster.CreateNode(nodeRoot, 1036227, None, 10, 465)
            Node[c4d.GV_REDSHIFT_SHADER_META_CLASSNAME] = 'TextureSampler'
            fileName = extraMapGlossyRough
            Node[(c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0, c4d.REDSHIFT_FILE_PATH)] = fileName

            nodeShaderReflectionColInput = RShader.AddPort(c4d.GV_PORT_INPUT,
                                            c4d.DescID(c4d.DescLevel(c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS)),
                                            message=True)

            Node.GetOutPort(0).Connect(nodeShaderReflectionColInput)
        if mat[c4d.MATERIAL_USE_REFLECTION]:
            layer = mat.GetReflectionLayerIndex(0)
            caca = mat[layer.GetDataID() + c4d.REFLECTION_LAYER_TRANS_TEXTURE]
            if caca:
                if caca.GetType() == 5833:
                    # Texture Node:
                    Node = gvNodeMaster.CreateNode(nodeRoot, 1036227, None, 10, 465)
                    Node[c4d.GV_REDSHIFT_SHADER_META_CLASSNAME] = 'TextureSampler'
                    fileName = caca[c4d.BITMAPSHADER_FILENAME]
                    Node[(c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0, c4d.REDSHIFT_FILE_PATH)] = fileName

                    nodeShaderReflectionColInput = RShader.AddPort(c4d.GV_PORT_INPUT,
                                                    c4d.DescID(c4d.DescLevel(c4d.REDSHIFT_SHADER_MATERIAL_REFL_COLOR)),
                                                    message=True)

                    Node.GetOutPort(0).Connect(nodeShaderReflectionColInput)


        for x in skinMats:  # Skin Stuff...
            if x in matName:
                RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_WEIGHT] = 0.4
                RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS] = 0.4

        if 'Eyelash' in matName:
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_WEIGHT] = 0.0
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(0.0, 0.0, 0.0)

        if 'Teeth' in matName:
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_WEIGHT] = 0.85
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS] = 0.35

        if 'Cornea' in matName or 'Tear' in matName or 'Reflection' in matName:
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_WEIGHT] = 1.0
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS] = 0.0
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFR_WEIGHT] = 1.0
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_IOR] = 1.8

        if 'Moisture' in matName:
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_WEIGHT] = 1.0
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS] = 0.0

            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFR_WEIGHT] = 1.0

        c4d.EventAdd()

    print('Convert to Redshift')

    

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

class AllSceneToZero:
    doc = documents.GetActiveDocument()

    def getMinY(self, obj):
        doc = documents.GetActiveDocument()
        # objs = doc.GetActiveObjects(0)
        # pts = obj.GetAllPoints()
        if obj.GetType() == 5100:
            # message = obj.GetName() + ' ' + str(len(pts))
            # c4d.gui.MessageDialog()
            mg = obj.GetMg()
            minPos = c4d.Vector(obj.GetPoint(0) * mg).y
            minId = None
            for i in range(obj.GetPointCount()):
                bufferMin = c4d.Vector(obj.GetPoint(i) * mg).y
                minPos = min(minPos, bufferMin)
                if minPos == bufferMin:
                    minId = i

            return minPos

    def rasterizeObj(self, obj):
        doc = documents.GetActiveDocument()
        collapsedName = obj.GetName() + '_Collapsed'
        c4d.CallCommand(100004767, 100004767)  # Deselect All
        obj.SetBit(c4d.BIT_ACTIVE)
        c4d.CallCommand(100004820)  # Copy
        c4d.CallCommand(100004821)  # Paste
        objPasted = doc.GetFirstObject()
        if objPasted.GetDown():
            if 'Poses' in objPasted.GetDown().GetName():
                objPasted.GetDown().Remove()

        c4d.CallCommand(100004772)  # Group Objects
        c4d.CallCommand(100004768)  # Select Children
        c4d.CallCommand(16768, 16768)  # Connect Objects + Delete
        collapsedObj = doc.GetFirstObject()
        collapsedObj.SetName(collapsedName)
        minY = self.getMinY(collapsedObj)
        collapsedObj.Remove()

        return minY

    def sceneLowestYobj(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()

        scene = ObjectIterator(obj)
        sceneYvalues = []
        sceneLowestY = 0.0
        dictYvalues = {}
        for obj in scene:
            if obj.GetUp() == None and obj.GetType() == 5100:
                    objPos = obj.GetAbsPos()  # The absolute object position.
                    objCenterOffset = obj.GetMp()  # The bounding box center.
                    boundBox = obj.GetRad()  # The bounding box width, height and depth.
                    realPos = objPos[1] + objCenterOffset[1]
                    lowestY = realPos - boundBox[1]
                    sceneYvalues.append(lowestY)
                    dictYvalues[lowestY] = obj

        sceneLowestObj = 0
        if len(sceneYvalues) > 0:
            sceneLowestY = min(sceneYvalues)
            sceneLowestObj = dictYvalues[sceneLowestY]

        return sceneLowestObj

    def moveAllToZero(self, baseObjs, posY):
        c4d.EventAdd()
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        c4d.EventAdd()
        doc = documents.GetActiveDocument()
        baseObjs = []
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for obj in scene:
            if obj.GetUp() == None:
                baseObjs.append(obj)

        newNull = c4d.BaseObject(c4d.Onull)  # Create new cube
        doc.InsertObject(newNull)
        newNull[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y] = posY
        c4d.EventAdd()

        for obj in baseObjs:
            if obj.GetUp() == None:
                mg = obj.GetMg()
                obj.InsertUnder(newNull)
                obj.SetMg(mg)

        c4d.EventAdd()
        newNull[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y] = 0
        c4d.CallCommand(12113, 12113)  # Deselect All
        newNull.SetBit(c4d.BIT_ACTIVE)
        c4d.CallCommand(100004773, 100004773)  # Expand Object Group
        newNull.Remove()
        c4d.EventAdd()

    def sceneToZero(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        baseObjs = []
        errorDetected = False

        for obj in scene:
            if scene.depth == 0:
                if obj.GetType() == 5100:
                    baseObjs.append(obj)
                if obj.GetType() == 1007455:
                    objSub = obj
                    objMesh = obj.GetDown()
                    c4d.CallCommand(100004767, 100004767)  # Deselect All
                    objSub.SetBit(c4d.BIT_ACTIVE)
                    c4d.CallCommand(100004773) # Expand Object Group
                    objSub.Remove()
                    c4d.EventAdd()
                    if objMesh:
                        if objMesh.GetType() == 5100:
                            baseObjs.append(objMesh)

        if len(baseObjs) >0:
            if errorDetected == False:
                getLowestY = self.rasterizeObj(self.sceneLowestYobj())
                self.moveAllToZero(baseObjs, getLowestY)
                c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD| c4d.DRAWFLAGS_STATICBREAK)
                c4d.EventAdd()


class autoAlignArms():
    def constraintObj(self, obj, target):
        doc = c4d.documents.GetActiveDocument()

        constraintTAG = c4d.BaseTag(1019364)
        constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM] = True
        constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_MAINTAIN] = True
        constraintTAG[20001] = target

        obj.InsertTag(constraintTAG)

        c4d.EventAdd()
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)
        return constraintTAG

    def newNullfromJoint(self, jointName, nullName):
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject(jointName)
        nullTemp = None
        if obj:
            tempMg = obj.GetMg()

            nullTemp = c4d.BaseObject(c4d.Onull)
            doc.InsertObject(nullTemp)
            nullTemp.SetMg(tempMg)
            nullTemp.SetName(nullName)
            nullTemp[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0.0
            nullTemp[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0.0
            nullTemp[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0.0
            # nullTemp[c4d.NULLOBJECT_DISPLAY] = 10
            # nullTemp[c4d.NULLOBJECT_ORIENTATION] = 1

            c4d.EventAdd()
        return nullTemp

    def alignJoint(self, side, jointName, jointTarget):
        doc = documents.GetActiveDocument()
        jointSource = doc.SearchObject(side + jointName)
        objSource = self.newNullfromJoint(side + jointName, 'ROTATOR')
        objTarget = self.newNullfromJoint(side + jointTarget, 'TARGET')
        if jointSource != None:
            xtag = self.constraintObj(jointSource, objTarget)
            objTarget.SetMg(objSource.GetMg())
            if side == 'l':
                xValue = 100
            if side == 'r':
                xValue = -100
            objTarget[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X] += xValue
            c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)
            c4d.EventAdd()
            xtag.Remove()
            objSource.Remove()
            objTarget.Remove()

    def __init__(self):
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject('lShldrTwist')
        if obj:
            self.alignJoint('l', 'ShldrBend', 'ForearmBend')
            self.alignJoint('l', 'ShldrTwist', 'ForearmBend')
            self.alignJoint('l', 'ForearmBend', 'Hand')
            self.alignJoint('l', 'ForearmTwist', 'Hand')

            self.alignJoint('l', 'Index1', 'Index2')
            self.alignJoint('l', 'Index2', 'Index3')
            self.alignJoint('l', 'Mid1', 'Mid2')
            self.alignJoint('l', 'Mid2', 'Mid3')
            self.alignJoint('l', 'Ring1', 'Ring2')
            self.alignJoint('l', 'Ring2', 'Ring3')
            self.alignJoint('l', 'Pinky1', 'Pinky2')
            self.alignJoint('l', 'Pinky2', 'Pinky3')

            self.alignJoint('r', 'ShldrBend', 'ForearmBend')
            self.alignJoint('r', 'ShldrTwist', 'ForearmBend')
            self.alignJoint('r', 'ForearmBend', 'Hand')
            self.alignJoint('r', 'ForearmTwist', 'Hand')

            self.alignJoint('r', 'Index1', 'Index2')
            self.alignJoint('r', 'Index2', 'Index3')
            self.alignJoint('r', 'Mid1', 'Mid2')
            self.alignJoint('r', 'Mid2', 'Mid3')
            self.alignJoint('r', 'Ring1', 'Ring2')
            self.alignJoint('r', 'Ring2', 'Ring3')
            self.alignJoint('r', 'Pinky1', 'Pinky2')
            self.alignJoint('r', 'Pinky2', 'Pinky3')

        obj = doc.SearchObject('lShldr')
        if obj:
            self.alignJoint('l', 'Shldr', 'ForeArm')
            self.alignJoint('l', 'ForeArm', 'Hand')
            self.alignJoint('r', 'Shldr', 'ForeArm')
            self.alignJoint('r', 'ForeArm', 'Hand')

class connectEyeLashesMorphXpresso:
    xtag = None
    

    def connectMorphsXpresso(self, morphMain, morphTagMain, morphTagSlave):
        xtag = c4d.BaseTag(c4d.Texpresso)

        #Set Tag priority to Animation
        pd = xtag[c4d.EXPRESSION_PRIORITY]
        pd.SetPriorityValue(c4d.PRIORITYVALUE_MODE, 1)
        # pd.SetPriorityValue(c4d.PRIORITYVALUE_PRIORITY, Value)
        xtag[c4d.EXPRESSION_PRIORITY] = pd
        xtag[c4d.ID_BASELIST_NAME] = 'DazToC4D Morphs Connect'
        morphMain.InsertTag(xtag)

        nodemaster = xtag.GetNodeMaster()
        # print nodemaster.GetOwner().GetName()
        def connectMorphNodes(x):
            morphNumber = 1001 + x*100
            node1 = nodemaster.CreateNode(nodemaster.GetRoot(),c4d.ID_OPERATOR_OBJECT,None,50, 50 * x)
            node1[c4d.GV_OBJECT_OBJECT_ID] = morphTagMain
            node2 = nodemaster.CreateNode(nodemaster.GetRoot(),c4d.ID_OPERATOR_OBJECT,None,400, 50 * x)
            node2[c4d.GV_OBJECT_OBJECT_ID] = morphTagSlave

            node1out = node1.AddPort(c4d.GV_PORT_OUTPUT,c4d.DescID(c4d.DescLevel(4000), c4d.DescLevel(morphNumber)))
            node2in = node2.AddPort(c4d.GV_PORT_INPUT,c4d.DescID(c4d.DescLevel(4000), c4d.DescLevel(morphNumber)))

            c4d.modules.graphview.RedrawMaster(nodemaster)
            try:
                node1out.Connect(node2in)
            except:
                return None

        for x in range(1, morphTagMain.GetMorphCount()):
            connectMorphNodes(x)
        c4d.EventAdd()

    def findMorphTag(self, obj):
        objTags =  TagIterator(obj)
        for t in objTags:
            if 'Morph' in t.GetName():
                return t

    def __init__(self):
        morphMain = dazToC4Dutils().getDazMesh()
        morphSlave = ''

        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for obj in scene:
            if 'Eyelashes' in obj.GetName():
                if obj.GetType() == 5100:
                    if self.findMorphTag(obj):
                        morphSlave = obj
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for obj in scene: #TOON GENERATION FIX
            if 'ToonBrows' in obj.GetName():
                if obj.GetType() == 5100:
                    if self.findMorphTag(obj):
                        morphSlave = obj


        if morphSlave != '':
            morphTagMain = self.findMorphTag(morphMain)  #GET FIGURE MESH OBJ!
            morphTagSlave = self.findMorphTag(morphSlave)
            self.connectMorphsXpresso(morphMain, morphTagMain, morphTagSlave)

    def __repr__(self):
        return self.xtag


def getJointFromSkin(obj, jointName):
    objTags =  TagIterator(obj)
    for t in objTags:
        if 'Weight' in t.GetName():
            for j in range(t.GetJointCount()):
                if jointName in t.GetJoint(j).GetName():
                    return t.GetJoint(j)
    return None

def getJointFromConstraint(jointName):
    objTags =  TagIterator(jointName)
    for t in objTags:
        if 'Constraint' in t.GetName():
            return t[10001]

    return None


class forceTpose():
    def dazRotFix(self, master, mode='', jointToFix='', rotValue=0):
        doc = documents.GetActiveDocument()

        nullObj = c4d.BaseObject(c4d.Onull)  # Create new cube
        nullObj.SetName('TempNull')
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
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_Y] = False
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_Z] = False
            constraintTAG[20004] = 5  # Axis X-
            constraintTAG[20001] = masterObj

        slaveObj.InsertTag(constraintTAG)
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)
        c4d.EventAdd()

        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)
        constraintTAG.Remove()

        addConstraint(jointToFix, slaveObj)

        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
        slaveObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = rotValue

    def dazRotationsFix(self, jointToFix, jointToAim, oppositeJoint, rotValue=0, allToZero=False):
        doc = documents.GetActiveDocument()

        mainJoint = doc.SearchObject(jointToFix)
        goalJoint = doc.SearchObject(jointToAim)
        self.dazRotFix(goalJoint, 'AIM', mainJoint, rotValue)

        jointOposite = doc.SearchObject(oppositeJoint)
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)

        rx = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X]
        ry = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y]
        rz = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z]

        jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = rx * -1
        if allToZero == True:
            jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0
            jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0

        tempNull = doc.SearchObject('TempNull')
        tempNull.Remove()
        caca = mainJoint.GetFirstTag()
        caca.Remove()

        c4d.EventAdd()

    def dazFix_All_To_T_Pose(self):
        # Genesis2
        doc = documents.GetActiveDocument()
        if doc.SearchObject('lShldr'):
            self.dazRotationsFix('lShldr', 'lForeArm', 'rShldr', 1.571)
        if doc.SearchObject('lForeArm'):
            self.dazRotationsFix('lForeArm', 'lHand', 'rForeArm', 1.571)

        # All Genesis..Maybe...
        if doc.SearchObject('lFoot'):
            self.dazRotationsFix('lFoot', 'lToe', 'rFoot')


class alignFingersFull():

    def fixRotations(self, jointName):
        doc = documents.GetActiveDocument()
        try:
            obj = doc.SearchObject(jointName)
            obj[c4d.ID_BASEOBJECT_ROTATION_ORDER] = 5

            objRotX = obj.GetAbsRot()[0]
            objRotY = obj.GetAbsRot()[1]
            objRotZ = obj.GetAbsRot()[2]
            obj.SetAbsRot(c4d.Vector(objRotX, 0, 0))
        except:
            print('FixR skipped...')

    def AlignBoneChain(self, rootBone, upAxis, primaryAxis=1, primaryDirection=0, upDirection=4):
        doc = documents.GetActiveDocument()
        try:
            c4d.CallCommand(12113, 12113)  # Deselect All
            joint = doc.SearchObject(rootBone)

            normalNull = doc.SearchObject('normalNull')  # Normal Null ...!!..

            doc.SetActiveObject(joint, c4d.SELECTION_NEW)
            # c4d.CallCommand(1021334, 1021334)
            c4d.CallCommand(1021334)  # Joint Align Tool
            tool = c4d.plugins.FindPlugin(doc.GetAction(), c4d.PLUGINTYPE_TOOL)
            if tool is not None:
                tool[c4d.ID_CA_JOINT_ALIGN_PRIMARY_AXIS] = primaryAxis
                tool[c4d.ID_CA_JOINT_ALIGN_PRIMARY_DIRECTION] = primaryDirection
                tool[c4d.ID_CA_JOINT_ALIGN_UP_AXIS] = upAxis
                tool[c4d.ID_CA_JOINT_ALIGN_UP_DIRECTION] = upDirection
                tool[c4d.ID_CA_JOINT_ALIGN_UP_FROMPREV] = True
                tool[c4d.ID_CA_JOINT_ALIGN_CHILDREN] = True
                tool[c4d.ID_CA_JOINT_ALIGN_UP_LINK] = normalNull
                c4d.CallButton(tool, c4d.ID_CA_JOINT_ALIGN)
        except:
            print('AlignBC Skipped...')
        c4d.EventAdd()

    def alignJoints(self, jointName):
        doc = documents.GetActiveDocument()
        try:
            obj = doc.SearchObject(jointName)

            obj[c4d.ID_CA_JOINT_OBJECT_BONE_AXIS] = 1
            c4d.CallCommand(1019883)  # Align
        except:
            print('alignPass skipped...')
        c4d.EventAdd()

    def constraintClamp(self, obj, normalPolyObj):
        doc = documents.GetActiveDocument()
        constraintTAG = c4d.BaseTag(1019364)
        constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_CLAMP] = True
        constraintTAG[50004, 1] = 4  # To: Surface
        constraintTAG[50004, 3] = 5  # Align: Z-
        constraintTAG[50004, 2] = 3  # Mode: Fix Axis
        constraintTAG[50004, 4] = 4  # As: Normal
        constraintTAG[50001] = normalPolyObj
        obj.InsertTag(constraintTAG)
        c4d.EventAdd()

    def generateNormalFromObjs(self, target1, target2, target3):
        doc = documents.GetActiveDocument()
        obj1 = doc.SearchObject('normalNull')
        obj2 = doc.SearchObject('normalPoly')
        obj3 = doc.SearchObject('normalPos1')
        obj4 = doc.SearchObject('normalPos2')
        obj5 = doc.SearchObject('normalPos3')

        try:
            obj1.Remove()
        except:
            pass
        try:
            obj2.Remove()
        except:
            pass
        try:
            obj3.Remove()
        except:
            pass
        try:
            obj4.Remove()
        except:
            pass
        try:
            obj5.Remove()
        except:
            pass

        objNull = c4d.BaseObject(c4d.Onull)
        objNull.SetName('normalNull')
        doc.InsertObject(objNull)
        c4d.EventAdd()

        obj1 = c4d.BaseObject(c4d.Onull)
        obj1.SetName('normalPos1')
        doc.InsertObject(obj1)
        obj2 = c4d.BaseObject(c4d.Onull)
        doc.InsertObject(obj2)
        obj2.SetName('normalPos2')
        obj3 = c4d.BaseObject(c4d.Onull)
        doc.InsertObject(obj3)
        obj3.SetName('normalPos3')

        targetObj1 = doc.SearchObject(target1)
        targetObj2 = doc.SearchObject(target2)
        targetObj3 = doc.SearchObject(target3)

        obj1.SetMg(targetObj1.GetMg())
        obj2.SetMg(targetObj2.GetMg())
        obj3.SetMg(targetObj3.GetMg())

        mypoly = c4d.BaseObject(c4d.Opolygon)  # Create an empty polygon object
        mypoly.ResizeObject(4, 1)  # New number of points, New number of polygons

        mypoly.SetPoint(0, obj1.GetAbsPos())
        mypoly.SetPoint(1, obj2.GetAbsPos())
        mypoly.SetPoint(2, obj3.GetAbsPos())
        mypoly.SetPoint(3, obj3.GetAbsPos())

        mypoly.SetName('normalPoly')
        mypoly.SetPolygon(0, c4d.CPolygon(0, 1, 2, 3))  # The Polygon's index, Polygon's points
        doc.InsertObject(mypoly, None, None)
        mypoly.Message(c4d.MSG_UPDATE)

        doc.SetActiveObject(mypoly, c4d.SELECTION_NEW)
        c4d.CallCommand(14039)  # Optimize...
        c4d.CallCommand(1011982)  # Center Axis to

        objNull.SetMg(mypoly.GetMg())

        c4d.EventAdd()

        self.constraintClamp(objNull, mypoly)
        c4d.EventAdd()

    def start(self, modelName, lastFinger=''):
        doc = c4d.documents.GetActiveDocument()
        # modelName = 'Human_Builder_' #Replace with model name....
        jHand = modelName + 'jHand'
        jIndex1 = modelName + 'jIndex1'
        jIndex2 = modelName + 'jIndex2'
        jIndex3 = modelName + 'jIndex3'
        jMiddle1 = modelName + 'jMiddle1'
        jMiddle2 = modelName + 'jMiddle2'
        jMiddle3 = modelName + 'jMiddle3'
        jRing1 = modelName + 'jRing1'
        jRing2 = modelName + 'jRing2'
        jRing3 = modelName + 'jRing3'
        jPink1 = modelName + 'jPink1'
        jPink2 = modelName + 'jPink2'
        jPink3 = modelName + 'jPink3'
        fingersList = ['jIndex1', 'jIndex2', 'jIndex3',
                       'jMiddle1', 'jMiddle2', 'jMiddle3',
                       'jRing1', 'jRing2', 'jRing3',
                       'jPink1', 'jPink2', 'jPink3']

        for j in fingersList:
            self.alignJoints(modelName + j)  # Replace with model name....

        # Generate plane if at least jIndex and other finger present...
        if lastFinger == 'jPink':
            self.generateNormalFromObjs(jHand, jIndex1, jPink1)
        if lastFinger == 'jRing':
            self.generateNormalFromObjs(jHand, jIndex1, jRing1)
        if lastFinger == 'jMiddle':
            self.generateNormalFromObjs(jHand, jIndex1, jMiddle1)

        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)

        self.AlignBoneChain(modelName + 'jIndex1', 2, 3, 0, 2)
        self.AlignBoneChain(modelName + 'jMiddle1', 2, 3, 0, 2)
        self.AlignBoneChain(modelName + 'jRing1', 2, 3, 0, 2)
        self.AlignBoneChain(modelName + 'jPink1', 2, 3, 0, 2)

        self.fixRotations(jIndex2)
        self.fixRotations(jIndex3)
        self.fixRotations(jMiddle2)
        self.fixRotations(jMiddle3)
        self.fixRotations(jRing2)
        self.fixRotations(jRing3)
        self.fixRotations(jPink2)
        self.fixRotations(jPink3)

        obj1 = doc.SearchObject('normalNull')
        obj2 = doc.SearchObject('normalPoly')
        obj3 = doc.SearchObject('normalPos1')
        obj4 = doc.SearchObject('normalPos2')
        obj5 = doc.SearchObject('normalPos3')
        try:
            obj1.Remove()
        except:
            pass
        try:
            obj2.Remove()
        except:
            pass
        try:
            obj3.Remove()
        except:
            pass
        try:
            obj4.Remove()
        except:
            pass
        try:
            obj5.Remove()
        except:
            pass

        c4d.EventAdd()


class DazToC4D():
    dialog = None

    def stdMatExtrafixes(self):
        doc = c4d.documents.GetActiveDocument()
        
        #--- Fix duplicated Moisture material...??
        myMaterials = doc.GetMaterials()
        for mat in myMaterials:
            if "EyeMoisture" in mat.GetName():
                mat.SetName('EyeMoisture2')
                return True

        def setRenderToPhysical():
            try:
                rdata = doc.GetActiveRenderData()
                vpost = rdata.GetFirstVideoPost()
                rdata[c4d.RDATA_RENDERENGINE] = c4d.RDATA_RENDERENGINE_PHYSICAL

                while vpost:
                    if vpost.CheckType(c4d.VPxmbsampler): break
                    vpost = vpost.GetNext()

                if not vpost:
                    vpost = c4d.BaseList2D(c4d.VPxmbsampler)
                    rdata.InsertVideoPost(vpost)

                c4d.EventAdd()
            except:
                pass

        setRenderToPhysical()
        figureModel = 'Genesis8'

        def findMatName(matToFind):
            matFound = None
            sceneMats = doc.GetMaterials()
            for mat in sceneMats:
                matName = mat.GetName()
                if matToFind in matName:
                    matFound = mat
                    return matFound
            return matFound

        if findMatName('EyeReflection'):
            figureModel = 'Genesis2'
        if findMatName('Fingernails'):
            figureModel = 'Genesis3'

        # FIX MATERIAL NAMES etc... USE THIS FOR ALL CONVERTIONS NOT JUST OCTANE!
        if findMatName('1_SkinFace') == None and findMatName('1_Nostril') != None:
            try:
                findMatName('1_Nostril').SetName('1_SkinFace')
            except:
                pass
        if findMatName('3_SkinHand') == None and findMatName('3_SkinFoot') != None:
            try:
                findMatName('3_SkinFoot').SetName('3_ArmsLegs')
            except:
                pass
        # ////
        doc = documents.GetActiveDocument()
        sceneMats = doc.GetMaterials()

        for mat in sceneMats:
            matName = mat.GetName()
            try:
                mat[c4d.MATERIAL_ALPHA_SHADER][c4d.BITMAPSHADER_WHITEPOINT] = 0.5
            except:
                pass
            try:
                layerTransp = mat.GetReflectionLayerTrans()
                mat[layerTransp.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS] = 0.0
            except:
                pass

            # GENESIS 3 Patches -------------------------
            if figureModel == 'Genesis3' or figureModel == 'Genesis2' or figureModel == 'Genesis8':
                if 'Cornea' in matName:
                    bmpPath = 'CACA'
                    shaderColor = c4d.BaseList2D(c4d.Xcolor)  # create a bitmap shader for the material
                    # bmpShader[c4d.BITMAPSHADER_FILENAME] = bmpPath
                    mat.InsertShader(shaderColor)
                    mat[c4d.MATERIAL_USE_ALPHA] = True
                    mat[c4d.MATERIAL_ALPHA_SHADER] = shaderColor
                    mat[c4d.MATERIAL_ALPHA_SHADER][c4d.COLORSHADER_BRIGHTNESS] = 0.0

                if 'Moisture' in matName or 'Tear' in matName:
                    mat[c4d.MATERIAL_USE_ALPHA] = True
                    mat[c4d.MATERIAL_ALPHA_SHADER] = None
                    mat[c4d.MATERIAL_COLOR_COLOR] = c4d.Vector(0, 0, 0)
                    mat[c4d.MATERIAL_TRANSPARENCY_REFRACTION] = 1.0



                if 'Sclera' in matName:
                    try:
                        mat[c4d.MATERIAL_COLOR_SHADER][c4d.BITMAPSHADER_WHITEPOINT] = 0.8
                    except:
                        pass

        c4d.EventAdd()

    def specificFiguresFixes(self):
        doc = c4d.documents.GetActiveDocument()

        figureModel = ''

        def findMatName(matToFind):
            matFound = None
            sceneMats = doc.GetMaterials()
            for mat in sceneMats:
                matName = mat.GetName()
                if matToFind in matName:
                    matFound = mat
                    return matFound
            return matFound

        #TOON GENERATION 2
        doc = documents.GetActiveDocument()
        sceneMats = doc.GetMaterials()
        #ZOMBIE ... GEN3...
        if findMatName('Cornea') != None and findMatName('EyeMoisture') == None:
            mat = findMatName('Cornea')
            mat[c4d.MATERIAL_USE_ALPHA] = False

        for mat in sceneMats:
            matName = mat.GetName()
            if 'Eyelashes' in matName:
                if mat[c4d.MATERIAL_ALPHA_SHADER] == None:
                    try:
                        shaderColor = c4d.BaseList2D(c4d.Xcolor)  # create a bitmap shader for the material
                        mat.InsertShader(shaderColor)
                        mat[c4d.MATERIAL_USE_ALPHA] = True
                        mat[c4d.MATERIAL_ALPHA_SHADER] = shaderColor
                        mat[c4d.MATERIAL_ALPHA_SHADER][c4d.COLORSHADER_BRIGHTNESS] = 0.0
                    except:
                        pass

        c4d.EventAdd()

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


    def dazEyesLookAtControls(self):
        doc = c4d.documents.GetActiveDocument()

        ojo1 = doc.SearchObject('rEye')  # Genesis2
        ojo2 = doc.SearchObject('lEye')  # Genesis2

        if ojo1 is None or ojo2 is None:
            return

        def constraintObj(slave, master, mode="", searchObj=1):
            doc = documents.GetActiveDocument()
            if searchObj == 1:
                slaveObj = doc.SearchObject(slave)
                masterObj = doc.SearchObject(master)
            else:
                slaveObj = slave
                masterObj = master
            mg = slaveObj.GetMg()

            constraintTAG = c4d.BaseTag(1019364)
            if mode == "":
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
                constraintTAG[10001] = masterObj
            if mode == "UPVECTOR":
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_UP] = True
                constraintTAG[40004] = 4
                constraintTAG[40005] = 3
                constraintTAG[40001] = masterObj
            if mode == "ROTATION":
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
                constraintTAG[10005] = False
                constraintTAG[10006] = False
                constraintTAG[10001] = masterObj
            if mode == "AIM":
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_MAINTAIN] = True
                constraintTAG[20001] = masterObj
            if mode == "PARENT":
                nullSlave = c4d.BaseObject(c4d.Onull)
                nullSlave.SetName('nullSlave')
                nullSlave.SetMg(slaveObj.GetMg())
                doc.InsertObject(nullSlave)
                nullParent = c4d.BaseObject(c4d.Onull)
                nullParent.SetName('nullParent')
                nullParent.SetMg(masterObj.GetMg())
                slaveMg = nullSlave.GetMg()
                doc.InsertObject(nullParent)
                nullSlave.InsertUnder(nullParent)
                nullSlave.SetMg(slaveMg)
                constraintTAG[c4d.EXPRESSION_ENABLE] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PARENT_MAINTAIN] = False
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PARENT_FROZEN] = False
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PARENT] = True
                constraintTAG[30001] = masterObj
                constraintTAG[30009, 1000] = c4d.Vector(nullSlave.GetRelPos()[0], nullSlave.GetRelPos()[1], nullSlave.GetRelPos()[2])
                constraintTAG[30009, 1002] = c4d.Vector(nullSlave.GetRelRot()[0], nullSlave.GetRelRot()[1], nullSlave.GetRelRot()[2])

                PriorityDataInitial = c4d.PriorityData()
                PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_MODE, c4d.CYCLE_GENERATORS)
                PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_PRIORITY, 0)
                PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_CAMERADEPENDENT, 0)
                constraintTAG[c4d.EXPRESSION_PRIORITY] = PriorityDataInitial
                try:
                    nullParent.Remove()
                except:
                    pass
            slaveObj.InsertTag(constraintTAG)
            # if mode == "PARENT":
            #     slaveObj.SetMg(mg)

            c4d.EventAdd()

        def makeNull(nullName, target):
            doc = c4d.documents.GetActiveDocument()
            objNull = c4d.BaseObject(c4d.Onull)
            objNull.SetName('_IKM-StartGuides')
            objNull.SetMg(target.GetMg())
            doc.InsertObject(objNull)
            c4d.EventAdd()

            return objNull

        def freezeChilds(self, parentObj=""):
            doc = c4d.documents.GetActiveDocument()
            obj = doc.SearchObject(parentObj)

            try:

                for x in self.iterateObjChilds(obj):
                    # Transfer coords info to freeze info
                    x.SetFrozenPos(x.GetAbsPos())
                    x.SetFrozenRot(x.GetAbsRot())
                    # x.SetFrozenScale(x.GetRelRot())

                    # Zero coords...
                    x.SetRelPos(c4d.Vector(0, 0, 0))
                    x.SetRelRot(c4d.Vector(0, 0, 0))
                    # x.SetRelScale(c4d.Vector(1, 1, 1))
            except:
                pass

            c4d.EventAdd()

        headJoint = doc.SearchObject('head')  # Genesis2
        joints = doc.SearchObject('pelvis')  # Genesis2
        ikControls = doc.SearchObject(dazName + 'IKM_Controls')
        ikHeadCtrl = doc.SearchObject(dazName + 'Head_ctrl')

        obj1 = makeNull('Eye1', ojo1)
        obj2 = makeNull('Eye2', ojo2)
        objParent = ojo1.GetUp()
        eyesParentNull = makeNull('EyesParent', headJoint)
        # eyesGroup = makeNull('EyesParent', headJoint)

        obj1.SetName(dazName + 'rEye_ctrl')
        obj2.SetName(dazName + 'lEye_ctrl')
        obj1.SetAbsScale(c4d.Vector(1, 1, 1))
        obj2.SetAbsScale(c4d.Vector(1, 1, 1))

        eyesParentNull.SetName(dazName + 'Eyes-LookAt')
        # eyesGroup.SetName('EyesGroup')

        # masterSize = IKMAXDialog.MASTERSIZE  # ikmaxUtils().getObjHeight(characterMesh)
        masterSize = 100  # ??????

        obj1[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z] -= masterSize / 4
        obj2[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z] -= masterSize / 4

        def nullStyle(obj):
            obj[c4d.ID_BASEOBJECT_USECOLOR] = True
            obj[c4d.ID_BASEOBJECT_COLOR] = c4d.Vector(0, 0.9, 0)
            obj[c4d.NULLOBJECT_DISPLAY] = 2
            obj[c4d.NULLOBJECT_ORIENTATION] = 1
            obj[c4d.NULLOBJECT_RADIUS] = 0.5
            try:
                obj[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 2
                obj[c4d.ID_BASELIST_ICON_COLOR] = obj[c4d.ID_BASEOBJECT_COLOR]
            except:
                obj[c4d.NULLOBJECT_ICONCOL] = True

        def nullStyleMaster(obj):
            obj[c4d.ID_BASEOBJECT_USECOLOR] = True
            obj[c4d.ID_BASEOBJECT_COLOR] = c4d.Vector(0, 1, 0)
            obj[c4d.NULLOBJECT_DISPLAY] = 7
            obj[c4d.NULLOBJECT_ASPECTRATIO] = 0.3
            obj[c4d.NULLOBJECT_ORIENTATION] = 1
            obj[c4d.NULLOBJECT_RADIUS] = (masterSize / 25)
            try:
                obj[c4d.ID_BASELIST_ICON_COLORIZE_MODE] = 2
                obj[c4d.ID_BASELIST_ICON_COLOR] = obj[c4d.ID_BASEOBJECT_COLOR]
            except:
                obj[c4d.NULLOBJECT_ICONCOL] = True

        def makeChild(child, parent):
            mg = child.GetMg()
            child.InsertUnder(parent)
            child.SetMg(mg)

        def protectTag(obj, protectPreset):
            doc = documents.GetActiveDocument()
            tagProtec = c4d.BaseTag(5629)  # Protection Tag
            if protectPreset == "Rotation":
                tagProtec[c4d.PROTECTION_P_X] = False
                tagProtec[c4d.PROTECTION_P_Y] = False
                tagProtec[c4d.PROTECTION_P_Z] = False
                tagProtec[c4d.PROTECTION_S_X] = True
                tagProtec[c4d.PROTECTION_S_Y] = True
                tagProtec[c4d.PROTECTION_S_Z] = True
                tagProtec[c4d.PROTECTION_R_X] = True
                tagProtec[c4d.PROTECTION_R_Y] = True
                tagProtec[c4d.PROTECTION_R_Z] = True
            obj.InsertTag(tagProtec)
            c4d.EventAdd()
        c4d.CallCommand(12113, 12113)  # Deselect All
        doc.SetActiveObject(obj1, c4d.SELECTION_NEW)
        doc.SetActiveObject(obj2, c4d.SELECTION_ADD)
        c4d.CallCommand(100004772, 100004772)  # Group Objects
        c4d.CallCommand(100004773, 100004773)  # Expand Object

        objMasterEyes = doc.GetActiveObjects(0)[0]
        objMasterEyes.SetName(dazName + 'EyesLookAtGroup')
        objMasterEyes.SetAbsScale(c4d.Vector(1, 1, 1))

        nullStyle(obj1)
        nullStyle(obj2)
        nullStyleMaster(objMasterEyes)
        try:
            obj1[c4d.NULLOBJECT_DISPLAY] = 14
            obj2[c4d.NULLOBJECT_DISPLAY] = 14
        except:
            pass
        constraintObj(ojo1, obj1, 'AIM', 0)
        constraintObj(ojo2, obj2, 'AIM', 0)

        makeChild(obj1, objMasterEyes)
        makeChild(obj2, objMasterEyes)
        makeChild(objMasterEyes, ikHeadCtrl)


        obj1.SetAbsRot(c4d.Vector(0))
        obj2.SetAbsRot(c4d.Vector(0))

        constraintObj(eyesParentNull, headJoint, '', 0)
        eyesParentNull.InsertAfter(joints)

        freezeChilds(dazName + "Eyes-LookAt")
        freezeChilds(dazName + "EyesLookAtGroup")
        protectTag(objMasterEyes, 'Rotation')

        # freezeChilds("EyesGroup")

        c4d.EventAdd()

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

    def hideEyePolys(self):
        doc = documents.GetActiveDocument()

        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)

        for obj in scene:
            self.hidePolyTagByName(obj, 'EyeMoisture')
            self.hidePolyTagByName(obj, 'Cornea')


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

    def morphsFixRemoveAndRename(self):
        def morphsRemoveAndRename(obj):
            
            def morphRemove():
                listMorphsToRemove = ['RIG',
                                      'HDLv2',
                                      'HDLv3',
                                      'pNeckHead',
                                      'Genesis8Male_',
                                      'Genesis8MaleEyelashes_',
                                      'Genesis8Female_',
                                      'Genesis8FemaleEyelashes_'
                                      ]
                    
                morphsAmount = len(list(range(pmTag.GetMorphCount())))
                for x in range(0, morphsAmount):
                    try:
                        pmTag.SetActiveMorphIndex(x)
                        morphName = pmTag.GetActiveMorph().GetName()
                        for morphToRemove in listMorphsToRemove:
                            try:
                                if morphToRemove in morphName:
                                    pmTag.RemoveMorph(x)
                                    try:
                                        obj = doc.SearchObject(morphName)
                                        obj.Remove()
                                    except:
                                        pass
                                    return
                            except:
                                print('skip remove')
                    except:
                        pass
                c4d.EventAdd()

            def morphRename():
                morphsAmount = len(list(range(pmTag.GetMorphCount())))
                for x in range(0, morphsAmount):
                    try:
                        pmTag.SetActiveMorphIndex(x)
                        morphName = pmTag.GetActiveMorph().GetName()
                        try:
                            newMorphName = morphName.replace('head__', '')
                            newMorphName = newMorphName.replace('eCTRLM7', '')
                            newMorphName = newMorphName.replace('eCTRL', '')
                            newMorphName = newMorphName.replace('3duTG2_10yo_', '')
                            newMorphName = newMorphName.replace('PBMSTEDIM7', '')
                            newMorphName = newMorphName.replace('PHM', '')
                            newMorphName = newMorphName.replace('CTRLB', '')
                            newMorphName = newMorphName.replace('CTRL', '')
                            newMorphName = newMorphName.replace('_', '')
                            pmTag.GetActiveMorph().SetName(newMorphName)
                        except Exception as e:
                            pass
                    except Exception as e:
                        pass
                c4d.EventAdd()

            pmTag = obj.GetTag(c4d.Tposemorph)  # Gets the pm tag
            pmTag.ExitEdit(doc, True)
            morphsAmount = len(list(range(pmTag.GetMorphCount())))
                
            for x in range(0, morphsAmount):
                morphRename()
            for x in range(0, morphsAmount):
                morphRemove()  # REMOVE
                
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for ob in scene:
            pmTag = ob.GetTag(c4d.Tposemorph)  # Gets the pm tag
            if pmTag:
                morphsRemoveAndRename(ob)

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

    def addLipsMaterial(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        objTags = TagIterator(obj)
        for ob in scene:
            objTags = TagIterator(ob)
            if objTags:
                for tag in objTags:
                    matSel = tag[c4d.TEXTURETAG_RESTRICTION]
                    if matSel == 'Lips':
                        try:
                            old_mat = tag[c4d.TEXTURETAG_MATERIAL]

                            doc.SetActiveMaterial(old_mat)
                            c4d.CallCommand(300001022, 300001022)  # Copy
                            c4d.CallCommand(300001023, 300001023)  # Paste
                            newMat = doc.GetFirstMaterial()
                            newMat[c4d.ID_BASELIST_NAME] = 'Lips'

                            tag[c4d.TEXTURETAG_MATERIAL] = newMat
                        except:
                            pass

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

    def mirrorPose(self):
        doc = documents.GetActiveDocument()

        def mirrorPose(jointName):
            # jointName = 'lShldrBend'
            jointNameR = 'r' + jointName[1:100]
            jointObjL = doc.SearchObject(jointName)
            jointObjR = doc.SearchObject(jointNameR)
            if jointObjL:
                objLRot = jointObjL[c4d.ID_BASEOBJECT_REL_ROTATION]
                jointObjR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = -objLRot[0]
                jointObjR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = objLRot[1]
                jointObjR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = -objLRot[2]

        mirrorPose('lCollar')
        mirrorPose('lShldr') # ----Genesis 2
        mirrorPose('lForeArm') # ----Genesis 2
        mirrorPose('lShldrBend')
        mirrorPose('lShldrTwist')
        mirrorPose('lForearmBend')
        mirrorPose('lForearmTwist')
        mirrorPose('lHand')

        mirrorPose('lThumb1')
        mirrorPose('lThumb2')
        mirrorPose('lThumb3')
        mirrorPose('lCarpal1')
        mirrorPose('lIndex1')
        mirrorPose('lIndex2')
        mirrorPose('lIndex3')
        mirrorPose('lCarpal2')
        mirrorPose('lMid1')
        mirrorPose('lMid2')
        mirrorPose('lMid3')
        mirrorPose('lCarpal3')
        mirrorPose('lRing1')
        mirrorPose('lRing2')
        mirrorPose('lRing3')
        mirrorPose('lCarpal4')
        mirrorPose('lPinky1')
        mirrorPose('lPinky2')
        mirrorPose('lPinky3')

        mirrorPose('lThigh') # ----Genesis 2
        mirrorPose('lShin') # ----Genesis 2
        mirrorPose('lToe') # ----Genesis 2

        mirrorPose('lThighBend')
        mirrorPose('lThighTwist')
        mirrorPose('lShin')
        mirrorPose('lFoot')
        mirrorPose('lMetatarsals')
        mirrorPose('lToe')

        mirrorPose('lSmallToe4')
        mirrorPose('lSmallToe4_2')
        mirrorPose('lSmallToe3')
        mirrorPose('lSmallToe3_2')
        mirrorPose('lSmallToe2')
        mirrorPose('lSmallToe2_2')
        mirrorPose('lSmallToe1')
        mirrorPose('lSmallToe1_2')
        mirrorPose('lBigToe')
        mirrorPose('lBigToe_2')

        c4d.EventAdd()

    def checkIfPosedResetPose(self, checkAndReset=True):
        doc = documents.GetActiveDocument()
        # isPosed = False

        def checkIfPosed():
            obj = doc.GetFirstObject()
            scene = ObjectIterator(obj)
            jointsList = ['Collar', 'head', 'ShldrTwist', 'Forearm', 'pelvis', 'abdomen', 'Shldr']
            caca = False

            def checkJoint(jointName):
                joint = doc.SearchObject(jointName)
                if joint:
                    rotRX = abs(joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                    rotRY = abs(joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                    rotRZ = abs(joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
                    # print(rotRX)
                    # print(rotRY)
                    # print(rotRZ)
                    if rotRX == rotRY == rotRZ == 0.0:
                        return False
                    else:
                        return True

            def compareJoints(jointName):
                jointR = doc.SearchObject('r' + jointName)
                jointL = doc.SearchObject('l' + jointName)
                if jointR:
                    rotRX = abs(jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                    rotRY = abs(jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                    rotRZ = abs(jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
                    rotLX = abs(jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                    rotLY = abs(jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                    rotLZ = abs(jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
                    rotRX = round(rotRX, 2)
                    rotRY = round(rotRY, 2)
                    rotRZ = round(rotRZ, 2)
                    rotLX = round(rotLX, 2)
                    rotLY = round(rotLY, 2)
                    rotLZ = round(rotLZ, 2)
                    # print(rotRX, rotLX)
                    # print(rotRY, rotLY)
                    # print(rotRZ, rotLZ)
                    if rotRX == rotLX and rotRY == rotLY and rotRZ == rotLZ:
                        return False
                    else:
                        return True

            isPosed = False

            if compareJoints('ForeArm'):
                isPosed = True
            if compareJoints('Shldr'):
                isPosed = True
            if compareJoints('ShldrBend'):
                isPosed = True
            if compareJoints('ForearmBend'):
                isPosed = True
            if compareJoints('Hand'):
                isPosed = True
            if compareJoints('ThighBend'):
                isPosed = True
            if checkJoint('chestUpper'):
                isPosed = True
            if checkJoint('chestLower'):
                isPosed = True
            if checkJoint('abdomenLower'):
                isPosed = True
            if checkJoint('abdomenUpper'):
                isPosed = True
            if checkJoint('neckLower'):
                isPosed = True

            return isPosed

        if checkAndReset == False:
            return checkIfPosed()

        jointHip = doc.SearchObject('hip')  # CAMBIIIIIIIIIIIIIIIAAARRR
        jointRig = ObjectIterator(jointHip)
        if checkIfPosed():
            answer = gui.MessageDialog('Reset Pose first before Auto-Ik.\nReset Pose now?\n\nWarning: No Undo', c4d.GEMB_YESNO)
            if answer == 6:
                for x in jointRig:
                    x[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0.0
                    x[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0.0
                    x[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0.0
                jointHip[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0.0
                jointHip[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0.0
                jointHip[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0.0

                try:
                    mainJoint = jointHip.GetUp()
                    mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0.0
                    mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0.0
                    mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0.0
                    mainJoint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X] = 0.0
                    # mainJoint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y] = 0.0
                    mainJoint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z] = 0.0
                except:
                    pass

                DazToC4D().dazManualRotationFixTpose()
                # dazToC4Dutils().sceneToZero()

                c4d.EventAdd()
                c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
                c4d.EventAdd()

                AllSceneToZero().sceneToZero()
                c4d.CallCommand(12168, 12168)  # Delete Unused Materials
                answer = gui.MessageDialog('Auto-Ik now?', c4d.GEMB_YESNO)
                if answer == 6:
                    DazToC4D().autoIK()
                    return False
                else:
                    return True
        else:
            DazToC4D().autoIK()

    def lockLayerOnOff(self):
        doc = documents.GetActiveDocument()
        root = doc.GetLayerObjectRoot()  # Gets the layer manager
        layer = ''
        LayersList = root.GetChildren()
        for layers in LayersList:
            name = layers.GetName()
            if (name == 'IKM_Lock'):
                layer = layers
        if layer:
            if layer.GetName() == "IKM_Lock":
                layer_data = layer.GetLayerData(doc)
                lockValue = layer_data['locked']
                dir, file = os.path.split(__file__)  # Gets the plugin's directory
                LogoFolder_Path = os.path.join(dir, 'res')  # Adds the res folder to the path
                LogoFolder_PathIcons = os.path.join(LogoFolder_Path, 'icons')  # Adds the res folder to the path
                img_lock = os.path.join(LogoFolder_PathIcons, 'm_lock.png')
                img_lockON = os.path.join(LogoFolder_PathIcons, 'm_lockON.png')

                print(lockValue)
                if lockValue == True:
                    layer_data['locked'] = False
                    guiDazToC4DLayerLockButton.SetImage(img_lock, True)
                else:
                    layer_data['locked'] = True
                    guiDazToC4DLayerLockButton.SetImage(img_lockON, True)

                layer.SetLayerData(doc, layer_data)

        c4d.EventAdd()

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

    def findIK(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        ikfound = 0
        for obj in scene:
            if 'Foot_PlatformBase' in obj.GetName():
                ikfound = 1
        return ikfound

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

    def checkStdMats(self):
        doc = c4d.documents.GetActiveDocument()
        docMaterials = doc.GetMaterials()
        noStd = True
        for mat in docMaterials:
            matName = mat.GetName()
            if mat.GetType() == 5703:
                noStd = False
        if noStd == True:
            gui.MessageDialog('No standard mats found. This scene was already converted')

        return noStd

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


    def dazMorphsFix(self):
        doc = documents.GetActiveDocument()

        def detectRIGmorph(obj):
            pmTag = obj.GetTag(c4d.Tposemorph)  # Gets the pm tag
            pmTag.ExitEdit(doc, True)
            count = 0
            for x in range(pmTag.GetMorphCount()):
                pmTag.SetActiveMorphIndex(x)
                morphName = pmTag.GetActiveMorph().GetName()
                if 'RIG' in morphName:
                    count = count + 1
            return count

        def morphsRename(obj):
            pmTag = obj.GetTag(c4d.Tposemorph)  # Gets the pm tag
            pmTag.ExitEdit(doc, True)

            for x in range(pmTag.GetMorphCount()):
                try:
                    pmTag.SetActiveMorphIndex(x)
                    morphName = pmTag.GetActiveMorph().GetName()
                    newMorphName = morphName.replace('head__', '')
                    newMorphName = newMorphName.replace('eCTRLM7', '')
                    newMorphName = newMorphName.replace('eCTRL', '')
                    newMorphName = newMorphName.replace('3duTG2_10yo_', '')
                    newMorphName = newMorphName.replace('PBMSTEDIM7', '')
                    newMorphName = newMorphName.replace('PHM', '')
                    newMorphName = newMorphName.replace('CTRLB', '')
                    newMorphName = newMorphName.replace('CTRL', '')
                    newMorphName = newMorphName.replace('_', '')
                    pmTag.GetActiveMorph().SetName(newMorphName)
                    if 'RIG' in newMorphName:
                        try:
                            pmTag.RemoveMorph(x)
                        except:
                            print('skip')
                except:
                    pass

            c4d.EventAdd()

        caca = doc.GetFirstObject()
        while caca.GetNext():
            caca = caca.GetNext()
            fTag = None
            if caca.GetFirstTag():
                if self.tagsIterator(caca):
                    for x in self.tagsIterator(caca):
                        if 'Pose Morph' in x.GetName():
                            morphsRename(caca)

    def unhideProps(self):
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject('hip')
        ObjectIterator(obj)
        for o in ObjectIterator(obj):
            if o.GetType() == 5100 or o.GetType() == 5140:
                o[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 0
                o[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 0
        c4d.EventAdd()

    def fixGenEyes(self):
        dir, file = os.path.split(__file__)  # Gets the plugin's directory
        folder_DazToC4D_res = os.path.join(dir, 'res')  # Adds the res folder to the path
        folder_DazToC4D_xtra = os.path.join(folder_DazToC4D_res, 'xtra')  # Adds the res folder to the path
        file_G3_IrisFixMap = os.path.join(folder_DazToC4D_xtra, 'G3_Iris_Alpha.psd')

        destination_G3_IrisFixMap = os.path.join(ROOT_DIR, "G3_Iris_Alpha.psd")
     
        try:
            copyfile(file_G3_IrisFixMap, destination_G3_IrisFixMap)
        except:
            print('Iris Map transfer...Skipped.')

        doc = c4d.documents.GetActiveDocument()
        docMaterials = doc.GetMaterials()
        for mat in docMaterials:
            if 'Iris' in mat.GetName():
                matDiffuseMap = ''
                try:
                    matDiffuseMap = mat[c4d.MATERIAL_COLOR_SHADER][c4d.BITMAPSHADER_FILENAME]
                except:
                    pass
                skipThis = False
                if '3duG3FTG2_Eyes' in matDiffuseMap:
                    skipThis = True

                if skipThis == False and os.path.exists(destination_G3_IrisFixMap):
                    mat[c4d.MATERIAL_USE_ALPHA] = True
                    shda = c4d.BaseList2D(c4d.Xbitmap)
                    shda[c4d.BITMAPSHADER_FILENAME] = destination_G3_IrisFixMap
                    mat[c4d.MATERIAL_ALPHA_SHADER] = shda
                    mat.InsertShader(shda)

    def dazManualRotationFixTpose(self):


        # return False #Quit TEMPORAL
        doc = documents.GetActiveDocument()

        def setRotAndMirror(jointName, x, y, z):
            joint = doc.SearchObject(jointName)
            if x != 0.0:
                joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = x
            if y != 0.0:
                joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = y
            if z != 0.0:
                joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = z

        dazType = ''
        if doc.SearchObject('lShldrBend'):
            if doc.SearchObject('lMetatarsals'):
                if doc.SearchObject('rThighTwist'):
                    obj1PosY = ''
                    obj1PosY = ''
                    obj1PosY = doc.SearchObject('lShldrBend').GetMg().off[1]
                    obj2PosY = doc.SearchObject('lForearmBend').GetMg().off[1]
                    distValue = obj1PosY - obj2PosY
                    if distValue < 2.9:
                        dazType = 'Genesis3' # TODO !!
                    else:
                        dazType = 'Genesis8'

        if doc.SearchObject('lThigh'):
            if doc.SearchObject('lShin'):
                if doc.SearchObject('abdomen2'):
                    dazType = 'Genesis2'
   
        if dazType == 'Genesis8':
            # GENESIS 8 --------------------------------------------
            # Genesis 8 LEFT Side:
            autoAlignArms()


        if dazType == 'Genesis3':
            self.fixGenEyes() # Apply IRIS alpha fix
            # GENESIS 3 -ZOMBIE WORKS TOO -------------------------------------------
            autoAlignArms()

        if dazType == 'Genesis2':
            # GENESIS 2 --------------------------------------------
            # Genesis 2 LEFT Side:
            setRotAndMirror('lShldr', 0.089, 0.0, -0.019)
            setRotAndMirror('lForeArm', 0.334, 0.0, 0.0)
            setRotAndMirror('lHand', 0.083, 0.222, -0.121)
            setRotAndMirror('lThigh', 0.0, 0.0, 0.0)
            # setRotAndMirror('lFoot', -0.23, 0.0, 0.0)

            # Genesis 2 RIGHT Side:
            setRotAndMirror('rShldr', -0.089, 0.0, 0.019)
            setRotAndMirror('rForeArm', -0.334, 0.0, 0.0)
            setRotAndMirror('rHand', -0.083, 0.222, 0.121)
            setRotAndMirror('rThigh', 0.0, 0.0, 0.0)
            # setRotAndMirror('rFoot', 0.23, 0.0, 0.0)
        c4d.EventAdd()
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
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

    def importDazFbx(self, filePath):

        file = c4d.documents.LoadDocument(filePath, c4d.SCENEFILTER_OBJECTS | c4d.SCENEFILTER_MATERIALS | c4d.SCENEFILTER_MERGESCENE)
        c4d.documents.InsertBaseDocument(file)

    def transpMapFix(self, mat):
        if mat[c4d.MATERIAL_TRANSPARENCY_SHADER] != None:
            mat[c4d.MATERIAL_ALPHA_SHADER] = mat[c4d.MATERIAL_TRANSPARENCY_SHADER]
            mat[c4d.MATERIAL_USE_TRANSPARENCY] = 0
            mat[c4d.MATERIAL_USE_ALPHA] = 1
            mat[c4d.MATERIAL_TRANSPARENCY_SHADER] = None

    def matSetSpec(self, setting, value):
        doc = c4d.documents.GetActiveDocument()

        # Process for all materials of scene
        docMaterials = doc.GetMaterials()
        for mat in docMaterials:
            matName = mat.GetName()
            skinMats = ['MainSkin', 'Legs', 'Torso', 'Arms', 'Face', 'Fingernails', 'Toenails', 'EyeSocket','Ears',
                        'Feet','Nipples','Forearms','Hips','Neck','Shoulders','Hands','Head','Nostrils']
            for x in skinMats:
                if x in matName:
                    if mat.GetType() == 1038954: #Vray
                        if setting == 'Rough':
                            mat[c4d.VRAYSTDMATERIAL_REFLECTGLOSSINESS] = 1.0 - value/100
                        if setting == 'Weight':
                            colorValue = value / 100
                            mat[c4d.VRAYSTDMATERIAL_REFLECTCOLOR] = c4d.Vector(colorValue, colorValue, colorValue)

                    if mat.GetType() == 5703: #Standard
                        layer = mat.GetReflectionLayerIndex(0)
                        if setting == 'Rough':
                            mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS] = value/100
                        if setting == 'Weight':
                            mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = value/100
                    if mat.GetType() == 1029501: #Octane
                        if setting == 'Weight':
                            mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = value/100
                        if setting == 'Rough':
                            mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = value/100
                    if mat.GetType() == 1036224: #Redshift
                        gvNodeMaster = redshift.GetRSMaterialNodeMaster(mat)
                        rootNode_ShaderGraph = gvNodeMaster.GetRoot()
                        output = rootNode_ShaderGraph.GetDown()
                        RShader = output.GetNext()
                        gvNodeMaster = redshift.GetRSMaterialNodeMaster(mat)
                        nodeRoot = gvNodeMaster.GetRoot()
                        rsMaterial = nodeRoot.GetDown().GetNext()
                        if setting == 'Weight':
                            rsMaterial[c4d.REDSHIFT_SHADER_MATERIAL_REFL_WEIGHT] = value/100
                            rsMaterial[c4d.REDSHIFT_SHADER_MATERIAL_REFL_IOR] = value/10
                        if setting == 'Rough':
                            rsMaterial[c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS] = value/100

    def fixMaterials(self):

        doc = c4d.documents.GetActiveDocument()

        # Process for all materials of scene
        docMaterials = doc.GetMaterials()
        for mat in docMaterials:
            self.transpMapFix(mat)
            matName = mat.GetName()
            eyesMats = ['Eyelashes', 'Cornea', 'EyeMoisture','EyeMoisture2', 'Sclera', 'Irises']
            layer = mat.GetReflectionLayerIndex(0)

            mat[c4d.MATERIAL_NORMAL_STRENGTH] = 0.25
            mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.05
            try: #Remove extra layers stuff...
                mat.RemoveReflectionLayerIndex(1)
                mat.RemoveReflectionLayerIndex(2)
                mat.RemoveReflectionLayerIndex(3)
                mat.RemoveReflectionLayerIndex(4)
            except:
                pass

            if matName in eyesMats:
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS] = 0.13

            if 'Moisture' in matName or 'Cornea' in matName or 'Tear' in matName or 'EyeReflection' in matName:
                mat[c4d.MATERIAL_COLOR_COLOR] = c4d.Vector(0.2, 0.2, 0.2)
                mat[c4d.MATERIAL_USE_TRANSPARENCY] = True
                mat[c4d.MATERIAL_TRANSPARENCY_COLOR] = c4d.Vector(0.9, 0.9, 0.9)
                mat[c4d.MATERIAL_TRANSPARENCY_REFRACTION] = 1.0
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION] = 0 #0 = Reflection(legacy)
                mat[c4d.MATERIAL_USE_TRANSPARENCY] = True
                mat[c4d.MATERIAL_TRANSPARENCY_FRESNEL] = False
                mat[c4d.MATERIAL_TRANSPARENCY_EXITREFLECTIONS] = False
                mat[c4d.MATERIAL_TRANSPARENCY_COLOR] = c4d.Vector(0.95, 0.95, 0.95)
                mat[c4d.MATERIAL_TRANSPARENCY_REFRACTION]=1.33

                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_COLOR_COLOR] = c4d.Vector(1.0, 1.0, 1.0)
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS] = 0.0
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_REFLECTION] = 0.7
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.0
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_BUMP] = 0.0
            if 'Eyes' in matName:
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.0
            if 'Pupils' in matName:
                mat[c4d.MATERIAL_USE_REFLECTION]=False
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.0
            if 'Teeth' in matName:
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION] = 0 #0 = Reflection(legacy)
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS] = 0.07
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_REFLECTION] = 0.09
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.03
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_BUMP] = 0.25
            if 'Mouth' in matName:
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION] = 0 #0 = Reflection(legacy)
            if 'Sclera' in matName:
                mat[c4d.MATERIAL_USE_REFLECTION]=False
                mat[c4d.MATERIAL_GLOBALILLUM_RECEIVE_STRENGTH]=2

            if 'Iris' in matName:
                mat[c4d.MATERIAL_USE_REFLECTION]=False
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_REFLECTION] = 0.0
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.0
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION] = 0 #0 = Reflection(legacy)
            if 'Eyelash' in matName:
                mat[c4d.MATERIAL_COLOR_SHADER] = None
                mat[c4d.MATERIAL_COLOR_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                try:
                    mat[c4d.MATERIAL_ALPHA_SHADER][c4d.BITMAPSHADER_FILENAME][c4d.BITMAPSHADER_EXPOSURE] = 1.0
                except:
                    print('Exposure Skipped...')

        c4d.CallCommand(12253, 12253)  # Render All Materials

        c4d.EventAdd()
    def getImportList(self, version):
        importList = []
        for export in os.listdir(os.path.join(EXPORT_DIR, version)):
            if os.path.isdir(os.path.join(EXPORT_DIR, version, export)):
                for fbx in os.listdir(os.path.join(EXPORT_DIR, version, export)):
                    if fbx.endswith(".fbx"):
                        importList.append(os.path.join(EXPORT_DIR, version, export, fbx))
        return importList


    def genesisImport(self):
        #self.buttonsChangeState(False)
        # Instant Classes
        dtu = DtuLoader.DtuLoader()
        mat = Materials.Materials()
        doc = documents.GetActiveDocument()
        importList = self.getImportList("FIG")
        for filePath in importList:
            if os.path.exists(filePath) == False:
                gui.MessageDialog(
                    'Nothing to import.\nYou have to export from DAZ Studio first',
                    c4d.GEMB_OK)
                #self.buttonsChangeState(True)
                return 0

            self.importDazFbx(filePath)
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

            DazToC4D().addLipsMaterial() # Add Lips Material # Needs to have iterators removed to be pull
            dazObj = dazToC4Dutils().getDazMesh() 

            DazToC4D().morphsFixRemoveAndRename()
            xpressoTag = connectEyeLashesMorphXpresso()

            c4d.EventAdd()
            c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)
            c4d.EventAdd()
            c4d.CallCommand(300001026, 300001026)  # Deselect All
            c4d.CallCommand(12168, 12168)  # Remove Unused Materials

            DazToC4D().stdMatExtrafixes()
            DazToC4D().specificFiguresFixes()
            self.fixMaterials()

            isPosed = DazToC4D().checkIfPosed()
            if isPosed == False:
                DazToC4D().preAutoIK() #Only if T pose detected...


            c4d.EventAdd()
            c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD | c4d.DRAWFLAGS_STATICBREAK)
            c4d.EventAdd()

            #self.buttonsChangeState(True)

            self.dialog = guiASKtoSave()
            self.dialog.Open(dlgtype=c4d.DLG_TYPE_MODAL, xpos=screen['sx2']//2-210, ypos=screen['sy2']//2-100, defaultw=200, defaulth=150)


    def checkIfPosed(self):
        doc = documents.GetActiveDocument()

        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        jointsList = ['Collar', 'head', 'ShldrTwist', 'Forearm', 'pelvis', 'abdomen', 'Shldr']
        caca = False

        def checkJoint(jointName):
            joint = doc.SearchObject(jointName)
            if joint:
                rotRX = abs(joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                rotRY = abs(joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                rotRZ = abs(joint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
                if rotRX == rotRY == rotRZ == 0.0:
                    return False
                else:
                    return True

        def compareJoints(jointName):
            jointR = doc.SearchObject('r' + jointName)
            jointL = doc.SearchObject('l' + jointName)
            if jointR:
                rotRX = abs(jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                rotRY = abs(jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                rotRZ = abs(jointR[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
                rotLX = abs(jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X])
                rotLY = abs(jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y])
                rotLZ = abs(jointL[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z])
                rotRX = round(rotRX, 2)
                rotRY = round(rotRY, 2)
                rotRZ = round(rotRZ, 2)
                rotLX = round(rotLX, 2)
                rotLY = round(rotLY, 2)
                rotLZ = round(rotLZ, 2)
                if rotRX == rotLX and rotRY == rotLY and rotRZ == rotLZ:
                    return False
                else:
                    return True

        isPosed = False

        if compareJoints('ForeArm'):
            isPosed = True
        if compareJoints('Shldr'):
            isPosed = True
        if compareJoints('ShldrBend'):
            isPosed = True
        if compareJoints('ForearmBend'):
            isPosed = True
        if compareJoints('Hand'):
            isPosed = True
        if compareJoints('ThighBend'):
            isPosed = True
        if checkJoint('chestUpper'):
            isPosed = True
        if checkJoint('chestLower'):
            isPosed = True
        if checkJoint('abdomenLower'):
            isPosed = True
        if checkJoint('abdomenUpper'):
            isPosed = True
        if checkJoint('neckLower'):
            isPosed = True

        return isPosed


    def preAutoIK(self):

        doc = documents.GetActiveDocument()
        obj = doc.SearchObject('hip')
        if obj:
            doc = documents.GetActiveDocument()
            if doc.SearchObject('lThighTwist') != True:
                if DazToC4D().checkIfPosedResetPose(False) == False:
                    forceTpose().dazFix_All_To_T_Pose()
            if doc.SearchObject('lThighTwist'):
                if DazToC4D().checkIfPosedResetPose(False) == False:
                    DazToC4D().dazManualRotationFixTpose()
        
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD   | c4d.DRAWFLAGS_STATICBREAK)
        c4d.EventAdd()


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

            DazToC4D().cleanMorphsGeoRemove()
            DazToC4D().dazMorphsFix()
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


class randomColors():
    IKMobjList = []

    def selchildren(self, obj, next):  # Scan obj hierarchy and select children

        while obj and obj != next:
            # global IKMobjList
            self.IKMobjList.append(obj)
            self.selchildren(obj.GetDown(), next)
            obj = obj.GetNext()
        return self.IKMobjList

    def get_random_color(self):
        """ Return a random color as c4d.Vector """

        def get_random_value():
            """ Return a random value between 0.0 and 1.0 """
            return randint(0, 255) / 256.0

        return c4d.Vector(get_random_value(), get_random_value(), get_random_value())

    def randomNullsColor(self, parentName, randomCol=1, rigColor1=0, rigColor2=0):
        doc = documents.GetActiveDocument()
        try:
            if randomCol == 1:
                rigColor1 = self.get_random_color()  # c4d.Vector(0,2,0)
                rigColor2 = self.get_random_color()  # c4d.Vector(1,0,0)
            self.IKMobjList = []
            parentOb = parentName
            for o in self.selchildren(parentOb, parentOb.GetNext()):
                o[c4d.ID_BASEOBJECT_USECOLOR] = 2
                o[c4d.ID_BASEOBJECT_COLOR] = rigColor1
                if 'HAND' in o.GetName() or \
                        'Pelvis' in o.GetName() or \
                        'Platform' in o.GetName() or \
                        'Head' in o.GetName():
                    o[c4d.ID_BASEOBJECT_USECOLOR] = 2
                    # o[c4d.ID_CA_JOINT_OBJECT_ICONCOL] = 1
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
        except:
            pass
        c4d.EventAdd()

    def randomPoleColors(self, parentName, randomCol=1, rigColor1=0, rigColor2=0):
        doc = documents.GetActiveDocument()
        try:
            if randomCol == 1:
                rigColor1 = self.get_random_color()  # c4d.Vector(0,2,0)
                rigColor2 = self.get_random_color()  # c4d.Vector(1,0,0)
            parentOb = parentName

            for o in self.selchildren(parentOb, parentOb.GetNext()):
                try:
                    tag = o.GetFirstTag()
                    tag[c4d.ID_CA_IK_TAG_DRAW_POLE_COLOR] = rigColor2
                except:
                    pass
            c4d.EventAdd()
        except:
            pass

    def randomRigColor(self, parentName, randomCol=1, rigColor1=0, rigColor2=0):
        doc = documents.GetActiveDocument()
        try:
            if randomCol == 1:
                rigColor1 = self.get_random_color()  # c4d.Vector(0,2,0)
                rigColor2 = self.get_random_color()  # c4d.Vector(1,0,0)
            parentOb = parentName
            self.IKMobjList = []
            for o in self.selchildren(parentOb, parentOb.GetNext()):
                o[c4d.ID_BASEOBJECT_USECOLOR] = 2

                if "Head" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Neck" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Chest" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = (rigColor2 * 0.9) + (rigColor1 * 0.1)
                if "Spine" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = (rigColor2 * 0.7) + (rigColor1 * 0.3)
                if "Abdomen" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = (rigColor2 * 0.7) + (rigColor1 * 0.3)
                if "Spine2" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = (rigColor2 * 0.7) + (rigColor1 * 0.3)
                if "Collar" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Arm" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "ForeArm" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Hand" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2

                if "Index" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Middle" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Ring" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Pink" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Thumb" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2

                if "Finger" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Thumb" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2

                if "Pelvis" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = (rigColor2 * 0.2) + (rigColor1 * 0.8)

                if "LegUpper" in o.GetName() or "jUpLeg" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor1 * 0.7
                if "LegLower" in o.GetName() or "jLeg" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor1 * 0.6
                if "Foot" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor1 * 0.3
                if "Toes" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor1 * 0.3
                if "ToesEnd" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor1 * 0.2
            c4d.EventAdd()
        except Exception as e:
            print(e)
            # pass


class IKMAXFastAttach(c4d.gui.GeDialog):
    dir, file = os.path.split(__file__)  # Gets the plugin's directory
    LogoFolder_Path = os.path.join(dir, 'res')  # Adds the res folder to the path
    LogoFolder_PathImgs = os.path.join(LogoFolder_Path, 'imgs')  # Adds the res folder to the path

    img_fa_head = os.path.join(LogoFolder_PathImgs, 'fa_head.png')
    img_fa_neck = os.path.join(LogoFolder_PathImgs, 'fa_neck.png')
    img_fa_chest = os.path.join(LogoFolder_PathImgs, 'fa_chest.png')
    img_fa_foot = os.path.join(LogoFolder_PathImgs, 'fa_foot.png')
    img_fa_jointV = os.path.join(LogoFolder_PathImgs, 'fa_jointV.png')
    img_fa_pelvis = os.path.join(LogoFolder_PathImgs, 'fa_pelvis.png')
    img_fa_spine = os.path.join(LogoFolder_PathImgs, 'fa_spine.png')
    img_fa_handL = os.path.join(LogoFolder_PathImgs, 'fa_hand_L.png')
    img_fa_handR = os.path.join(LogoFolder_PathImgs, 'fa_hand_R.png')

    jointPelvis = 'naaa'

    PREFFIX = ''
    MODEL = ''

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
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_ROUND)  # Sets the border to look like a button
        if presetLook == "Preset0":
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE)  # Sets the border to look like a button
        if presetLook == "Preset1":
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE)  # Sets the border to look like a button
            bc.SetBool(c4d.BITMAPBUTTON_BUTTON, False)

        return bc
        # Logo Image #############################################################

    def CreateLayout(self):
        doc = c4d.documents.GetActiveDocument()

        MU = 0.8
        self.SetTitle("FastAttach")

        objs = doc.GetActiveObjects(1)
        objText = ''
        if len(objs) == 1:
            objText = objs[0].GetName()
        if len(objs) > 1:
            objText = str(len(objs)) + ' objects'

        self.MODEL = objs

        self.GroupBegin(11, c4d.BFV_TOP, 1, 1, title="")  # DIALOG MARGINNNNS
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(0 * MU, 10 * MU, 10 * MU, 5 * MU)

        self.GroupBegin(11, c4d.BFV_TOP, 1, 1, title="")  # DIALOG MARGINNNNS
        self.GroupBorderNoTitle(c4d.BORDER_ACTIVE_4)
        self.GroupBorderSpace(20 * MU, 10 * MU, 20 * MU, 10 * MU)
        self.FA_text = self.AddStaticText(self.TEXT_ATTACHOBJ, c4d.BFH_CENTER, 0, 0, name='object')
        self.SetString(self.TEXT_ATTACHOBJ, objText)
        self.GroupEnd()
        self.FA_text2 = self.AddStaticText(self.TEXT_ATTACHOBJ2, c4d.BFH_CENTER, 0, 0, name='will be constrainted to...')

        self.GroupEnd()

        self.GroupBegin(11, c4d.BFV_TOP, 1, 2, title="")  # DIALOG MARGINNNNS
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(10 * MU, 10 * MU, 10 * MU, 30 * MU)

        self.GroupBegin(11, c4d.BFV_TOP, 1, 2, title="")  # HEAD ------------------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(100 * MU, 0 * MU, 100 * MU, 0 * MU)

        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_HEAD, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 60, 70, self.buttonBC("Head", "Preset0"))
        self.btnFA_head.SetImage(self.img_fa_head, True)  # Add the image to the button

        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_NECK, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        self.btnFA_head.SetImage(self.img_fa_neck, True)  # Add the image to the button

        self.GroupEnd()

        self.GroupBegin(11, c4d.BFV_TOP, 3, 1, title="")  # MIDDLE ----------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(0, 0, 0, 0)

        self.GroupBegin(11, c4d.BFV_TOP, 1, 3, title="")  # MIDDLE - ARM LEFT --------------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(10 * MU, 0 * MU, 10 * MU, 0 * MU)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_ARM_RIGHT, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        self.btnFA_head.SetImage(self.img_fa_jointV, True)  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_FOREARM_RIGHT, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        self.btnFA_head.SetImage(self.img_fa_jointV, True)  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_HAND_RIGHT, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        self.btnFA_head.SetImage(self.img_fa_handR, True)  # Add the image to the button
        self.GroupEnd()

        self.GroupBegin(11, c4d.BFV_TOP, 1, 3, title="")  # MIDDLE - SPINES AND CHEST --------------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(10 * MU, 4 * MU, 10 * MU, 4 * MU)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_CHEST, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        self.btnFA_head.SetImage(self.img_fa_chest, True)  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_SPINE, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        self.btnFA_head.SetImage(self.img_fa_spine, True)  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_PELVIS, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        self.btnFA_head.SetImage(self.img_fa_pelvis, True)  # Add the image to the button
        self.GroupEnd()

        self.GroupBegin(11, c4d.BFV_TOP, 1, 3, title="")  # MIDDLE - ARM RIGHT --------------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(10 * MU, 0 * MU, 10 * MU, 0 * MU)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_ARM_LEFT, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        self.btnFA_head.SetImage(self.img_fa_jointV, True)  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_FOREARM_LEFT, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        self.btnFA_head.SetImage(self.img_fa_jointV, True)  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_HAND_LEFT, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        self.btnFA_head.SetImage(self.img_fa_handL, True)  # Add the image to the button
        self.GroupEnd()

        self.GroupEnd()

        self.GroupBegin(11, c4d.BFV_TOP, 2, 1, title="")  # LEGS ----------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(0, 0, 0, 0)

        self.GroupBegin(11, c4d.BFV_TOP, 1, 3, title="")  # LEGS - LEFT --------------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(0 * MU, 0 * MU, 10 * MU, 0)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_UPLEG_LEFT, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        self.btnFA_head.SetImage(self.img_fa_jointV, True)  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_LEG_LEFT, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        self.btnFA_head.SetImage(self.img_fa_jointV, True)  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_FOOT_LEFT, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        self.btnFA_head.SetImage(self.img_fa_foot, True)  # Add the image to the button

        self.GroupEnd()

        self.GroupBegin(11, c4d.BFV_TOP, 1, 3, title="")  # LEGS - RIGHT --------------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(5 * MU, 0 * MU, 5 * MU, 0 * MU)
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_UPLEG_RIGHT, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        self.btnFA_head.SetImage(self.img_fa_jointV, True)  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_LEG_RIGHT, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
        self.btnFA_head.SetImage(self.img_fa_jointV, True)  # Add the image to the button
        self.btnFA_head = self.AddCustomGui(self.BUTTON_ATTACH_FOOT_RIGHT, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Head", "Preset0"))
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

                        if 'Constraint' in tag.GetName():
                            answer = gui.MessageDialog('Object >>>  ' + obj.GetName() + '  <<< already constrainted.\nOverwrite constraint?', c4d.GEMB_YESNO)
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
        jointSelected = ''

        print('asdasd')
        print(self.jointPelvis)
        print('-------')

        if id == self.BUTTON_ATTACH_HEAD:
            jointSelected = 'jHead'
        if id == self.BUTTON_ATTACH_NECK:
            jointSelected = 'jNeck'
        if id == self.BUTTON_ATTACH_CHEST:
            jointSelected = 'jChest'
        if id == self.BUTTON_ATTACH_SPINE:
            jointSelected = 'jSpine'
        if id == self.BUTTON_ATTACH_PELVIS:
            jointSelected = 'jPelvis'

        if id == self.BUTTON_ATTACH_ARM_LEFT:
            jointSelected = 'jArm'
        if id == self.BUTTON_ATTACH_FOREARM_LEFT:
            jointSelected = 'jForeArm'
        if id == self.BUTTON_ATTACH_HAND_LEFT:
            jointSelected = 'jHand'

        if id == self.BUTTON_ATTACH_UPLEG_LEFT:
            jointSelected = 'jUpLeg'
        if id == self.BUTTON_ATTACH_LEG_LEFT:
            jointSelected = 'jLeg'
        if id == self.BUTTON_ATTACH_FOOT_LEFT:
            jointSelected = 'jFoot'

        if id == self.BUTTON_ATTACH_ARM_RIGHT:
            jointSelected = 'jArm___R'
        if id == self.BUTTON_ATTACH_FOREARM_RIGHT:
            jointSelected = 'jForeArm___R'
        if id == self.BUTTON_ATTACH_HAND_RIGHT:
            jointSelected = 'jHand___R'

        if id == self.BUTTON_ATTACH_UPLEG_RIGHT:
            jointSelected = 'jUpLeg___R'
        if id == self.BUTTON_ATTACH_LEG_RIGHT:
            jointSelected = 'jLeg___R'
        if id == self.BUTTON_ATTACH_FOOT_RIGHT:
            jointSelected = 'jFoot___R'

        objParent = ''
        joints = ikmaxUtils().iterateObjChilds(self.jointPelvis)
        if '___R' in jointSelected:
            for j in joints:
                if jointSelected in j.GetName() and '___R' in j.GetName():
                    objParent = j
        else:
            for j in joints:
                if jointSelected in j.GetName() and '___R' not in j.GetName():
                    objParent = j
        objChild = self.MODEL


        if len(objChild) == 1:
            objChild = self.MODEL[0]
            if self.removeConstraint(objChild) == 1:
                ikmGenerator().constraintObj(objChild, objParent, 'PARENT', 0)
                c4d.CallCommand(12113, 12113)  # Deselect All
                c4d.EventAdd()
                self.Close()

        if len(objChild) > 1:
            for obj in objChild:
                if self.removeConstraint(obj) == 1:
                    ikmGenerator().constraintObj(obj, objParent, 'PARENT', 0)
                    c4d.EventAdd()
            c4d.CallCommand(12113, 12113)  # Deselect All
            c4d.EventAdd()
            self.Close()

        c4d.EventAdd()

        return True


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

    LogoFolder_Path = os.path.join(dir, 'res')  # Adds the res folder to the path
    LogoFolder_PathIcons = os.path.join(LogoFolder_Path, 'icons')  # Adds the res folder to the path
    LogoFolder_PathImgs = os.path.join(LogoFolder_Path, 'imgs')  # Adds the res folder to the path

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
    img_adjustGuides = os.path.join(LogoFolder_PathImgs, 'adjustMainGuides.png')

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

    img_COMPLETE_GUIDES = os.path.join(LogoFolder_PathImgs, 'completeGuides.jpg')
    img_COMPLETE_GUIDESADJUST = os.path.join(LogoFolder_PathImgs, 'guidesAdjust.jpg')
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
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_ROUND)  # Sets the border to look like a button
        if presetLook == "Preset0":
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE)  # Sets the border to look like a button
        if presetLook == "Preset1":
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE)  # Sets the border to look like a button
            bc.SetBool(c4d.BITMAPBUTTON_BUTTON, False)

        return bc
        # Logo Image #############################################################

    def checkVer(self):
        caca = c4d.GetC4DVersion()
        if caca > 23500:
            gui.MessageDialog('Cinema4D version not supported by this DazToC4D version.\nVisit 3DtoAll for update or news.', c4d.GEMB_OK)
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

        self.GroupBegin(11, c4d.BFH_SCALEFIT, 1, 1, title="Character Mesh: ")  # ----------------------------------------------------------
        self.GroupBorder(c4d.BORDER_GROUP_IN)
        self.GroupBorderSpace(10, 5, 10, 5)

        self.LinkBox = self.AddCustomGui(self.IDC_LINKBOX_1, c4d.CUSTOMGUI_LINKBOX, 'Character Mesh', c4d.BFH_SCALEFIT, 350, 0)
        self.LinkBox.SetLink(dazToC4Dutils().getDazMesh())

        meshObj = self.LinkBox.GetLink()

        if DazToC4D().findIK() == 1:
            if meshObj:
                dazJoint = getJointFromSkin(meshObj, 'hip')
                self.jointPelvis = getJointFromConstraint(dazJoint)
                self.dazIkmControls = getJointFromConstraint(self.jointPelvis).GetUp()
                IKMAXFastAttach.jointPelvis = self.jointPelvis


        self.GroupEnd()


        self.GroupBegin(11, c4d.BFH_CENTER, 1, 1, title="AAAAAA")  #-----------Main Group
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(15, 5, 15, 5)



        self.GroupBegin(11, c4d.BFH_SCALEFIT, 1, 1, title="AAAAAA")  #-----------Main Group
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(15, 5, 15, 5)

        self.GroupBegin(11, c4d.BFH_SCALEFIT, 1, 1, title="")  #-----------Main Group
        self.GroupBorderNoTitle(c4d.BORDER_GROUP_OUT)
        self.GroupBorderSpace(15, 5, 15, 5)

        self.AddCheckbox(208,c4d.BFH_LEFT, 0, 0, "Reduce (similar) materials on import")
        if dazReduceSimilar == True:
            self.SetBool(208, True)
        else:
            self.SetBool(208, False)

        self.AddCheckbox(209,c4d.BFH_LEFT, 0, 0, "Keep facial morphs only")

        self.GroupEnd()
        self.GroupEnd()

        self.GroupBegin(11, c4d.BFH_CENTER, 8, 1, title="Rig Display: ")  # ----------------------------------------------------------
        self.GroupBorder(c4d.BORDER_GROUP_OUT)
        self.GroupBorderSpace(10, 5, 12, 5)

        self.LogoButton10 = self.AddCustomGui(self.BUTTON_RIG_SHOW, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("<b>Show/Hide Rig</b>", "Preset0"))
        self.LogoButton10.SetImage(self.img_r_hideshow, True)  # Add the image to the button

        self.LogoButton11 = self.AddCustomGui(self.BUTTON_RIG_MODE, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("<b>Rig Display Mode</b><br>Switch between standard and<br>box lines display style", "Preset0"))
        self.LogoButton11.SetImage(self.img_r_box, True)  # Add the image to the button

        self.AddColorField(self.BUTTON_COL1, c4d.BFH_CENTER, 20, 20, c4d.DR_COLORFIELD_NO_SCREENPICKER | c4d.DR_COLORFIELD_NO_SWATCHES | c4d.DR_COLORFIELD_NO_MIXER | c4d.DR_COLORFIELD_NO_MODE_BUTTONS | c4d.DR_COLORFIELD_NO_COLORWHEEL | c4d.DR_COLORFIELD_NO_BRIGHTNESS | c4d.DR_COLORFIELD_NO_COLOR)
        self.AddColorField(self.BUTTON_COL2, c4d.BFH_CENTER, 20, 20, c4d.DR_COLORFIELD_NO_SCREENPICKER | c4d.DR_COLORFIELD_NO_SWATCHES | c4d.DR_COLORFIELD_NO_MIXER | c4d.DR_COLORFIELD_NO_MODE_BUTTONS | c4d.DR_COLORFIELD_NO_COLORWHEEL | c4d.DR_COLORFIELD_NO_BRIGHTNESS | c4d.DR_COLORFIELD_NO_COLOR)
        self.AddColorField(self.BUTTON_COL3, c4d.BFH_CENTER, 20, 20, c4d.DR_COLORFIELD_NO_SCREENPICKER | c4d.DR_COLORFIELD_NO_SWATCHES | c4d.DR_COLORFIELD_NO_MIXER | c4d.DR_COLORFIELD_NO_MODE_BUTTONS | c4d.DR_COLORFIELD_NO_COLORWHEEL | c4d.DR_COLORFIELD_NO_BRIGHTNESS | c4d.DR_COLORFIELD_NO_COLOR)
        self.AddColorField(self.BUTTON_COL4, c4d.BFH_CENTER, 20, 20, c4d.DR_COLORFIELD_NO_SCREENPICKER | c4d.DR_COLORFIELD_NO_SWATCHES | c4d.DR_COLORFIELD_NO_MIXER | c4d.DR_COLORFIELD_NO_MODE_BUTTONS | c4d.DR_COLORFIELD_NO_COLORWHEEL | c4d.DR_COLORFIELD_NO_BRIGHTNESS | c4d.DR_COLORFIELD_NO_COLOR)
 
        self.SetColorField(self.BUTTON_COL1, c4d.Vector(1.0, 0.0, 0.4), 1, 1, 1)
        self.SetColorField(self.BUTTON_COL2, c4d.Vector(0.4, 0.8, 1.0), 1, 1, 1)
        self.SetColorField(self.BUTTON_COL3, c4d.Vector(0.0, 1.0, 0.5), 1, 1, 1)
        self.SetColorField(self.BUTTON_COL4, c4d.Vector(1.0, 0.9, 0.0), 1, 1, 1)

        self.LogoButton12 = self.AddCustomGui(self.BUTTON_COL_SET, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("<b>Set Rig and IK Colors</b><br>Sets specified colors to<br>Rig and IK Controls", "Preset0"))
        self.LogoButton12.SetImage(self.img_setColor, True)  # Add the image to the button

        self.LogoButton13 = self.AddCustomGui(self.BUTTON_COL_RANDOM, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("<b>Random Rig Colors</b><br>Assign random colors<br>to the Rig joints", "Preset0"))
        self.LogoButton13.SetImage(self.img_r_randomcolor, True)  # Add the image to the button

        self.GroupEnd()

        self.GroupBegin(11, c4d.BFH_CENTER, 6, 1, title="Extra: ")  # ----------------------------------------------------------
        self.GroupBorder(c4d.BORDER_GROUP_OUT)
        self.GroupBorderSpace(13, 5, 14, 5)

        self.LogoButton16 = self.AddCustomGui(self.BUTTON_MODEL_MIRRORPOSE, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("<b>Mirror Joints pose before Auto-IK</b>", "Preset0"))
        self.LogoButton16.SetImage(self.img_char_mirror, True)  # Add the image to the button

        self.LogoButton16 = self.AddCustomGui(self.BUTTON_MODEL_XRAY, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("<b>X-Ray Mode</b>", "Preset0"))
        self.LogoButton16.SetImage(self.img_xray, True)  # Add the image to the button

        self.LogoButton16 = self.AddCustomGui(self.BUTTON_MODEL_FREEZE, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("<b>Lock/Unlock</b>", "Preset0"))
        self.LogoButton16.SetImage(self.img_lock, True)  # Add the image to the button
        global guiDazToC4DLayerLockButton
        guiDazToC4DLayerLockButton = self.LogoButton16

        self.LogoButton15 = self.AddCustomGui(self.BUTTON_EXTRA_FIGURE, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("<b>Reset to Orig Pose</b>", "Preset0"))
        self.LogoButton15.SetImage(self.img_ani_mode, True)  # Add the image to the button

        self.LogoButton18 = self.AddCustomGui(self.BUTTON_EXTRA_ATTACH, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("<b>Fast-Attach</b><br>Attach object/s easy and<br>fast to body part", "Preset0"))
        self.LogoButton18.SetImage(self.img_QuickAttach, True)  # Add the image to the button

        self.GroupEnd()

        self.GroupEnd() #-------------------------------------Main Group

        self.AddSeparatorV(100, c4d.BFH_FIT)

        self.GroupEnd()

        layer = ikmaxUtils().getLayer('IKM_Lock')
        if layer != None:
            try:
                layer_data = layer.GetLayerData(doc)
                lockValue = layer_data['locked']
                if lockValue == True:
                    self.LogoButton16.SetImage(self.img_lockON, True)
            except:
                print('Layer test skipped...')

        return True

    def Command(self, id, msg):

        EXTRADialog().checkVer()
        # id is the id number of the object the command was issued from, usually a button
        if id == 208:
            #Reduce Materials on Import
            global dazReduceSimilar
            dazReduceSimilar = self.GetBool(208)
            return 0

        if id == self.BUTTON_MODEL_MIRRORPOSE:
            DazToC4D().mirrorPose()
            return 0

        obj = self.LinkBox.GetLink()
        if obj == None and id != self.BUTTON_MODEL_FREEZE:
            gui.MessageDialog('Select your Character object first', c4d.GEMB_OK)

            return 0

        # MESH SELECT
        if id == self.IDC_LINKBOX_1:
            doc = c4d.documents.GetActiveDocument()
            meshObj = self.LinkBox.GetLink()
            dazJoint = getJointFromSkin(meshObj, 'hip')
            self.jointPelvis = getJointFromConstraint(dazJoint)
            self.dazIkmControls =  getJointFromConstraint(self.jointPelvis).GetUp()
            IKMAXFastAttach.jointPelvis = self.jointPelvis

        # GUIDES
        if DazToC4D().findIK() == 1:

            if id == self.BUTTON_RESET:
                caca = ikmaxUtils().removeStuff()
                if caca is 1:
                    self.imgSelect.SetImage(self.img_select, True)  # Add the image to the button
                    self.LogoButton3.SetImage(self.img_RigStart, True)  # Add the image to the button
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
                        answer = gui.MessageDialog('Object rotations needs to be reseted. Do you want to proceed?', c4d.GEMB_YESNO)
                        if answer == 6:
                            objFixed = ikmaxUtils().resetObj(obj)
                            self.LinkBox.SetLink(objFixed)
                            EXTRADialog.MASTERSIZE = objHeight = (objFixed.GetRad()[1] * objFixed[c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_Y]) * 2
                            # Start main guides and placement...
                            self.startGuides(objFixed)
                    else:
                        self.startGuides(obj)

            if id == self.BUTTON_HELP:
                dialog = IKMAXhelp()
                dialog.Open(dlgtype=c4d.DLG_TYPE_MODAL, defaultw=200, defaulth=150, xpos=-1, ypos=-1)


            # AUTO-RIG
            if id == self.BUTTON_REMOVE_RIG:
                answer = gui.MessageDialog('Remove RIG?', c4d.GEMB_YESNO)
                if answer == 6:
                    ikmaxUtils().removeRIGandMirrorsandGuides()

                    self.LogoButton9.SetImage(self.img_AutoIK_NO, True)
                    self.LogoButton14.SetImage(self.img_AutoSkin_NO, True)
                    self.imgSelect.SetImage(self.img_adjustGuides, True)

            if id == self.BUTTON_MIRROR:
                doc = documents.GetActiveDocument()
                ikControls = doc.SearchObject(EXTRADialog.PREFFIX + 'IKM_Controls')
                jointsRoot = doc.SearchObject(EXTRADialog.PREFFIX + 'jPelvis')
                answer = 0
                if ikControls:
                    answer = gui.MessageDialog('Remove IK to make rig changes/mirror rig, etc.\nWhen happy generate Auto-IK again.\n\nRemove IK now and mirror RIG?', c4d.GEMB_YESNO)
                    if answer == 6:
                        ikmaxUtils().removeIK()
                        print('Removing IK...')

                if ikControls == None or answer == 6:
                    suffix = "___R"
                    objArm = doc.SearchObject(EXTRADialog.PREFFIX + 'jCollar')
                    objLeg = doc.SearchObject(EXTRADialog.PREFFIX + 'jUpLeg')
                    ikmaxUtils().mirrorObjects(objArm, suffix)
                    ikmaxUtils().mirrorObjects(objLeg, suffix)
                doc.FlushUndoBuffer()

            if id == self.BUTTON_IK_COL_RANDOM:
                obj = self.LinkBox.GetLink()
                objName = obj.GetName().replace('.Shape','') + '_'
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
                    firstTAG =  obj.GetFirstTag()
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

                obj = self.jointPelvis

                getDisplayTAG(obj)
                c4d.EventAdd()

            if id == self.BUTTON_COL_RANDOM:
                print('random colors')

                randomColors().randomRigColor(self.jointPelvis)
                print(self.dazIkmControls.GetName())
                randomColors().randomNullsColor(self.dazIkmControls)
                randomColors().randomPoleColors(self.jointPelvis)

            if id == self.BUTTON_COL_SET:
                obj = self.LinkBox.GetLink()
                objName = obj.GetName().replace('.Shape','') + '_'

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

                answer = gui.MessageDialog('This is an experimental feature, you may want to save your scene first. Do you want to proceed?', c4d.GEMB_YESNO )
                if answer != 6:
                    return 0

                selected = doc.GetActiveObjects(0)

                if len(selected) != 2:
                    gui.MessageDialog('You need to select 2 eyes/objects o.O!', c4d.GEMB_OK)
                    allOk = 0
                if ikmaxUtils().checkIfExist('jHead') != 1:
                    gui.MessageDialog('No rig detected, first you need to\ngenerate a rig for your Character', c4d.GEMB_OK)
                    allOk = 0

                if allOk == 1:
                    ojo1 = selected[0]
                    ojo2 = selected[1]

                    headJoint = doc.SearchObject(EXTRADialog.PREFFIX + 'jHead')
                    joints = doc.SearchObject(EXTRADialog.PREFFIX + 'jPelvis')

                    obj1 = ikmaxUtils().makeNull('lEye_ctrl', ojo1)
                    obj2 = ikmaxUtils().makeNull('rEye_ctrl', ojo2)

                    objParent = ojo1.GetUp()
                    eyesParentNull = ikmaxUtils().makeNull('EyesParent', headJoint)
                    eyesGroup = ikmaxUtils().makeNull('EyesParent', headJoint)
                    eyesGroup2 = ikmaxUtils().makeNull('EyesParent', headJoint)

                    obj1.SetAbsScale(c4d.Vector(1,1,1))
                    obj2.SetAbsScale(c4d.Vector(1,1,1))

                    eyesParentNull.SetName(EXTRADialog.PREFFIX + 'Eyes-LookAt')
                    eyesGroup.SetName(EXTRADialog.PREFFIX + 'EyesGroup')

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
                    objMasterEyes.SetName(EXTRADialog.PREFFIX + 'EyesLookAtGroup')
                    objMasterEyes.SetAbsScale(c4d.Vector(1,1,1))

                    nullStyle(obj1)
                    nullStyle(obj2)
                    nullStyleMaster(objMasterEyes)

                    ikmGenerator().constraintObj(ojo1, obj1, 'AIM', 0)
                    ikmGenerator().constraintObj(ojo2, obj2, 'AIM', 0)

                    makeChild(obj1, objMasterEyes)
                    makeChild(obj2, objMasterEyes)
                    makeChild(objMasterEyes, eyesParentNull)



                    obj1.SetAbsRot(c4d.Vector(0))
                    obj2.SetAbsRot(c4d.Vector(0))

                    ikmGenerator().constraintObj(eyesParentNull, headJoint, '', 0)

                    eyesParentNull.InsertAfter(joints)

                    ikmaxUtils().freezeChilds(EXTRADialog.PREFFIX + "Eyes-LookAt")
                    ikmaxUtils().freezeChilds(EXTRADialog.PREFFIX + "EyesLookAtGroup")

                    c4d.EventAdd()
                    c4d.CallCommand(12288, 12288)  # Frame All

            if id == self.BUTTON_EXTRA_ATTACH:
                doc = documents.GetActiveDocument()

                if len(doc.GetActiveObjects(1)) == 0:
                    gui.MessageDialog('Select object(s) that you want to attach to joints')
                    return 0
                else:
                    dialog = IKMAXFastAttach()
                    dialog.Open(dlgtype=c4d.DLG_TYPE_MODAL, defaultw=200, defaulth=150, xpos=-1, ypos=-1)



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
        c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD   | c4d.DRAWFLAGS_STATICBREAK)
        c4d.DrawViews()
        # gui.MessageDialog('Popup')
        # guiDazToC4Dloading.Close()
        # guiDazToC4Dloading.KillEvents()
        # print(guiDazToC4Dloading)
        return True

    def Command(self, id, msg):
        print ('OOOOOOOOOOOOOOOOOOOOO')
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
    daztoC4D_Folder = os.path.join(dir, 'res')  # Adds the res folder to the path
    daztoC4D_FolderImgs = os.path.join(daztoC4D_Folder, 'imgs')  # Adds the res folder to the path

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
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_ROUND)  # Sets the border to look like a button
        if presetLook == "Preset0":
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE)  # Sets the border to look like a button
        if presetLook == "Preset1":
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE)  # Sets the border to look like a button
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

        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0, name=r'To transfer from DAZ Studio to Cinema 4D you are using a Temp folder.')
        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0, name=r'Now is a good time to save the scene+textures to another location.')

        self.GroupEnd()  # END ///////////////////////////////////////////////

        self.GroupBegin(10000, c4d.BFH_CENTER, 2, title='Import:')
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(10, 5, 10, 5)

        self.LogoButton6 = self.AddCustomGui(self.BUTTON_SAVE, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("", "Preset0"))
        self.LogoButton6.SetImage(self.img_btnSave, True)  # Add the image to the button

        self.LogoButton6 = self.AddCustomGui(self.BUTTON_CANCEL, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("", "Preset0"))
        self.LogoButton6.SetImage(self.img_btnLater, True)  # Add the image to the button

        # self.AddButton(self.BUTTON_SAVE, c4d.BFV_MASK, initw=150, inith=35, name="Save Now!")
        # self.AddButton(self.BUTTON_CANCEL, c4d.BFV_MASK, initw=150, inith=35, name="*Later")
        self.GroupEnd()  # END ///////////////////////////////////////////////


        self.AddSeparatorH(c4d.BFV_SCALEFIT)  # Separator H

        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0, name=r'*If you save later remember to save using File\Save Project with Assets...')
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

        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0, name=r'Importing. Please Wait...')
        self.AddSeparatorH(280,c4d.BFH_SCALEFIT)  # Separator H

        self.GroupEnd()

        return True

    def Command(self, id, msg):

        if id == self.BUTTON_SAVE:
            c4d.CallCommand(12255, 12255)  # Save Project with Assets...

        if id == self.BUTTON_CANCEL:
            self.Close()

        return True

class guiDazToC4DMain(gui.GeDialog):
    
    dialog = None
    extraDialog = None
    
    BUTTON_CONFIG = 923123
    BUTTON_AUTO_IMPORT_FIG = 923124
    BUTTON_AUTO_IMPORT_PROP = 923131
    BUTTON_CONVERT_MATERIALS = 923126
    BUTTON_CONFIG = 923127
    BUTTON_TEMP = 923128
    BUTTON_HELP = 923129
    BUTTON_AUTO_IK = 923130


    MY_BITMAP_BUTTON = 9353535

    LogoButton = ''

    dir, file = os.path.split(__file__)  # Gets the plugin's directory
    daztoC4D_Folder = os.path.join(dir, 'res')  # Adds the res folder to the path
    
    # Set Images for UI
    img_d2c4dLogo = os.path.join(daztoC4D_Folder, 'd2c4d_logo.png')
    img_loading = os.path.join(daztoC4D_Folder, 'd2c4d_loading.png')
    img_d2c4dHelp = os.path.join(daztoC4D_Folder, 'd2c4d_help.png')
    img_btnAutoImport_FIG = os.path.join(daztoC4D_Folder, 'btnGenesisImport.png')
    img_btnAutoImportOff_FIG = os.path.join(daztoC4D_Folder, 'btnGenesisImport.png')
    img_btnAutoImport_PROP = os.path.join(daztoC4D_Folder, 'btnPropImport.png')
    img_btnAutoImportOff_PROP = os.path.join(daztoC4D_Folder, 'btnPropImport.png')
    img_btnManualImport = os.path.join(daztoC4D_Folder, 'btnImport.png')
    img_btnManualImportOff = os.path.join(daztoC4D_Folder, 'btnImport0.png')
    img_btnConvertMaterials = os.path.join(daztoC4D_Folder, 'btnConvertMaterials.png')
    img_btnConvertMaterialsOff = os.path.join(daztoC4D_Folder, 'btnConvertMaterials0.png')
    img_btnAutoIK = os.path.join(daztoC4D_Folder, 'btnAutoIK.png')
    img_btnAutoIKOff = os.path.join(daztoC4D_Folder, 'btnAutoIK0.png')
    img_btnConfig = os.path.join(daztoC4D_Folder, 'btnConfig.png')


    def __init__(self):
        try:
            self.AddGadget(c4d.DIALOG_NOMENUBAR, 0)#disable menubar
        except:
            pass

    def buttonsChangeState(self, btnState):
            c4d.StatusClear()
            c4d.EventAdd()
            c4d.EventAdd(c4d.EVENT_FORCEREDRAW)
            c4d.DrawViews(c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW | c4d.DRAWFLAGS_NO_THREAD  | c4d.DRAWFLAGS_STATICBREAK)
            c4d.DrawViews(c4d.EVMSG_CHANGEDSCRIPTMODE)
            c4d.EventAdd(c4d.EVENT_ANIMATE)
            c4d.StatusClear()
            if btnState == False:
                self.main_logo.SetImage(self.img_loading, False)  # Add the image to the button
                try:
                    self.main_logo.LayoutChanged()
                    self.main_logo.Redraw()
                except:
                    print("DazToC4D: LayoutChanged skip...")

                self.auto_import_fig_but.SetImage(self.img_btnAutoImportOff_FIG, False)  # Add the image to the button
                self.auto_import_prop_but.SetImage(self.img_btnAutoImportOff_PROP, False)  # Add the image to the button
                self.convert_mat_but.SetImage(self.img_btnConvertMaterialsOff, False)  # Add the image to the button
                self.auto_ik_but.SetImage(self.img_btnAutoIKOff, False)  # Add the image to the button

            if btnState == True:
                self.main_logo.SetImage(self.img_d2c4dLogo, False)  # Add the image to the button
                self.auto_import_fig_but.SetImage(self.img_btnAutoImport_FIG, False)  # Add the image to the button
                self.auto_import_prop_but.SetImage(self.img_btnAutoImport_PROP, False)  # Add the image to the button
                self.convert_mat_but.SetImage(self.img_btnConvertMaterials, False)  # Add the image to the button
                self.auto_ik_but.SetImage(self.img_btnAutoIK, False)  # Add the image to the button

            bc = c4d.BaseContainer()
            c4d.gui.GetInputState(c4d.BFM_INPUT_MOUSE, c4d.BFM_INPUT_CHANNEL, bc)

            return True

    def buttonBC(self, tooltipText="", presetLook=""):
        # Logo Image #############################################################
        bc = c4d.BaseContainer()  # Create a new container to store the button image
        bc.SetBool(c4d.BITMAPBUTTON_BUTTON, True)
        bc.SetString(c4d.BITMAPBUTTON_TOOLTIP, tooltipText)

        if presetLook == "":
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_ROUND)  # Sets the border to look like a button
        if presetLook == "Preset0":
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE)  # Sets the border to look like a button
        if presetLook == "Preset1":
            bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_NONE)  # Sets the border to look like a button
            bc.SetBool(c4d.BITMAPBUTTON_BUTTON, False)

        return bc
        # Logo Image #############################################################


    def CreateLayout(self):
        self.SetTitle('DazToC4D v1.1.2')
        self.AddSeparatorH(c4d.BFV_SCALEFIT)  # Separator H

        # Logo Image #############################################################
        bc = c4d.BaseContainer()  # Create a new container to store the button image
        bc.SetInt32(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_ROUND)  # Sets the border to look like a button
        self.LogoButton = self.AddCustomGui(self.MY_BITMAP_BUTTON, c4d.CUSTOMGUI_BITMAPBUTTON, "Logo", c4d.BFH_CENTER, 0, 0, bc)
        self.LogoButton.SetImage(self.img_d2c4dLogo, False)  # Add the image to the button
    
        self.main_logo = self.LogoButton
        print('**********************')
        print(self.LogoButton)
        print('**********************')

        # Logo Image #############################################################

        # Import
        self.GroupBegin(10000, c4d.BFH_CENTER, 1, title='')
        self.GroupBorderNoTitle(c4d.BORDER_OUT)
        self.GroupBorderSpace(0, 0, 0, 0)

        self.GroupBegin(10000, c4d.BFH_SCALEFIT, 5)  # BEGIN ----------------------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(12, 5, 10, 5)

        self.LogoButton6 = self.AddCustomGui(self.BUTTON_CONFIG, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("", "Preset0"))
        self.LogoButton6.SetImage(self.img_btnConfig, True)  # Add the image to the button

        self.AddSeparatorV(0, c4d.BFV_SCALEFIT)  # Separator V

        self.GroupBegin(10000, c4d.BFH_CENTER, 1, title='')
        self.GroupBorderNoTitle(c4d.BORDER_OUT)
        self.GroupBorderSpace(0, 0, 0, 0)
        self.LogoButton6 = self.AddCustomGui(self.BUTTON_AUTO_IMPORT_FIG, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("", "Preset0"))
        self.LogoButton6.SetImage(self.img_btnAutoImportOff_FIG, True)  # Add the image to the button
        self.auto_import_fig_but = self.LogoButton6

        self.LogoButton7 = self.AddCustomGui(self.BUTTON_AUTO_IMPORT_PROP, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("", "Preset0"))
        self.LogoButton7.SetImage(self.img_btnAutoImportOff_PROP, True)  # Add the image to the button
        self.auto_import_prop_but = self.LogoButton7

        self.GroupEnd()  # END ///////////////////////////////////////////////
        self.AddSeparatorV(0, c4d.BFV_SCALEFIT)  # Separator V


        self.LogoButton6 = self.AddCustomGui(self.BUTTON_AUTO_IK, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("", "Preset0"))
        self.LogoButton6.SetImage(self.img_btnAutoIK, True)  # Add the image to the button
        self.auto_ik_but = self.LogoButton6


        self.GroupEnd()  # END ///////////////////////////////////////////////
        self.GroupEnd()  # END ///////////////////////////////////////////////
    
        self.GroupEnd()  # END ///////////////////////////////////////////////

        self.AddSeparatorH(c4d.BFV_SCALEFIT)  # Separator H

        self.GroupBegin(10000, c4d.BFH_SCALEFIT, 1, title='Materials:') #MATERIALS BEGIN -----------------------------------------------------
        self.GroupBorder(c4d.BORDER_OUT)
        self.GroupBorderSpace(10, 0, 10, 10)

        self.GroupBegin(10000, c4d.BFH_SCALEFIT, 3)  # BEGIN ----------------------
        self.GroupBorderNoTitle(c4d.BORDER_NONE)
        self.GroupBorderSpace(20, 5, 20, 5)

        self.LogoButton6 = self.AddCustomGui(self.BUTTON_CONVERT_MATERIALS, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("", "Preset0"))
        self.LogoButton6.SetImage(self.img_btnConvertMaterials, True)  # Add the image to the button
        self.convert_mat_but = self.LogoButton6
        self.AddSeparatorV(0, c4d.BFV_SCALEFIT)  # Separator V
        self.AddComboBox(2001, c4d.BFH_SCALEFIT, 100, 15, False)
        self.AddChild(2001, 0, ' - Select -')
        self.AddChild(2001, 1, 'V-Ray')
        self.AddChild(2001, 2, 'Redshift')
        self.AddChild(2001, 3, 'Octane')

        self.GroupEnd()  # END ///////////////////////////////////////////////


        self.GroupBegin(10000, c4d.BFH_SCALEFIT, 2, title='Global Skin Parameters:')  # BEGIN ----------------------
        self.GroupBorder(c4d.BORDER_THIN_OUT)
        self.GroupBorderSpace(20, 5, 20, 5)

        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0, name='Specular Weight:')
        self.AddEditSlider(17524, c4d.BFH_SCALEFIT, initw=40, inith=0)
        self.SetInt32(17524, value=20, min=0, max=100)

        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0, name='Specular Roughtness:')
        self.AddEditSlider(17525, c4d.BFH_SCALEFIT, initw=40, inith=0)
        self.SetInt32(17525, value=57, min=0, max=100)

        self.GroupEnd()  # END ///////////////////////////////////////////////

        self.GroupBegin(10001, c4d.BFH_CENTER, 2, title="Redshift Settings: ")
        self.GroupBorder(c4d.BORDER_THIN_OUT)
        self.GroupBorderSpace(20, 5, 20, 5)
        self.AddStaticText(99, c4d.BFH_CENTER, 0, 0, name='Choose Bump Type:')
        self.AddComboBox(2002,c4d.BFH_SCALEFIT, 0, 0, False)
        self.AddChild(2002, 0, 'Tangent-Space Normal')
        self.AddChild(2002, 1, 'Bump/Height Field')
        self.AddChild(2002, 2, 'Object-Space Normal')
        self.GroupEnd()

        self.GroupEnd() # MATERIALS END ///////////////////////////////////////////////

        self.AddSeparatorH(c4d.BFV_SCALEFIT)  # Separator H

        self.GroupBegin(10000, c4d.BFH_CENTER, 2, title='Global Skin Parameters:')  # BEGIN ----------------------
        self.GroupBegin(10001, c4d.BFH_CENTER, 2, title="Redshift Settings: ")
        self.AddStaticText(99, c4d.BFH_SCALEFIT, 0, 0, name='Copyright(c) 2020. All Rights Reserved.')

        self.LogoButtonHelp = self.AddCustomGui(self.BUTTON_HELP, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_CENTER, 0, 0, self.buttonBC("Help", "Preset0"))
        self.LogoButtonHelp.SetImage(self.img_d2c4dHelp, True)  # Add the image to the button

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

        if id == self.BUTTON_AUTO_IMPORT_FIG:
            DazToC4D().genesisImport()

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
                gui.MessageDialog('No rig found to apply IK, Auto-Import a Figure and try again.', c4d.GEMB_OK)
                return 0
            else:
                if IKFound == True:
                    gui.MessageDialog('IK Already Found, Auto-Import and try again.', c4d.GEMB_OK)
                    return 0
                else:
                    if DazToC4D().findMesh() == False:
                        gui.MessageDialog('No Figure found, Auto-Import a Figure and try again.', c4d.GEMB_OK)
                    else:
                        DazToC4D().checkIfPosedResetPose() #THIS RUNS AUTO-IK !

            self.buttonsChangeState(True)

        if id == self.BUTTON_CONFIG:
            if self.extraDialog != None:
                self.extraDialog.Close()
            if self.extraDialog == None:
                self.extraDialog = EXTRADialog()
                guiDazToC4DExtraDialog = self.extraDialog
            self.extraDialog = EXTRADialog()

            guiDazToC4DExtraDialog = self.extraDialog
            self.extraDialog.Open(dlgtype=c4d.DLG_TYPE_ASYNC, xpos=-1, ypos=-1, defaultw=200, defaulth=150)

            '''

            '''

        if id == self.BUTTON_CONVERT_MATERIALS:
            #CONVERT MATERIAL
            doc = c4d.documents.GetActiveDocument()
            comboRender = self.GetInt32(2001)
            redshiftBumpType = self.GetInt32(2002)
            if comboRender == 0:
                gui.MessageDialog('Please select renderer from the list')

            else:
                if DazToC4D().checkStdMats() == True:
                    return
                else:
                    answer = gui.MessageDialog('::: WARNING :::\n\nNo Undo for this.\nSave your scene first, in case you want to revert changes.\n\nProceed and Convert Materials now?', c4d.GEMB_YESNO)
                    if answer is 6:
                        if comboRender == 1:
                            convertMaterials().convertTo('Vray')
                            c4d.CallCommand(1026375)  # Reload Python Plugins

                        if comboRender == 2:
                            convert_to_redshift = convertToRedshift()
                            convert_to_redshift.getBumpType(redshiftBumpType)
                            convert_to_redshift.execute()
                            DazToC4D().hideEyePolys()
                            c4d.CallCommand(100004766, 100004766)  # Select All
                            c4d.CallCommand(100004767, 100004767)  # Deselect All

                        if comboRender == 3:
                            Materials.Materials().convertToOctane()
                            DazToC4D().hideEyePolys()
                            c4d.CallCommand(100004766, 100004766)  # Select All
                            c4d.CallCommand(100004767, 100004767)  # Deselect All

        if id == self.BUTTON_TEMP:
            if self.dialog == None:
                self.dialog = EXTRADialog()
            self.dialog = EXTRADialog()
            self.dialog.Open(dlgtype=c4d.DLG_TYPE_ASYNC, xpos=-1, ypos=-1, pluginid=103299851, defaultw=200, defaulth=150)

        if id == self.BUTTON_HELP:
            new = 2  # open in a new tab, if possible
            url = "http://www.daz3d.com"
            webbrowser.open(url, new=new)


        return True
