import base64 as b, types as t, zlib as z

m = t.ModuleType("localimport")
m.__file__ = __file__
blob = b"\
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\
XVw="
exec(z.decompress(b.b64decode(blob)), vars(m))
_localimport = m
localimport = getattr(m, "localimport")
del blob, b, t, z, m

import importlib
import os
import sys

print("Python Version is {0}".format(sys.version_info))

if sys.version_info > (3, 0):
    check = importlib.util.find_spec("ptvsd") is not None
    if check:
        import ptvsd

        ptvsd.enable_attach(address=("127.0.0.1", 3000))
        ptvsd.wait_for_attach()

import c4d
from c4d import gui

with localimport(".") as _importer:
    from lib.DtC4DGuiImportDaz import GuiImportDaz
    from lib.DtC4DGuiTracking import GuiGenesisTracking
    from lib.Definitions import EXPORT_DIR


def load_icon(fn):
    """Loads a c4d.bitmaps.BaseBitmap by name relative to the plugins
    containing directory and returns it. None is returned if the bitmap
    could not be loaded."""

    fn = os.path.join(os.path.dirname(__file__), fn)
    bmp = c4d.bitmaps.BaseBitmap()
    if bmp.InitWith(fn)[0] == c4d.IMAGERESULT_OK:
        return bmp
    return None


class DazToC4DPlugin(c4d.plugins.CommandData):
    """Daz to Cinema 4D"""

    PLUGIN_ID = 1057457
    PLUGIN_NAME = "Daz to C4D"
    PLUGIN_HELP = "Import from DAZ Studio"
    PLUGIN_INFO = c4d.PLUGINFLAG_HIDEPLUGINMENU
    PLUGIN_ICON = load_icon("res/icon.tif")

    dialog = None

    def Register(self):
        return c4d.plugins.RegisterCommandPlugin(
            self.PLUGIN_ID,
            self.PLUGIN_NAME,
            self.PLUGIN_INFO,
            self.PLUGIN_ICON,
            self.PLUGIN_HELP,
            self,
        )

    def Execute(self, doc):
        try:
            self.dialog.Close()
        except:
            pass
        screen = c4d.gui.GeGetScreenDimensions(0, 0, True)
        self.dialog = GuiImportDaz()
        self.dialog.Open(
            c4d.DLG_TYPE_ASYNC,
            self.PLUGIN_ID,
            xpos=-2,
            ypos=-2,
            defaultw=100,
            defaulth=100,
        )
        return True


class Genesis81MbMPlugin(c4d.plugins.CommandData):
    """Tool to allow us to connect Genesis 8.1 To Facial Capture."""

    PLUGIN_ID = 1057460
    PLUGIN_NAME = "Connect Genesis 8.1 to Move By Maxon"
    PLUGIN_HELP = "Import from DAZ Studio"
    PLUGIN_INFO = c4d.PLUGINFLAG_HIDEPLUGINMENU
    PLUGIN_ICON = load_icon("res/icon.tif")

    dialog = None

    def Register(self):
        return c4d.plugins.RegisterCommandPlugin(
            self.PLUGIN_ID,
            self.PLUGIN_NAME,
            self.PLUGIN_INFO,
            self.PLUGIN_ICON,
            self.PLUGIN_HELP,
            self,
        )

    def Execute(self, doc):
        try:
            self.dialog.Close()
        except:
            pass
        screen = c4d.gui.GeGetScreenDimensions(0, 0, True)
        self.dialog = GuiGenesisTracking()
        self.dialog.Open(
            c4d.DLG_TYPE_ASYNC,
            self.PLUGIN_ID,
            xpos=-2,
            ypos=-2,
            defaultw=100,
            defaulth=100,
        )
        return True


def EnhanceMainMenu():
    mainMenu = gui.GetMenuResource("M_EDITOR")
    pluginsMenu = gui.SearchPluginMenuResource()
    menu = c4d.BaseContainer()
    menu.InsData(c4d.MENURESOURCE_SUBTITLE, "Daz 3D")
    menu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_1057457")
    menu.InsData(c4d.MENURESOURCE_COMMAND, "PLUGIN_CMD_1057460")
    if pluginsMenu:
        mainMenu.InsDataAfter(c4d.MENURESOURCE_STRING, menu, pluginsMenu)
    else:
        mainMenu.InsData(c4d.MENURESOURCE_STRING, menu)


def PluginMessage(id, data):
    if id == c4d.C4DPL_BUILDMENU:
        EnhanceMainMenu()


"""Plugin has full support for R23 R24 and minor issues with R22
Cinema 4D R22 == 22123
Cinema 4D R24 == 24035
"""


def main():
    DazToC4DPlugin().Register()
    Genesis81MbMPlugin().Register()


if __name__ == "__main__":
    main()
    print("DazToC4D : has successfully loaded")
    print("DaztoC4D : Exports to {0}.".format(EXPORT_DIR))
