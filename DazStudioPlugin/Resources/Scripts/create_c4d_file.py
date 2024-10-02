import c4d
from c4d import gui
import sys, json, os, shutil

from pathlib import Path
script_dir = str(Path( __file__ ).parent.absolute())

try:
    import plugins
except:
    c4d_exe_path=os.path.dirname(sys.executable).replace("\\","/")
    print("DEBUG: c4dpath=" + c4d_exe_path)
    sys.path.append(c4d_exe_path)
    sys.path.append(script_dir)
import DazToC4D.lib.DtuLoader as DtuLoader
import DazToC4D.lib.Definitions as Definitions
import DazToC4D.lib.CustomImports as CustomImports

g_logfile = ""

def _print_usage():
    print("\nUSAGE: c4dpy.exe create_c4d_file.py <fbx file>\n")

def _add_to_log(message):
    if (g_logfile == ""):
        logfile = script_dir + "/create_c4d.log"
    else:
        logfile = g_logfile

    print(str(message))
    with open(logfile, "a") as file:
        file.write(str(message) + "\n")


# Main function
def _main(argv):
    try:
        line = str(argv[-1])
    except:
        _print_usage()
        return

    fbx_path = line.replace("\\","/").strip()
    if (not os.path.exists(fbx_path)):
        _add_to_log("ERROR: main(): fbx file not found: " + str(fbx_path))
        raise Exception("FBX file not found: " + str(fbx_path))

    if ("B_FIG" in fbx_path):
        json_path = fbx_path.replace("B_FIG.fbx", "FIG.dtu")
    elif ("B_ENV" in fbx_path):
        json_path = fbx_path.replace("B_ENV.fbx", "ENV.dtu")
    else:
        json_path = fbx_path.replace(".fbx", ".dtu")

    custom_importer = CustomImports.CustomImports()
    os.chdir(Definitions.EXPORT_DIR)
    imported_dir = os.path.dirname(json_path)
    _add_to_log("DEBUG: Import path: " + imported_dir + "...");
    dtu = DtuLoader.DtuLoader(imported_dir)
    if ("FIG" in fbx_path):
        custom_importer.genesis_import(fbx_path, dtu, 0, 0, 0)
    else:
        custom_importer.prop_import(fbx_path, dtu, 0, 0, 0)

    if "Output C4D Filepath" in dtu.dtu_dict:
        destination_file_path = dtu.dtu_dict["Output C4D Filepath"]
    else:
        raise Exception("Output C4D Filepath not found in dtu_dict")

    doc = c4d.documents.GetActiveDocument()
    missingAssets = []
    assets = []

    result = c4d.documents.SaveProject(doc,
        c4d.SAVEPROJECT_ASSETS | c4d.SAVEPROJECT_SCENEFILE | c4d.SAVEPROJECT_DONTFAILONMISSINGASSETS,
        destination_file_path, assets, missingAssets)

    if not result:
        _add_to_log("ERROR: Failed trying to save project: " + destination_file_path)
        return

    _add_to_log("C4D Project Saved: " + str(destination_file_path))


# Execute main()
if __name__=='__main__':
    print("Starting script...")
    _add_to_log("Starting script... DEBUG: sys.argv=" + str(sys.argv))
    _main(sys.argv[1:])
    print("script completed.")
    exit(0)
