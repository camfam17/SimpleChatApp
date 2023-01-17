from socket import *
import threading
from datetime import datetime
from Error_Detection import *
import time
import random

serverName = "127.0.0.1"
serverPort = 12000

global nameG
clientSocket = socket(AF_INET, SOCK_DGRAM)

unackmsg = []   # stores all messages that have not received an acknowledgment from the server

lossRate = 0  # lossRate is percentage chance that a packet will be lost


def packetLost(lossPercent):  # returns True lossPercent% of the time
    return random.randrange(100) < lossPercent


# this function has two loops
# the first loop ensures the client chooses a unique name and establishes a connection to the server
# the second loop iterates continuously to handle incoming messages
def receive():
    global nameG
    clientSocket.bind(('', 0))
    while True:
        # loop will iterate until client chooses a unique name and connection is established
        nameG = input("Enter name: ")
        if len(nameG) == 0: # name must contain characters
            continue
        elif nameG[0] == "/":   # name cant start with /
            print("No special characters (\"/\" is a special character)")
            continue

        msg = "/knock knock" + nameG + getTimeStamp()

        packet = create_packet(msg.encode(), clientSocket.getsockname()[1], serverPort)
        clientSocket.sendto(packet, (serverName, serverPort))
        message, address = clientSocket.recvfrom(2048)
        message, checksum = unpack_packet(message)

        message = message.decode()
        print(message)
        if message[:len("Welcome, " + nameG)] == "Welcome, " + nameG:   # server confirms name is unique, connection is established
            sendThread.start()
            break

    while True:     # this loop continuously receives packets from the server
        packet, address = clientSocket.recvfrom(2048)
        data, checksum = unpack_packet(packet)

        if error_detection(data, checksum):  # check for packet corruption, only send ACK if there is no corruption
            data = data.decode()
            message = data[:-19]
            timestamp = data[-19:]

            if message[:3] == "ACK":    # this block handles the acknowledgment from server
                lock.acquire()      # for thread safety (unackmsg list is also used in lossThread)
                for i in range(len(unackmsg)):
                    c = unackmsg[i]
                    msg = c[:-19]
                    t = c[-19:]
                    if t == timestamp:
                        unackmsg.pop(i)
                lock.release()
            else:   # this block sends acknowledgment to the server and then prints the message received from the server
                ack = "ACK" + timestamp
                p = create_packet(ack.encode(), clientSocket.getsockname()[1], serverPort)
                clientSocket.sendto(p, (serverName, serverPort))
                print("\n" + message)

# this function handles the sending of messages
# only once a connection has been established to the server does this thread start
def send():
    while True:     # this loop receives input from the user and sends it to the server. includes packet loss simulation
        message = input()
        if len(message) == 0:
            continue

        message += getTimeStamp()

        packet = create_packet(message.encode(), clientSocket.getsockname()[1], serverPort)

        if not packetLost(lossRate):  # simulated packet loss
            clientSocket.sendto(packet, (serverName, serverPort))
        else:
            print("Failed to send")
        unackmsg.append(message)    # adds message to list of unacknowledged messages


# this function handles packet loss/error but iterating through the list of unacknowledged messages,
# checking to see if it has been 5 seconds since being sent and then resends the messages
def lossDetection():
    while True:     # this loop detects if messages have not received acknowledgement and retransmits them after 5 seconds without acknowledgment
        if len(unackmsg) > 0:

            lock.acquire()  # for thread safety (unackmsg list is also used in receiveThread)
            for i in range(len(unackmsg)):
                c = unackmsg[i]
                msg = c[:-19]
                timestamp = c[-19:]

                duration = (datetime.strptime(getTimeStamp(), '%Y-%m-%d %H:%M:%S') - datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')).total_seconds()
                if duration > 5:
                    print("retransmitting")
                    p = create_packet(c.encode(), clientSocket.getsockname()[1], serverPort)
                    clientSocket.sendto(p, (serverName, serverPort))
                else:
                    print("Retrying in ", int(5-duration))
            lock.release()
        time.sleep(1)   # loop sleeps for 1 second to not over-use resources


def getTimeStamp():     # returns a timestamp in format YYYY-MM-DD hh-mm-ss
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Three threads: one for receiving messages, one for sending messages, one for detecting packet loss
receiveThread = threading.Thread(target=receive)
sendThread = threading.Thread(target=send)
lossThread = threading.Thread(target=lossDetection)

lock = threading.Lock()

lossThread.start()
receiveThread.start()
