import os

import c4d

from .MaterialHelpers import MaterialHelpers
from .dependencies.RedshiftWrapper.Redshift import Redshift
from .TextureLib import texture_library

try:
    import redshift

except ImportError:
    print("DaztoC4D : Redshift not installed can not convert.")


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
            print("DaztoC4D : Redshift not installed can not convert.")
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
                    rs_material.ExposeParameter(
                        c4d.REDSHIFT_SHADER_MATERIAL_DIFFUSE_COLOR, c4d.GV_PORT_INPUT
                    )
                    rs.CreateConnection(texture_node, rs_material, 0, 0)
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
                    rs.CreateConnection(texture_node, bump_node, 0, 0)
                    rs.CreateConnection(bump_node, rs_material, 0, 0)
                    bump_exists = True
        for prop_name in lib["normal"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    strength = prop[prop_name]["Value"]
                    strength = self.check_value("float", strength)
                    texture_node = self.create_texture_rs(path, rs, -100, -200)
                    normal_node = rs.CreateShader("BumpMap", 0, 0)
                    normal_node[c4d.REDSHIFT_SHADER_BUMPMAP_INPUTTYPE] = 1
                    normal_node.ExposeParameter(
                        c4d.REDSHIFT_SHADER_BUMPMAP_INPUT, c4d.GV_PORT_INPUT
                    )
                    normal_node[c4d.REDSHIFT_SHADER_BUMPMAP_SCALE] = (
                        strength * self.normal_value / 100
                    )
                    rs.CreateConnection(texture_node, normal_node, 0, 0)
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
            rs.CreateConnection(bump_node, bump_blend, 0, 0)
            rs.CreateConnection(normal_node, bump_blend, 0, 1)
            rs.CreateConnection(bump_blend, rs_material, 0, 1)
        elif normal_exists:
            rs.CreateConnection(normal_node, rs_material, 0, 1)
        elif bump_exists:
            rs.CreateConnection(bump_node, rs_material, 0, 1)
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
                    rs_material.ExposeParameter(
                        c4d.REDSHIFT_SHADER_MATERIAL_REFL_ROUGHNESS, c4d.GV_PORT_INPUT
                    )
                    rs.CreateConnection(texture_node, rs_material, 0, 2)
                if value > 0:
                    rs_material[c4d.REDSHIFT_SHADER_MATERIAL_REFL_WEIGHT] = value
                rs_material[c4d.REDSHIFT_SHADER_MATERIAL_REFL_BRDF] = 1

        for prop_name in lib["metalness"]["Name"]:
            if prop_name in prop.keys():
                if prop[prop_name]["Texture"] != "":
                    path = prop[prop_name]["Texture"]
                    texture_node = self.create_texture_rs(path, rs, 10, 400)
                    rs_material[c4d.REDSHIFT_SHADER_MATERIAL_REFL_FRESNEL_MODE] = 2
                    rs_material.ExposeParameter(
                        c4d.REDSHIFT_SHADER_MATERIAL_REFL_REFLECTIVITY,
                        c4d.GV_PORT_INPUT,
                    )
                    rs.CreateConnection(texture_node, rs_material, 0, 3)

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
        c4d.EventAdd()

    def makeRSmat(self, mat, prop):
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

        def getRSnode(mat):
            gvNodeMaster = redshift.GetRSMaterialNodeMaster(mat)
            rootNode_ShaderGraph = gvNodeMaster.GetRoot()
            output = rootNode_ShaderGraph.GetDown()
            RShader = output.GetNext()
            return RShader

        matName = mat.GetName()
        matDiffuseColor = mat[c4d.MATERIAL_COLOR_COLOR]

        INPORT = 0
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

        extraMapGlossyRough = self.find_map_by_type("roughness", prop)
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
