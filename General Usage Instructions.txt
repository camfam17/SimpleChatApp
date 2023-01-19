First the serverApp is started.
When the clientApp is started, it requests the user’s name. 
 It then automatically establishes a connection with the serverApp through the “/knock knock” command, ensuring that the name is unique. 
 If the name is not unique, then the client will be asked repeatedly until a unique name is chosen.
After the connection is established, the client is welcomed to the waiting room with the message: "Welcome, " + name + ", to the waiting room. 
 “Type /list, /create [room name] or /join [room name]".
From here, the client may use the following three commands 
 (commands are denoted by the first character being a forward slash (“/”):
 /list will print a list of the current chatrooms.
 /create + [room name] will create a new chatroom with that name, but the client will not automatically join it.
 /join + [room name] will allow the client to join that chatroom. The client will be welcomed to the chatroom with the message:  
	"Welcome to " + roomName + "Type /exit to go back to waiting room". From this point, the client may send messages to the chatroom. These messages will be broadcast to all members of the chatroom.

/exit will take the client out of the current chatroom and put it back in the waiting room. 
