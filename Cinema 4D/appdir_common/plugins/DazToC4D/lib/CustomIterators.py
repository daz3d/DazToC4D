class ObjectIterator :
    def __init__(self, baseObject):
        self.baseObject = baseObject
        self.currentObject = baseObject
        self.objectStack = []
        self.depth = 0
        self.nextDepth = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.currentObject == None :
            raise StopIteration

        obj = self.currentObject
        self.depth = self.nextDepth

        child = self.currentObject.GetDown()
        if child :
            self.nextDepth = self.depth + 1
            self.objectStack.append(self.currentObject.GetNext())
            self.currentObject = child
        else :
            self.currentObject = self.currentObject.GetNext()
            while( self.currentObject == None and len(self.objectStack) > 0 ) :
                self.currentObject = self.objectStack.pop()
                self.nextDepth = self.nextDepth - 1
        return obj
    
    next = __next__                 #To Support Python 2.0

class TagIterator:

    def __init__(self, obj):
        currentTag = None
        if obj:
            self.currentTag = obj.GetFirstTag()

    def __iter__(self):
        return self

    def __next__(self):

        tag = self.currentTag
        if tag == None:
            raise StopIteration

        self.currentTag = tag.GetNext()

        return tag
    next = __next__             #To Support Python 2.0


