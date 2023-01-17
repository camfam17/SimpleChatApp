import imp
import re
from socket import *
import struct
import zlib


# Calculates the checksum of the data
def checksum_calculator(encoded_message):
    checksum = zlib.crc32(encoded_message)
    return checksum


# Creates the UDP Header.
def UDP_Header(encoded_message, sourcePort, destinationPort):
    data_length = len(encoded_message)
    checksum = checksum_calculator(encoded_message)
    header = struct.pack("!IIII", sourcePort, destinationPort, data_length, checksum)
    return header


# Creates packet to be sent over
def create_packet(encoded_message, sourceport, destination_port):
    return UDP_Header(encoded_message, sourceport, destination_port) + encoded_message


# Unpacks the packet that just came through
def unpack_packet(packet):
    header = packet[:16]
    header = struct.unpack("!IIII", header)
    data = packet[16:]
    correct_checksum = header[3]

    return data, correct_checksum


# Performs Error detection
# True - No error detected
# False- Error detected
def error_detection(data, correct_checksum):
    return correct_checksum == checksum_calculator(data)
