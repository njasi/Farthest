#!/usr/bin/env python3

# The main script runs on a crontab
# 0 0 * * 1-5 /usr/bin/python3 /home/pi/Documents/Farthest/src/quiet_client.py 1
# 0 2 * * 6,0 /usr/bin/python3 /home/pi/Documents/Farthest/src/quiet_client.py 1
# 0 7 * * * /usr/bin/python3 /home/pi/Documents/Farthest/src/quiet_client.py 2


import socket
import sys
from handlers.helpers import is_quiet_hour

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server


def ping(message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(message)
        data = s.recv(1024)


def listen():
    '''Listen to incoming pings from the contab script'''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        # listen as long as bot is active
        while True:
            conn, addr = s.accept()
            with conn:
                if not addr[0] == HOST:
                    continue
                while True:
                    data = conn.recv(1024)
                    if data == b"sush":
                        conn.sendall(data)
                        # QUEUE.set_volume(0)
                        # TODO change to new volume method
                        break
                    elif data == b"wake" and not is_quiet_hour():
                        conn.sendall(data)
                        # QUEUE.set_volume(20)
                        # TODO change to new volume method
                        break
                    break


if __name__ == "__main__":
    if sys.argv[1] == '1':
        ping(b'sush')
    else:
        ping(b'wake')
