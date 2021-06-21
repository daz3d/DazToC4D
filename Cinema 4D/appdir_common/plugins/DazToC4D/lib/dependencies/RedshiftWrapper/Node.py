"""
MIT License

Copyright (c) 2017 Gr4ph0s

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import sys
import c4d

try:
    import redshift
except:
    pass


from .ImportTester import ImportTester
from .MetaName import MetaName


class Node(MetaName):
    __metaclass__ = ImportTester
    """Represent a Node that already exist in a Material.

    :member _GvNode: (c4d.modules.graphview.GvNode) - The GvNode linked to this Node. READ-ONLY DO NOT EDIT !!! 
    :member _NodeType: (Int or Str) - Int (a Cinema 4D Node look at https://developers.maxon.net/docs/Cinema4DPythonSDK/html/types/gvnodes.html) or a Redshift Node member loot at :class:`MetaclassName`.
    :member __DoUndo: (Bool) DEFINE BY :class:`.Redshift`,  True if the wrapper have to call GvMaster.AddUndo() before any change otherwise False
    """

    _GvNode = None
    _NodeType = None  # string if redshift int if xpresso
    __DoUndo = True

    def __init__(self, gvNode, undo=True):
        """Initialization of the node

        :param gvNode: The GvNode linked to this Node.
        :type gvNode: c4d.modules.graphview.GvNode
        :param undo: If undo need to be done.
        :type undo: Bool
        """
        if not isinstance(gvNode, c4d.modules.graphview.GvNode):
            raise TypeError("gvNode is not a c4d.modules.graphview.GvNode")

        self.__DoUndo = undo
        self._GvNode = gvNode
        self._SetNodeType()

    def __getitem__(self, key):
        return self.GvNode[key]

    def __setitem__(self, key, value):

        try:
            if isinstance(key, unicode):
                key = str(key)
            if isinstance(value, unicode):
                value = str(value)
        except:
            pass

        self._GvNode[key] = value

    def __repr__(self):
        return self.GetName()

    def _SetNodeType(self):
        """Set self._NodeType according the GvNode

        Int => a Cinema 4D Node look at https://developers.maxon.net/docs/Cinema4DPythonSDK/html/types/gvnodes.html
        Str => a Redshift Node look at ::class:: MetaclassName
        """
        global redshift
        if self._GvNode.IsInstanceOf(redshift.GVrsshader):
            self._NodeType = self._GvNode[c4d.GV_REDSHIFT_SHADER_META_CLASSNAME]
        elif self._GvNode.GetOperatorID() == 1036746:
            self._NodeType = self.Output
        elif self._GvNode.GetOperatorID() == 1036762:
            self._NodeType = self.UtBaker
        else:
            self._NodeType = self._GvNode.GetOperatorID()

    def GetNode(self):
        """Get the GvNode linked.

        :return: The GvNode linked to this Node.
        :rtype: c4d.modules.graphview.GvNode
        """
        return self._GvNode

    def GetType(self):
        """Get the GvNode Type.

        :return: Int (a Cinema 4D Node look at https://developers.maxon.net/docs/Cinema4DPythonSDK/html/types/gvnodes.html) or a Redshift Node member loot at :class:`MetaclassName`
        :rtype: Int or Str
        """
        return self._NodeType

    def GetColor(self):
        """Get the color of a GvNode Type.

        :return: Color of the GvNode linked to this Node.
        :rtype: c4d.Vector
        """
        return self[c4d.ID_GVBASE_COLOR]

    def SetColor(self, color=None):
        """Set the color of the GvNode.

        :param color: New color of the node, if None default color according the type of the node type
        :type color: c4d.Vector or None
        """
        if not isinstance(color, c4d.Vector) and color is not None:
            raise TypeError("color is not a valid color")

        if color is None:
            color = self.GetDefaultColorNode(self.GetType())

        if self.__DoUndo:
            self._GvNode.GetNodeMaster().AddUndo()
        self[c4d.ID_GVBASE_COLOR] = color

    def SetName(self, newName):
        """Set the name of the GvNode.

        :param newName: New name of the GvNode.
        :type newName: str
        """
        if self.__DoUndo:
            self._GvNode.GetNodeMaster().AddUndo()
        self._GvNode.SetName(newName)

    def GetName(self):
        """Get the name of the GvNode.

        :return: Name of the GvNode.
        :rtype: str
        """
        return self._GvNode.GetName()

    def SearchPort(self, portToSearch, searchType=None):
        """Search a GvPort in the Node, parameter should be exposed.

        :param portToSearch: The name of the parameter or The port ID of the Node.
        :type portToSearch: str or int
        :param searchType: GV_PORT_INPUT or GV_PORT_OUTPUT if None for both (None is only working for str portToSearch).
        :return: GvPort that match the search.
        :rtype: c4d.modules.graphview.GvPort or None
        """
        if not isinstance(portToSearch, int) and not isinstance(portToSearch, str):
            raise TypeError("portToSearch is not parameter or not name of a parameter")

        # Search by Name
        if isinstance(portToSearch, str):
            # Set the list of gvPort to check
            gvPortList = list()
            if searchType is None:
                gvPortList += self._GvNode.GetOutPorts()
                gvPortList += self._GvNode.GetInPorts()
            elif searchType == c4d.GV_PORT_OUTPUT:
                gvPortList += self._GvNode.GetOutPorts()
            elif searchType == c4d.GV_PORT_INPUT:
                gvPortList += self._GvNode.GetInPorts()
            else:
                raise TypeError("SearchType Unknow")

            for gvPort in gvPortList:
                if gvPort.GetName(self._GvNode) == portToSearch:
                    return gvPort

        # Get port ID
        if isinstance(portToSearch, int):
            if searchType is None:
                raise TypeError("Cant search int without SearchType")
            elif searchType == c4d.GV_PORT_OUTPUT:
                return self._GvNode.GetOutPort(portToSearch)
            elif searchType == c4d.GV_PORT_INPUT:
                return self._GvNode.GetInPort(portToSearch)

        return None

    def ExposeParameter(self, parameterID, portType):
        """Expose a parameter in a GvNode.

        :param parameterID: The ID of the parameter or the full c4d.DescID.
        :type paramaterID: int or c4d.DescID
        :param portType: c4d.GV_PORT_INPUT or c4d.GV_PORT_OUTPUT.
        :type portType: int
        :return: True if success otherwise False.
        :rtype: Bool
        """
        if not isinstance(parameterID, int) and not isinstance(parameterID, c4d.DescID):
            raise TypeError("parameterID is not valid")

        if isinstance(parameterID, int):
            if self._GvNode.AddPortIsOK(portType, parameterID):
                if self.__DoUndo:
                    self._GvNode.GetNodeMaster().AddUndo()
                return self._GvNode.AddPort(
                    portType, c4d.DescID(c4d.DescLevel(parameterID)), message=True
                )
        else:
            if self.__DoUndo:
                self._GvNode.GetNodeMaster().AddUndo()
            return self._GvNode.AddPort(portType, parameterID, message=True)

        return False
