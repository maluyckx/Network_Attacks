import subprocess

# Run a simple shell command (e.g., 'ls' for Unix-based systems or 'dir' for Windows)
for i in range(5):
    print("[+] Starting DDOS Syn Flood Attack id: {}".format(i))
    subprocess.run(['python3'], ['main.py'], ['&'])


