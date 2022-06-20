import os
import platform

if (platform.system() == "Windows"):
    try:
        import ctypes.wintypes
        CSIDL_PERSONAL=5
        SHGFP_TYPE_CURRENT=0
        buffer = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(0, CSIDL_PERSONAL, 0, SHGFP_TYPE_CURRENT, buffer)
        HOME_DIR = buffer.value
    except:
        HOME_DIR = os.path.expanduser("~").replace("\\","/") + "/Documents"
        print(f"ERROR: unable to query the correct Documents path for Windows, failing back to user folder=\"{HOME_DIR}\".")
elif (platform.system() == "Darwin"):
    HOME_DIR = os.path.expanduser("~") + "/Documents"
else:
    HOME_DIR = os.path.expanduser("~")

ROOT_DIR = os.path.join(HOME_DIR, "DAZ 3D", "Bridges", "Daz To Cinema 4D")
EXPORT_DIR = os.path.join(ROOT_DIR, "Exports")

LIB_DIR = os.path.dirname(__file__)
PLUGIN_DIR = os.path.dirname(LIB_DIR)
RES_DIR = os.path.join(PLUGIN_DIR, "res")
