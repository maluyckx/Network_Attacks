# Network Attacks

## Mininet topology

![Topology](/img/topo.png)

## Requirements for the project

Before doing anything, you should do a `pip install -r requirements.txt`

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

To save time deploying all of our scripts at once, we created a simple Python script. To use it, simply run the command `source commands_basic_protection.py` in Mininet. Here's what the script looks like :
```bash
py r1.cmd("sudo nft -f protections/basic_network_protection/firewall_r1.nft")
py r2.cmd("sudo nft -f protections/basic_network_protection/firewall_r2.nft")
py dns.cmd("sudo nft -f protections/basic_network_protection/firewall_DMZ.nft")
py http.cmd("sudo nft -f protections/basic_network_protection/firewall_DMZ.nft")
py ftp.cmd("sudo nft -f protections/basic_network_protection/firewall_DMZ.nft")
py ntp.cmd("sudo nft -f protections/basic_network_protection/firewall_DMZ.nft")
```

## How to launch attacks and protections

All scripts are written in Python. To run them, simply use the command `python3 <script name>.py`.

## Network scans
The attack script can be found in the `attacks/network_scans` folder. It performs a parallelized scan of every port from 1 to 65535.

To launch the attack on `DMZ_servers` from `internet` (like a real attacker would do), follow these steps :

1) Open a new terminal window using the command `xterm internet`.
2) Move to the `attacks/network_scans/` directory.
3) Run the command `python3 main.py`.
4) Enjoy.

### Attack
The attack script uses the socket library to create TCP sockets and attempt to connect to ports within the range of 1-65535. For each port, the script attempts to connect to the IP address and port combination using the `s.connect((t_IP, port))` statement. If a connection is successful, the script prints the port number and the protocol name associated with the port using the `socket.getservbyport(port)` function call.

To manage a thread pool of up to 100 worker threads, the script uses the `concurrent.futures.ThreadPoolExecutor` function. This allows multiple port scan requests to be processed concurrently.

Additionally, the script uses a timeout of 0.25 seconds for each port scan to prevent the script from hanging indefinitely if a port is unresponsive or blocked.


### Validation of the attack
```
Starting scan on host : 192.168.56.101
21 is open. Possibly : ftp
22 is open. Possibly : ssh
80 is open. Possibly : http
5353 is open. Possibly : mdns
Time taken : 2.68119740486145
```

### Protection

TODO

### Validation of the protection

TODO



## SSH/FTP brute-force attack
The attack scripts can be found in the `attacks/ssh_ftp_brute_force` directory.

Our scripts performs a threaded brute-force attack against an SSH/FTP server using a list of commonly used passwords (stored in `10k-most-common.txt`).

To launch the attack on `SSH/FTP` from `internet` (like a real attacker would do), follow these steps :

1) Open a new terminal window using the command `xterm internet`.
2) Move to the `attacks/ssh_ftp_brute_force/` directory.
3) For SSH  : Run the command `python3 main_ssh.py`. <br />
    For FTP : Run the command `python3 main_ftp.py`.
4) Enjoy.


### Attack on SSH

We use the `paramiko` library to connect to the SSH server with the specified host IP address, username, and password. It reads in `10k-most-common.txt` and attempts to log in with each password in the list, using a separate thread for each login attempt.

The `multiprocessing.Pool` is used to manage a pool of worker processes, allowing multiple login attempts to be processed concurrently. For each password in the wordlist, the script submits a `ssh_connect` function call with the specified host IP address, username, and password to the pool using `pool.imap_unordered()`. The `imap_unordered` method returns an iterable that yields the result of each function call as soon as it becomes available, allowing the script to efficiently process the login attempts in parallel.

### Validation of the attack
```
Starting threaded SSH bruteforce on 192.168.56.101 with account : mininet
Incorrect Login : 123456
Incorrect Login : password
Incorrect Login : 1234
.
.
.
.
Incorrect Login : iloveyou
Incorrect Login : bailey
Incorrect Login : jackson
Incorrect Login : guitar
Found Password : mininet for account : mininet
Password Found : mininet
Time taken : 74.14346504211426
```

### Protection on SSH

TODO

### Validation of the protection

TODO

