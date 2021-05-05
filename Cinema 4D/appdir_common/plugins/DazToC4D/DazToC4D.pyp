import sys
import importlib
import os

check = importlib.util.find_spec("ptvsd") is not None
if check:
    import ptvsd
    ptvsd.enable_attach(address = ('127.0.0.1', 3000))
    ptvsd.wait_for_attach()

import c4d
from c4d import plugins

folder = os.path.dirname( __file__ )
if folder not in sys.path: 
    sys.path.insert( 0, folder )

from DtC4DWindow import guiDazToC4DMain

PLUGIN_ID=1052690
# To Deal with modules needing to be reimported 
# c4d.CallCommand(1026375) # Reload Python Plugins
def module_reload():
    modules = ['Utilities', 'DazToC4DClasses', 'CustomIterators', \
               'CustomImports', 'CustomColors', 'Materials', \
               'IkMax', 'DtC4DPosing', 'DtC4DPosing', \
               'DtC4DDialogs', 'DtC4DWindow', 'Morphs']
    for module in modules:
        if module not in sys.modules:
            continue
        importlib.reload(sys.modules[module])


class DazToC4DPlugin(c4d.plugins.CommandData):
    dialog = None
    def Execute(self, doc):
        try:
            self.dialog.Close()
        except:
            pass
        screen = c4d.gui.GeGetScreenDimensions(0, 0, True)
        self.dialog = guiDazToC4DMain()
        self.dialog.Open(c4d.DLG_TYPE_ASYNC, PLUGIN_ID, xpos=-2, ypos=-2, defaultw=100, defaulth=100)
        return True


if __name__=='__main__':
    module_reload()
    icon = c4d.bitmaps.BaseBitmap()
    icon.InitWith(os.path.join(os.path.dirname(__file__), "res", "icon.tif"))

    initialize = plugins.RegisterCommandPlugin(PLUGIN_ID, "DazToC4D", 0, icon, "Import from DAZ Studio", DazToC4DPlugin())
    if initialize:
        print("DazToC4D : has successfully loaded")