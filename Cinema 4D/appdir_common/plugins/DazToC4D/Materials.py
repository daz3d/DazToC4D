import c4d
import os
import sys

folder = os.path.dirname( __file__ )
if folder not in sys.path: 
    sys.path.insert( 0, folder )

from Utilities import dazToC4Dutils

class Materials:
    # TODO: Very if necessary with Material Rework
    def eyeLashAndOtherFixes(self):
        doc = c4d.documents.GetActiveDocument()
        docMaterials = doc.GetMaterials()
        irisMap = ''
        for mat in docMaterials:  # Lashes fix... Gen2 and maybe others...
            matName = mat.GetName()
            if 'Lashes' in matName:
                try:
                    mat[c4d.MATERIAL_COLOR_SHADER] = None
                except:
                    print('mat skip...')
                    pass
            if 'Iris' in matName:
                try:
                    irisMap = mat[c4d.MATERIAL_COLOR_SHADER][c4d.BITMAPSHADER_FILENAME]
                except:
                    pass

        for mat in docMaterials:  # Iris fix Gen2 and maybe others...
            if mat[c4d.MATERIAL_COLOR_SHADER]:
                if mat[c4d.MATERIAL_COLOR_SHADER].GetType() == 5833:
                    matTexture = mat[c4d.MATERIAL_COLOR_SHADER][c4d.BITMAPSHADER_FILENAME]
                    matName = mat.GetName()
                    if irisMap == matTexture:
                        if 'Sclera' not in matName:
                            mat[c4d.MATERIAL_USE_REFLECTION] = False

        for mat in docMaterials:  # Fix to Tear.. Gen2...
            matName = mat.GetName()
            if 'Tear' in matName:
                mat[c4d.MATERIAL_TRANSPARENCY_COLOR] = c4d.Vector(0.94, 0.94, 0.94)
    

    def reduceMatFix(self):
        doc = c4d.documents.GetActiveDocument()
        myMaterials = doc.GetMaterials()
        matHead = False
        matTorso = False
        matLegs = False
        matHands = False
        for mat in myMaterials:
            # print mat.GetName()
            if 'Torso' in mat.GetName():
                matTorso = mat
            if 'Hands' in mat.GetName():
                matHands = mat
            if 'Legs' in mat.GetName():
                matLegs = mat
            if 'Head' in mat.GetName():
                matHead = mat

        if matTorso == False and matHead != False:
            matHead.SetName('MainSkin')
        if matHands == False and matLegs != False:
            matLegs.SetName('LegsAndArms')

        c4d.EventAdd()

    
    def disableDisplace(self):
        doc = c4d.documents.GetActiveDocument()
        myMaterials = doc.GetMaterials()
        for mat in myMaterials:
            mat[c4d.MATERIAL_USE_DISPLACEMENT] = False

        c4d.EventAdd()

    # TODO: Refactor and Use DTU for Materials
    def convertToOctane(self):
        doc = documents.GetActiveDocument()
        standMats = []

        c4d.CallCommand(300001026, 300001026)  # Deselect All
        sceneMats = doc.GetMaterials()
        for mat in sceneMats:
            matName = mat.GetName()
            if mat.GetType() == 5703:
                standMats.append(mat)
                mat.SetBit(c4d.BIT_ACTIVE)
        c4d.EventAdd()

        if len(standMats) != 0:
            c4d.CallCommand(1029770, 1029770)  # Convert Materials
            c4d.CallCommand(1035351, 1035351)  # Remove Unused Materials
        c4d.CallCommand(300001026, 300001026)  # Deselect All

        doc = c4d.documents.GetActiveDocument()

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

        foundFingerNails = False  # If not, assume is Gneesis3... hide Cornea...

        if findMatName('EyeReflection'):
            figureModel = 'Genesis2'
        if findMatName('FingerNails'):
            figureModel = 'Genesis3'

        # FIX MATERIAL NAMES etc... USE THIS FOR ALL CONVERTIONS NOT JUST OCTANE!
        if findMatName('1_SkinFace') == None and findMatName('1_Nostril') != None:
            findMatName('1_Nostril').SetName('1_SkinFace')
        if findMatName('3_SkinHand') == None and findMatName('3_SkinFoot') != None:
            findMatName('3_SkinFoot').SetName('3_ArmsLegs')
        # ////

        sceneMats = doc.GetMaterials()
        for mat in sceneMats:
            matName = mat.GetName()
            mat[c4d.OCT_MATERIAL_SPECULAR_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
            mat[c4d.OCT_MATERIAL_INDEX] = 2
            
            extraMapGlossyRough = dazToC4Dutils().findTextInFile(matName, 'Glossy_Roughness_Map')
            if extraMapGlossyRough != None:
                # c4d.gui.MessageDialog(extraMapGlossyRough)
                ID_OCTANE_IMAGE_TEXTURE = 1029508
                shd = c4d.BaseShader(ID_OCTANE_IMAGE_TEXTURE)

                mat.InsertShader(shd)
                mat[c4d.OCT_MATERIAL_ROUGHNESS_LINK] = shd
                shd[c4d.IMAGETEXTURE_FILE] = extraMapGlossyRough
                shd[c4d.IMAGETEXTURE_MODE] = 0
                shd[c4d.IMAGETEXTURE_GAMMA] = 2.2
                shd[c4d.IMAGETEX_BORDER_MODE] = 0
                doc.InsertMaterial(mat)
            
            extraMapSpec = dazToC4Dutils().findTextInFile(matName, 'Glossy_Layered_Weight_Map')
            extraMapSpec2 = dazToC4Dutils().findTextInFile(matName, 'spec')
            extraMapGlossy = dazToC4Dutils().findTextInFile(matName, 'Metallicity_Map')
            if extraMapSpec2 != None and extraMapSpec == None:
                extraMapSpec = extraMapSpec2
            if extraMapGlossy != None and extraMapSpec == None:
                extraMapSpec = extraMapGlossy
            if extraMapSpec != None:
                # c4d.gui.MessageDialog(extraMapGlossyRough)
                ID_OCTANE_IMAGE_TEXTURE = 1029508
                shd = c4d.BaseShader(ID_OCTANE_IMAGE_TEXTURE)

                mat.InsertShader(shd)
                mat[c4d.OCT_MATERIAL_SPECULAR_LINK] = shd
                shd[c4d.IMAGETEXTURE_FILE] = extraMapSpec
                shd[c4d.IMAGETEXTURE_MODE] = 0
                shd[c4d.IMAGETEXTURE_GAMMA] = 2.2
                shd[c4d.IMAGETEX_BORDER_MODE] = 0
                doc.InsertMaterial(mat)


            try:
                mat[c4d.OCT_MATERIAL_BUMP_LINK][c4d.IMAGETEXTURE_POWER_FLOAT] = 0.1
            except:
                pass
            try:
                mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = 0.15
            except:
                pass
            try:
                mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.15
            except:
                pass
            # Transp map fix compensation alpha...
            try:
                mat[c4d.OCT_MATERIAL_OPACITY_LINK][c4d.IMAGETEXTURE_POWER_FLOAT] = 1.5
                mat[c4d.OCT_MATERIAL_OPACITY_LINK][c4d.IMAGETEXTURE_GAMMA] = 1.0
                mat[c4d.OCT_MATERIAL_OPACITY_LINK][c4d.IMAGETEXTURE_MODE] = 0
            except:
                pass
            if 'Moisture' in matName or 'Cornea' in matName:
                mat[c4d.OCT_MATERIAL_TYPE] = 2511
                mat[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = 1.0
                mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.0
                mat[c4d.OCT_MAT_USE_BUMP] = False
                mat[c4d.OCT_MATERIAL_INDEX] = 6
                mat[c4d.OCT_MATERIAL_OPACITY_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_OPACITY_FLOAT] = 0.25
                mat[c4d.OCT_MATERIAL_OPACITY_LINK] = None
            if 'Sclera' in matName:
                try:
                    mat[c4d.OCT_MATERIAL_DIFFUSE_LINK][c4d.IMAGETEXTURE_POWER_FLOAT] = 3.0
                    mat[c4d.OCT_MATERIAL_DIFFUSE_LINK][c4d.IMAGETEXTURE_GAMMA] = 2.0
                    mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.0
                except:
                    pass
            if 'Irises' in matName:
                try:
                    mat[c4d.OCT_MATERIAL_DIFFUSE_LINK][c4d.IMAGETEXTURE_POWER_FLOAT] = 2.0
                    mat[c4d.OCT_MATERIAL_DIFFUSE_LINK][c4d.IMAGETEXTURE_GAMMA] = 2.0
                    mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.0
                except:
                    pass
            if 'Teeth' in matName:
                mat[c4d.OCT_MATERIAL_TYPE] = 2511
                mat[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = 1.0
                mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.03
                mat[c4d.OCT_MATERIAL_INDEX] = 2
            if 'Lips' in matName:
                mat[c4d.OCT_MATERIAL_TYPE] = 2511
                mat[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = 0.5
                mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.16
                mat[c4d.OCT_MATERIAL_INDEX] = 2
            if 'Tongue' in matName:
                mat[c4d.OCT_MATERIAL_TYPE] = 2511
                mat[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = 0.20
                mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.10
                mat[c4d.OCT_MATERIAL_INDEX] = 6
            if 'Gums' in matName:
                mat[c4d.OCT_MATERIAL_TYPE] = 2511
                mat[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = 0.8
                mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.21
                mat[c4d.OCT_MATERIAL_INDEX] = 2
            if 'Mouth' in matName:
                mat[c4d.OCT_MATERIAL_TYPE] = 2511
                mat[c4d.OCT_MATERIAL_INDEX] = 5
            if 'Tear' in matName:
                mat[c4d.OCT_MATERIAL_TYPE] = 2511
                mat[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = 0.8
                mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.0
                mat[c4d.OCT_MATERIAL_INDEX] = 8
                mat[c4d.OCT_MATERIAL_OPACITY_FLOAT] = 0.25
            # GENESIS 1 Patch ----------------------------
            if '5_Cornea' in matName:
                mat[c4d.OCT_MATERIAL_OPACITY_FLOAT] = 0.15

            # GENESIS 2 Patches -------------------------
            if figureModel == 'Genesis2':
                if 'Nostrils' in matName:
                    mat.SetName('Head')
                if 'Sclera' in matName:
                    try:
                        mat[c4d.OCT_MATERIAL_DIFFUSE_LINK][c4d.IMAGETEXTURE_POWER_FLOAT] = 2.0
                    except:
                        pass
                if mat[c4d.OCT_MATERIAL_OPACITY_LINK]:
                    try:
                        mat[c4d.OCT_MATERIAL_OPACITY_LINK][c4d.IMAGETEXTURE_MODE] = 1
                        mat[c4d.OCT_MATERIAL_OPACITY_LINK][c4d.IMAGETEXTURE_GAMMA] = 1.0
                    except:
                        pass
                if 'EyeReflection' in matName or 'Tear' in matName:
                    mat[c4d.OCT_MATERIAL_TYPE] = 2511  # 2511 Glossy
                    mat[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                    mat[c4d.OCT_MATERIAL_SPECULAR_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                    mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = 1.0
                    mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.0
                    mat[c4d.OCT_MAT_USE_BUMP] = False
                    mat[c4d.OCT_MATERIAL_INDEX] = 6
                    mat[c4d.OCT_MATERIAL_OPACITY_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                    mat[c4d.OCT_MATERIAL_OPACITY_FLOAT] = 0.20
                    mat[c4d.OCT_MATERIAL_OPACITY_LINK] = None
                    if 'Tear' in matName:
                        mat[c4d.OCT_MATERIAL_OPACITY_FLOAT] = 0.1
                        mat[c4d.OCT_MATERIAL_INDEX] = 3
                if 'Lacrimals' in matName:
                    mat[c4d.OCT_MATERIAL_TYPE] = 2511  # 2511 Glossy
                    mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.0
                    mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = 0.15
                    mat[c4d.OCT_MATERIAL_INDEX] = 3
                    try:
                        mat[c4d.OCT_MATERIAL_DIFFUSE_LINK][c4d.IMAGETEXTURE_POWER_FLOAT] = 2.0
                    except:
                        pass

            # GENESIS 3 Patches -------------------------
            if figureModel == 'Genesis3':
                if 'Cornea' in matName:
                    mat[c4d.OCT_MAT_USE_OPACITY] = True
                    mat[c4d.OCT_MATERIAL_OPACITY_FLOAT] = 0.0

        c4d.EventAdd()