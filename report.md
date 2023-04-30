# Network Attacks

## Mininet topology

![Topology](/img/topo.png)

## Firewall rules for basic enterprise network protection

To make the topology more secure, we need to make changes : 
1) Workstations can send a ping and initiate a connection towards any other host (other workstations, DMZ servers, internet).
2) DMZ servers cannot send any ping or initiate any connection. They can only respond to  incoming connections.
3) The Internet can send a ping or initiate a connection only towards DMZ servers. They cannot  send a ping or initiate connections towards workstations. 
 
To implement these changes, we set up several nft tables.

The first one is one the router R1.
```
#!/usr/sbin/nft -f

flush ruleset

table inet filter {
    chain input {
        type filter hook input priority 0; policy accept;
    }

    chain forward {
        type filter hook forward priority 0; policy drop;

        # Allow workstations to send a ping and initiate a connection towards any other hosts
        iif "r1-eth0" ip saddr 10.1.0.0/24 accept

        # Allow DMZ servers & Internet to only respond to incoming connections
        iif "r1-eth12" ip saddr {10.12.0.0/24,10.2.0.0/24} ip daddr 10.1.0.0/24 ct state established,related accept

    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}
```

The second one is one the router R2.
```
#!/usr/sbin/nft -f

flush ruleset

table inet filter {
    chain input {
        type filter hook input priority 0; policy accept;
    }

    chain forward {
        type filter hook forward priority 0; policy drop;

        # Allow workstations to send a ping and initiate a connection towards any other hosts
        iif "r2-eth12" ip saddr 10.1.0.0/24 accept

        # Allow DMZ servers to only respond to incoming connections (from Internet)
        iif "r2-eth12" ip saddr 10.12.0.0/24 ip daddr 10.2.0.0/24 ct state established,related accept

        # #### Bypass Command ####
        iif "r2-eth12" ip saddr 10.12.0.0/24 ip daddr 10.1.0.0/24 accept

        # Allow Internet to only respond to incoming connections towards workstations
        iif "r2-eth0" ip saddr 10.2.0.0/24 ip daddr 10.1.0.0/24 ct state established,related accept

        # Allow Internet to send ping and initiate a connection towards DMZ servers
        iif "r2-eth0" ip saddr 10.2.0.0/24 ip daddr 10.12.0.0/24 ct state new,established,related accept

    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}
```

And the last one need to be deployed on every host of the DMZ (http, dns, ntp and ftp).
```
#!/usr/sbin/nft -f

flush ruleset

table inet filter {
    chain input {
        type filter hook input priority 0; policy accept;
    }

    chain forward {
        type filter hook forward priority 0; policy drop;

    }

    chain output {
        type filter hook output priority 0; policy drop;

        ip daddr {10.2.0.0/24, 10.1.0.0/24, 10.12.0.1, 10.12.0.2} ct state established,related accept

    }
}
```


To validate our results, we used the `pingall` command :
```
mininet> pingall
*** Ping: testing ping reachability 
dns -> X X X X X X X X
ftp -> X X X X X X X X 
http -> X X X X X X X X
internet -> dns ftp http ntp X r2 X X 
ntp-> X X X X X X X X
r1 -> dns ftp http X ntp r2 ws2 ws3 
r2 -> dns ftp http internet ntp r1 X X 
ws2 -> dns ftp http internet ntp r1 r2 ws3 
ws3 -> dns ftp http internet ntp r1 r2 ws2 
*** Results: 52% dropped (34/72 received) 
```

To save time deploying all of our scripts at once, we created a simple Python script. To use it, simply run the command `source commands.py` in Mininet. Here's what the script looks like :
```bash
py r1.cmd("sudo nft -f firewall_r1.nft")
py r2.cmd("sudo nft -f firewall_r2.nft")
py dns.cmd("sudo nft -f firewall_DMZ.nft")
py http.cmd("sudo nft -f firewall_DMZ.nft")
py ftp.cmd("sudo nft -f firewall_DMZ.nft")
py ntp.cmd("sudo nft -f firewall_DMZ.nft")
```

## How to launch attacks and protections

All scripts are written in Python. To run them, simply use the command `python3 <script name>.py`.

## Network scans
The attack script can be found in the `network_scans` folder. It performs a parallelized scan of every port from 1 to 65535.

To launch the attack on `ws2` or `ws3`, follow these steps (TODO A AMELIORER):

1) Open a new terminal window using the command xterm X.
2) Navigate to the network_scans folder.
3) Run the command python3 main.py.
4) When prompted with the IP address, enter the target IP address.

### Attack
The attack script uses the socket library to create TCP sockets and attempt to connect to ports within the range of 1-65535. For each port, the script attempts to connect to the IP address and port combination using the `s.connect((t_IP, port))` statement. If a connection is successful, the script prints the port number and the protocol name associated with the port using the `socket.getservbyport(port)` function call.

To manage a thread pool of up to 100 worker threads, the script uses the `concurrent.futures.ThreadPoolExecutor` function. This allows multiple port scan requests to be processed concurrently.

Additionally, the script uses a timeout of 0.25 seconds for each port scan to prevent the script from hanging indefinitely if a port is unresponsive or blocked.

### Protection

TODO




## SSH/FTP brute-force attack
The attack scripts can be found in the `ssh_ftp_brute_force` directory.

Our script performs a threaded brute-force attack against an SSH/FTP server using a list of commonly used passwords (stored in `10k-most-common.txt`).

### Attack on SSH

We use the `paramiko` library to connect to the SSH server with the specified host IP address, username, and password. It reads in `10k-most-common.txt` and attempts to log in with each password in the list, using a separate thread for each login attempt.

The `multiprocessing.Pool` is used to manage a pool of worker processes, allowing multiple login attempts to be processed concurrently. For each password in the wordlist, the script submits a `ssh_connect` function call with the specified host IP address, username, and password to the pool using `pool.imap_unordered()`. The `imap_unordered` method returns an iterable that yields the result of each function call as soon as it becomes available, allowing the script to efficiently process the login attempts in parallel.

### Protection on SSH

TODO

### Attack on FTP

We use the `ftplib` library to connect to the FTP server with the specified host IP address, username, and password. It reads in a wordlist file of commonly used passwords and attempts to log in with each password in the list using a separate thread for each login attempt.

The `concurrent.futures.ThreadPoolExecutor` is used to manage a thread pool of up to 16 worker threads, allowing multiple login attempts to be processed concurrently.

For each password in the wordlist, the script submits a `ftp_login` function call with the specified host IP address, username and password to the thread pool using `executor.submit()`. If the `ftp_login` function is successful in logging in, the password is printed to the console and the program exits.

### Protection on FTP

TODO




## Reflected DDoS

### Attack

### Protection



## DNS/ARP cache poisoning

### Attack

### Protection



## SYN Flooding

### Attack

### Protection


## Authors (ULB matricule)
LUYCKX Marco 496283
BOUHNINE Ayoub 500048