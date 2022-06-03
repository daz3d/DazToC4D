import c4d
from .TextureLib import texture_library
from .MaterialHelpers import MaterialHelpers, convert_color, convert_to_vector


class StdMaterials(MaterialHelpers):
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
            # DB 2022-June-03: New Standard Color Channel Assignment
            # Adding the diffuse texture file here fixes errors in C4D r25 about
            #   "Unable to find..." diffuse texture during "Save Project with Assets"
            #    operations.
            for prop_name in lib["color"]["Name"]:
                if prop_name in prop.keys():
                    if prop[prop_name]["Texture"] != "":
                        path = prop[prop_name]["Texture"]
                        hex_str = prop[prop_name]["Value"]
                        hex_str = self.check_value("hex", hex_str)
                        color = convert_color(hex_str)
                        vector = c4d.Vector(color[0], color[1], color[2])
                        texture = StdMaterials.create_texture(mat, path)
                        mat[c4d.MATERIAL_USE_COLOR] = True
                        mat[c4d.MATERIAL_COLOR_SHADER] = texture
                        mat[c4d.MATERIAL_COLOR_COLOR] = vector
                        mat[c4d.MATERIAL_COLOR_TEXTUREMIXING] = c4d.MATERIAL_TEXTUREMIXING_MULTIPLY

            # Original Code: ?Adds IrayUber Diffuse Component as a Custom "Diffuse
            #   Layer" to the C4D Reflection Channel? I am uncertain about the
            #   full intent of this code block, leaving for now.
            #   -DB (2022-June-03)
            diffuse = mat.AddReflectionLayer()
            diffuse.SetName("Diffuse Layer")
            mat[
                diffuse.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION
            ] = c4d.REFLECTION_DISTRIBUTION_LAMBERTIAN
            for prop_name in lib["color"]["Name"]:
                if prop_name in prop.keys():
                    if prop[prop_name]["Texture"] != "":
                        path = prop[prop_name]["Texture"]
                        texture = StdMaterials.create_texture(mat, path)
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
                    texture = StdMaterials.create_texture(mat, path)
                    mat[
                        daz_mat.GetDataID() + c4d.REFLECTION_LAYER_COLOR_TEXTURE
                    ] = texture
        for prop_name in lib["roughness"]["Name"]:
            if prop_name in prop.keys():
                value = prop[prop_name]["Value"]
                value = self.check_value("float", value)
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    texture = StdMaterials.create_texture(mat, path)
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
                    texture = StdMaterials.create_texture(mat, path)
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
                    texture = StdMaterials.create_texture(mat, path)
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
                    texture = StdMaterials.create_texture(mat, path)
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
                    texture = StdMaterials.create_texture(mat, path)
                    mat[c4d.MATERIAL_USE_BUMP] = True
                    mat[c4d.MATERIAL_BUMP_SHADER] = texture
                    mat[c4d.MATERIAL_BUMP_STRENGTH] = strength * self.bump_value / 100

        for prop_name in lib["normal"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    strength = prop[prop_name]["Value"]
                    strength = self.check_value("float", strength)
                    texture = StdMaterials.create_texture(mat, path)
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
                    texture = StdMaterials.create_texture(mat, path)
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
                        texture = StdMaterials.create_texture(mat, path)
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