### Attack on FTP

We use the `ftplib` library to connect to the FTP server with the specified host IP address, username, and password. It reads in a wordlist file of commonly used passwords and attempts to log in with each password in the list using a separate thread for each login attempt.

The `concurrent.futures.ThreadPoolExecutor` is used to manage a thread pool of up to 16 worker threads, allowing multiple login attempts to be processed concurrently.

For each password in the wordlist, the script submits a `ftp_login` function call with the specified host IP address, username and password to the thread pool using `executor.submit()`. If the `ftp_login` function is successful in logging in, the password is printed to the console and the program exits.

### Validation of the attack
```
Trying Login : calendar
Trying Login : cheeky
Trying Login : camel1
.
.
.
.
Trying Login : hevnm4
Trying Login : hugohugo
Trying Login : eighty
Trying Login : epson
Trying Login : evangeli
Trying Login : eeeee1
Trying Login : eyphed
Found Password : mininet for account : mininet
Time taken : 18.703977584838867
```

### Protection on FTP

TODO


### Validation of the protection

TODO



## Reflected DDoS
The attack scripts can be found in the `attacks/reflected_ddos` directory.

To launch the DDoS attack from `internet` (like a real attacker would do), follow these steps :

1) Open a new terminal window using the command `xterm internet`.
2) Move to the `attacks/reflected_ddos/` directory.
3) Run the command `python3 main.py`.
4) Enjoy.

### Attack


### Validation of the attack


### Protection

TODO


### Validation of the protection

TODO


## DNS/ARP cache poisoning
The attack scripts can be found in the `attacks/dns_arp_cache_poisoning` directory.

To launch the attack on `DNS/ARP` from `ws2` (to target `ws3`), follow these steps :

1) Open a new terminal window using the command `xterm ws2`.
2) Move to the `attacks/ssh_ftp_brute_force/` directory.
3) For SSH  : Run the command `python3 main_arp.py`. <br />
    For FTP : Run the command `python3 main_dns.py`.
4) Enjoy.



### Attack on ARP
The `getmac()` function takes a `targetip` argument and creates an ARP request packet using the `Ether()` and `ARP()` functions with the destination MAC address set to the broadcast address (`ff:ff:ff:ff:ff:ff`) and the target IP address set to the `targetip` value. The `srp()` function is used to send the ARP request and wait for a response. If a response is received, the function returns the MAC address of the target IP address.

The `spoofarpcache()` function takes `targetip`, `targetmac` and `sourceip` arguments and creates a spoofed ARP response packet using the `ARP()` function with the operation code set to 2 (ARP reply), the target IP address set to the `targetip` value, the source IP address set to the `sourceip` value, and the destination MAC address set to the `targetmac` value.


### Validation of the attack
```

```

### Protection on ARP

TODO

### Validation of the protection

TODO

### Attack on DNS
### Validation of the attack
```

```

### Protection on DNS

TODO

### Validation of the protection

TODO



## SYN Flooding
The attack scripts can be found in the `attacks/syn_flood_ddos` directory.

We want to flood the target IP with a large number of packets. This type of attack is intended to overwhelm the target's ability to respond to legitimate network requests, causing it to become unavailable or slow to respond.

To launch the attack on `SSH/FTP` from `internet` (like a real attacker would do), follow these steps :

1) Open a new terminal window using the command `xterm internet`.
2) Move to the `attacks/syn_flood_ddos/` directory.
3) Run the command `python3 syn_flood.py`.
4) Enjoy.

### Attack

The script creates an IP packet using the `IP()` function with the destination IP address set to the `target_ip` value. The `TCP()` function is then used to create a TCP SYN packet with a random source port and the destination port set to the `target_port\ value. The `flags` parameter is set to "S" to indicate that this is a SYN packet.

Finally, the script creates a Raw packet with a payload of 1024 bytes, consisting of the letter "A" repeated 1024 times. The `packet` variable is then created by concatenating the IP, TCP and Raw packets together using the `/` operator.

### Validation of the attack
```

```

### Protection

TODO

### Validation of the protection

TODO





## Authors (ULB matricule)
- LUYCKX Marco 496283
- BOUHNINE Ayoub 500048