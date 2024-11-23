# ==============================================
#                   Import
# ==============================================
import os
import sys
import c4d

try:
    import redshift
except:
    pass


from .ImportTester import ImportTester
from .Node import Node
from .MetaName import MetaName

# ==============================================
#                   Import
# ==============================================

__author__ = "Adam Maxime - Graphos <gr4ph0s(at)hotmail.fr>"
__project__ = "https://github.com/gr4ph0s/C4D_RedshiftWrapper_API"
__version__ = "1.1"


class Redshift(MetaName):
    __metaclass__ = ImportTester
    """The main wrapper arround Redshift API.

    :member doUndo: (Bool) True if the wrapper have to call GvMaster.AddUndo() before any change otherwise False.
    :member _mat: (c4d.BaseMaterial) The redshift material we act on.
    :member _gvMaster: (c4d.modules.graphview.GvNodeMaster) The Node master of self.mat.
    :member _gvMaster: (c4d.modules.graphview.GvNodeMaster) The Node master of self.mat.
    """

    doUndo = True
    _mat = None
    _gvMaster = None

    @staticmethod
    def RedhisftIsInstalled():
        return ImportTester._CheckImport("redshift")

    def SetMat(self, mat):
        """Set the mat to act on.

        :param mat: The material to act on. Only accept a Redshift Material.
        :type mat: c4d.BaseMaterial.
        :raises: TypeError
        """
        global redshift
        if not isinstance(mat, c4d.BaseMaterial):
            raise TypeError("material is not a c4d.BaseMaterial")
        if not mat.IsInstanceOf(redshift.Mrsmaterial):
            print("DEBUG: Redshift Conversion: unable to convert material, removing material: " + mat.GetName())
            mat.Remove()
            raise TypeError("material is not a redshift material")

        self._mat = mat
        self._gvMaster = redshift.GetRSMaterialNodeMaster(mat)
        if not self._gvMaster:
            raise TypeError("can't get GvMaster from mat")

    def _CheckMatIsValid(self):
        """Check if :member:`._self.mat` is currently set and valid"""
        global redshift
        if self._mat is None:
            raise TypeError("Mat is not define")
        if not isinstance(self._mat, c4d.BaseMaterial):
            raise TypeError("material is not a c4d.BaseMaterial")
        if not self._mat.IsInstanceOf(redshift.Mrsmaterial):
            raise TypeError("material is not a redshift material")

    def GetAllNodes(self, removeMasterGroup=True, gvNode=None, nodeList=None):
        """Get all nodes inside the material.
        Use redshift.GatAllNodes(), only removeMasterGroup is needed other parameters are for internal use.

        :param removeMasterGroup: True to remove the Shader Group that hold all other Node otherwise false.
        :type removeMasterGroup: Bool.
        :return: All Nodes inside the material.
        :rtype: List of :class:`.Node`
        """
        self._CheckMatIsValid()

        if nodeList is None:
            nodeList = list()
            gvNode = self._gvMaster.GetRoot()

        while gvNode:
            nodeList.append(Node(gvNode, self.doUndo))
            self.GetAllNodes(False, gvNode.GetDown(), nodeList)
            gvNode = gvNode.GetNext()

        if len(nodeList) > 1 and removeMasterGroup:
            nodeList = nodeList[1:]
        return nodeList

    def CreateShader(self, shaderType, x=-1, y=-1, NodeBefore=None):
        """Create a shader inside the material.

        :param shaderType: Int (a Cinema 4D Node look at https://developers.maxon.net/docs/Cinema4DPythonSDK/html/types/gvnodes.html) or a Redshift Node member loot at :class:`MetaclassName`.
        :type shaderType: Int or Str.
        :param x: X position in the Xpresso windows.
        :type x: int
        :param y: Y position in the Xpresso windows.
        :type y: int
        :param NodeBefore: The node to insert before (Change execution order !!)
        :type NodeBefore: :class:`.Node` or c4d.modules.graphview.GvNode
        :return: All Nodes inside the material
        :rtype: List of :class:`.Node`
        """
        self._CheckMatIsValid()

        if not isinstance(shaderType, str) and not isinstance(shaderType, int):
            raise TypeError("shaderType is not valid type")

        if not isinstance(x, int):
            raise TypeError("x is not valid type")

        if not isinstance(y, int):
            raise TypeError("y is not valid type")

        if (
            not isinstance(NodeBefore, Node)
            and not isinstance(NodeBefore, c4d.modules.graphview.GvNode)
            and NodeBefore is not None
        ):
            raise TypeError("NodeBefore is not valid type")

        # Create redshift node
        if isinstance(shaderType, str):
            if self.doUndo:
                self._gvMaster.AddUndo()

            # Check if we accept this meta class
            if not self._TestProperty(shaderType):
                raise TypeError("shaderType is not a valid metaclassname")

            # Get a GvNode
            if isinstance(NodeBefore, Node) and NodeBefore is not None:
                NodeBefore = NodeBefore.GetNode()

            # Check if it' a C4D Baked
            if shaderType == self.UtBaker:
                node = Node(
                    self._gvMaster.CreateNode(
                        self._gvMaster.GetRoot(), 1036762, NodeBefore, x, y
                    ),
                    self.doUndo,
                )

            # Check Output
            elif shaderType == self.Output:
                # Check if there is already an output node
                nodeList = self.GetAllNodes()
                for node in nodeList:
                    if node.GetType() == self.Output:
                        return None

                node = Node(
                    self._gvMaster.CreateNode(
                        self._gvMaster.GetRoot(), 1036746, NodeBefore, x, y
                    ),
                    self.doUndo,
                )

            # Other
            else:
                node = self._gvMaster.CreateNode(
                    self._gvMaster.GetRoot(), 1036227, NodeBefore, x, y
                )
                node[c4d.GV_REDSHIFT_SHADER_META_CLASSNAME] = shaderType
                node = Node(node, self.doUndo)

            if node:
                node.SetColor()
            return node

        # Create c4d node
        else:
            if self.doUndo:
                self._gvMaster.AddUndo()

            return Node(
                self._gvMaster.CreateNode(
                    self._gvMaster.GetRoot(), shaderType, NodeBefore, x, y
                ),
                self.doUndo,
            )

        return None

    def RemoveShader(self, node):
        """Remove a shader inside the material.

        :param node: Tee node object to remove.
        :type node: :class:`.Node`
        :return: True if delete overthiwe False.
        :rtype: Bool
        """
        self._CheckMatIsValid()

        # Check Type
        if not isinstance(node, Node):
            raise TypeError("node is not valid Node Object")

        if self.doUndo:
            self._gvMaster.AddUndo()
        return node.GetNode().Remove()

    def CreateConnection(
        self, SrcNode, DestNode, SrcParameter=None, DestParameter=None
    ):
        """Connect two Nodes together.

        :param SrcNode: The source Node (The one with an output) or GvPort of the source Node returned by Node.ExposeParameter or Node.SearchPort
        :type SrcNode: :class:`.Node` or c4d.modules.graphview.GvPort
        :param DestNode: The destination Node (The one with an input) or GvPort of the destination Node returned by Node.ExposeParameter or Node.SearchPort
        :type DestNode: :class:`.Node` or c4d.modules.graphview.GvPort
        :param SrcParameter: Id of the source GvPort (not the ID of the parameter) or the name of the source GvPort PARAMETER WILL BE IGNORED IF GvPORT IS USED IN SrcNode !!!
        :type SrcParameter: int or str
        :param DestParameter: Id of the destination GvPort (not the ID of the parameter) or the name of the destination GvPort PARAMETER WILL BE IGNORED IF GvPORT IS USED IN DestNode !!!
        :type DestParameter: int or str
        :return: True if connection is created overthiwe False
        :rtype: Bool
        """
        self._CheckMatIsValid()

        # Check Type
        if not isinstance(SrcNode, Node) and not isinstance(
            SrcNode, c4d.modules.graphview.GvPort
        ):
            raise TypeError("SrcNode is not valid Node Object or gvPort")

        if not isinstance(DestNode, Node) and not isinstance(
            DestNode, c4d.modules.graphview.GvPort
        ):
            raise TypeError("DestNode is not valid Node Object or gvPort")

        if not isinstance(SrcNode, c4d.modules.graphview.GvPort):
            if not isinstance(SrcParameter, int) and not isinstance(SrcParameter, str):
                raise TypeError(
                    "SrcParameter is not parameter or not name of a parameter"
                )

        if not isinstance(DestNode, c4d.modules.graphview.GvPort):
            if not isinstance(DestParameter, int) and not isinstance(
                DestParameter, str
            ):
                raise TypeError(
                    "DestParameter is not parameter or not name of a parameter"
                )

        # Get GvNode
        gvNodeSrc = SrcNode.GetNode()
        gvNodeDest = DestNode.GetNode()
        if not gvNodeSrc or not gvNodeDest:
            return False

        # Get Src GvPort
        if isinstance(SrcNode, c4d.modules.graphview.GvPort):
            gvPortSrc = SrcNode
        else:
            gvPortSrc = SrcNode.SearchPort(SrcParameter, c4d.GV_PORT_OUTPUT)

        # Get Dest GvPort
        if isinstance(DestNode, c4d.modules.graphview.GvPort):
            gvPortDest = DestNode
        else:
            gvPortDest = DestNode.SearchPort(DestParameter, c4d.GV_PORT_INPUT)

        # Check if they can be linked
        if not gvPortSrc or not gvPortDest:
            return False
        if gvNodeSrc.GetNodeMaster() != gvNodeDest.GetNodeMaster():
            return False
        if gvPortDest.IsIncomingConnected():
            return False

        if self.doUndo:
            self._gvMaster.AddUndo()
        return gvPortSrc.Connect(gvPortDest)

    def CreateMaterial(self, MatType=1000, doc=None):
        """Create a new redshift material.

        :param MatType: The type of the Redshift shader (from 1001, Material to 1010 Volume)
        :type MatType: int
        :type doc: c4d.documents.BaseDocument the document to insert material
        :return: Created material or None if it's fail
        :rtype: c4d.Material or None.
        """
        if not isinstance(MatType, int):
            raise TypeError("MatType is not an Integer")
        c4d.documents.BaseDocument
        if not isinstance(doc, c4d.documents.BaseDocument) and doc is not None:
            raise TypeError("doc is not a BaseDocument")

        if doc is None:
            doc = c4d.documents.GetActiveDocument()

        if MatType < 1000 or MatType > 1010:
            raise ValueError("Invalid value for matType, must be from 1000 to 1010")

        c4d.CallCommand(1036759, MatType)
        mat = doc.GetFirstMaterial()
        if not mat:
            return None

        return mat

    def IsRedshiftMaterial(self, mat):
        global redshift
        if mat is None:
            return False
        if not isinstance(mat, c4d.BaseMaterial):
            return False
        if not mat.IsInstanceOf(redshift.Mrsmaterial):
            return False

        return True

    def RemoveConnection(self, port, node=None, portType=None):
        """Disconnect all connection from a given port of Nodes.

        :param port: Id of the GvPort (not the ID of the parameter), Name of the GvPort or The GvPort of the Node returned by Node.ExposeParameter or Node.SearchPort
        :type port: int, str or c4d.modules.graphview.GvPort
        :param node: The Node that host the GvPort who want to remove connection ..note:: PARAMETER WILL BE IGNORED IF GvPORT IS USED IN port !!!
        :type node: :class:`.Node`
        :param portType: GV_PORT_INPUT or GV_PORT_OUTPUT ..note:: PARAMETER WILL BE IGNORED IF GvPORT IS USED IN port !!!
        :type portType: int
        :return: True if connection is created overthiwe False
        :rtype: Bool
        """
        self._CheckMatIsValid()

        # Check Type
        if not isinstance(port, c4d.modules.graphview.GvPort):
            if not isinstance(node, Node):
                raise TypeError("node is not valid Node Object")

        if (
            not isinstance(port, int)
            and not isinstance(port, str)
            and not isinstance(port, c4d.modules.graphview.GvPort)
        ):
            raise TypeError("port is not parameter or not name of a parameter")

        # Get the GvPort
        gvPort = None
        if isinstance(port, c4d.modules.graphview.GvPort):
            gvPort = port
        else:
            gvPort = node.SearchPort(port, portType)

        # Undo if needed
        if self.doUndo:
            self._gvMaster.AddUndo()

        # Remove connection
        return gvPort.Remove()
