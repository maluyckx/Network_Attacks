"""
Luyckx Marco 496283
Bouhnine Ayoub 500048

Network port scan

This script is used to thread a network port scan for open ports with a particular focus on the NTP port. For more information, see the README.md file.

Usage : python3 main.py
"""


import socket
import threading
from queue import Queue
import time
from scapy.all import *

target_hosts = ["10.12.0.10", "10.12.0.20", "10.12.0.30", "10.12.0.40"]
port_range = (1, 65535)
num_threads = 100
ntp_port = 123

def scan_ntp(host):
    """
    Function to scan the NTP port
    """
    global ntp_port
    packet = IP(dst=host)/UDP(sport=random.randint(2000,65535),dport=123)/NTP(version=4)
    ans = sr(packet, timeout=2, verbose=False)[0]
    # check if response is a NTP response packet
    if ans and ans[0][1].haslayer(UDP):
        print(f"Host : {host}, Port : {ntp_port} is open")
        
def scan_host(host, port_queue):
    """
    Function to scan ports on a single host
    """
    while not port_queue.empty():
        port = port_queue.get()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.25)
            result = sock.connect_ex((host, port))

            if result == 0:
                print(f"Host : {host}, Port : {port} is open")

            sock.close()
        except Exception as e:
            print(f"Error scanning host {host}, port {port} : {e}")

def main():
    for host in target_hosts:
        print(f"Scanning host : {host}")
        scan_ntp(host)
        start_time = time.time()
        port_queue = Queue()
        for port in range(*port_range):
            port_queue.put(port)

        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=scan_host, args=(host, port_queue))
            t.start()
            threads.append(t)

        # Wait for all the threads to complete before moving on to the next host
        for t in threads:
            t.join()
            
        print(f"Time taken : {time.time() - start_time}")


if __name__ == "__main__":
    main()