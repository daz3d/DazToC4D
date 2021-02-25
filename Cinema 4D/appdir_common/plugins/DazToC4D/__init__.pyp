from __future__ import division
import os
import sys
import hashlib
import c4d
from c4d import gui, documents
from c4d import utils
from c4d import plugins
from random import randint
from shutil import copyfile
import webbrowser
import json
from xml.etree import ElementTree

folder = os.path.dirname(__file__)
if folder not in sys.path:
    sys.path.insert(0, folder)

from DtcGui import *
print(sys.path)

"""
Converted to Python 3 to deal with changes in Cinema 4D R23
Manual Changes to the code:
Removed  c4d.DRAWFLAGS_NO_REDUCTION as it was removed from the Python SDK
Changes for Division from / to // to achieve an integer instead of a float
Added Backwards Support for __next__ for Python 2 Versions
"""
try:
    import redshift
except:
    print('Redshift not found')


class DazToC4dPlugin(c4d.plugins.CommandData):
    dialog = None

    def Execute(self, doc):
        try:
            self.dialog.Close()
        except:
            pass

        screen = c4d.gui.GeGetScreenDimensions(0, 0, True)

        # if authDialogDazToC4D().VersionCheck_C4D(22) == False: #Check if supported version!
        #     return True

        self.dialog = guiDazToC4dMain()
        self.dialog.Open(c4d.DLG_TYPE_ASYNC, PLUGIN_ID, xpos=-
                         2, ypos=-2, defaultw=100, defaulth=100)

        return True


if __name__ == '__main__':
    icon = c4d.bitmaps.BaseBitmap()
    icon.InitWith(os.path.join(os.path.dirname(__file__), "res", "icon.tif"))

    okyn = plugins.RegisterCommandPlugin(
        PLUGIN_ID, "DazToC4D", 0, icon, "Import from DAZ Studio", DazToC4dPlugin())
    if (okyn):
        print("DazToC4D ..:::> Started")