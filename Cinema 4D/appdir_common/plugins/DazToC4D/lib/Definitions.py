import os

HOME_DIR = os.path.expanduser("~")
ROOT_DIR = os.path.join(HOME_DIR, "Documents", "DAZ 3D", "Bridges", "Daz To C4D")
EXPORT_DIR = os.path.join(ROOT_DIR, "Exports")

LIB_DIR = os.path.dirname(__file__)
PLUGIN_DIR = os.path.dirname(LIB_DIR)
RES_DIR = os.path.join(PLUGIN_DIR, "res")
