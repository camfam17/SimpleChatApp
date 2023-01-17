class clientObj:

    # object for the purpose of storing attributes of a client
    # attributes are client name, client socket address and which chatroom they are in

    def __init__(self, name):
        self.name = name

        self.address = None
        self.chatRoom = None

    def getAddress(self):
        return self.address
    def setAddress(self, address):
        self.address = address
    def hasAddress(self):
        return self.address is not None

    def getName(self):
        return self.name
    def setName(self, name):
        self.name = name

    def getChatRoom(self):
        return self.chatRoom
    def setChatRoom(self, chatRoom):
        self.chatRoom = chatRoom
    def hasChatRoom(self):
        return self.chatRoom != "waiting room"