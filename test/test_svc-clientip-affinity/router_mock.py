#!/usr/bin/python3
import socket
import select
import threading
import time
import random
import sys
import datetime

#Create the fake BGP session
def tcp4_connect(remote_ip, tcp_port, local_ip):
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind((local_ip, 0))
    tcp.settimeout(5) #Fail fast (sometimes it gets stuck in connect() for a long time)
    tcp.connect((remote_ip, tcp_port))
    return tcp

def udp4_bind(remote_ip, udp_port, local_ip):
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind((local_ip, 0))
    return udp

def ts():
    return datetime.datetime.now().timestamp()

def main():
    tcp_port = 179
    udp_port = 2055

    remote_ip=sys.argv[1]
    local_ip=sys.argv[2]

    while True:
        tcp = udp = None
        sleep_time = 1
        try:
            #Attempt to TCP connect; keep trying
            print(f"[{local_ip}][{ts()}] Connecting to tcp://{remote_ip}:{tcp_port}...")
            tcp = tcp4_connect(remote_ip, tcp_port, local_ip)
            if not tcp:
                raise Exception()
            print(f"[{local_ip}][{ts()}] Connected")
        except:
            print(f"[{local_ip}][{ts()}] ERROR: unable to connect to tcp://{remote_ip}:{tcp_port}. Will retry in {sleep_time} seconds")
            time.sleep(sleep_time)
            continue

        try:
            #Should never fail, unless bind fails
            print(f"[{local_ip}][{ts()}] Binding to udp://{remote_ip}:{udp_port}...")
            udp = udp4_bind(remote_ip, udp_port, local_ip)
            if not udp:
                raise Exception()
            print(f"[{local_ip}][{ts()}] Bound")
        except:
            tcp.close()
            print(f"[{local_ip}][{ts()}] ERROR: unable to connect to udp://{remote_ip}:{udp_port}. Bind error? Will retry in {sleep_time} seconds")
            time.sleep(sleep_time)
            continue

        #Wait sometime to remove noise in the logs (github runners are not
        #so powerful)
        time.sleep(sleep_time)

        #Main I/O loop
        print(f"[{local_ip}][{ts()}] main I/O loop...")
        sleep_time = 0.25 #4 pkts/s
        while True:
            udp.sendto("HELLO".encode(), (remote_ip, udp_port))
            time.sleep(sleep_time)

if __name__ == "__main__":
    main()
