#!/usr/bin/env python 
# Python Network Programming Cookbook, Second Edition -- Chapter - 1 
# This program is optimized for Python 2.7.12 and Python 3.5.2. 
# It may run on any other version with/without modifications. 
 
import socket 
import sys 
import argparse
import time

data_payload = 2048 
 
def echo_client(host, port, delay=5, repeat=5, tun=None): 
    """ A simple echo client """ 
    # Create a UDP socket 
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
    if tun:
        sock.bind(tun, 0)
 
    server_address = (host, port) 
    print("Connecting to %s port %s" % server_address) 
    message = 'This is the message. It will be repeated.' 

    for i in range(repeat):
 
        # Send data 
        message = "Test message. This will be echoed" 
        print("Sending %s" % message) 
        sent = sock.sendto(message.encode('utf-8'), server_address) 
 
        # Receive response 
        data, server = sock.recvfrom(data_payload) 
        print("received %s" % data) 
        time.sleep(delay)

    print("Closing connection to the server") 
    sock.close() 
 
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Socket Server Example') 
    parser.add_argument('--host', action="store", dest="host", type=str, required=True,
                        help="server host address") 
    parser.add_argument('-p', action="store", dest="p", type=int, required=True,
                        help="server host port")
    parser.add_argument('-d', action="store", dest="d", type=int, required=False,
                        help="delay between each message")
    parser.add_argument('-r', action="store", dest="r", type=int, required=False,
                        help="send messege x times") 
    parser.add_argument('-t', action="store", dest="t", type=int, required=False,
                        help="tunnel interface") 
    given_args = parser.parse_args()  
    host = given_args.host
    port = given_args.p
    delay = given_args.d
    repeat = given_args.r
    tun = given_args.t
    echo_client(host, port, delay, repeat, tun)