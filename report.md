# Network Attacks

## Mininet topology

![Topology](/img/topo.png)

## Requirements for the project

Assuming the `mininet-vm` is already launched, the following files need to be copied inside the VM before proceeding with the project :

`attacks` -> `/home/mininet/attacks`

`protections` -> `/home/mininet/protections`

`topo.py` -> `/home/mininet/LINFO2347/topo.py`

`requirements.txt` -> `/home/mininet/requirements.txt`

Once the files are copied, you need to use the command `pip3 install -r requirements.txt` to install the required dependencies.


## How to launch the topology

You can launch the topology with the following command (after copying our files in the VM) :

To launch the mininet topology, execute this command in the VM : `sudo -E python3 ~/LINFO2347/topo.py`

For all other sections in this report, the default state will be inside the mininet environnement.

## Firewall rules for basic enterprise network protection

To make the topology more secure, we need to make changes : 
1) Workstations can send a ping and initiate a connection towards any other host (other workstations, DMZ servers, internet).
2) DMZ servers cannot send any ping or initiate any connection. They can only respond to  incoming connections.
3) The Internet can send a ping or initiate a connection only towards DMZ servers. They cannot  send a ping or initiate connections towards workstations. 
 
To implement these changes, we set up several nft tables that you can find in the folder `protections/basic_network/`.

The first one is one the router r1.
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

The second one is one the router r2.
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

        # #### Bypass Command #### # to redirect the packets to the other router (R1) because R2 is the default gateway for DMZ servers
        iif "r2-eth12" ip saddr 10.12.0.0/24 ip daddr 10.1.0.0/24 accept

        # Allow Internet to only respond to incoming connections towards workstations
        iif "r2-eth0" ip saddr 10.2.0.0/24 ip daddr 10.1.0.0/24 ct state established,related accept

        # Allow Internet to send ping and initiate a connection towards DMZ servers
        # 10.12.0.10 accepts port 80
        iif "r2-eth0" ip saddr 10.2.0.0/24 ip daddr 10.12.0.10 tcp dport 80 ct state new,established,related accept

        # 10.12.0.20 accepts port 5353
        iif "r2-eth0" ip saddr 10.2.0.0/24 ip daddr 10.12.0.20 udp dport 5353 ct state new,established,related accept

        # 10.12.0.30 accepts port 123
        iif "r2-eth0" ip saddr 10.2.0.0/24 ip daddr 10.12.0.30 udp dport 123 ct state new,established,related accept

        # 10.12.0.40 accepts port 21
        iif "r2-eth0" ip saddr 10.2.0.0/24 ip daddr 10.12.0.40 tcp dport 21 ct state new,established,related accept
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

