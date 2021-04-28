import os
import sys
import c4d
from c4d import plugins

folder = os.path.dirname( __file__ )
if folder not in sys.path: 
    sys.path.insert( 0, folder )

from DazToC4DClasses import guiDazToC4DMain

PLUGIN_ID=1052690

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
    icon = c4d.bitmaps.BaseBitmap()
    icon.InitWith(os.path.join(os.path.dirname(__file__), "res", "icon.tif"))

    okyn = plugins.RegisterCommandPlugin(PLUGIN_ID, "DazToC4D", 0, icon, "Import from DAZ Studio", DazToC4DPlugin())
    if (okyn):
        print("DazToC4D ..:::> Started")