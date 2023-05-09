import socket
import threading
from queue import Queue
import struct
import time
from scapy.all import *

# Replace with your target hosts
target_hosts = ["10.12.0.10","10.12.0.20","10.12.0.30","10.12.0.40"]
port_range = (1, 65535)
num_threads = 100
ntp_port = 123

NTP_PACKET = struct.pack("!12I", *(2 << 3, ) + (0,) * 11)

def scan_host(host, port_queue):
    while not port_queue.empty():
        port = port_queue.get()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            
            if result == 0:
                print(f"Host: {host}, Port: {port} is open")

            # elif port == ntp_port: # TODO : revoir cette partie /!\ /!\ /!\ /!\ /!\ /!\ /!\ /!\
            #     ntp_packet = IP(dst=host)/UDP(dport=123)/Raw(load='\x1b' + 47 * '\0')
            #     ans, unans = sr(ntp_packet,timeout=2) # or add the parameter loop=1
            #     # Check if there is a response
            #     print("ans : ", ans)
            #     print("unans : ", unans)
            #     if ans:
            #         print("There is a response!")
            #     else:
            #         print("No response.")

            sock.close()
        except Exception as e:
            print(f"Error scanning host {host}, port {port}: {e}")

def main():
    for host in target_hosts:
        print(f"Scanning host: {host}")
        start_time = time.time()
        port_queue = Queue()
        for port in range(*port_range):
            port_queue.put(port)

        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=scan_host, args=(host, port_queue))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()
        print(f"Time taken : {time.time() - start_time}")

if __name__ == "__main__":
    main()
