#!/usr/bin/env python3

# This runs on a crontab
# 0 0 * * 1-5 /usr/bin/python3 /home/pi/Documents/Farthest/src/quiet_client.py 1
# 0 2 * * 6,0 /usr/bin/python3 /home/pi/Documents/Farthest/src/quiet_client.py 1
# 0 7 * * * /usr/bin/python3 /home/pi/Documents/Farthest/src/quiet_client.py 2


import socket
import sys


def ping(message):
    HOST = '127.0.0.1'  # The server's hostname or IP address
    PORT = 65432        # The port used by the server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(message)
        data = s.recv(1024)


if __name__ == "__main__":
    if sys.argv[1] == '1':
        ping(b'sush')
    else:
        ping(b'wake')
