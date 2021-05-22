import c4d
from c4d import documents

from .CustomIterators import ObjectIterator


class Cinema4DCommands:
    """Call Commands stored to be reused for cleaner code."""

    def __init__(self, arg):
        super(Cinema4DCommands, self).__init__()

    @staticmethod
    def deselect_all():
        c4d.CallCommand(12113, 12113)  # deselect all

    @staticmethod
    def update_viewport():
        c4d.CallCommand(12148)  # Frame Geometry
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )

    @staticmethod
    def ungroupDazGeo():
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject("hip")
        children = obj.GetUp().GetChildren()
        Cinema4DCommands.deselect_all()  # Deselect All
        geoDetected = False
        for c in children:
            if c.GetType() == 5100:
                geoDetected = True
                c.SetBit(c4d.BIT_ACTIVE)
        if geoDetected == True:
            c4d.CallCommand(12106, 12106)  # Cut
            c4d.CallCommand(12108, 12108)  # Paste
        Cinema4DCommands.deselect_all()  # Deselect All
        c4d.EventAdd()

    @staticmethod
    def findIK():
        """Hard Coded Find of IK Replace with User Data"""
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        ikfound = 0
        for obj in scene:
            if "Foot_PlatformBase" in obj.GetName():
                ikfound = 1
        return ikfound

    @staticmethod
    def model_mode():
        c4d.CallCommand(12298)

    @staticmethod
    def object_mode():
        c4d.CallCommand(12101)

    @staticmethod
    def del_unused_mats():
        c4d.CallCommand(12168, 12168)
