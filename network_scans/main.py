"""
Luyckx Marco 496283
Bouhnine Ayoub 500048

Network scans
"""
import socket
import time
import concurrent.futures
import threading

def portscan(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((t_IP, port))
            protocol_name = socket.getservbyport(port)
            with print_lock:
                print(port, 'is open. Possibly :', protocol_name) # possibly prc c threadé donc ça peut mélanger les outputs
        except:
            pass



if __name__ == "__main__":
    socket.setdefaulttimeout(0.25)
    print_lock = threading.Lock()

    target = "192.168.56.101"
    t_IP = socket.gethostbyname(target)
    print('Starting scan on host :', t_IP)
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        start_time = time.time()
        ports = [port for port in range(1, 65557)]
        results = executor.map(portscan, ports)

    print('Time taken :', time.time() - start_time)