To save time deploying all of our scripts at once, we created a simple python script. To use it, simply run the command `source protections/commands_basic_protection.py` in Mininet. Here's what the script looks like :
```bash
py r1.cmd("sudo nft -f protections/basic_network_protection/firewall_r1.nft")
py r2.cmd("sudo nft -f protections/basic_network_protection/firewall_r2.nft")
py dns.cmd("sudo nft -f protections/basic_network_protection/firewall_DMZ.nft")
py http.cmd("sudo nft -f protections/basic_network_protection/firewall_DMZ.nft")
py ftp.cmd("sudo nft -f protections/basic_network_protection/firewall_DMZ.nft")
py ntp.cmd("sudo nft -f protections/basic_network_protection/firewall_DMZ.nft")
```
[comment]: <> (###########################################)
[comment]: <> (###########################################)
[comment]: <> (###########################################)


## How to launch attacks and protections

All scripts are written in Python. To run them, simply use the command `python3 <script name>.py`.

General comment regarding our protections against reflected DDoS and syn flood attacks :  we conducted a test both before and after implementing the protection. We measured the time it took to `curl` a defined host to determine if our protection was working effectively. While we did find that the protection was able to reduce the number of requests passing through, we also observed that the time taken by the `curl` command was still longer than usual.

Upon further investigation, we found that the cause of the delay was not due to our protection not working as intended, but rather the mininet topology being **overloaded** (dropping packets, etc). We confirmed this by using the `tcpdump` command on the correct interface to observe a reduction in the number of requests passing through.

[comment]: <> (###########################################)
[comment]: <> (###########################################)

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
To protect against TCP Network scan, we need to keep track of the number of syn packets sent by a host that enters to the company netwok then if the rate of these packets exceeds a certain threshold, the host concerned is blacklisted for 1 hour. // TODO

To implement these changes, we added these rules to the `firewall_r2.nft` file.

```
    set blacklist {
        type ipv4_addr
        flags timeout
        timeout 1h
    }
    ...
    chain forward {
        type filter hook forward priority 0; policy drop;

        # Check if the source IP is in the blacklist and drop the packet if it is
        ip saddr @blacklist drop

        # Add the source IP to the blacklist if it exceeds the connection rate limit
        tcp flags & (fin|syn|rst|psh|ack|urg) == syn limit rate over 5/second burst 10 packets add @blacklist { ip saddr timeout 1h }
        tcp flags & (fin|syn|rst|psh|ack|urg) == syn limit rate 5/second accept
    ...
    }
}
```

### Validation of the protection

After putting some protection in place and re-running the script, the attacker was not able to get a single port : 
```


```



[comment]: <> (###########################################)
[comment]: <> (###########################################)

## FTP brute-force attack
The attack scripts can be found in the `attacks/ftp_brute_force` directory.

Our script performs a threaded brute-force attack against an FTP server using a list of commonly used passwords (stored in `10k-most-common.txt`).

To launch the attack on `FTP` from `internet` (like a real attacker would do), follow these steps :

1) Open a new terminal window using the command `xterm internet`.
2) Move to the `attacks/ftp_brute_force/` directory.
3) Run the command `python3 main_ftp.py`.
4) Enjoy.


### Attack

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

To protect against `FTP` brute-force attacks, we need to keep track of the number of new, not-yet-established connection packets sent to the destination port `21` then if the rate of these packets exceeds a certain threshold, we drop them. // TODO

To implement these changes, we added these rules to the `firewall_r2.nft` file.
```
...
tcp dport 21 ct state new counter packets 1 bytes 60 jump block_ftp_bruteforce
...
chain block_ftp_bruteforce {
    ct state new tcp dport 21 limit rate over 10/minute burst 5 packets counter drop
}

```


### Validation of the protection
As shown earlier, brute-forcing the password required approximately 18 seconds. Now, with the applied modifications : 
```
Trying Login : calendar
Trying Login : cheeky
Trying Login : camel1
.
.
.
.
Trying Login : hugohugo
Trying Login : eighty
Trying Login : epson
Trying Login : evangeli
Trying Login : eeeee1
Trying Login : eyphed
Found Password : mininet for account : mininet
Time taken : 372.4294068813324

```


[comment]: <> (###########################################)
[comment]: <> (###########################################)

## Reflected DDoS
The attack scripts can be found in the `attacks/reflected_ddos` directory. By default, the attack launchs from `internet` to `http`. It benefits from the return values of `dns` and `ntp` sent to `http` (using a spoofed source address) which usually are bigger than the requests. 

To launch the DDoS attack from `internet` (like a real attacker would do), follow these steps :

1) Open a new terminal window using the command `xterm internet`.
2) Move to the `attacks/reflected_ddos/` directory.
3) Run the command `python3 main.py`.
4) Enjoy.

### Attack

We use the `scapy` library to craft DNS and NTP packets with the specified target IP address as the source IP, and send them to the DNS and NTP servers, respectively. The script performs a reflected DDoS attack by alternating between DNS and NTP requests which are submitted to separate threads for each attack attempt.

The `concurrent.futures.ThreadPoolExecutor` is used to manage a thread pool of up to 16 worker threads, allowing multiple DDoS attack attempts to be processed concurrently.

For each attack attempt, the script submits either a `dns_ddos` or `ntp_ddos` function call with the specified target IP address, DNS server or and NTP server (depending on the funtion called) to the thread pool using `executor.submit()`. If any of the attack attempts complete, the program checks the result, and if it does not return a `None` value, the script shuts down the executor, prints the time taken, and exits.

### Validation of the attack

In a separate host (`ws2` for example), we measured the time for getting a response from the `http` server

<ins>Before Reflected DDoS</ins>

```
real    0m0.017s
user    0m0.001s
sys     0m0.007s
```

<ins>After Reflected DDoS</ins>

```
real    0m0.574s
user    0m0.000s
sys     0m0.006s
```

### Protection

Initially, we attempted to implement `rate limiting` and `packet dropping` rules only on `r2`. But after a while, we thought that it was a better idea to solve this issue, by implementing some `load balancing`. We applied a rate limiter to the `r2` and closed all unnecessary ports in the architecture, while implementing packet dropping on the `DMZ-servers`.

For `r2`, we added these rules to the `firewall_r2.nft` file. The values we used for the rate limiter are not typical real-world values, but they were chosen to validate the effectiveness of our protection and easily demonstrate it to you.

```
    iif "r2-eth0" ip protocol udp ip daddr { 10.12.0.20, 10.12.0.30 } jump protect_services
    ...
    chain protect_services {
        udp dport 5353 limit rate 3/second burst 5 packets accept
        udp dport 123 limit rate 3/second burst 5 packets accept
    }
}
```
The first rule is added to the chain `forward`.

For `DMZ-servers`, we added these rules to the `firewall_DMZ.nft` file.

```
    ip daddr {10.2.0.0/24, 10.1.0.0/24, 10.12.0.1, 10.12.0.2} ct state established,related accept
    ...
    chain protect_services {
        ip saddr != { 10.2.0.0/24 } drop
    }
}
```
The first rule is added to the chain `output`.

### Validation of the protection

As we said earlier, we are going to use `tcpdump` on the interface `r2-eth12` of `r2` to validate our protection : 

```
11:41:55.293670 IP 10.12.0.10.domain > 10.12.0.20.mdns: 0+ Type225? test.com. (26)
11:41:55.433769 IP 10.12.0.10.62249 > 10.12.0.30.ntp: NTPv2, Reserved, length 8
11:41:55.627118 IP 10.12.0.10.domain > 10.12.0.20.mdns: 0+ Type225? domain.oof. (28)
11:41:55.665084 IP 10.12.0.10.37178 > 10.12.0.30.ntp: NTPv2, Reserved, length 8
11:41:55.961650 IP 10.12.0.10.domain > 10.12.0.20.mdns: 0+ Type225? example.be. (28)
11:41:55.971535 IP 10.12.0.10.3024 > 10.12.0.30.ntp: NTPv2, Reserved, length 8

11:41:56.293736 IP 10.12.0.10.domain > 10.12.0.20.mdns: 0+ Type225? www.example.com. (33)
11:41:56.429228 IP 10.12.0.10.46145 > 10.12.0.30.ntp: NTPv2, Reserved, length 8
11:41:56.628870 IP 10.12.0.10.domain > 10.12.0.20.mdns: 0+ Type225? example.com. (29)
11:41:56.632363 IP 10.12.0.10.48964 > 10.12.0.30.ntp: NTPv2, Reserved, length 8
11:41:56.960321 IP 10.12.0.10.domain > 10.12.0.20.mdns: 0+ Type225? a-very-long-domain-name.com. (45)

11:41:57.083972 IP 10.12.0.10.61670 > 10.12.0.30.ntp: NTPv2, Reserved, length 8
11:41:57.293529 IP 10.12.0.10.domain > 10.12.0.20.mdns: 0+ Type225? domain.oof. (28)
11:41:57.386182 IP 10.12.0.10.8808 > 10.12.0.30.ntp: NTPv2, Reserved, length 8
11:41:57.629414 IP 10.12.0.10.domain > 10.12.0.20.mdns: 0+ Type225? a-very-long-domain-name.com. (45)
11:41:57.687568 IP 10.12.0.10.12357 > 10.12.0.30.ntp: NTPv2, Reserved, length 8
11:41:57.960520 IP 10.12.0.10.domain > 10.12.0.20.mdns: 0+ Type225? i-hope-this-domain-name-is-not-used-for-reflection-attacks.oof. (80)
```

We can see that it validates our protection since, every seconds, only 3 packets of each types (DNS and NTP) are permitted to go through.

[comment]: <> (###########################################)
[comment]: <> (###########################################)


## DNS/ARP cache poisoning

The attack script for ARP and DNS can both be found in the `attacks/dns_arp_cache_poisoning` folder. The first script performs an ARP cache poisoning attack by sending forged ARP packets (with the ip of the router for example) to the target, therefore, the packets will be redirected to the attacker's computer. The second script intercepts DNS responses and modifies them to redirect specified domain names to a fake IP address. However, since this type of attack requires to be between the victim and the DNS server, it will be required to launch the ARP poisoning first.

To launch the `ARP`/`DNS` attack from `ws2` (to target `ws3`), follow these steps :

1) Open a new terminal window using the command `xterm ws2`.
2) Move to the `attacks/dns_arp_cache_poisoning/` directory.
3) Run the command `python3 main_arp.py`. For the DNS cache poisoning, we also need to run `python3 main_dns.py` (on another `xterm` terminal or in background)
4) When the victime (`ws3`) tries to perform requests, it will first goes through `ws2` before reaching its destination. For the DNS cache poisoning, the script will replace the domain names by fake IP addresses before sending them back to the victim 

