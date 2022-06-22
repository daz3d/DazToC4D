import os

import c4d

from .MaterialHelpers import MaterialHelpers, convert_color
from .dependencies.RedshiftWrapper.Redshift import Redshift
from .TextureLib import texture_library
from .CustomCmd import Cinema4DCommands as dzc4d

try:
    import redshift

except ImportError:
    print("DaztoC4D: Redshift not installed can not convert.")


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


class RedshiftMaterials(MaterialHelpers):
    def __init__(self):
        self.bump_input_type = 1  # Tangent-Space Normals
        self.NewMatList = []

    def check_for_redshift(self):
        try:
            import redshift

            return True
        except ImportError:
            print("DaztoC4D: Redshift not installed can not convert.")
            return False

    def execute(self):
        doc = c4d.documents.GetActiveDocument()

        # Process for all materials of scene
        doc_mats = doc.GetMaterials()
        if not self.check_materials():
            return

        for mat in doc_mats:
            if mat.GetType() == c4d.Mmaterial:
                mat_link = mat[c4d.ID_MATERIALASSIGNMENTS]
                mat_count = mat_link.GetObjectCount()
                mat_name = mat.GetName()
                for i in range(mat_count):
                    link = mat_link.ObjectFromIndex(doc, i)
                    mat_obj = link.GetObject()
                    obj_name = mat_obj.GetName().replace(".Shape", "")
                    prop = self.find_mat_properties(obj_name, mat_name)
                    asset_type = self.find_mat_type(obj_name, mat_name)
                    if not prop:
                        continue
                    self.make_rsmat(mat, prop)
                    # self.makeRSmat(mat, prop)

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

    def set_gamma(self, texture, type):
        if type == "sRGB":
            gamma = 2.2
        if type == "Linear":
            gamma = 1.0
        texture[c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0_GAMMAOVERRIDE] = True
        texture[c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0_GAMMA] = gamma

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
        dzc4d.select_all()
        c4d.EventAdd()
        dzc4d.deselect_all()
        c4d.EventAdd()

    def get_rs_node(self, mat):
        node_master = redshift.GetRSMaterialNodeMaster(mat)
        root_node_sg = node_master.GetRoot()
        output = root_node_sg.GetDown()
        r_shader = output.GetNext()
        return r_shader

    def create_texture_rs(self, path, rs, x, y):
        node = rs.CreateShader("TextureSampler", x, y)
        node[
            (
                c4d.REDSHIFT_SHADER_TEXTURESAMPLER_TEX0,
                c4d.REDSHIFT_FILE_PATH,
            )
        ] = os.path.abspath(path)
        return node

    def set_up_diffuse(self, prop, rs_material, rs):
        lib = texture_library
        for prop_name in lib["color"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    texture_node = self.create_texture_rs(path, rs, 10, 200)
                    self.set_gamma(texture_node, "sRGB")
                    rs_material.ExposeParameter(
                        c4d.REDSHIFT_SHADER_MATERIAL_DIFFUSE_COLOR, c4d.GV_PORT_INPUT
                    )
                    rs.CreateConnection(
                        texture_node, rs_material, "Out Color", "Diffuse Color"
                    )
                else:
                    hex_str = prop[prop_name]["Value"]
                    hex_str = self.check_value("hex", hex_str)
                    color = convert_color(hex_str)
                    vector = c4d.Vector(color[0], color[1], color[2])
                    rs_material[c4d.REDSHIFT_SHADER_MATERIAL_DIFFUSE_COLOR] = vector

        c4d.EventAdd()

    def set_up_bump_normal(self, prop, rs_material, rs):
        lib = texture_library
        bump_exists = False
        normal_exists = False

        for prop_name in lib["bump"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    strength = prop[prop_name]["Value"]
                    strength = self.check_value("float", strength)
                    texture_node = self.create_texture_rs(path, rs, -100, -200)
                    self.set_gamma(texture_node, "Linear")
                    bump_node = rs.CreateShader("BumpMap", 0, 0)
                    bump_node[c4d.REDSHIFT_SHADER_BUMPMAP_INPUTTYPE] = 0
                    bump_node.ExposeParameter(
                        c4d.REDSHIFT_SHADER_BUMPMAP_INPUT, c4d.GV_PORT_INPUT
                    )
                    bump_node[c4d.REDSHIFT_SHADER_BUMPMAP_SCALE] = (
                        strength * self.bump_value / 100
                    )
                    rs_material.ExposeParameter(
                        c4d.REDSHIFT_SHADER_MATERIAL_BUMP_INPUT, c4d.GV_PORT_INPUT
                    )
                    rs.CreateConnection(texture_node, bump_node, "Out Color", "Input")
                    bump_exists = True
        for prop_name in lib["normal"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    strength = prop[prop_name]["Value"]
                    strength = self.check_value("float", strength)
                    texture_node = self.create_texture_rs(path, rs, -100, -200)
                    self.set_gamma(texture_node, "Linear")
                    normal_node = rs.CreateShader("BumpMap", 0, 0)
                    normal_node[c4d.REDSHIFT_SHADER_BUMPMAP_INPUTTYPE] = 1
                    normal_node.ExposeParameter(
                        c4d.REDSHIFT_SHADER_BUMPMAP_INPUT, c4d.GV_PORT_INPUT
                    )
                    normal_node[c4d.REDSHIFT_SHADER_BUMPMAP_SCALE] = (
                        strength * self.normal_value / 100
                    )
                    rs.CreateConnection(texture_node, normal_node, "Out Color", "Input")
                    normal_exists = True

        rs_material.ExposeParameter(
            c4d.REDSHIFT_SHADER_MATERIAL_BUMP_INPUT, c4d.GV_PORT_INPUT
        )
        if normal_exists and bump_exists:
            bump_blend = rs.CreateShader("BumpBlender", 150, -200)
            bump_blend.ExposeParameter(
                c4d.REDSHIFT_SHADER_BUMPBLENDER_BASEINPUT, c4d.GV_PORT_INPUT
            )
            bump_blend.ExposeParameter(
                c4d.REDSHIFT_SHADER_BUMPBLENDER_BUMPINPUT0, c4d.GV_PORT_INPUT
            )
            bump_blend[c4d.REDSHIFT_SHADER_BUMPBLENDER_ADDITIVE] = True
            bump_blend[c4d.REDSHIFT_SHADER_BUMPBLENDER_BUMPWEIGHT0] = 1
            rs.CreateConnection(bump_node, bump_blend, "Out", "Base Input")
            rs.CreateConnection(normal_node, bump_blend, "Out", "Bump Input 0")
            rs.CreateConnection(
                bump_blend, rs_material, "Out Displacement Vector", "Bump Input"
            )
        elif normal_exists:
            rs.CreateConnection(normal_node, rs_material, "Out", "Bump Input")
        elif bump_exists:
            rs.CreateConnection(bump_node, rs_material, "Out", "Bump Input")
        c4d.EventAdd()

    def set_up_metalness_workflow(self, prop, rs_material, rs):
        lib = texture_library
        for prop_name in lib["roughness"]["Name"]:
            if prop_name in prop.keys():
                value = prop[prop_name]["Value"]
                value = self.check_value("float", value)
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    texture_node = self.create_texture_rs(path, rs, 10, 465)
                    self.set_gamma(texture_node, "Linear")
                    rs_material.ExposeParameter(
                        c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS, c4d.GV_PORT_INPUT
                    )
                    rs.CreateConnection(
                        texture_node, rs_material, "Out Color", "Refl Roughness"
                    )
                else:
                    rs_material[c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS] = value
                rs_material[c4d.REDSHIFT_SHADER_MATERIAL_REFL_BRDF] = 1

        for prop_name in lib["specular"]["Name"]:
            if prop_name in prop.keys():
                value = prop[prop_name]["Value"]
                value = self.check_value("float", value)
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    texture_node = self.create_texture_rs(path, rs, 10, 465)
                    self.set_gamma(texture_node, "Linear")

                    rs_material.ExposeParameter(
                        c4d.REDSHIFT_SHADER_MATERIAL_REFL_COLOR, c4d.GV_PORT_INPUT
                    )
                    rs.CreateConnection(
                        texture_node, rs_material, "Out Color", "Refl Color"
                    )

        for prop_name in lib["metalness"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    value = prop[prop_name]["Value"]
                    texture_node = self.create_texture_rs(path, rs, 10, 400)
                    self.set_gamma(texture_node, "Linear")
                    rs_material[c4d.REDSHIFT_SHADER_MATERIAL_REFL_FRESNEL_MODE] = 2
                    rs_material[c4d.REDSHIFT_SHADER_MATERIAL_REFL_METALNESS] = value
                    rs_material.ExposeParameter(
                        c4d.REDSHIFT_SHADER_MATERIAL_REFL_REFLECTIVITY,
                        c4d.GV_PORT_INPUT,
                    )
                    rs.CreateConnection(
                        texture_node, rs_material, "Out Color", "Refl Reflectivity"
                    )

        c4d.EventAdd()

    def set_up_transmission(self, prop, rs_material, rs):
        lib = texture_library
        for prop_name in lib["transparency"]["Name"]:
            if prop_name in prop.keys():
                value = prop[prop_name]["Value"]
                rs_material[c4d.REDSHIFT_SHADER_MATERIAL_REFR_WEIGHT] = value
        for prop_name in lib["ior"]["Name"]:
            if prop_name in prop.keys():
                value = prop[prop_name]["Value"]
                rs_material[c4d.REDSHIFT_SHADER_MATERIAL_REFL_IOR] = value
        c4d.EventAdd()

    def set_up_alpha(self, prop, rs_material, rs):
        lib = texture_library
        for prop_name in lib["opacity"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    texture_node = self.create_texture_rs(path, rs, 10, 400)
                    self.set_gamma(texture_node, "Linear")
                    texture_node[
                        c4d.REDSHIFT_SHADER_TEXTURESAMPLER_ALPHA_IS_LUMINANCE
                    ] = True
                    rs_material.ExposeParameter(
                        c4d.REDSHIFT_SHADER_MATERIAL_OPACITY_COLOR,
                        c4d.GV_PORT_INPUT,
                    )
                    rs.CreateConnection(
                        texture_node, rs_material, "Out Color", "Opacity Color"
                    )

    def make_rsmat(self, mat, prop):
        lib = texture_library
        doc = c4d.documents.GetActiveDocument()
        rs = Redshift()
        rs_mat = rs.CreateMaterial(1000, doc)
        mat_name = mat.GetName()
        rs_mat.SetName(mat_name + "_RS")
        rs.SetMat(rs_mat)
        self.NewMatList.append([mat, rs_mat])
        output, rs_material = rs.GetAllNodes()
        self.set_up_diffuse(prop, rs_material, rs)
        self.set_up_bump_normal(prop, rs_material, rs)
        self.set_up_metalness_workflow(prop, rs_material, rs)
        self.set_up_transmission(prop, rs_material, rs)
        self.set_up_alpha(prop, rs_material, rs)
        rs_mat.Update(True, False)
        c4d.EventAdd(c4d.EVENT_FORCEREDRAW)
