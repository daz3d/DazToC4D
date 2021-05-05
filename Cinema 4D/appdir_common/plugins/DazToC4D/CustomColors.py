import c4d 
from c4d import documents

class randomColors():
    IKMobjList = []

    def selchildren(self, obj, next):  # Scan obj hierarchy and select children

        while obj and obj != next:
            # global IKMobjList
            self.IKMobjList.append(obj)
            self.selchildren(obj.GetDown(), next)
            obj = obj.GetNext()
        return self.IKMobjList

    def get_random_color(self):
        """ Return a random color as c4d.Vector """

        def get_random_value():
            """ Return a random value between 0.0 and 1.0 """
            return randint(0, 255) / 256.0

        return c4d.Vector(get_random_value(), get_random_value(), get_random_value())

    def randomNullsColor(self, parentName, randomCol=1, rigColor1=0, rigColor2=0):
        doc = documents.GetActiveDocument()
        try:
            if randomCol == 1:
                rigColor1 = self.get_random_color()  # c4d.Vector(0,2,0)
                rigColor2 = self.get_random_color()  # c4d.Vector(1,0,0)
            self.IKMobjList = []
            parentOb = parentName
            for o in self.selchildren(parentOb, parentOb.GetNext()):
                o[c4d.ID_BASEOBJECT_USECOLOR] = 2
                o[c4d.ID_BASEOBJECT_COLOR] = rigColor1
                if 'HAND' in o.GetName() or \
                        'Pelvis' in o.GetName() or \
                        'Platform' in o.GetName() or \
                        'Head' in o.GetName():
                    o[c4d.ID_BASEOBJECT_USECOLOR] = 2
                    # o[c4d.ID_CA_JOINT_OBJECT_ICONCOL] = 1
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
        except:
            pass
        c4d.EventAdd()

    def randomPoleColors(self, parentName, randomCol=1, rigColor1=0, rigColor2=0):
        doc = documents.GetActiveDocument()
        try:
            if randomCol == 1:
                rigColor1 = self.get_random_color()  # c4d.Vector(0,2,0)
                rigColor2 = self.get_random_color()  # c4d.Vector(1,0,0)
            parentOb = parentName

            for o in self.selchildren(parentOb, parentOb.GetNext()):
                try:
                    tag = o.GetFirstTag()
                    tag[c4d.ID_CA_IK_TAG_DRAW_POLE_COLOR] = rigColor2
                except:
                    pass
            c4d.EventAdd()
        except:
            pass

    def randomRigColor(self, parentName, randomCol=1, rigColor1=0, rigColor2=0):
        doc = documents.GetActiveDocument()
        try:
            if randomCol == 1:
                rigColor1 = self.get_random_color()  # c4d.Vector(0,2,0)
                rigColor2 = self.get_random_color()  # c4d.Vector(1,0,0)
            parentOb = parentName
            self.IKMobjList = []
            for o in self.selchildren(parentOb, parentOb.GetNext()):
                o[c4d.ID_BASEOBJECT_USECOLOR] = 2

                if "Head" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Neck" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Chest" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = (rigColor2 * 0.9) + (rigColor1 * 0.1)
                if "Spine" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = (rigColor2 * 0.7) + (rigColor1 * 0.3)
                if "Abdomen" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = (rigColor2 * 0.7) + (rigColor1 * 0.3)
                if "Spine2" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = (rigColor2 * 0.7) + (rigColor1 * 0.3)
                if "Collar" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Arm" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "ForeArm" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Hand" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2

                if "Index" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Middle" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Ring" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Pink" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Thumb" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2

                if "Finger" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2
                if "Thumb" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor2

                if "Pelvis" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = (rigColor2 * 0.2) + (rigColor1 * 0.8)

                if "LegUpper" in o.GetName() or "jUpLeg" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor1 * 0.7
                if "LegLower" in o.GetName() or "jLeg" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor1 * 0.6
                if "Foot" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor1 * 0.3
                if "Toes" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor1 * 0.3
                if "ToesEnd" in o.GetName():
                    o[c4d.ID_BASEOBJECT_COLOR] = rigColor1 * 0.2
            c4d.EventAdd()
        except Exception as e:
            print(e)
            # pass