[comment]: <> (###########################################)

### Attack on ARP
The `getmac()` function takes a `targetip` argument and creates an ARP request packet using the `Ether()` and `ARP()` functions with the destination MAC address set to the broadcast address (`ff:ff:ff:ff:ff:ff`) and the target IP address set to the `targetip` value. The `srp()` function is used to send the ARP request and wait for a response. If a response is received, the function returns the MAC address of the target IP address.

The `spoofarpcache()` function takes `targetip`, `targetmac` and `sourceip` arguments and creates a spoofed ARP response packet using the `ARP()` function with the operation code set to 2 (ARP reply), the target IP address set to the `targetip` value, the source IP address set to the `sourceip` value, and the destination MAC address set to the `targetmac` value.


### Attack on DNS

The script sets up a netfilter queue by adding a ruleset using nftables, binds the queue number to the `process_packet()` callback, and starts the queue. If the script is interrupted with a keyboard interrupt, it flushes the rulesets and exits.

The `process_packet()` is a callback function that is executed whenever a new packet is redirected to the netfilter queue. It first converts the netfilter queue packet to a Scapy packet. If the Scapy packet has a DNS Resource Record (DNS reply) layer, the function prints the packet summary before modification and attempts to modify the packet using the `modify_packet()` function. After modification, the packet summary is printed again, and the modified Scapy packet is set back as a netfilter queue packet. Finally, the packet is accepted.

The `modify_packet()` function takes a `packet` argument containing a DNS Resource Record. It extracts the domain name and checks if it exists in the `dns_hosts` dictionary. If the domain name is not in the dictionary, the function prints "no modification" and returns the original packet. If the domain name is in the dictionary, the function crafts a new DNS answer with the spoofed IP address specified in the `dns_hosts` dictionary. It updates the DNS answer count to 1 and removes the checksums and length fields of the IP and UDP layers, allowing Scapy to recalculate them automatically. The modified packet is then returned.


### Validation of the attack (ARP)

For the validation, we launch the script then after, we can see the packets going through `ws2` using the command `tcpdump`. 

Note that when running `tcpdump`, it will show a lot of `ARP` packets. These are the packets forged for cache poisoning. Therefore, we stopped the attack script after several seconds to easily find the packets going from `ws3` to the gateway through `ws2`.


Result on the `ws3` when performing a ping to `http`

```bash
root@mininet-vm:~# ping 10.12.0.10
PING 10.12.0.10 (10.12.0.10) 56(84) bytes of data.
From 10.1.0.2: icmp_seq=1 Redirect Host(New nexthop: 10.1.0.1)
64 bytes from 10.12.0.10: icmp_seq=1 ttl=61 time=2.36 ms
```

Result on the `ws2` when using `tcpdump`

```bash
root@mininet-vm:~# tcpdump
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on ws2-eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
09:52:46.513125 IP 10.1.0.3 > 10.12.0.10: ICMP echo request, id 2805, seq 11, length 64
09:52:46.513179 IP 10.1.0.2 > 10.1.0.3: ICMP redirect 10.12.0.10 to host 10.1.0.1, length 92

```

### Protection on ARP

TODO

### Validation of the protection

TODO

[comment]: <> (###########################################)

### Validation of the attack (DNS)

From `ws3`, open a `xterm` terminal, then type, for example, `dig @10.12.0.20 example.com -p 5353`

```
; <<>> DiG 9.16.1-Ubuntu <<>> @10.12.0.20 example.com -p 5353
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 53412
;; flags: qr aa rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4096
;; QUESTION SECTION:
;example.com.			IN	A

;; ANSWER SECTION:
example.com.		0	IN	A	10.12.0.10

;; Query time: 23 msec
;; SERVER: 10.12.0.20#5353(10.12.0.20)
;; WHEN: Tue May 02 15:07:30 PDT 2023
;; MSG SIZE  rcvd: 67
```

Here we can directly see that the response from the DNS has been modified and therefore the address of `example.com` is no longer `192.192.192.192`. We choose in the script the address `10.12.0.10`, we can chose any address we want. 


### Protection on DNS

TODO

### Validation of the protection

TODO


[comment]: <> (###########################################)
[comment]: <> (###########################################)


## SYN Flooding
The attack scripts can be found in the `attacks/syn_flood_ddos` directory.

We want to flood the target IP with a large number of packets. This type of attack is intended to overwhelm the target's ability to respond to legitimate network requests, causing it to become unavailable or slow to respond.

To launch the attack on `http` from `internet` (like a real attacker would do), follow these steps :

1) Open a new terminal window using the command `xterm internet`.
2) Move to the `attacks/syn_flood_ddos/` directory.
3) Run the command `python3 main.py`.
4) Enjoy.

