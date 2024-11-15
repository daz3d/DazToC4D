import c4d
from .TextureLib import texture_library
from .MaterialHelpers import MaterialHelpers, convert_color, convert_to_vector


class StdMaterials(MaterialHelpers):
    use_makeup_layer = False
    makeup_layer_shader = None

    def __init__(self):
        self.use_makeup_layer = False

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
                # self.set_up_makeup(mat, prop)
                self.set_up_transmission(mat, prop)
                self.set_up_diffuse(mat, prop)
                self.set_up_daz_mat(mat, prop)
                self.set_up_bump_normal(mat, prop)
                self.set_up_alpha(mat, prop)
                self.set_up_translucency(mat, prop)
                self.set_up_tiling(mat_obj, mat, prop)
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

    def set_up_makeup(self, mat, prop):  
        return
        # DB 2023-June-19: PBRSkin Makeup Support
        lib = texture_library

        # DB 2023-June-19: Create a new layer-based shader for makeup blending
        # 1. Retrieve makeup weight, makeup base, and diffuse texture paths
        # 2. Create a layer-based shader
        # 3. Add diffuse texture to layer 1 and set blending mode to "Normal"
        # 4. Add makeup weight to layer 2 and set blending mode to "Mask"
        # 5. Add makeup base to layer 3 and set blending mode to "Normal"
        makeup_base_texture = None
        makeup_weight_texture = None
        diffuse_texture = None
        for prop_name in lib["makeup-weight"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    makeup_weight_value = prop[prop_name]["Value"]
                    makeup_weight_value = self.check_value("float", makeup_weight_value)
                    makeup_weight_path = prop[prop_name]["Texture"]
                    makeup_weight_texture = StdMaterials.create_texture(mat, makeup_weight_path)
                    print("DEBUG (ln 73, StandardMaterials.py): makeup_weight_texture = " + str(makeup_weight_texture))
        for prop_name in lib["makeup-base"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    hex_str = prop[prop_name]["Value"]
                    hex_str = self.check_value("hex", hex_str)
                    color = convert_color(hex_str)
                    makeup_base_color_vector = c4d.Vector(color[0], color[1], color[2])
                    makeup_base_path = prop[prop_name]["Texture"]
                    makeup_base_texture = StdMaterials.create_texture(mat, makeup_base_path)
                    print("DEBUG (ln 84, StandardMaterials.py): makeup_base_texture = " + str(makeup_base_texture))
        for prop_name in lib["color"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    hex_str = prop[prop_name]["Value"]
                    hex_str = self.check_value("hex", hex_str)
                    color = convert_color(hex_str)
                    diffuse_color_vector = c4d.Vector(color[0], color[1], color[2])
                    diffuse_path = prop[prop_name]["Texture"]
                    diffuse_texture = StdMaterials.create_texture(mat, diffuse_path)
        if makeup_weight_texture and makeup_base_texture and diffuse_texture:
            self.use_makeup_layer = True
            # create a layer-based shader
            makeup_layer_shader = c4d.BaseShader(c4d.Xlayer)
            # add layers to the shader
            layer1 =makeup_layer_shader.AddLayer(c4d.TypeShader)
            layer2 = makeup_layer_shader.AddLayer(c4d.TypeShader)
            layer3 = makeup_layer_shader.AddLayer(c4d.TypeShader)

            # assign textures to bitmap shaders and assign bitmap shaders to layers
            # layer2[c4d.BITMAPSHADER_COLOR_SHADER] = makeup_weight_texture
            # layer2[c4d.BITMAPSHADER_COLOR_TEXTUREMIXING] = c4d.MATERIAL_TEXTUREMIXING_MULTIPLY
            # layer3[c4d.BITMAPSHADER_COLOR_SHADER] = makeup_base_texture
            # layer3[c4d.BITMAPSHADER_COLOR_TEXTUREMIXING] = c4d.MATERIAL_TEXTUREMIXING_MULTIPLY
            # layer1[c4d.BITMAPSHADER_COLOR_SHADER] = diffuse_texture
            # layer1[c4d.BITMAPSHADER_COLOR_TEXTUREMIXING] = c4d.MATERIAL_TEXTUREMIXING_MULTIPLY
            layer1.SetParameter(c4d.LAYER_S_PARAM_SHADER_LINK, diffuse_texture)
            layer2.SetParameter(c4d.LAYER_S_PARAM_SHADER_LINK, makeup_weight_texture)
            layer3.SetParameter(c4d.LAYER_S_PARAM_SHADER_LINK, makeup_base_texture)

            # # set layer blending modes
            # layer1[c4d.XLAYER_BLENDING_MODE] = c4d.XLAYER_BLENDING_MODE_NORMAL
            # layer2[c4d.XLAYER_BLENDING_MODE] = c4d.XLAYER_BLENDING_MODE_MASK
            # layer3[c4d.XLAYER_BLENDING_MODE] = c4d.XLAYER_BLENDING_MODE_NORMAL
            layer1.SetParameter(c4d.LAYER_S_PARAM_SHADER_MODE, 0)
            layer2.SetParameter(c4d.LAYER_S_PARAM_SHADER_MODE, 20)
            layer3.SetParameter(c4d.LAYER_S_PARAM_SHADER_MODE, 0)

            # connect layer to material
            mat[c4d.MATERIAL_USE_COLOR] = True
            #mat[c4d.MATERIAL_COLOR_SHADER] = makeup_layer_shader
            #mat[c4d.MATERIAL_COLOR_TEXTUREMIXING] = c4d.MATERIAL_TEXTUREMIXING_MULTIPLY
            mat.InsertShader(makeup_layer_shader)
            mat.SetParameter(c4d.MATERIAL_COLOR_SHADER, makeup_layer_shader, c4d.DESCFLAGS_SET_0)
            # self.makeup_layer_shader = makeup_layer_shader

        return

    def set_up_diffuse(self, mat, prop):
        lib = texture_library

        if self.is_diffuse(prop):
            # DB 2022-June-03: New Standard Color Channel Assignment
            # Creating an empty "Color" layer to fix error in R25+ about...
            #   "Unable to find..." diffuse texture during "Save Project with Assets"
            #    operations and Rendering.
            for prop_name in lib["color"]["Name"]:
                if prop_name in prop.keys():
                    hex_str = "#000000"
                    hex_str = self.check_value("hex", hex_str)
                    color = convert_color(hex_str)
                    vector = c4d.Vector(color[0], color[1], color[2])
                    mat[c4d.MATERIAL_USE_COLOR] = False
                    mat[c4d.MATERIAL_COLOR_COLOR] = vector
                    mat[c4d.MATERIAL_COLOR_SHADER] = None
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
            layer_shader = c4d.BaseShader(c4d.Xlayer)
            mat.InsertShader(layer_shader)
            mat[
                diffuse.GetDataID() + c4d.REFLECTION_LAYER_COLOR_TEXTURE
            ] = layer_shader
            mat.SetParameter(c4d.REFLECTION_LAYER_COLOR_TEXTURE, layer_shader, c4d.DESCFLAGS_SET_0)

            for prop_name in lib["color"]["Name"]:
                if prop_name in prop.keys():
                    if prop[prop_name]["Texture"] != "":
                        # Texture to new layer
                        path = prop[prop_name]["Texture"]
                        texture = StdMaterials.create_texture(mat, path)
                        try:
                            layer = layer_shader.AddLayer(c4d.TypeShader)
                            layer.SetParameter(c4d.LAYER_S_PARAM_SHADER_LINK, texture)
                            layer.SetParameter(c4d.LAYER_S_PARAM_SHADER_MODE, 0)
                        except:
                            mat[
                                diffuse.GetDataID() + c4d.REFLECTION_LAYER_COLOR_TEXTURE
                            ] = texture
                        # Color Value
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

            for prop_name in lib["makeup-weight"]["Name"]:
                if prop_name in prop.keys():
                    if prop[prop_name]["Texture"] != "":
                        makeup_weight_value = prop[prop_name]["Value"]
                        makeup_weight_value = self.check_value("float", makeup_weight_value)
                        makeup_weight_path = prop[prop_name]["Texture"]
                        texture = StdMaterials.create_texture(mat, makeup_weight_path)
                        texture.SetParameter(c4d.BITMAPSHADER_COLORPROFILE, c4d.BITMAPSHADER_COLORPROFILE_LINEAR, c4d.DESCFLAGS_SET_0)
                        try:
                            layer = layer_shader.AddLayer(c4d.TypeShader)
                            layer.SetParameter(c4d.LAYER_S_PARAM_SHADER_LINK, texture)
                            layer.SetParameter(c4d.LAYER_S_PARAM_SHADER_MODE, 20)
                            #print("DEBUG (ln 198, StandardMaterials.py): makeup_weight_path = " + str(makeup_weight_path))
                        except:
                            print("Error: Could not add makeup layer to shader, requires support for AddLayer function.")

            for prop_name in lib["makeup-base"]["Name"]:
                if prop_name in prop.keys():
                    if prop[prop_name]["Texture"] != "":
                        hex_str = prop[prop_name]["Value"]
                        hex_str = self.check_value("hex", hex_str)
                        color = convert_color(hex_str)
                        makeup_base_color_vector = c4d.Vector(color[0], color[1], color[2])
                        makeup_base_path = prop[prop_name]["Texture"]
                        texture = StdMaterials.create_texture(mat, makeup_base_path)
                        try:
                            layer = layer_shader.AddLayer(c4d.TypeShader)
                            layer.SetParameter(c4d.LAYER_S_PARAM_SHADER_LINK, texture)
                            layer.SetParameter(c4d.LAYER_S_PARAM_SHADER_MODE, 0)
                            #print("DEBUG (ln 212, StandardMaterials.py): makeup_weight_path = " + str(makeup_base_path))
                        except:
                            print("Error: Could not add makeup layer to shader, requires support for AddLayer function.")


    def set_up_daz_mat(self, mat, prop):
        lib = texture_library
        daz_mat = mat.AddReflectionLayer()
        daz_mat.SetName("Daz Material Layer")
        mat[
            daz_mat.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION
        ] = c4d.REFLECTION_DISTRIBUTION_GGX

        if self.is_metal(prop):
            # TODO: only enable "REFLECTION_ADDITIVE_MODE_METAL" for non-skin
            # mat[
            #     daz_mat.GetDataID() + c4d.REFLECTION_LAYER_MAIN_ADDITIVE
            # ] = c4d.REFLECTION_ADDITIVE_MODE_METAL
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
                    try:
                        strength = float(prop[prop_name]["Value"])
                    except:
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
       
    def set_up_tiling(self, obj, mat, prop):
        lib = texture_library
        for prop_name in lib["tile-x"]["Name"]:
            if prop_name in prop.keys():
                try:
                    tile_x = float(prop[prop_name]["Value"])
                except:
                    tile_x = prop[prop_name]["Value"]

        for prop_name in lib["tile-y"]["Name"]:
            if prop_name in prop.keys():
                try:
                    tile_y = float(prop[prop_name]["Value"])
                except:
                    tile_y = prop[prop_name]["Value"]
        
        for prop_name in lib["tile-offset-x"]["Name"]:
            if prop_name in prop.keys():
                try:
                    offset_x = float(prop[prop_name]["Value"])
                except:
                    offset_x = prop[prop_name]["Value"]
        
        for prop_name in lib["tile-offset-y"]["Name"]:
            if prop_name in prop.keys():
                try:
                    offset_y = float(prop[prop_name]["Value"])
                except:
                    offset_y = prop[prop_name]["Value"]

        if (tile_x and tile_y):
            texture_tag = self.get_texture_tag_by_name(obj, mat.GetName())
            if texture_tag:
                texture_tag[c4d.TEXTURETAG_TILESX] = tile_x
                texture_tag[c4d.TEXTURETAG_TILESY] = tile_y

        if (offset_x and offset_y):
            texture_tag = self.get_texture_tag_by_name(obj, mat.GetName())
            if texture_tag:
                texture_tag[c4d.TEXTURETAG_OFFSETX] = offset_x
                texture_tag[c4d.TEXTURETAG_OFFSETY] = offset_y

    def get_texture_tag_by_name(self, obj, tag_name):
        i = 0
        tag = obj.GetTag(c4d.Ttexture, i)
        while tag:
            if tag.GetName() == tag_name:
                return tag
            i += 1
            tag = obj.GetTag(c4d.Ttexture, i)
        return None
