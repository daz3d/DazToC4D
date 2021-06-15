import os
import c4d
import json
from c4d import documents, utils
from xml.etree import ElementTree

from .Definitions import ROOT_DIR
from .CustomIterators import TagIterator, ObjectIterator
from .CustomCmd import Cinema4DCommands as dzc4d
from . import Database
from .DtuLoader import DtuLoader
from .TextureLib import texture_library


class Variables:
    """
    import_name(str): represents the Node name in Daz Studio
    dtu(object): instance of the DtuLoader()
    skeleton(CAJointObject): Represents the Root Joint of the Skeleton
    skeleton_name(str): Represents the name of the root joint
    body(Polygon Object): Represents the Genesis Figure Mesh
    body_name(str): Represents the name of the Genesis figure mesh
    c_meshes(list[Polygon Object]): Array of all polygon objects parented to the Root Joint
    c_morphs(list[Polygon Object]): Array of all absolute polygon objects that represent Morphs as geometry
    c_poses(list[Null Object]): Array of the nulls that store all the poses/morphs
    c_joints(list[CAJointObject]): Array of all the joints parented to the root joint
    c_skin_data(list[Skin Object]): Array of all the skinning for the Imported Character
    unique_id(int): is created with the plugin manager off plugin-cafe
    """

    import_name = None
    dtu = None
    skeleton = None
    skeleton_name = None
    body = None
    body_name = None

    c_meshes = None
    c_morphs = None
    c_poses = None
    c_joints = None
    c_skin_data = None

    unique_id = 1057461

    def store_dtu(self, dtu):
        """Will find if the dtu exists either as a function or a dict."""
        if isinstance(dtu, dict):
            dtu_dict = dtu
            dtu = DtuLoader("")
            dtu.load_dtu_dict(dtu_dict)
        self.import_name = dtu.get_import_name()
        self.dtu = dtu

    def check_if_valid(self):
        """
        Checks if Scene Contains Genesis Skeleton.
        """
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject("hip")
        if obj:
            return True

    def find_skeleton(self, name):
        doc = documents.GetActiveDocument()
        self.skeleton = doc.SearchObject(name)
        return self.skeleton

    def find_skeleton_name(self):
        self.skeleton_name = self.skeleton.GetName()
        return self.skeleton_name

    def find_body(self, name):
        body_name = name + ".Shape"
        doc = documents.GetActiveDocument()
        self.body = doc.SearchObject(body_name)
        return self.body

    def find_body_name(self):
        """Features the body of the figure's name.
        Returns:
            A string that is the bodies name.
        """
        self.body_name = self.body.GetName()
        return self.body_name

    def find_children(self, obj):
        """
        Returns all children of skeleton.
        """
        if not isinstance(obj, c4d.GeListNode):
            return []

        res = []
        self.c_meshes = []
        self.c_morphs = []
        self.c_poses = []
        self.c_joints = []
        self.c_skin_data = []

        for child in obj.GetChildren():
            res.append(child)
            res += self.find_children(child)  # recursion happens here

        for child in res:
            if child.GetType() == 5100:  # Meshes
                parent = child.GetUp()
                if parent.GetType() == 5140:
                    self.c_morphs.append(child)
                else:
                    self.c_meshes.append(child)
            if child.GetType() == 5140:  # Poses
                self.c_poses.append(child)
            if child.GetType() == 1019362:  # Joints
                self.c_joints.append(child)
            if child.GetType() == 1019363:  # Skinning Data
                self.c_skin_data.append(child)

        self.children = res
        return res

    def store_to_scene(self):
        """Stores the dtu contents as a string inside of the active document."""
        doc = c4d.documents.GetActiveDocument()
        doc_bc = doc.GetDataInstance()
        sub_bc = c4d.BaseContainer()
        sub_bc[1000] = json.dumps(self.dtu.get_dtu_dict())
        sub_bc[2000] = self.skeleton_name
        sub_bc[3000] = self.body_name
        sub_bc[4000] = self.import_name
        doc_bc.SetContainer(self.unique_id, sub_bc)
        doc.SetData(doc_bc)

    def prepare_variables(self):
        """
        Sets up Variables
        Returns True if Scene Does not contain a valid import
        """
        if self.check_if_valid():
            self.find_skeleton(self.import_name)
            self.find_skeleton_name()
            self.find_body(self.import_name)
            self.find_body_name()
            self.find_children(self.skeleton)
            self.store_to_scene()
        else:
            return True

    def restore_variables(self):
        """
        Restores Variables Based on the Unique ID
        """
        doc = c4d.documents.GetActiveDocument()
        dtu_dict = json.loads(doc[self.unique_id][1000])
        self.store_dtu(dtu_dict)
        self.find_skeleton(self.import_name)
        self.find_skeleton_name()
        self.find_body(self.import_name)
        self.find_body_name()
        self.find_children(self.skeleton)


