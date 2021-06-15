import c4d
from c4d import gui
from .Morphs import Morphs
from .MaxonTracking import Tracking


class GuiGenesisTracking(gui.GeDialog):
    LINK_BOX_MORPHS = 341797999
    LINK_BOX_FACE = 341798000
    BUTTON_CONNECT_MORPH = 341798001
    BUTTON_CONNECT_HEAD = 341798003
    BUTTON_CONNECT_EYES = 341798005

    def find_face_captures(self):
        obj = self.face_link.GetLink()
        if obj.GetType() == 1040464:
            c4d.MessageDialog(
                "Do not connect the Face Capture\nCreate Pose Morphs first.",
                type=c4d.GEMB_ICONEXCLAMATION,
            )
        if obj.GetTag(1040839):
            self.face_link.SetLink(obj)

    def CreateLayout(self):
        self.SetTitle("Genesis 8.1 Connect Facial Capture")
        self.GroupBegin(11, c4d.BFH_SCALEFIT, 1, 1, title="Moves By Maxon: ")
        self.GroupBorder(c4d.BORDER_GROUP_IN)
        self.GroupBorderSpace(10, 5, 10, 5)
        self.GroupBegin(11, c4d.BFH_SCALEFIT, 2, 1, title="")
        self.GroupBegin(11, c4d.BFH_SCALEFIT, 8, 1, title="Morph Controller")
        self.GroupBorder(c4d.BORDER_GROUP_IN)
        self.morph_link = self.AddCustomGui(
            self.LINK_BOX_MORPHS,
            c4d.CUSTOMGUI_LINKBOX,
            "Morph Group:",
            c4d.BFH_SCALEFIT,
            350,
            0,
        )
        self.GroupEnd()
        self.GroupBegin(11, c4d.BFH_SCALEFIT, 8, 1, title="Face Capture")
        self.GroupBorder(c4d.BORDER_GROUP_IN)
        self.face_link = self.AddCustomGui(
            self.LINK_BOX_FACE,
            c4d.CUSTOMGUI_LINKBOX,
            "Face Capture:",
            c4d.BFH_SCALEFIT,
            350,
            0,
        )
        self.GroupEnd()
        self.GroupEnd()
        self.GroupBegin(11, c4d.BFV_CENTER, 8, 3, title="Connect Face Capture: ")
        self.GroupBorder(c4d.BORDER_GROUP_IN)
        self.GroupBorderSpace(10, 5, 12, 5)

        self.connect_morphs = self.AddButton(
            self.BUTTON_CONNECT_MORPH, c4d.BFV_CENTER, name="Connect Morphs"
        )
        self.add_head_rotation = self.AddButton(
            self.BUTTON_CONNECT_HEAD, c4d.BFV_CENTER, name="Connect Head Rotation"
        )
        self.add_eye_rotation = self.AddButton(
            self.BUTTON_CONNECT_EYES, c4d.BFV_CENTER, name="Connect Eye Rotation"
        )

        self.GroupEnd()
        self.GroupEnd()

        return True

    def Command(self, id, msg):

        if id == self.BUTTON_CONNECT_MORPH:
            morph_controller = self.morph_link.GetLink()
            face_capture = self.face_link.GetLink()
            Tracking().connect_face_morphs(morph_controller, face_capture)

        if id == self.BUTTON_CONNECT_HEAD:
            face_capture = self.face_link.GetLink()
            Tracking().add_head_tracking(face_capture)

        if id == self.BUTTON_CONNECT_EYES:
            face_capture = self.face_link.GetLink()
            Tracking().add_eye_tracking(face_capture)

        return True
