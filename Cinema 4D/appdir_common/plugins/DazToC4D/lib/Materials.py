from __future__ import division
from xml.etree.ElementTree import TreeBuilder
import c4d
import os
import sys
from shutil import copyfile
from c4d import documents, gui

from .Utilities import dazToC4Dutils
from .CustomIterators import ObjectIterator, TagIterator
from .Definitions import RES_DIR
from .TextureLib import texture_library

try:
    import redshift

except:
    pass


# region top-level methods
def srgb_to_linear_rgb(srgb):
    if srgb < 0:
        return 0
    elif srgb < 0.04045:
        return srgb / 12.92
    else:
        return ((srgb + 0.055) / 1.055) ** 2.4


def hex_to_col(hex, normalize=True, precision=6):
    col = []
    it = iter(str(hex))
    if c4d.GetC4DVersion() <= 22123:
        for index, char in enumerate(it):
            col.append(int(char + next(it), 16))
    else:
        for char in it:
            col.append(int(char + it.__next__(), 16))
    if normalize:
        col = map(lambda x: x / 255, col)
        col = map(lambda x: round(x, precision), col)
    return list(c for c in col)


def convert_color(color):
    color_hex = str(color).lstrip("#")
    color_rgb = hex_to_col(color_hex)
    return color_rgb


def convert_to_vector(value):
    num = 1
    num *= value
    return c4d.Vector(num, num, num)