### Attack

The script creates an IP packet using the `IP()` function with the destination IP address set to the `target_ip` value. The `TCP()` function is then used to create a TCP SYN packet with a random source port and the destination port set to the `target_port\ value. The `flags` parameter is set to "S" to indicate that this is a SYN packet.

Finally, the script creates a Raw packet with a payload of 1024 bytes, consisting of the letter "A" repeated 1024 times. The `packet` variable is then created by concatenating the IP, TCP and Raw packets together using the `/` operator.

### Validation of the attack

In a separate host (`ws2` for example), we measured the time for getting a response from the `http` server

<ins>Before SYN Flooding</ins>

```
real    0m0.023s
user    0m0.000s
sys     0m0.010s
```

<ins>After SYN Flooding</ins>

```
real    0m0.305s
user    0m0.000s
sys     0m0.008s
```


### Protection

To implement these changes, we added these rules to the `firewall_r2.nft` file.

The first rule filters incoming `TCP` packets with only the `SYN` flag set. The `SYN` flag is set in the initial packet of the `TCP` handshake process which is used to establish a connection between two hosts. The rule counts the number of packets that match these conditions using the `counter` keyword and, if a packet matches, it jumps to the `syn_flood_protection` chain for additional evaluation.

A chain block is defined for processing the `SYN `packets that match the rule. The `ct state new` keyword is used to match packets that are part of a new connection. The `limit rate 3/second burst 5 packets` keywords are used to limit the number of packets that are accepted to 3 per second with a burst of 5 packets. This means that up to 5 packets can be processed in a short burst without triggering the rule. However, if the incoming packet rate consistently exceeds 3 packets per second, the rule will be triggered and the specified action will be taken. We estimate that a legitimate number of connections per second is 3 with temporary spikes of 5 connections. The `counter` keyword is used to count the number of packets that are accepted and dropped by the rule. If the number of packets exceeds the limit, the `drop` keyword is used to drop the packet. Otherwise, the `accept` keyword is used to accept the packet.

Remark : When too many threads are launched, the VM is overloaded and the results are not necessarily reliable. In a real situation, the server would be more powerful and would be able to handle more requests.
We can see that the time is not constant and that it is not necessarily longer than before the attack. 

```
# SYN flood protection
tcp flags syn tcp flags == syn counter jump syn_flood_protection
...
chain syn_flood_protection {
    ct state new limit rate 3/second burst 5 packets counter accept
    counter drop
}
```

### Validation of the protection

After all the modifications with the modifications : 
```
real    0m0.089s
user    0m0.006s
sys     0m0.000s
```

[comment]: <> (###########################################)
[comment]: <> (###########################################)


## Authors (ULB matricule)
- LUYCKX Marco 496283
- BOUHNINE Ayoub 500048