def get_daz_mesh():
    doc = documents.GetActiveDocument()
    obj = doc.SearchObject("hip")
    if obj:
        dazRigName = obj.GetUp().GetName()
        dazMeshObj = doc.SearchObject(dazRigName + ".Shape")
        return dazMeshObj
    return None


def get_daz_name():
    doc = documents.GetActiveDocument()
    obj = doc.SearchObject("hip")
    if obj:
        dazRigName = obj.GetUp().GetName()
        dazMeshObj = doc.SearchObject(dazRigName + ".Shape")
        return dazMeshObj.GetName().replace(".Shape", "")
    return ""


def getJointFromSkin(obj, jointName):
    objTags = TagIterator(obj)
    for t in objTags:
        if t.GetType() == c4d.Tweights:
            for j in range(t.GetJointCount()):
                if jointName in t.GetJoint(j).GetName():
                    return t.GetJoint(j)
    return None


def getJointFromConstraint(jointName):
    objTags = TagIterator(jointName)
    for t in objTags:
        if t.GetType() == dzc4d.Tconstraint():
            return t[10001]

    return None


class dazToC4Dutils:
    def findTextInFile(self, matName, propertyName):
        lib = texture_library
        dazExtraMapsFile = os.path.join(ROOT_DIR, "DazToC4D.xml")

        if os.path.exists(dazExtraMapsFile) == False:
            return
        xmlFilePath = dazExtraMapsFile
        xmlFile = ElementTree.parse(xmlFilePath)
        xmlMaterials = xmlFile.getroot()
        xmlMaterial = xmlMaterials.find("material")
        texturePath = None
        for node in xmlMaterials:
            if node.attrib["name"] == matName:
                # xmlValue = node.attrib[xmlMatProperty]
                try:
                    texturePath = node.attrib[propertyName]
                except:
                    pass

        if texturePath == "":
            return None

        if texturePath:
            texturePath = os.path.abspath(texturePath)  # OS Path Fix...

        return texturePath

    def readExtraMapsFromFile(self):
        doc = c4d.documents.GetActiveDocument()
        docMaterials = doc.GetMaterials()
        for mat in docMaterials:
            matName = mat.GetName()
            extraMapBump = self.findTextInFile(matName, "bump")
            extraMapBump2 = self.findTextInFile(matName, "bump2")
            if extraMapBump == None and extraMapBump2 != None:
                extraMapBump = extraMapBump2
            extraMapNormal = self.findTextInFile(matName, "Normal_Map_Map")
            if extraMapNormal != None and extraMapBump == None:
                extraMapBump = extraMapNormal
            if extraMapBump != None:
                mat[c4d.MATERIAL_USE_BUMP] = True
                shda = c4d.BaseList2D(c4d.Xbitmap)
                shda[c4d.BITMAPSHADER_FILENAME] = extraMapBump
                mat[c4d.MATERIAL_BUMP_SHADER] = shda
                mat.InsertShader(shda)

            extraMapNormal = self.findTextInFile(matName, "Normal_Map_Map")
            if extraMapNormal != None:
                mat[c4d.MATERIAL_USE_NORMAL] = True
                shda = c4d.BaseList2D(c4d.Xbitmap)
                shda[c4d.BITMAPSHADER_FILENAME] = extraMapNormal
                mat[c4d.MATERIAL_NORMAL_SHADER] = shda
                mat.InsertShader(shda)

            extraMapSpec = self.findTextInFile(matName, "Glossy_Layered_Weight_Map")
            extraMapSpec2 = self.findTextInFile(matName, "spec")
            extraMapGlossy = self.findTextInFile(matName, "Metallicity_Map")
            if extraMapSpec2 != None and extraMapSpec == None:
                extraMapSpec = extraMapSpec2
            if extraMapGlossy != None and extraMapSpec == None:
                extraMapSpec = extraMapGlossy
            if extraMapSpec != None:
                mat[c4d.MATERIAL_USE_REFLECTION] = True
                shda = c4d.BaseList2D(c4d.Xbitmap)
                shda[c4d.BITMAPSHADER_FILENAME] = extraMapSpec
                layer = mat.GetReflectionLayerIndex(0)
                mat[layer.GetDataID() + c4d.REFLECTION_LAYER_TRANS_TEXTURE] = shda
                mat.InsertShader(shda)
                try:
                    mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION] = 4
                except:
                    pass

            extraMapGlossyRough = self.findTextInFile(matName, "Glossy_Roughness_Map")
            if extraMapGlossyRough != None:
                mat[c4d.MATERIAL_USE_REFLECTION] = True
                shda = c4d.BaseList2D(c4d.Xbitmap)
                shda[c4d.BITMAPSHADER_FILENAME] = extraMapGlossyRough
                layer = mat.GetReflectionLayerIndex(0)
                mat[
                    layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_SHADER_ROUGHNESS
                ] = shda
                try:
                    mat.InsertShader(shda)
                    mat[layer.GetDataID() + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION] = 4
                except:
                    pass

    def walker(self, parent, obj):
        if not obj:
            return  # if obj is None, the function returns None and breaks the while loop
        elif obj.GetDown():  # if there is a child of obj
            return obj.GetDown()  # the walker function returns that child
        while (
            obj.GetUp() and not obj.GetNext() and obj.GetUp() != parent
        ):  # if there is a parent of the obj and there isn't another object after the obj and the parent object is not the same object stored in "parent"
            obj = obj.GetUp()  # it set's the current obj to that parent
        return (
            obj.GetNext()
        )  # and return the object that's after that parent, not under, after :)

    def iterateObjChilds(self, obj):
        parent = obj  # stores the active object in a 'parent' variable, so it always stays the same
        children = []  # create an empty list to store children

        while (
            obj != None
        ):  # while there is a object (the "walker" function will return None at some point and that will exit the while loop)
            obj = self.walker(
                parent, obj
            )  # set the obj to the result of the walker function
            if obj != None:  # if obj is not None
                children.append(obj)  # append that object to the children list

        return children

    def zeroTwistRotationFix(self, twistName, jointName):
        doc = c4d.documents.GetActiveDocument()

        objTarget = doc.SearchObject(twistName)
        joint = doc.SearchObject(jointName)
        xtag = None
        objTags = TagIterator(joint)
        for t in objTags:
            if "Constraint" in t.GetName():
                xtag = t
        xtag[10001] = None

        mgTarget = objTarget.GetMg()
        newNull = c4d.BaseObject(c4d.Onull)
        newNull.SetName("TARGET")
        newNull.SetMg(mgTarget)
        doc.InsertObject(newNull)
        newNull[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0.0

        c4d.EventAdd()
        objTarget.SetMg(newNull.GetMg())
        c4d.EventAdd()
        xtag[10001] = objTarget

        objTarget[c4d.ID_BASEOBJECT_ROTATION_ORDER] = 6
        c4d.EventAdd()

    def fixMoisure(self):
        def removeMoisureTag(obj):
            # validate object and selectiontag
            if not obj:
                return
            if not obj.IsInstanceOf(c4d.Opolygon):
                return
            tags = obj.GetTags()

            # deselect current polygonselection and store a backup to reselect
            polyselection = obj.GetPolygonS()

            # define the name to search for
            name = "EyeMoisture"

            # loop through the tags and check if name and type fits
            # if so split
            t = obj.GetFirstTag()
            while t:
                if t.GetType() == c4d.Tpolygonselection:
                    if name in t.GetName():

                        # select polygons from selectiontag
                        tagselection = t.GetBaseSelect()
                        tagselection.CopyTo(polyselection)

                        # split: polygonselection to a new object
                        sec = utils.SendModelingCommand(
                            command=c4d.MCOMMAND_DELETE,
                            list=[obj],
                            mode=c4d.MODELINGCOMMANDMODE_POLYGONSELECTION,
                            doc=doc,
                        )

                        if not sec:
                            print(sec)
                            return

                t = t.GetNext()

            c4d.EventAdd()

        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()
        scene = ObjectIterator(obj)
        for obj in scene:
            if obj.GetType() == 5100:
                removeMoisureTag(obj)

    def fixDazFootRot(self, master, mode="", jointToFix="", rotValue=0):
        doc = documents.GetActiveDocument()

        nullObj = c4d.BaseObject(c4d.Onull)  # Create new cube
        doc.InsertObject(nullObj)
        armJoint = doc.SearchObject("lShldrBend")
        handJoint = doc.SearchObject("lForearmBend")

        mg = jointToFix.GetMg()
        nullObj.SetMg(mg)

        nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0
        nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0
        nullObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0
        c4d.EventAdd()

        slaveObj = nullObj
        masterObj = master

        def addConstraint(slaveObj, masterObj, mode="Parent"):
            if mode == "Parent":
                constraintTAG = c4d.BaseTag(1019364)

                constraintTAG[c4d.EXPRESSION_ENABLE] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR_MAINTAIN] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
                constraintTAG[10005] = True
                constraintTAG[10007] = True
                constraintTAG[10001] = masterObj

                PriorityDataInitial = c4d.PriorityData()
                PriorityDataInitial.SetPriorityValue(
                    c4d.PRIORITYVALUE_MODE, c4d.CYCLE_EXPRESSION
                )
                PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_PRIORITY, 0)
                PriorityDataInitial.SetPriorityValue(
                    c4d.PRIORITYVALUE_CAMERADEPENDENT, 0
                )
                constraintTAG[c4d.EXPRESSION_PRIORITY] = PriorityDataInitial
            slaveObj.InsertTag(constraintTAG)

        mg = slaveObj.GetMg()
        constraintTAG = c4d.BaseTag(1019364)

        if mode == "ROTATION":
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
            constraintTAG[10005] = False
            constraintTAG[10006] = False
            constraintTAG[10001] = masterObj
        if mode == "AIM":
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM] = True
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_MAINTAIN] = False

            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_X] = True
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_Y] = False
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_Z] = False
            constraintTAG[20004] = 0  # Axis X-
            constraintTAG[20001] = masterObj

        slaveObj.InsertTag(constraintTAG)
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        c4d.EventAdd()
        caca = slaveObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X]

        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )

        addConstraint(jointToFix, slaveObj)
        constraintTAG.Remove()

        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )

        slaveObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = -1.571
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )

        caca = jointToFix.GetFirstTag()
        caca.Remove()
        slaveObj.Remove()

    def dazFootRotfix(self):
        doc = documents.GetActiveDocument()

        mainJoint = doc.SearchObject("lFoot")
        goalJoint = doc.SearchObject("lToe")
        self.fixDazFootRot(goalJoint, "AIM", mainJoint)

        jointOposite = doc.SearchObject("rFoot")
        rx = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X]
        ry = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y]
        rz = mainJoint[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z]

        jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = rx * -1
        jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0
        jointOposite[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0

    def ikGoalsZeroRot(self):
        def ikZeroRot(jointObj):
            tag = jointObj.GetFirstTag()
            goalObj = tag[10001]

            ry = jointObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y]

            tag[10001] = None

            jointObj[c4d.ID_BASEOBJECT_FROZEN_ROTATION, c4d.VECTOR_Y] = ry
            jointObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0

            c4d.EventAdd()
            c4d.DrawViews(
                c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
                | c4d.DRAWFLAGS_NO_THREAD
                | c4d.DRAWFLAGS_STATICBREAK
            )

            c4d.EventAdd()

            goalObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X] = 0
            goalObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y] = 0
            goalObj[c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z] = 0
            goalObj[c4d.ID_BASEOBJECT_FROZEN_ROTATION, c4d.VECTOR_X] = 0
            goalObj[c4d.ID_BASEOBJECT_FROZEN_ROTATION, c4d.VECTOR_Y] = 0
            goalObj[c4d.ID_BASEOBJECT_FROZEN_ROTATION, c4d.VECTOR_Z] = 0

            tag[c4d.ID_CA_CONSTRAINT_TAG_PSR_MAINTAIN] = True

            c4d.EventAdd()
            tag[10001] = goalObj

            c4d.EventAdd()
            c4d.DrawViews(
                c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
                | c4d.DRAWFLAGS_NO_THREAD
                | c4d.DRAWFLAGS_STATICBREAK
            )
            c4d.EventAdd()

        doc = documents.GetActiveDocument()
        dazName = get_daz_name() + "_"
        jointObj = doc.SearchObject(dazName + "jHand")
        ikZeroRot(jointObj)

        jointObj = doc.SearchObject(dazName + "jHand___R")
        ikZeroRot(jointObj)

        jointObj = doc.SearchObject(dazName + "jUpLeg.Pole___R")
        jointObj[c4d.ID_BASEOBJECT_FROZEN_ROTATION, c4d.VECTOR_X] = 0
        jointObj = doc.SearchObject(dazName + "jArm.Pole___R")
        jointObj[c4d.ID_BASEOBJECT_FROZEN_ROTATION, c4d.VECTOR_X] = 0
        c4d.EventAdd()

    # TODO: Remove/Find better Method
    def getDazMesh(self):
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject("hip")
        if obj:
            dazRigName = obj.GetUp().GetName()
            dazMeshObj = doc.SearchObject(dazRigName + ".Shape")
            return dazMeshObj
        return None

    def initialDisplaySettings(self):
        doc = documents.GetActiveDocument()
        dazName = self.getDazMesh()
        if dazName:
            dazName = dazName.GetName().replace(".Shape", "")
            dazName = dazName + "_"

            def hideJoint(obj, value):
                obj[c4d.ID_CA_JOINT_OBJECT_BONE_DISPLAY] = value
                obj[c4d.ID_CA_JOINT_OBJECT_JOINT_DISPLAY] = value

            def hideJoints(jName, value):
                jointParent = doc.SearchObject(dazName + jName)
                if jointParent:
                    listObjs = ObjectIterator(jointParent)
                    for obj in listObjs:
                        hideJoint(obj, value)

            objPelvis = doc.SearchObject(dazName + "jPelvis")
            hideJoint(objPelvis, 0)
            hideJoints("jSpine", 0)
            hideJoints("jUpLeg", 0)
            hideJoints("jUpLeg___R", 0)

            hideJoints("jHand", 2)  # Show
            hideJoints("jHand___R", 2)  # Show

            c4d.EventAdd()

    def jointsDisplayInitialSettings(self):

        [c4d.ID_CA_JOINT_OBJECT_JOINT_DISPLAY] = 0
        self.getDazMesh()

        boneDisplay = self.jointPelvis[c4d.ID_CA_JOINT_OBJECT_BONE_DISPLAY]
        if boneDisplay != 0:
            boneDisplay = 0
        else:
            boneDisplay = 2
        for x in self.iterateObjChilds(self.jointPelvis):
            x[c4d.ID_CA_JOINT_OBJECT_BONE_DISPLAY] = boneDisplay
        self.jointPelvis[c4d.ID_CA_JOINT_OBJECT_BONE_DISPLAY] = boneDisplay

        c4d.EventAdd()

    def changeSkinType(self):
        doc = documents.GetActiveDocument()
        obj = doc.GetFirstObject()

        scene = ObjectIterator(obj)
        baseObjs = []

        for obj in scene:
            if obj.GetType() == 1019363:
                obj[c4d.ID_CA_SKIN_OBJECT_TYPE] = 1

        c4d.EventAdd()

    def twistBoneSetup(self):
        doc = documents.GetActiveDocument()
        dazName = get_daz_name() + "_"

        def aimObj(slave, master, mode="", searchObj=1):
            doc = documents.GetActiveDocument()
            if searchObj == 1:
                slaveObj = doc.SearchObject(slave)
                masterObj = doc.SearchObject(master)
            else:
                slaveObj = slave
                masterObj = master
            mg = slaveObj.GetMg()

            constraintTAG = c4d.BaseTag(1019364)

            if mode == "ROTATION":
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
                constraintTAG[10005] = False
                constraintTAG[10006] = False
                constraintTAG[10001] = masterObj
            if mode == "AIM":
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_MAINTAIN] = False
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_X] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_Y] = True
                constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_CONSTRAIN_Z] = True
                constraintTAG[20004] = 0  # Axis X-
                constraintTAG[20001] = masterObj

            slaveObj.InsertTag(constraintTAG)

            c4d.EventAdd()
            c4d.DrawViews(
                c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
                | c4d.DRAWFLAGS_NO_THREAD
                | c4d.DRAWFLAGS_STATICBREAK
            )
            constraintTAG.Remove()

        twistJoint = doc.SearchObject(dazName + "ForearmTwist_ctrl")
        handJoint = doc.SearchObject("lHand")
        aimObj(twistJoint, handJoint, "AIM", 0)
        twistJoint = doc.SearchObject(dazName + "ForearmTwist_ctrl___R")
        handJoint = doc.SearchObject("rHand")
        aimObj(twistJoint, handJoint, "AIM", 0)

    def fixConstraints(self):
        def fixConstraint(jointName):
            doc = documents.GetActiveDocument()
            obj = doc.SearchObject(jointName)
            if obj:
                tag = obj.GetFirstTag()
                tag[c4d.ID_CA_CONSTRAINT_TAG_PSR_MAINTAIN] = True
                c4d.EventAdd()

        fixConstraint("lForearmTwist")
        fixConstraint("rForearmTwist")

    def hideRig(self):
        doc = documents.GetActiveDocument()
        obj = doc.SearchObject("hip")
        dazRig = obj.GetUp()
        guideNulls = self.iterateObjChilds(dazRig)
        for obj in guideNulls:
            obj()[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 1
            obj()[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 1
        dazRig()[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = 1
        dazRig()[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = 1

        c4d.EventAdd()

    def addProtection(self):
        def protectObj(objName, lock="Position"):
            doc = documents.GetActiveDocument()
            obj = doc.SearchObject(objName)
            protectionTAG = c4d.BaseTag(c4d.Tprotection)
            if lock == "Position":
                protectionTAG[c4d.PROTECTION_P_X] = True
                protectionTAG[c4d.PROTECTION_P_Y] = True
                protectionTAG[c4d.PROTECTION_P_Z] = True
                protectionTAG[c4d.PROTECTION_R_X] = False
                protectionTAG[c4d.PROTECTION_R_Y] = False
                protectionTAG[c4d.PROTECTION_R_Z] = False
                protectionTAG[c4d.PROTECTION_S_Z] = False
                protectionTAG[c4d.PROTECTION_S_Y] = False
                protectionTAG[c4d.PROTECTION_S_X] = False
            obj.InsertTag(protectionTAG)
            c4d.EventAdd()

        dazName = get_daz_name() + "_"
        protectObj(dazName + "Toe_Rot")
        protectObj(dazName + "Toe_Rot___R")
        protectObj(dazName + "Foot_Roll")
        protectObj(dazName + "Foot_Roll___R")

    def addHeadEndBone(self):
        doc = documents.GetActiveDocument()
        jointHeadEnd = doc.SearchObject("head_end")
        if jointHeadEnd == None:
            jointCollar = doc.SearchObject("lCollar")

            jointHead = doc.SearchObject("head")
            newJoint = c4d.BaseObject(c4d.Ojoint)
            newJoint.SetName("head_end")
            doc.InsertObject(newJoint)
            newJoint.InsertUnder(jointHead)
            newJoint.SetMg(jointHead.GetMg())

            headHeight = 9
            if jointCollar:
                headHeight = jointCollar[c4d.ID_CA_JOINT_OBJECT_LENGTH]

            newJoint[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y] = headHeight
            c4d.EventAdd()

    def removeConstraintTags(self, obj):

        doc = c4d.documents.GetActiveDocument()
        tags = TagIterator(obj)
        try:
            for t in tags:
                if "Constraint" in t.GetName():
                    t.Remove()
        except:
            pass
        c4d.EventAdd()

    def addConstraint(self, slave, master, mode="Parent"):
        doc = documents.GetActiveDocument()
        slaveObj = doc.SearchObject(slave)
        masterObj = doc.SearchObject(master)
        self.removeConstraintTags(slaveObj)

        if mode == "Parent":
            constraintTAG = c4d.BaseTag(1019364)

            constraintTAG[c4d.EXPRESSION_ENABLE] = True
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR_MAINTAIN] = True
            constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_PSR] = True
            constraintTAG[10005] = True
            constraintTAG[10007] = True
            constraintTAG[10001] = masterObj

            PriorityDataInitial = c4d.PriorityData()
            PriorityDataInitial.SetPriorityValue(
                c4d.PRIORITYVALUE_MODE, c4d.CYCLE_EXPRESSION
            )
            PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_PRIORITY, 0)
            PriorityDataInitial.SetPriorityValue(c4d.PRIORITYVALUE_CAMERADEPENDENT, 0)
            constraintTAG[c4d.EXPRESSION_PRIORITY] = PriorityDataInitial
        try:
            slaveObj.InsertTag(constraintTAG)
        except:
            print("constr skip")
            pass

    def parentTo(self, childName, parentName):
        doc = documents.GetActiveDocument()
        child = doc.SearchObject(childName)
        parent = doc.SearchObject(parentName)
        mg = child.GetMg()
        child.InsertUnder(parent)
        child.SetMg(mg)

    def extend3Dline(self, nameA, nameB, actObjName, offset=1):
        doc = documents.GetActiveDocument()
        dazName = self.getDazMesh().GetName()
        meshName = dazName + "_"
        meshName = meshName.replace(".Shape", "")
        actObj = doc.SearchObject(meshName + actObjName)
        Aobj = doc.SearchObject(meshName + nameA)  # Direction line Start
        Bobj = doc.SearchObject(meshName + nameB)  # Direction line End

        targetObj = c4d.BaseObject(c4d.Onull)
        targetObj.SetName("TARGET")
        doc.InsertObject(targetObj)

        targetObjExtend = c4d.BaseObject(c4d.Onull)
        targetObjExtend.SetName("TARGET_Extend")
        doc.InsertObject(targetObjExtend)
        targetObj.SetMg(Aobj.GetMg())

        targetObjExtend.InsertUnder(targetObj)

        constraintTAG = c4d.BaseTag(1019364)
        constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM] = True
        constraintTAG[c4d.ID_CA_CONSTRAINT_TAG_AIM_MAINTAIN] = False
        constraintTAG[20004] = 2
        constraintTAG[20001] = Bobj
        targetObj.InsertTag(constraintTAG)

        caca = targetObj.GetFirstTag()
        c4d.DrawViews(
            c4d.DRAWFLAGS_ONLY_ACTIVE_VIEW
            | c4d.DRAWFLAGS_NO_THREAD
            | c4d.DRAWFLAGS_STATICBREAK
        )
        caca.Remove()
        targetMg = None
        try:
            targetObjExtend.SetMg(Bobj.GetMg())
            objDistance = targetObjExtend[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z]
            targetObj.SetAbsPos(Bobj.GetAbsPos())
            targetObjExtend[c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z] = (
                objDistance * offset
            )
            targetObjExtend[c4d.NULLOBJECT_DISPLAY] = 9

            targetMg = targetObjExtend.GetMg()
            actObj.SetMg(targetObjExtend.GetMg())
        except:
            print("skip extend")

        targetObj.Remove()

        c4d.EventAdd()
        return targetMg

    def moveToObj(self, source, target):
        doc = documents.GetActiveDocument()
        dazName = get_daz_name()
        parentGuidesName = dazName + "__IKM-Guides"

        if doc.SearchObject(parentGuidesName) == None:
            newNull = c4d.BaseObject(c4d.Onull)
            newNull.SetName(parentGuidesName)
            doc.InsertObject(newNull)

        guidesParent = doc.SearchObject(parentGuidesName)

        newNull = c4d.BaseObject(c4d.Onull)
        newNull.SetName(source)
        doc.InsertObject(newNull)
        newNull[c4d.NULLOBJECT_DISPLAY] = 11
        newNull[c4d.NULLOBJECT_RADIUS] = 1
        newNull[c4d.NULLOBJECT_ORIENTATION] = 1

        sourceObj = newNull
        targetObj = doc.SearchObject(target)
        sourceObj.SetMg(targetObj.GetMg())

        mg = sourceObj.GetMg()
        sourceObj.InsertUnder(guidesParent)
        sourceObj.SetMg(mg)

        c4d.EventAdd()

    def guidesToDaz(self):
        dazName = get_daz_name()
        doc = documents.GetActiveDocument()
        meshName = dazName + "_"
        self.addHeadEndBone()
        guides = Database.guides_for_rig
        for objs in guides:
            guide_suffix = objs[0]
            joint = objs[1]
            if doc.SearchObject(joint):
                self.moveToObj(meshName + guide_suffix, joint)
            elif len(objs) == 3:
                self.moveToObj(meshName + guide_suffix, objs[2])

    def cleanJointsDaz(self, side="Left"):
        doc = documents.GetActiveDocument()
        prefix = "l"
        suffix = ""
        if side == "Right":
            prefix = "r"
            suffix = "___R"
        if doc.SearchObject(prefix + "SmallToe4"):
            self.parentTo(prefix + "SmallToe4", prefix + "Toe")
        if doc.SearchObject(prefix + "SmallToe3"):
            self.parentTo(prefix + "SmallToe3", prefix + "Toe")
        if doc.SearchObject(prefix + "SmallToe2"):
            self.parentTo(prefix + "SmallToe2", prefix + "Toe")
        if doc.SearchObject(prefix + "SmallToe1"):
            self.parentTo(prefix + "SmallToe1", prefix + "Toe")
        if doc.SearchObject(prefix + "BigToe"):
            self.parentTo(prefix + "BigToe", prefix + "Toe")
        c4d.EventAdd()

    def constraintJointsToDaz(self, side="Left"):
        doc = documents.GetActiveDocument()
        dazName = get_daz_name()
        meshName = dazName + "_"
        prefix = "l"
        suffix = ""
        if side == "Right":
            prefix = "r"
            suffix = "___R"

        joints = Database.constraint_joints
        for joint in joints:
            dz_joint = joint[0]
            ctrl_joint = joint[1]
            if doc.SearchObject(dz_joint):
                if doc.SearchObject(meshName + ctrl_joint):
                    self.addConstraint(dz_joint, meshName + ctrl_joint)
            elif doc.SearchObject(prefix + dz_joint):
                if doc.SearchObject(meshName + ctrl_joint + suffix):
                    self.addConstraint(
                        prefix + dz_joint, meshName + ctrl_joint + suffix
                    )
