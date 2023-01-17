import random
from socket import *
from clientObj import clientObj
import threading
from datetime import datetime
from Error_Detection import *
import time

clients = []
chatrooms = []
newPackets = []
unackmsg = []

lossRate = 0  # lossRate is percentage chance that a packet will be lost

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))


def clientExists(name):     # returns true if clientObj object with the same name exists
    for i in range(len(clients)):
        if clients[i].getName() == name:
            return True
    return False


def getClient(name):    # returns a clientObj object with the same name
    for i in range(len(clients)):
        if clients[i].getName() == name:
            return clients[i]


def getClientFromAddress(address):  # returns a clientObj object with the same address
    for i in range(len(clients)):
        if clients[i].getAddress() == address:
            return clients[i]


def packetLost(lossPercent):  # returns True lossPercent% of the time
    return random.randrange(100) < lossPercent


def getTimeStamp():     # returns a timestamp in format YYYY-MM-DD hh-mm-ss
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# this is a light-weight thread that receives a list and appends it to the newPackets list
# no packet processing is done here, in case the server receives multiple messages at the same time
def receiveMessages():
    print("Server is ready to receive")
    while True:
        rec = serverSocket.recvfrom(2048)
        newPackets.append(rec)

# this function process messages
# it either listens to commands denoted by "/"
# or broadcasts messages to all members of a chatroom
def processMessages():
    while True:
        if len(newPackets) != 0:
            print("Message received: " + getTimeStamp())
            rec = newPackets.pop(0)

            data, checksum = unpack_packet(rec[0])
            clientAddress = rec[1]
            data = data.decode()

            message = data[:-19]
            timestamp = data[-19:]

            sendmsg = "Empty"
            if message[:len("/knock knock")] == "/knock knock":  # signal received from client receiver port
                # this block is to establish connection to the client
                name = message[len("/knock knock"):]
                if clientExists(name) or name == "Server":
                    p = create_packet("name already taken, try again".encode(), serverPort, clientAddress[1])
                    serverSocket.sendto(p, clientAddress)
                else:
                    c = clientObj(name)
                    c.setAddress(clientAddress)
                    c.setChatRoom("waiting room")
                    clients.append(c)
                    p = create_packet(("Welcome, " + name + ", to the waiting room\nType /list, /create [room name] or /join [room name]").encode(), serverPort, clientAddress[1])
                    serverSocket.sendto(p, clientAddress)
                    # connection is now established
            else:

                if message[:3] == "ACK":
                    # this block receives and processes acknowledgments
                    lock.acquire()
                    for i in range(len(unackmsg)):
                        x = unackmsg[i]
                        data = x[0]
                        cln = x[1]

                        msg = data[:-19]
                        unackts = data[-19:]

                        if unackts == timestamp and cln == clientAddress:
                            unackmsg.pop(i)
                            break
                    lock.release()
                else:
                    if error_detection(data.encode(), checksum):     # check for packet corruption, only send ACK if there is no corruption
                        ack = "ACK" + timestamp
                        p = create_packet(ack.encode(), serverPort, clientAddress[1])
                        serverSocket.sendto(p, clientAddress)

                    if message[0] == "/":   # "/" is used to signal a command
                        # this block handles commands (list, create, join and exit) appropriately
                        if clientExists((getClientFromAddress(clientAddress)).getName()):
                            c = getClientFromAddress(clientAddress)
                            if c.getChatRoom() == "waiting room":
                                if message[:len("/list")] == "/list":  # return a list of all open chatrooms
                                    rooms = ""
                                    if len(chatrooms) == 0:
                                        sendmsg = "No chatrooms open"
                                    else:
                                        for p in chatrooms:
                                            rooms += p + ", "
                                        sendmsg = rooms[:len(rooms)-2]
                                elif message[:len("/create")] == "/create":  # creates a chatrooms and sends confirmation of chatroom being created
                                    if message == "/create":
                                        sendmsg = "Invalid command"
                                    else:
                                        roomName = message[len("/create"):]
                                        chatrooms.append(roomName)
                                        sendmsg = roomName + " created successfully"
                                elif message[:len("/join")] == "/join":  # adds the client to the open chatroom specified
                                    if message == "/join":
                                        sendmsg = "Invalid command"
                                    else:
                                        roomName = message[len("/join"):]
                                        if roomName in chatrooms:
                                            c.setChatRoom(roomName)
                                            sendmsg = "Welcome to " + roomName + "\nType /exit to go back to waiting room"
                                        else:
                                            sendmsg = "chatroom does not exist"
                            else:
                                if message[:len("/exit")] == "/exit":  # exits the client from the chatroom and brings them back to waiting room
                                    sendmsg = "Exited " + c.getChatRoom() + ". Back in waiting room"
                                    c.setChatRoom("waiting room")

                        if sendmsg != "Empty":  # sends a message if a valid command was used
                            sendmsg += getTimeStamp()
                            p = create_packet(sendmsg.encode(), serverPort, clientAddress[1])
                            if not packetLost(lossRate):   # simulates packet loss
                                serverSocket.sendto(p, clientAddress)
                            else:
                                print("Failed to send")
                            unackmsg.append((sendmsg, clientAddress))
                    elif getClientFromAddress(clientAddress).getChatRoom() != "waiting room":
                        # broadcast message to all other clients in the chatroom
                        c = getClientFromAddress(clientAddress)
                        if clientExists(c.getName()):
                            for i in range(len(clients)):
                                if clients[i] is not c and clients[i].getChatRoom() == c.getChatRoom():
                                    msg = c.getName() + " in " + c.getChatRoom() + " at " + timestamp + ": " + message + getTimeStamp()
                                    p = create_packet(msg.encode(), serverPort, clientAddress[1])
                                    if not packetLost(lossRate):  # simulates packet loss
                                        serverSocket.sendto(p, clients[i].getAddress())
                                    else:
                                        print("Failed to send")
                                    unackmsg.append((msg, clients[i].getAddress()))


# this function handles packet loss/error but iterating through the list of unacknowledged messages,
# checking to see if it has been 5 seconds since being sent and then resends the messages
def lossDetection():
    while True:  # this loop detects if messages have not received acknowledgement and retransmits them after 5 seconds without acknowledgment
        if len(unackmsg) > 0:
            lock.acquire()
            for i in range(len(unackmsg)):

                x = unackmsg[i]
                data = x[0]
                clientAddress = x[1]

                msg = data[:-19]
                timestamp = data[-19:]

                dur = (datetime.strptime(getTimeStamp(), '%Y-%m-%d %H:%M:%S') - datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')).total_seconds()
                if dur > 5:
                    print("retransmitting")
                    packet = create_packet(data.encode(), serverPort, clientAddress[1])
                    serverSocket.sendto(packet, clientAddress)
                else:
                    print("Retrying in ", int(5-dur))
            lock.release()
        time.sleep(1)  # loop sleeps for 1 second to not over-use resources


# Three threads: one for receiving packets, one for process those packets and one for detecting packet loss
processThread = threading.Thread(target=processMessages)
receiveThread = threading.Thread(target=receiveMessages)
lossThread = threading.Thread(target=lossDetection)

lock = threading.Lock()

lossThread.start()
receiveThread.start()
processThread.start()
