import c4d
from c4d import documents

from .CustomIterators import ObjectIterator


class Cinema4DCommands:
    """Call Commands stored to be reused for cleaner code."""

    def __init__(self, arg):
        super(Cinema4DCommands, self).__init__()

    @staticmethod
    def Tconstraint():
        return 1019364

    @staticmethod
    def deselect_all():
        c4d.CallCommand(12113, 12113)  # deselect all

    @staticmethod
    def select_all():
        c4d.CallCommand(12112, 12112)  # select all

    @staticmethod
    def update_viewport():
        c4d.CallCommand(12148)  # Frame Geometry
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )

    @staticmethod
    def add_obj_to_new_group(children):
        doc = documents.GetActiveDocument()
        Cinema4DCommands.deselect_all()  # Deselect All
        null = c4d.BaseObject(c4d.Onull)  # Create new null
        doc.InsertObject(null)
        null.SetName("Daz Character Geometry")
        for c in children:
            if c.GetType() == 5100:
                mat = c.GetMg()
                doc.AddUndo(c4d.UNDOTYPE_CHANGE, c)
                c.InsertUnder(null)
                c.SetMg(mat)

        Cinema4DCommands.deselect_all()  # Deselect All
        c4d.EventAdd()
        return null

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

    @staticmethod
    def move_obj_to_top(obj):
        doc = documents.GetActiveDocument()
        fobj = doc.GetFirstObject()
        obj.InsertBefore(fobj)

    @staticmethod
    def move_obj_to_top(obj):
        doc = documents.GetActiveDocument()
        fobj = doc.GetFirstObject()
        if obj:
            obj.InsertBefore(fobj)

    @staticmethod
    def add_sub_div(obj):
        doc = documents.GetActiveDocument()
        Cinema4DCommands.deselect_all()  # Deselect All
        subdiv = c4d.BaseObject(c4d.Osds)  # Create new null
        doc.InsertObject(subdiv)
        subdiv.SetName("Daz Character SubDiv")
        subdiv[c4d.SDSOBJECT_SUBEDITOR_CM] = 0
        if obj:
            children = obj.GetChildren()
            subdiv.InsertUnder(obj)
            for child in children:
                mat = child.GetMg()
                child.InsertUnder(subdiv)
                child.SetMg(mat)
                phong_tag = c4d.BaseTag(c4d.Tphong)
                child.InsertTag(phong_tag)

        Cinema4DCommands.deselect_all()  # Deselect All
        c4d.EventAdd()
