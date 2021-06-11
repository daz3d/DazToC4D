import os
import c4d

from .TextureLib import texture_library

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


class MaterialHelpers:
    material_dict = {}

    @staticmethod
    def create_texture(mat, path):
        path = str(path)
        path = os.path.abspath(path)
        texture = c4d.BaseList2D(c4d.Xbitmap)
        texture[c4d.BITMAPSHADER_FILENAME] = path
        mat.InsertShader(texture)
        return texture

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