class Materials:
    material_dict = {}

    def store_materials(self, dtu):
        """
        Pass the Material Information to be used for the current import
        """
        self.material_dict = {}
        materials = dtu.get_materials_list()
        for mat in materials:
            asset_name = mat["Asset Name"]
            mat_name = mat["Material Name"]
            if asset_name not in self.material_dict.keys():
                self.material_dict[asset_name] = {}
            self.material_dict[asset_name][mat_name] = mat

    def store_sliders(self, sss_value, normal_value, bump_value):
        """Stores the Sliders from UI Before Material Creation"""
        self.sss_value = sss_value
        self.normal_value = normal_value
        self.bump_value = bump_value

    @staticmethod
    def create_texture(mat, path):
        path = str(path)
        path = os.path.abspath(path)
        texture = c4d.BaseList2D(c4d.Xbitmap)
        texture[c4d.BITMAPSHADER_FILENAME] = path
        mat.InsertShader(texture)
        return texture

    def is_trans(self, prop):
        lib = texture_library
        for prop_name in lib["transparency"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Value"] > 0:
                    return True

    def is_diffuse(self, prop):
        lib = texture_library
        for prop_name in lib["color"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    return True

    def is_metal(self, prop):
        lib = texture_library
        for prop_name in lib["metalness"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Value"] > 0:
                    return True

    def is_sss(self, prop):
        lib = texture_library
        for prop_name in lib["sss-enable"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Value"] > 0:
                    return True

    def check_value(self, type, value):
        if type == "float":
            if isinstance(value, str):
                return 1
            else:
                return value

        if type == "hex":
            if c4d.GetC4DVersion() <= 22123:
                if not isinstance(value, float):
                    value = str(value)

            if isinstance(value, float):
                return "#FFFFFF"
            else:
                return value

    def find_mat_properties(self, obj, mat):
        if obj not in self.material_dict.keys():
            return
        if mat not in self.material_dict[obj].keys():
            return
        properties = {}
        for prop in self.material_dict[obj][mat]["Properties"]:
            properties[prop["Name"]] = prop
        return properties

    def find_mat_type(self, obj, mat):
        if obj not in self.material_dict.keys():
            return
        if mat not in self.material_dict[obj].keys():
            return
        return self.material_dict[obj][mat]["Value"]

    def update_materials(self):
        doc = c4d.documents.GetActiveDocument()
        doc_mat = doc.GetMaterials()
        for mat in doc_mat:
            mat_name = mat.GetName()
            mat_link = mat[c4d.ID_MATERIALASSIGNMENTS]
            mat_count = mat_link.GetObjectCount()
            for i in range(mat_count):
                link = mat_link.ObjectFromIndex(doc, i)
                mat_obj = link.GetObject()
                obj_name = mat_obj.GetName().replace(".Shape", "")
                prop = self.find_mat_properties(obj_name, mat_name)
                asset_type = self.find_mat_type(obj_name, mat_name)
                if not prop:
                    continue
                self.clean_up_layers(mat)
                self.set_up_transmission(mat, prop)
                self.set_up_diffuse(mat, prop)
                self.set_up_daz_mat(mat, prop)
                self.set_up_bump_normal(mat, prop)
                self.set_up_alpha(mat, prop)
                self.set_up_translucency(mat, prop)
                self.viewport_settings(mat, asset_type)

    def clean_up_layers(self, mat):
        mat[c4d.MATERIAL_USE_COLOR] = False
        mat.RemoveReflectionAllLayers()

    def set_up_transmission(self, mat, prop):
        lib = texture_library
        if self.is_trans(prop):
            mat[c4d.MATERIAL_USE_TRANSPARENCY] = True
            for prop_name in lib["transparency"]["Name"]:
                if prop_name in prop.keys():
                    vector = convert_to_vector(prop[prop_name]["Value"])
                    mat[c4d.MATERIAL_TRANSPARENCY_COLOR] = vector
            for prop_name in lib["ior"]["Name"]:
                if prop_name in prop.keys():
                    mat[c4d.MATERIAL_TRANSPARENCY_REFRACTION] = prop[prop_name]["Value"]

    def set_up_diffuse(self, mat, prop):
        lib = texture_library
        if self.is_diffuse(prop):
            diffuse = mat.AddReflectionLayer()
            diffuse.SetName("Diffuse Layer")
            mat[
                diffuse.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION
            ] = c4d.REFLECTION_DISTRIBUTION_LAMBERTIAN
            for prop_name in lib["color"]["Name"]:
                if prop_name in prop.keys():
                    if prop[prop_name]["Texture"] != "":
                        path = prop[prop_name]["Texture"]
                        texture = Materials.create_texture(mat, path)
                        mat[
                            diffuse.GetDataID() + c4d.REFLECTION_LAYER_COLOR_TEXTURE
                        ] = texture
                        hex_str = prop[prop_name]["Value"]
                        hex_str = self.check_value("hex", hex_str)
                        color = convert_color(hex_str)
                        vector = c4d.Vector(color[0], color[1], color[2])
                        mat[
                            diffuse.GetDataID() + c4d.REFLECTION_LAYER_COLOR_COLOR
                        ] = vector
                        mat[
                            diffuse.GetDataID() + c4d.REFLECTION_LAYER_COLOR_MIX_MODE
                        ] = 3

    def set_up_daz_mat(self, mat, prop):
        lib = texture_library
        daz_mat = mat.AddReflectionLayer()
        daz_mat.SetName("Daz Material Layer")
        mat[
            daz_mat.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION
        ] = c4d.REFLECTION_DISTRIBUTION_GGX

        if self.is_metal(prop):
            mat[
                daz_mat.GetDataID() + c4d.REFLECTION_LAYER_MAIN_ADDITIVE
            ] = c4d.REFLECTION_ADDITIVE_MODE_METAL
            mat[
                daz_mat.GetDataID() + c4d.REFLECTION_LAYER_FRESNEL_MODE
            ] = c4d.REFLECTION_FRESNEL_CONDUCTOR
        else:
            mat[
                daz_mat.GetDataID() + c4d.REFLECTION_LAYER_FRESNEL_MODE
            ] = c4d.REFLECTION_FRESNEL_DIELECTRIC

        for prop_name in lib["color"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    texture = Materials.create_texture(mat, path)
                    mat[
                        daz_mat.GetDataID() + c4d.REFLECTION_LAYER_COLOR_TEXTURE
                    ] = texture
        for prop_name in lib["roughness"]["Name"]:
            if prop_name in prop.keys():
                value = prop[prop_name]["Value"]
                value = self.check_value("float", value)
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    texture = Materials.create_texture(mat, path)
                    mat[
                        daz_mat.GetDataID() + c4d.REFLECTION_LAYER_MAIN_SHADER_ROUGHNESS
                    ] = texture
                    mat[
                        daz_mat.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS
                    ] = value
                if value > 0:
                    mat[
                        daz_mat.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS
                    ] = value

        for prop_name in lib["relection"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    texture = Materials.create_texture(mat, path)
                    mat[
                        daz_mat.GetDataID()
                        + c4d.REFLECTION_LAYER_MAIN_SHADER_REFLECTION
                    ] = texture

        for prop_name in lib["relection-strength"]["Name"]:
            if prop_name in prop.keys():
                value = prop[prop_name]["Value"]
                value = self.check_value("float", value)
                if value > 0:
                    mat[
                        daz_mat.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_REFLECTION
                    ] = value

        for prop_name in lib["specular"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    value = prop[prop_name]["Value"]
                    value = self.check_value("float", value)
                    texture = Materials.create_texture(mat, path)
                    mat[
                        daz_mat.GetDataID() + c4d.REFLECTION_LAYER_MAIN_SHADER_SPECULAR
                    ] = texture
                    mat[
                        daz_mat.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR
                    ] = value

        for prop_name in lib["metalness"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    texture = Materials.create_texture(mat, path)
                    mat[
                        daz_mat.GetDataID() + c4d.REFLECTION_LAYER_TRANS_TEXTURE
                    ] = texture

    def set_up_bump_normal(self, mat, prop):
        lib = texture_library
        for prop_name in lib["bump"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    strength = prop[prop_name]["Value"]
                    strength = self.check_value("float", strength)
                    texture = Materials.create_texture(mat, path)
                    mat[c4d.MATERIAL_USE_BUMP] = True
                    mat[c4d.MATERIAL_BUMP_SHADER] = texture
                    mat[c4d.MATERIAL_BUMP_STRENGTH] = strength * self.bump_value / 100

        for prop_name in lib["normal"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    strength = prop[prop_name]["Value"]
                    strength = self.check_value("float", strength)
                    texture = Materials.create_texture(mat, path)
                    mat[c4d.MATERIAL_USE_NORMAL] = True
                    mat[c4d.MATERIAL_NORMAL_SHADER] = texture
                    mat[c4d.MATERIAL_NORMAL_STRENGTH] = (
                        strength * self.normal_value / 100
                    )

    def set_up_alpha(self, mat, prop):
        lib = texture_library
        for prop_name in lib["opacity"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    texture = Materials.create_texture(mat, path)
                    mat[c4d.MATERIAL_USE_ALPHA] = True
                    mat[c4d.MATERIAL_ALPHA_SHADER] = texture

    def set_up_translucency(self, mat, prop):
        lib = texture_library
        if self.is_sss(prop):
            doc = c4d.documents.GetActiveDocument()
            sss = c4d.BaseList2D(c4d.Xxmbsubsurface)
            mat[c4d.MATERIAL_USE_LUMINANCE] = True
            mat[c4d.MATERIAL_LUMINANCE_SHADER] = sss
            doc.InsertShader(sss)
            for prop_name in lib["sss"]["Name"]:
                if prop_name in prop.keys():
                    if prop[prop_name]["Texture"] != "":
                        path = prop[prop_name]["Texture"]
                        texture = Materials.create_texture(mat, path)
                        sss[c4d.XMBSUBSURFACESHADER_SHADER] = texture

            for prop_name in lib["sss-color"]["Name"]:
                if prop_name in prop.keys():
                    hex_str = prop[prop_name]["Value"]
                    hex_str = self.check_value("hex", hex_str)
                    color = convert_color(hex_str)
                    vector = c4d.Vector(color[0], color[1], color[2])
                    sss[c4d.XMBSUBSURFACESHADER_DIFFUSE] = vector

            for prop_name in lib["sss-strength"]["Name"]:
                if prop_name in prop.keys():
                    strength = prop[prop_name]["Value"]
                    strength = self.check_value("float", strength)
                    sss[c4d.XMBSUBSURFACESHADER_STRENGTH] = (
                        strength * self.sss_value / 10
                    )

            for prop_name in lib["transmitted-color"]["Name"]:
                if prop_name in prop.keys():
                    hex_str = prop[prop_name]["Value"]
                    hex_str = self.check_value("hex", hex_str)
                    color = convert_color(hex_str)
                    vector = c4d.Vector(color[0], color[1], color[2])
                    mat[c4d.MATERIAL_LUMINANCE_COLOR] = vector

            for prop_name in lib["transmitted-strength"]["Name"]:
                if prop_name in prop.keys():
                    strength = prop[prop_name]["Value"]
                    strength = self.check_value("float", strength)
                    mat[c4d.MATERIAL_LUMINANCE_BRIGHTNESS] = strength

    def viewport_settings(self, mat, asset_type):
        if asset_type == "Follower/Hair":
            mat[c4d.MATERIAL_DISPLAY_USE_ALPHA] = False
        mat[c4d.MATERIAL_DISPLAY_USE_LUMINANCE] = False

    @staticmethod
    def update_bump(multiply):
        doc = c4d.documents.GetActiveDocument()
        doc_mat = doc.GetMaterials()
        for mat in doc_mat:
            original = 10
            if mat[c4d.MATERIAL_BUMP_STRENGTH] == 0:
                mat[c4d.MATERIAL_BUMP_STRENGTH] = 0.01
            strength = mat[c4d.MATERIAL_BUMP_STRENGTH] * 100 / original
            mat[c4d.MATERIAL_BUMP_STRENGTH] = strength * multiply / 100

    def checkStdMats(self):
        doc = c4d.documents.GetActiveDocument()
        docMaterials = doc.GetMaterials()
        noStd = True
        for mat in docMaterials:
            matName = mat.GetName()
            if mat.GetType() == 5703:
                noStd = False
        if noStd == True:
            gui.MessageDialog(
                "No standard mats found. This scene was already converted"
            )

        return noStd

    def fixGenEyes(self, path):
        folder_DazToC4D_res = RES_DIR  # Adds the res folder to the path
        folder_DazToC4D_xtra = os.path.join(
            folder_DazToC4D_res, "xtra"
        )  # Adds the res folder to the path
        file_G3_IrisFixMap = os.path.join(folder_DazToC4D_xtra, "G3_Iris_Alpha.psd")

        destination_G3_IrisFixMap = os.path.join(path, "G3_Iris_Alpha.psd")

        try:
            copyfile(file_G3_IrisFixMap, destination_G3_IrisFixMap)
        except:
            print("Iris Map transfer...Skipped.")

        doc = c4d.documents.GetActiveDocument()
        docMaterials = doc.GetMaterials()
        for mat in docMaterials:
            if "Iris" in mat.GetName():
                matDiffuseMap = ""
                try:
                    matDiffuseMap = mat[c4d.MATERIAL_COLOR_SHADER][
                        c4d.BITMAPSHADER_FILENAME
                    ]
                except:
                    pass
                skipThis = False
                if "3duG3FTG2_Eyes" in matDiffuseMap:
                    skipThis = True

                if skipThis == False and os.path.exists(destination_G3_IrisFixMap):
                    mat[c4d.MATERIAL_USE_ALPHA] = True
                    shda = c4d.BaseList2D(c4d.Xbitmap)
                    shda[c4d.BITMAPSHADER_FILENAME] = destination_G3_IrisFixMap
                    mat[c4d.MATERIAL_ALPHA_SHADER] = shda
                    mat.InsertShader(shda)

    def specificFiguresFixes(self):
        doc = c4d.documents.GetActiveDocument()

        figureModel = ""

        def findMatName(matToFind):
            matFound = None
            sceneMats = doc.GetMaterials()
            for mat in sceneMats:
                matName = mat.GetName()
                if matToFind in matName:
                    matFound = mat
                    return matFound
            return matFound

        # TOON GENERATION 2
        doc = documents.GetActiveDocument()
        sceneMats = doc.GetMaterials()
        # ZOMBIE ... GEN3...
        if findMatName("Cornea") != None and findMatName("EyeMoisture") == None:
            mat = findMatName("Cornea")
            mat[c4d.MATERIAL_USE_ALPHA] = False

        for mat in sceneMats:
            matName = mat.GetName()
            if "Eyelashes" in matName:
                if mat[c4d.MATERIAL_ALPHA_SHADER] == None:
                    try:
                        shaderColor = c4d.BaseList2D(
                            c4d.Xcolor
                        )  # create a bitmap shader for the material
                        mat.InsertShader(shaderColor)
                        mat[c4d.MATERIAL_USE_ALPHA] = True
                        mat[c4d.MATERIAL_ALPHA_SHADER] = shaderColor
                        mat[c4d.MATERIAL_ALPHA_SHADER][c4d.COLORSHADER_BRIGHTNESS] = 0.0
                    except:
                        pass

        c4d.EventAdd()

    def transpMapFix(self, mat):
        if mat[c4d.MATERIAL_TRANSPARENCY_SHADER] != None:
            mat[c4d.MATERIAL_ALPHA_SHADER] = mat[c4d.MATERIAL_TRANSPARENCY_SHADER]
            mat[c4d.MATERIAL_USE_TRANSPARENCY] = 0
            mat[c4d.MATERIAL_USE_ALPHA] = 1
            mat[c4d.MATERIAL_TRANSPARENCY_SHADER] = None

    def fixMaterials(self):

        doc = c4d.documents.GetActiveDocument()

        # Process for all materials of scene
        docMaterials = doc.GetMaterials()
        for mat in docMaterials:
            self.transpMapFix(mat)
            matName = mat.GetName()
            eyesMats = [
                "Eyelashes",
                "Cornea",
                "EyeMoisture",
                "EyeMoisture2",
                "Sclera",
                "Irises",
            ]
            layer = mat.GetReflectionLayerIndex(0)

            mat[c4d.MATERIAL_NORMAL_STRENGTH] = 0.25
            mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.05
            try:  # Remove extra layers stuff...
                mat.RemoveReflectionLayerIndex(1)
                mat.RemoveReflectionLayerIndex(2)
                mat.RemoveReflectionLayerIndex(3)
                mat.RemoveReflectionLayerIndex(4)
            except:
                pass

            if matName in eyesMats:
                mat[
                    layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS
                ] = 0.13

            if (
                "Moisture" in matName
                or "Cornea" in matName
                or "Tear" in matName
                or "EyeReflection" in matName
            ):
                mat[c4d.MATERIAL_COLOR_COLOR] = c4d.Vector(0.2, 0.2, 0.2)
                mat[c4d.MATERIAL_USE_TRANSPARENCY] = True
                mat[c4d.MATERIAL_TRANSPARENCY_COLOR] = c4d.Vector(0.9, 0.9, 0.9)
                mat[c4d.MATERIAL_TRANSPARENCY_REFRACTION] = 1.0
                mat[
                    layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION
                ] = 0  # 0 = Reflection(legacy)
                mat[c4d.MATERIAL_USE_TRANSPARENCY] = True
                mat[c4d.MATERIAL_TRANSPARENCY_FRESNEL] = False
                mat[c4d.MATERIAL_TRANSPARENCY_EXITREFLECTIONS] = False
                mat[c4d.MATERIAL_TRANSPARENCY_COLOR] = c4d.Vector(0.95, 0.95, 0.95)
                mat[c4d.MATERIAL_TRANSPARENCY_REFRACTION] = 1.33

                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_COLOR_COLOR] = c4d.Vector(
                    1.0, 1.0, 1.0
                )
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS] = 0.0
                mat[
                    layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_REFLECTION
                ] = 0.7
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.0
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_BUMP] = 0.0
            if "Eyes" in matName:
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.0
            if "Pupils" in matName:
                mat[c4d.MATERIAL_USE_REFLECTION] = False
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.0
            if "Teeth" in matName:
                mat[
                    layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION
                ] = 0  # 0 = Reflection(legacy)
                mat[
                    layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS
                ] = 0.07
                mat[
                    layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_REFLECTION
                ] = 0.09
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.03
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_BUMP] = 0.25
            if "Mouth" in matName:
                mat[
                    layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION
                ] = 0  # 0 = Reflection(legacy)
            if "Sclera" in matName:
                mat[c4d.MATERIAL_USE_REFLECTION] = False
                mat[c4d.MATERIAL_GLOBALILLUM_RECEIVE_STRENGTH] = 2

            if "Iris" in matName:
                mat[c4d.MATERIAL_USE_REFLECTION] = False
                mat[
                    layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_REFLECTION
                ] = 0.0
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR] = 0.0
                mat[
                    layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION
                ] = 0  # 0 = Reflection(legacy)
            if "Eyelash" in matName:
                mat[c4d.MATERIAL_COLOR_SHADER] = None
                mat[c4d.MATERIAL_COLOR_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                try:
                    mat[c4d.MATERIAL_ALPHA_SHADER][c4d.BITMAPSHADER_FILENAME][
                        c4d.BITMAPSHADER_EXPOSURE
                    ] = 1.0
                except:
                    print("Exposure Skipped...")

        c4d.CallCommand(12253, 12253)  # Render All Materials

        c4d.EventAdd()

    def stdMatExtrafixes(self):
        def setRenderToPhysical():
            try:
                rdata = doc.GetActiveRenderData()
                vpost = rdata.GetFirstVideoPost()
                rdata[c4d.RDATA_RENDERENGINE] = c4d.RDATA_RENDERENGINE_PHYSICAL

                while vpost:
                    if vpost.CheckType(c4d.VPxmbsampler):
                        break
                    vpost = vpost.GetNext()

                if not vpost:
                    vpost = c4d.BaseList2D(c4d.VPxmbsampler)
                    rdata.InsertVideoPost(vpost)

                c4d.EventAdd()
            except:
                pass

        def findMatName(matToFind):
            matFound = None
            sceneMats = doc.GetMaterials()
            for mat in sceneMats:
                matName = mat.GetName()
                if matToFind in matName:
                    matFound = mat
                    return matFound
            return matFound

        doc = c4d.documents.GetActiveDocument()

        # --- Fix duplicated Moisture material...??
        myMaterials = doc.GetMaterials()
        for mat in myMaterials:
            if "EyeMoisture" in mat.GetName():
                mat.SetName("EyeMoisture2")
                return TreeBuilder
        setRenderToPhysical()
        figureModel = "Genesis8"
        if findMatName("EyeReflection"):
            figureModel = "Genesis2"
        if findMatName("Fingernails"):
            figureModel = "Genesis3"
        # FIX MATERIAL NAMES etc... USE THIS FOR ALL CONVERTIONS NOT JUST OCTANE!
        if findMatName("1_SkinFace") == None and findMatName("1_Nostril") != None:
            try:
                findMatName("1_Nostril").SetName("1_SkinFace")
            except:
                pass
        if findMatName("3_SkinHand") == None and findMatName("3_SkinFoot") != None:
            try:
                findMatName("3_SkinFoot").SetName("3_ArmsLegs")
            except:
                pass

        sceneMats = doc.GetMaterials()
        for mat in sceneMats:
            matName = mat.GetName()
            try:
                mat[c4d.MATERIAL_ALPHA_SHADER][c4d.BITMAPSHADER_WHITEPOINT] = 0.5
            except:
                pass
            try:
                layerTransp = mat.GetReflectionLayerTrans()
                mat[
                    layerTransp.GetDataID() + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS
                ] = 0.0
            except:
                pass

            # GENESIS 3 Patches -------------------------
            if (
                figureModel == "Genesis3"
                or figureModel == "Genesis2"
                or figureModel == "Genesis8"
            ):
                if "Cornea" in matName:
                    bmpPath = "CACA"
                    shaderColor = c4d.BaseList2D(
                        c4d.Xcolor
                    )  # create a bitmap shader for the material
                    # bmpShader[c4d.BITMAPSHADER_FILENAME] = bmpPath
                    mat.InsertShader(shaderColor)
                    mat[c4d.MATERIAL_USE_ALPHA] = True
                    mat[c4d.MATERIAL_ALPHA_SHADER] = shaderColor
                    mat[c4d.MATERIAL_ALPHA_SHADER][c4d.COLORSHADER_BRIGHTNESS] = 0.0

                if "Moisture" in matName or "Tear" in matName:
                    mat[c4d.MATERIAL_USE_ALPHA] = True
                    mat[c4d.MATERIAL_ALPHA_SHADER] = None
                    mat[c4d.MATERIAL_COLOR_COLOR] = c4d.Vector(0, 0, 0)
                    mat[c4d.MATERIAL_TRANSPARENCY_REFRACTION] = 1.0

                if "Sclera" in matName:
                    try:
                        mat[c4d.MATERIAL_COLOR_SHADER][
                            c4d.BITMAPSHADER_WHITEPOINT
                        ] = 0.8
                    except:
                        pass
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
                    if matSel == "Lips":
                        try:
                            old_mat = tag[c4d.TEXTURETAG_MATERIAL]

                            doc.SetActiveMaterial(old_mat)
                            c4d.CallCommand(300001022, 300001022)  # Copy
                            c4d.CallCommand(300001023, 300001023)  # Paste
                            newMat = doc.GetFirstMaterial()
                            newMat[c4d.ID_BASELIST_NAME] = "Lips"

                            tag[c4d.TEXTURETAG_MATERIAL] = newMat
                        except:
                            pass

        c4d.EventAdd()

    def matSetSpec(self, setting, value):
        doc = c4d.documents.GetActiveDocument()

        # Process for all materials of scene
        docMaterials = doc.GetMaterials()
        for mat in docMaterials:
            matName = mat.GetName()
            skinMats = [
                "MainSkin",
                "Legs",
                "Torso",
                "Arms",
                "Face",
                "Fingernails",
                "Toenails",
                "EyeSocket",
                "Ears",
                "Feet",
                "Nipples",
                "Forearms",
                "Hips",
                "Neck",
                "Shoulders",
                "Hands",
                "Head",
                "Nostrils",
            ]
            for x in skinMats:
                if x in matName:
                    if mat.GetType() == 1038954:  # Vray
                        if setting == "Rough":
                            mat[c4d.VRAYSTDMATERIAL_REFLECTGLOSSINESS] = (
                                1.0 - value / 100
                            )
                        if setting == "Weight":
                            colorValue = value / 100
                            mat[c4d.VRAYSTDMATERIAL_REFLECTCOLOR] = c4d.Vector(
                                colorValue, colorValue, colorValue
                            )

                    if mat.GetType() == 5703:  # Standard
                        layer = mat.GetReflectionLayerIndex(0)
                        if setting == "Rough":
                            mat[
                                layer.GetDataID()
                                + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS
                            ] = (value / 100)
                        if setting == "Weight":
                            mat[
                                layer.GetDataID()
                                + c4d.REFLECTION_LAYER_MAIN_VALUE_SPECULAR
                            ] = (value / 100)
                    if mat.GetType() == 1029501:  # Octane
                        if setting == "Weight":
                            mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = value / 100
                        if setting == "Rough":
                            mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = value / 100
                    if mat.GetType() == 1036224:  # Redshift
                        gvNodeMaster = redshift.GetRSMaterialNodeMaster(mat)
                        rootNode_ShaderGraph = gvNodeMaster.GetRoot()
                        output = rootNode_ShaderGraph.GetDown()
                        RShader = output.GetNext()
                        gvNodeMaster = redshift.GetRSMaterialNodeMaster(mat)
                        nodeRoot = gvNodeMaster.GetRoot()
                        rsMaterial = nodeRoot.GetDown().GetNext()
                        if setting == "Weight":
                            rsMaterial[c4d.REDSHIFT_SHADER_MATERIAL_REFL_WEIGHT] = (
                                value / 100
                            )
                            rsMaterial[c4d.REDSHIFT_SHADER_MATERIAL_REFL_IOR] = (
                                value / 10
                            )
                        if setting == "Rough":
                            rsMaterial[c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS] = (
                                value / 100
                            )

    # TODO: Verify if necessary with Material Rework
    def eyeLashAndOtherFixes(self):
        """
        Hard Code Changes to Eyelashes plus other Eye Mats
        """
        doc = c4d.documents.GetActiveDocument()
        docMaterials = doc.GetMaterials()
        irisMap = ""
        for mat in docMaterials:  # Lashes fix... Gen2 and maybe others...
            matName = mat.GetName()
            if "Lashes" in matName:
                try:
                    mat[c4d.MATERIAL_COLOR_SHADER] = None
                except:
                    print("mat skip...")
                    pass
            if "Iris" in matName:
                try:
                    irisMap = mat[c4d.MATERIAL_COLOR_SHADER][c4d.BITMAPSHADER_FILENAME]
                except:
                    pass

        for mat in docMaterials:  # Iris fix Gen2 and maybe others...
            if mat[c4d.MATERIAL_COLOR_SHADER]:
                if mat[c4d.MATERIAL_COLOR_SHADER].GetType() == 5833:
                    matTexture = mat[c4d.MATERIAL_COLOR_SHADER][
                        c4d.BITMAPSHADER_FILENAME
                    ]
                    matName = mat.GetName()
                    if irisMap == matTexture:
                        if "Sclera" not in matName:
                            mat[c4d.MATERIAL_USE_REFLECTION] = False

        for mat in docMaterials:  # Fix to Tear.. Gen2...
            matName = mat.GetName()
            if "Tear" in matName:
                mat[c4d.MATERIAL_TRANSPARENCY_COLOR] = c4d.Vector(0.94, 0.94, 0.94)

    # Unused code to be deleted
    def reduceMatFix(self):
        doc = c4d.documents.GetActiveDocument()
        myMaterials = doc.GetMaterials()
        matHead = False
        matTorso = False
        matLegs = False
        matHands = False
        for mat in myMaterials:
            # print mat.GetName()
            if "Torso" in mat.GetName():
                matTorso = mat
            if "Hands" in mat.GetName():
                matHands = mat
            if "Legs" in mat.GetName():
                matLegs = mat
            if "Head" in mat.GetName():
                matHead = mat

        if matTorso == False and matHead != False:
            matHead.SetName("MainSkin")
        if matHands == False and matLegs != False:
            matLegs.SetName("LegsAndArms")

        c4d.EventAdd()

    # Unused code to be deleted
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

        figureModel = "Genesis8"

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

        if findMatName("EyeReflection"):
            figureModel = "Genesis2"
        if findMatName("FingerNails"):
            figureModel = "Genesis3"

        # FIX MATERIAL NAMES etc... USE THIS FOR ALL CONVERTIONS NOT JUST OCTANE!
        if findMatName("1_SkinFace") == None and findMatName("1_Nostril") != None:
            findMatName("1_Nostril").SetName("1_SkinFace")
        if findMatName("3_SkinHand") == None and findMatName("3_SkinFoot") != None:
            findMatName("3_SkinFoot").SetName("3_ArmsLegs")
        # ////

        sceneMats = doc.GetMaterials()
        for mat in sceneMats:
            matName = mat.GetName()
            mat[c4d.OCT_MATERIAL_SPECULAR_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
            mat[c4d.OCT_MATERIAL_INDEX] = 2

            extraMapGlossyRough = dazToC4Dutils().findTextInFile(
                matName, "Glossy_Roughness_Map"
            )
            if extraMapGlossyRough != None:
                ID_OCTANE_IMAGE_TEXTURE = 1029508
                shd = c4d.BaseShader(ID_OCTANE_IMAGE_TEXTURE)

                mat.InsertShader(shd)
                mat[c4d.OCT_MATERIAL_ROUGHNESS_LINK] = shd
                shd[c4d.IMAGETEXTURE_FILE] = extraMapGlossyRough
                shd[c4d.IMAGETEXTURE_MODE] = 0
                shd[c4d.IMAGETEXTURE_GAMMA] = 2.2
                shd[c4d.IMAGETEX_BORDER_MODE] = 0
                doc.InsertMaterial(mat)

            extraMapSpec = dazToC4Dutils().findTextInFile(
                matName, "Glossy_Layered_Weight_Map"
            )
            extraMapSpec2 = dazToC4Dutils().findTextInFile(matName, "spec")
            extraMapGlossy = dazToC4Dutils().findTextInFile(matName, "Metallicity_Map")
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
            if "Moisture" in matName or "Cornea" in matName:
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
            if "Sclera" in matName:
                try:
                    mat[c4d.OCT_MATERIAL_DIFFUSE_LINK][
                        c4d.IMAGETEXTURE_POWER_FLOAT
                    ] = 3.0
                    mat[c4d.OCT_MATERIAL_DIFFUSE_LINK][c4d.IMAGETEXTURE_GAMMA] = 2.0
                    mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.0
                except:
                    pass
            if "Irises" in matName:
                try:
                    mat[c4d.OCT_MATERIAL_DIFFUSE_LINK][
                        c4d.IMAGETEXTURE_POWER_FLOAT
                    ] = 2.0
                    mat[c4d.OCT_MATERIAL_DIFFUSE_LINK][c4d.IMAGETEXTURE_GAMMA] = 2.0
                    mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.0
                except:
                    pass
            if "Teeth" in matName:
                mat[c4d.OCT_MATERIAL_TYPE] = 2511
                mat[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = 1.0
                mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.03
                mat[c4d.OCT_MATERIAL_INDEX] = 2
            if "Lips" in matName:
                mat[c4d.OCT_MATERIAL_TYPE] = 2511
                mat[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = 0.5
                mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.16
                mat[c4d.OCT_MATERIAL_INDEX] = 2
            if "Tongue" in matName:
                mat[c4d.OCT_MATERIAL_TYPE] = 2511
                mat[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = 0.20
                mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.10
                mat[c4d.OCT_MATERIAL_INDEX] = 6
            if "Gums" in matName:
                mat[c4d.OCT_MATERIAL_TYPE] = 2511
                mat[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = 0.8
                mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.21
                mat[c4d.OCT_MATERIAL_INDEX] = 2
            if "Mouth" in matName:
                mat[c4d.OCT_MATERIAL_TYPE] = 2511
                mat[c4d.OCT_MATERIAL_INDEX] = 5
            if "Tear" in matName:
                mat[c4d.OCT_MATERIAL_TYPE] = 2511
                mat[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_COLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = 0.8
                mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.0
                mat[c4d.OCT_MATERIAL_INDEX] = 8
                mat[c4d.OCT_MATERIAL_OPACITY_FLOAT] = 0.25
            # GENESIS 1 Patch ----------------------------
            if "5_Cornea" in matName:
                mat[c4d.OCT_MATERIAL_OPACITY_FLOAT] = 0.15

            # GENESIS 2 Patches -------------------------
            if figureModel == "Genesis2":
                if "Nostrils" in matName:
                    mat.SetName("Head")
                if "Sclera" in matName:
                    try:
                        mat[c4d.OCT_MATERIAL_DIFFUSE_LINK][
                            c4d.IMAGETEXTURE_POWER_FLOAT
                        ] = 2.0
                    except:
                        pass
                if mat[c4d.OCT_MATERIAL_OPACITY_LINK]:
                    try:
                        mat[c4d.OCT_MATERIAL_OPACITY_LINK][c4d.IMAGETEXTURE_MODE] = 1
                        mat[c4d.OCT_MATERIAL_OPACITY_LINK][c4d.IMAGETEXTURE_GAMMA] = 1.0
                    except:
                        pass
                if "EyeReflection" in matName or "Tear" in matName:
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
                    if "Tear" in matName:
                        mat[c4d.OCT_MATERIAL_OPACITY_FLOAT] = 0.1
                        mat[c4d.OCT_MATERIAL_INDEX] = 3
                if "Lacrimals" in matName:
                    mat[c4d.OCT_MATERIAL_TYPE] = 2511  # 2511 Glossy
                    mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.0
                    mat[c4d.OCT_MATERIAL_SPECULAR_FLOAT] = 0.15
                    mat[c4d.OCT_MATERIAL_INDEX] = 3
                    try:
                        mat[c4d.OCT_MATERIAL_DIFFUSE_LINK][
                            c4d.IMAGETEXTURE_POWER_FLOAT
                        ] = 2.0
                    except:
                        pass

            # GENESIS 3 Patches -------------------------
            if figureModel == "Genesis3":
                if "Cornea" in matName:
                    mat[c4d.OCT_MAT_USE_OPACITY] = True
                    mat[c4d.OCT_MATERIAL_OPACITY_FLOAT] = 0.0

        c4d.EventAdd()


class convertToRedshift:
    def __init__(self):
        try:
            import redshift
        except ImportError:
            print("DaztoC4D : Redshift not installed can not convert.")

        self.bump_input_type = 1  # Tangent-Space Normals
        self.NewMatList = []

    def execute(self):
        # Execute main()
        doc = c4d.documents.GetActiveDocument()

        # Process for all materials of scene
        docMaterials = doc.GetMaterials()
        if Materials().checkStdMats() == True:
            return

        for mat in docMaterials:
            matName = mat.GetName()
            if mat.GetType() == 5703:
                self.makeRSmat(mat)

        self.applyMaterials()

        c4d.EventAdd()
        bc = c4d.BaseContainer()
        c4d.gui.GetInputState(c4d.BFM_INPUT_MOUSE, c4d.BFM_INPUT_CHANNEL, bc)

    def getBumpType(self, index):
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
        skinMats = [
            "Legs",
            "Torso",
            "Body",
            "Arms",
            "Face",
            "Fingernails",
            "Toenails",
            "Lips",
            "EyeSocket",
            "Ears",
            "Feet",
            "Nipples",
            "Forearms",
            "Hips",
            "Neck",
            "Shoulders",
            "Hands",
            "Head",
            "Nostrils",
        ]
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
        newMat.SetName(matName + "_RS")

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
            print("RootNode color skip...")

        if mat[c4d.MATERIAL_USE_COLOR]:
            if mat[c4d.MATERIAL_COLOR_SHADER]:
                if mat[c4d.MATERIAL_COLOR_SHADER].GetType() == 5833:
                    # Texture Node:
                    Node = gvNodeMaster.CreateNode(nodeRoot, 1036227, None, 10, 200)
                    Node[c4d.GV_REDSHIFT_SHADER_META_CLASSNAME] = "TextureSampler"
                    fileName = mat[c4d.MATERIAL_COLOR_SHADER][c4d.BITMAPSHADER_FILENAME]
                    Node[
                        (
                            c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0,
                            c4d.REDSHIFT_FILE_PATH,
                        )
                    ] = fileName

                    if "Sclera" in mat.GetName():
                        Node[
                            c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0_GAMMAOVERRIDE
                        ] = True
                        Node[c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0_GAMMA] = 1.0

                    nodeShaderDiffuseColInput = RShader.AddPort(
                        c4d.GV_PORT_INPUT,
                        c4d.DescID(
                            c4d.DescLevel(c4d.REDSHIFT_SHADER_MATERIAL_DIFFUSE_COLOR)
                        ),
                        message=True,
                    )

                    Node.GetOutPort(0).Connect(nodeShaderDiffuseColInput)

        if mat[c4d.MATERIAL_USE_ALPHA]:
            if mat[c4d.MATERIAL_ALPHA_SHADER]:
                if mat[c4d.MATERIAL_ALPHA_SHADER].GetType() == 5833:
                    # Texture Node:
                    Node = gvNodeMaster.CreateNode(nodeRoot, 1036227, None, 10, 400)
                    Node[c4d.GV_REDSHIFT_SHADER_META_CLASSNAME] = "TextureSampler"
                    fileName = mat[c4d.MATERIAL_ALPHA_SHADER][c4d.BITMAPSHADER_FILENAME]
                    Node[
                        (
                            c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0,
                            c4d.REDSHIFT_FILE_PATH,
                        )
                    ] = fileName
                    Node[c4d.REDSHIFT_SHADER_TEXTURESAMPLER_ALPHA_IS_LUMINANCE] = True
                    Node[c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0_GAMMAOVERRIDE] = True
                    Node[c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0_GAMMA] = 0.1
                    if "Eyelash" in mat.GetName():
                        Node[
                            c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0_GAMMAOVERRIDE
                        ] = True
                        Node[c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0_GAMMA] = 1.0

                    nodeShaderOpacityColInput = RShader.AddPort(
                        c4d.GV_PORT_INPUT,
                        c4d.DescID(
                            c4d.DescLevel(c4d.REDSHIFT_SHADER_MATERIAL_OPACITY_COLOR)
                        ),
                        message=True,
                    )

                    Node.GetOutPort(0).Connect(nodeShaderOpacityColInput)

        if mat[c4d.MATERIAL_USE_BUMP]:
            if mat[c4d.MATERIAL_BUMP_SHADER]:
                if mat[c4d.MATERIAL_BUMP_SHADER].GetType() == 5833:
                    # Bump Node:
                    NodeBump = gvNodeMaster.CreateNode(
                        nodeRoot, 1036227, None, 200, 150
                    )  # Always use this to create any nodeee!!!
                    NodeBump[
                        c4d.GV_REDSHIFT_SHADER_META_CLASSNAME
                    ] = "BumpMap"  # This defines the node!!!
                    NodeBump[
                        c4d.REDSHIFT_SHADER_BUMPMAP_INPUTTYPE
                    ] = self.bump_input_type
                    NodeBump[c4d.REDSHIFT_SHADER_BUMPMAP_SCALE] = 0.5
                    # Texture Node:
                    NodeTexture = gvNodeMaster.CreateNode(
                        nodeRoot, 1036227, None, 80, 150
                    )  # Always use this to create any nodeee!!!
                    NodeTexture[
                        c4d.GV_REDSHIFT_SHADER_META_CLASSNAME
                    ] = "TextureSampler"  # This defines the node!!!
                    fileName = mat[c4d.MATERIAL_BUMP_SHADER][c4d.BITMAPSHADER_FILENAME]
                    NodeTexture[
                        (
                            c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0,
                            c4d.REDSHIFT_FILE_PATH,
                        )
                    ] = fileName

                    nodeShaderBumpInput = RShader.AddPort(
                        c4d.GV_PORT_INPUT,
                        c4d.DescID(
                            c4d.DescLevel(c4d.REDSHIFT_SHADER_MATERIAL_BUMP_INPUT)
                        ),
                        message=True,
                    )
                    nodeBumpMapInput = NodeBump.AddPort(
                        c4d.GV_PORT_INPUT,
                        c4d.DescID(c4d.DescLevel(c4d.REDSHIFT_SHADER_BUMPMAP_INPUT)),
                        message=True,
                    )

                    NodeTexture.GetOutPort(0).Connect(nodeBumpMapInput)
                    NodeBump.GetOutPort(0).Connect(nodeShaderBumpInput)

        extraMapGlossyRough = dazToC4Dutils().findTextInFile(
            mat.GetName(), "Glossy_Roughness_Map"
        )
        if extraMapGlossyRough != None:
            Node = gvNodeMaster.CreateNode(nodeRoot, 1036227, None, 10, 465)
            Node[c4d.GV_REDSHIFT_SHADER_META_CLASSNAME] = "TextureSampler"
            fileName = extraMapGlossyRough
            Node[
                (c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0, c4d.REDSHIFT_FILE_PATH)
            ] = fileName

            nodeShaderReflectionColInput = RShader.AddPort(
                c4d.GV_PORT_INPUT,
                c4d.DescID(c4d.DescLevel(c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS)),
                message=True,
            )

            Node.GetOutPort(0).Connect(nodeShaderReflectionColInput)
        if mat[c4d.MATERIAL_USE_REFLECTION]:
            layer = mat.GetReflectionLayerIndex(0)
            caca = mat[layer.GetDataID() + c4d.REFLECTION_LAYER_TRANS_TEXTURE]
            if caca:
                if caca.GetType() == 5833:
                    # Texture Node:
                    Node = gvNodeMaster.CreateNode(nodeRoot, 1036227, None, 10, 465)
                    Node[c4d.GV_REDSHIFT_SHADER_META_CLASSNAME] = "TextureSampler"
                    fileName = caca[c4d.BITMAPSHADER_FILENAME]
                    Node[
                        (
                            c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0,
                            c4d.REDSHIFT_FILE_PATH,
                        )
                    ] = fileName

                    nodeShaderReflectionColInput = RShader.AddPort(
                        c4d.GV_PORT_INPUT,
                        c4d.DescID(
                            c4d.DescLevel(c4d.REDSHIFT_SHADER_MATERIAL_REFL_COLOR)
                        ),
                        message=True,
                    )

                    Node.GetOutPort(0).Connect(nodeShaderReflectionColInput)

        for x in skinMats:  # Skin Stuff...
            if x in matName:
                RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_WEIGHT] = 0.4
                RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS] = 0.4

        if "Eyelash" in matName:
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_WEIGHT] = 0.0
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(
                0.0, 0.0, 0.0
            )

        if "Teeth" in matName:
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_WEIGHT] = 0.85
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS] = 0.35

        if "Cornea" in matName or "Tear" in matName or "Reflection" in matName:
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_WEIGHT] = 1.0
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS] = 0.0
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFR_WEIGHT] = 1.0
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_DIFFUSE_COLOR] = c4d.Vector(
                0.0, 0.0, 0.0
            )
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_IOR] = 1.8

        if "Moisture" in matName:
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_WEIGHT] = 1.0
            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS] = 0.0

            RShader[c4d.REDSHIFT_SHADER_MATERIAL_REFR_WEIGHT] = 1.0

        c4d.EventAdd()


class convertMaterials:
    def _GetNextHierarchyObject(self, op):
        """Return the next object in hieararchy."""
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
            bmpShader[c4d.VRAY_SHADERS_LIST] = 10  # Set as Bitmap Shader
            bc = bmpShader.GetData()
            # bc[89981968] = 2 # Sets to sRGB but no - leave as default.
            bc.SetFilename(4999, bmpPath)
            bmpShader.SetData(bc)
            mat.InsertShader(bmpShader)
            if slotName == "diffuse":
                mat[c4d.VRAYSTDMATERIAL_DIFFUSECOLOR_TEX] = bmpShader
            if slotName == "mapRough":
                mat[c4d.VRAYSTDMATERIAL_REFLECTGLOSSINESS_TEX] = bmpShader
            if slotName == "bump":
                mat[c4d.VRAYSTDMATERIAL_BUMP_BUMPMAP] = bmpShader
                try:
                    mat[c4d.VRAYSTDMATERIAL_BUMP_BUMPMAP_MULT] = 0.2
                except:
                    pass
            if slotName == "mapAlpha":
                mat[c4d.VRAYSTDMATERIAL_OPACITY_TEX] = bmpShader
            if slotName == "mapSpec":
                mat[c4d.VRAYSTDMATERIAL_REFLECTCOLOR] = c4d.Vector(0.0, 0.0, 0.0)
                mat[c4d.VRAYSTDMATERIAL_REFLECTGLOSSINESS] = 0.7
                mat[c4d.VRAYSTDMATERIAL_REFLECTFRESNELIOR_LOCK] = False
                mat[c4d.VRAYSTDMATERIAL_REFLECTCOLOR_TEX] = bmpShader
                try:
                    mat[c4d.VRAYSTDMATERIAL_REFLECTCOLOR_TEX][
                        107820085
                    ] = True  # ALPHA_FROM_INTENSITY
                except:
                    pass

        bmpPath = r""

        # To all Octane mats... With or without Bitmap:
        if self.matType == "Octane":
            mat[c4d.OCT_MATERIAL_TYPE] = 2511  # Glossy
            mat[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = sourceMat[c4d.MATERIAL_COLOR_COLOR]
            mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.3
            if "LENS" in mat.GetName():
                mat[c4d.OCT_MATERIAL_OPACITY_FLOAT] = 0.0
            if "Moisture" in mat.GetName():
                mat[c4d.OCT_MATERIAL_TYPE] = 2513  # Specular
                mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.0
            if "Cornea" in mat.GetName():
                mat[c4d.OCT_MATERIAL_TYPE] = 2513  # Specular
                mat[c4d.OCT_MATERIAL_INDEX] = 2.8
                mat[c4d.OCT_MATERIAL_OPACITY_FLOAT] = 0.2
                mat[c4d.OCT_MATERIAL_ROUGHNESS_FLOAT] = 0.0
            if "Mouth" in mat.GetName():
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

        if self.matType == "Std":
            bmpShader = c4d.BaseList2D(
                c4d.Xbitmap
            )  # create a bitmap shader for the material
            bmpShader[c4d.BITMAPSHADER_FILENAME] = bmpPath
            mat.InsertShader(bmpShader)
            mat[dstSlotID] = bmpShader
        elif self.matType == "Vray":
            mat[c4d.VRAYSTDMATERIAL_DIFFUSECOLOR] = sourceMat[c4d.MATERIAL_COLOR_COLOR]
            mat[c4d.VRAYSTDMATERIAL_REFRACTCOLOR] = sourceMat[
                c4d.MATERIAL_TRANSPARENCY_COLOR
            ]
            mat[c4d.VRAYSTDMATERIAL_REFRACTIOR] = sourceMat[
                c4d.MATERIAL_TRANSPARENCY_REFRACTION
            ]

            extraMapGlossyRough = dazToC4Dutils().findTextInFile(
                sourceMat.GetName(), "Glossy_Roughness_Map"
            )

            # If Bitmap found:
            if diffuseMap != None:
                makeVrayShader("diffuse", diffuseMap)
            if mapBump != None:
                makeVrayShader("bump", mapBump)
            if mapSpec != None:
                makeVrayShader("mapSpec", mapSpec)
            if mapAlpha != None:
                makeVrayShader("mapAlpha", mapAlpha)
            if extraMapGlossyRough != None:
                makeVrayShader("mapRough", extraMapGlossyRough)

            # Extra adjust.. specular and stuff..
            matName = mat.GetName()
            if "Cornea" in matName or "Sclera" in matName or "Pupil" in matName:
                mat[c4d.VRAYSTDMATERIAL_REFLECTCOLOR] = c4d.Vector(1, 1, 1)
                mat[c4d.VRAYSTDMATERIAL_REFLECTFRESNELIOR_LOCK] = False
                mat[c4d.VRAYSTDMATERIAL_REFLECTFRESNELIOR] = 1.6
            if "Mouth" in matName or "Teeth" in matName:
                mat[c4d.VRAYSTDMATERIAL_REFLECTCOLOR] = c4d.Vector(0.8, 0.8, 0.8)
                mat[c4d.VRAYSTDMATERIAL_REFLECTFRESNELIOR_LOCK] = False
                mat[c4d.VRAYSTDMATERIAL_REFLECTFRESNELIOR] = 1.6

        elif self.matType == "Redshift":
            bmpShader = mat.CreateShader(dstSlotID, "TextureSampler")
            bmpShader[
                c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0, c4d.REDSHIFT_FILE_PATH
            ] = bmpPath.encode("utf-8")
        elif self.matType == "Octane":
            bmpShader = c4d.BaseList2D(1029508)

            if isinstance(bmpPath, str):
                bmpShader[c4d.IMAGETEXTURE_FILE] = bmpPath
                bmpShader[c4d.IMAGETEXTURE_MODE] = 0
                bmpShader[c4d.IMAGETEXTURE_GAMMA] = 2.2
                bmpShader[c4d.IMAGETEX_BORDER_MODE] = 0
                if slotName == "diffuse":
                    mat[c4d.OCT_MATERIAL_DIFFUSE_LINK] = bmpShader
                    mat[c4d.OCT_MATERIAL_DIFFUSE_COLOR] = sourceMat[
                        c4d.MATERIAL_COLOR_COLOR
                    ]
                if slotName == "alpha":
                    mat[c4d.OCT_MATERIAL_OPACITY_LINK] = bmpShader
                    mat[c4d.OCT_MATERIAL_OPACITY_LINK][c4d.IMAGETEXTURE_GAMMA] = 0.5

                if slotName == "glossy":
                    mat[c4d.OCT_MATERIAL_ROUGHNESS_LINK] = bmpShader
                mat[c4d.OCT_MATERIAL_TYPE] = 2511  # Glossy
                mat.InsertShader(bmpShader)
                mat.Message(c4d.MSG_UPDATE)

                c4d.DrawViews(
                    c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
                    | c4d.DRAWFLAGS_NO_THREAD
                    | c4d.DRAWFLAGS_STATICBREAK
                )
                mat.Message(c4d.MSG_UPDATE)
                mat.Update(True, True)
                c4d.EventAdd()

        elif self.matType == "Corona":
            bmpShader = c4d.BaseList2D(
                c4d.Xbitmap
            )  # create a bitmap shader for the material
            bmpShader[1036473] = bmpPath
            mat.InsertShader(bmpShader)
            mat[dstSlotID] = bmpShader

        return True

    def convertMat(self, sourceMat, matType="Std"):

        self.matType = matType

        print("----- Converting : " + sourceMat.GetName() + " -----")

        matName = sourceMat.GetName()
        mat = None

        if matType == "Std":
            mat = c4d.BaseMaterial(5703)
            self.MatNameAdd = "_STD"
        elif matType == "Vray":
            mat = c4d.BaseMaterial(1038954)
            self.MatNameAdd = "_VR"
        elif matType == "Redshift":
            mat = RedshiftMaterial()
            self.MatNameAdd = "_RS"
        elif matType == "Octane":
            mat = c4d.BaseMaterial(1029501)
            self.MatNameAdd = "_OCT"
        elif matType == "Corona":
            mat = c4d.BaseMaterial(1032100)
            self.MatNameAdd = "_CRNA"

        mat.SetName(matName + self.MatNameAdd)
        self.NewMatList.append([sourceMat, mat])

        self.convertShader(sourceMat, mat)

        if mat == None:
            return False

        mat.Message(c4d.MSG_UPDATE)
        mat.Update(True, True)

        doc = c4d.documents.GetActiveDocument()
        doc.InsertMaterial(mat)
        c4d.EventAdd()

        print("----- Converted : " + matName + " : " + mat.GetName() + " -----")
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

    def convertTo(self, matType="Std"):
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

        if matType == "Octane":
            dzc4d.del_unused_mats()
            c4d.CallCommand(100004766, 100004766)  # Select All
            c4d.CallCommand(100004819, 100004819)  # Cut
            c4d.CallCommand(100004821, 100004821)  # Paste

        return True


def _GetNextHierarchyObject(op):
    """Return the next object in hieararchy."""
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
