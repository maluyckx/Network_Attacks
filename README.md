# Network Attacks

## Authors (ULB matricule)
- LUYCKX Marco 496283
- BOUHNINE Ayoub 500048

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

`sudo -E python3 ~/LINFO2347/topo.py`

For all other sections in this report, the default state will be inside the mininet environnement. 

**Remark** : After each protection (we made the assumption that you did the attack first without it), you will need to restart the entire topology. To do so, exit the topology with the command `exit` and then use the command `sudo mn -c` to clear the mininet cache and then relaunch the topology with the command above. We will repeat these steps after each protection so you do not need to remember them.

## Firewall rules for basic enterprise network protection

To make the topology more secure, we need to make changes : 
1) Workstations can send a ping and initiate a connection towards any other host (other workstations, DMZ servers, internet).
2) DMZ servers cannot send any ping or initiate any connection. They can only respond to  incoming connections.
3) The Internet can send a ping or initiate a connection only towards DMZ servers. They cannot  send a ping or initiate connections towards workstations. 
 
To implement these changes, we set up several nft tables that you can find in the folder `protections/basic_network/`.

The first one is on the router r1.
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

The second one is on the router r2.
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
        
        # Allow to redirect the packets to the other router (R1) because R2 is the default gateway for DMZ servers
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

And the last one needs to be deployed on every host of the DMZ (http, dns, ntp and ftp).
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

To save time deploying all of our scripts at once, we created a simple python script. To use it, simply run the command `source protections/basic_network/commands_basic_protection.py` in Mininet. Here's what the script looks like :
```bash
py r1.cmd("sudo nft -f protections/basic_network/firewall_r1.nft")
py r2.cmd("sudo nft -f protections/basic_network/firewall_r2.nft")
py dns.cmd("sudo nft -f protections/basic_network/firewall_DMZ.nft")
py http.cmd("sudo nft -f protections/basic_network/firewall_DMZ.nft")
py ftp.cmd("sudo nft -f protections/basic_network/firewall_DMZ.nft")
py ntp.cmd("sudo nft -f protections/basic_network/firewall_DMZ.nft")
```

We created similar scripts for the other protections. You can find them in the folder `protections/`.

[comment]: <> (###########################################)
[comment]: <> (###########################################)
[comment]: <> (###########################################)


## How to launch attacks and protections

All attack scripts are written in Python. To run them, simply use the command `python3 <script name>.py` on the correct host. More information will be provided in the following sections.

To launch the protections, you will need to use the `source protections/<attack name>/commands_<attack name>.py` command in Mininet. More information will be provided in the following sections.

**General comment regarding our protections against reflected DDoS and SYN flood attacks** :  we conducted a test both before and after implementing the protection. We measured the time it took to `curl` a defined host to determine if our protection was working effectively. While we did find that the protection was able to reduce the number of requests passing through, we also observed that the time taken by the `curl` command was still longer than usual.

Upon further investigation, we found that the cause of the delay was not due to our protection not working as intended, but rather the mininet topology being **overloaded** (dropping packets, etc). We confirmed this by using the `tcpdump` command on the correct interface to observe a reduction in the number of requests passing through.

**Remark** : For all the attacks, we hardcoded some information (IP addresses of the hosts, target, gateway, username, etc) in the script. If you want to test it on a different topology, you will need to change these information. 


[comment]: <> (###########################################)
[comment]: <> (###########################################)

## Network port scan
The attack script can be found in the `attacks/network_port_scan` folder. It performs a parallelized scan of every port from 1 to 65535.

To launch the attack on `DMZ_servers` from `internet` (like a real attacker would do), follow these steps :

1) Open a new terminal window using the command `xterm internet`.
2) Move to the `attacks/network_port_scan/` directory.
3) Run the command `python3 main.py`.
4) Enjoy.

### Attack
The attack script uses the socket library to create TCP sockets and attempts to connect to ports within the range of 1-65535. For each port, the script attempts to connect to the IP address and port combination using the `sock.connect_ex((host, port))` statement. If a connection is successful, the script prints the port number and the protocol name associated with the port.

To manage a thread pool of up to 100 worker threads. This allows multiple port scan requests to be processed concurrently.

Additionally, the script uses a timeout of 0.25 seconds for each port scan to prevent the script from hanging indefinitely if a port is unresponsive or blocked.

For the NTP server, we implemented a separate function that send a NTP request to the port 123. However, as discussed with François De Keersmaeker, the NTP port of the IP address `10.12.0.30` was unresponsive to our NTP request. Even when using the nmap tool (`nmap -sU -vv 10.12.0.30 -p123`) to verify that we did not make a mistake in our code, we were not able to get a response from the NTP server. Here is the output of the nmap command : 
```
root@mininet-vm:~# nmap -sU -vv 10.12.0.30 -p123
Starting Nmap 7.80 ( https://nmap.org ) at 2023-05-15 04:40 PDT
Initiating Ping Scan at 04:40
Scanning 10.12.0.30 [4 ports]
Completed Ping Scan at 04:40, 0.03s elapsed (1 total hosts)
Initiating Parallel DNS resolution of 1 host. at 04:40
Completed Parallel DNS resolution of 1 host. at 04:40, 13.02s elapsed
Initiating UDP Scan at 04:40
Scanning 10.12.0.30 [1 port]
Completed UDP Scan at 04:40, 0.04s elapsed (1 total ports)
Nmap scan report for 10.12.0.30
Host is up, received echo-reply ttl 63 (0.00055s latency).
Scanned at 2023-05-15 04:40:13 PDT for 13s

PORT    STATE  SERVICE REASON
123/udp closed ntp     port-unreach ttl 63
```

After asking help to François De Keersmaeker, he gave us some instructions : 
```
sudo apt-get purge openntpd
sudo apt-get update
sudo apt-get install ntpd
```

After that, he told us to remove one line from the `topo.py` but the version that we provided with the project is already up to date.

Here is the output of the `nmap` command after the change : 
```
root@mininet-vm:~# nmap -sU -vv 10.12.0.30 -p123
Starting Nmap 7.80 ( https://nmap.org ) at 2023-05-15 12:01 PDT
Initiating Ping Scan at 12:01
Scanning 10.12.0.30 [4 ports]
Completed Ping Scan at 12:01, 0.05s elapsed (1 total hosts)
Initiating Parallel DNS resolution of 1 host. at 12:01
Completed Parallel DNS resolution of 1 host. at 12:01, 13.04s elapsed
Initiating UDP Scan at 12:01
Scanning 10.12.0.30 [1 port]
Discovered open port 123/udp on 10.12.0.30
Completed UDP Scan at 12:01, 0.04s elapsed (1 total ports)
Nmap scan report for 10.12.0.30
Host is up, received reset ttl 63 (0.0014s latency).
Scanned at 2023-05-15 12:01:03 PDT for 13s

PORT    STATE SERVICE REASON
123/udp open  ntp     udp-response ttl 63

Read data files from: /usr/bin/../share/nmap
Nmap done: 1 IP address (1 host up) scanned in 13.29 seconds
           Raw packets sent: 5 (228B) | Rcvd: 2 (116B)
```


### Validation of the attack

As explained earlier, the scan displays all the ports that are on the topology except for the NTP port.
```
root@mininet-vm:~# python3 attacks/network_port_scan/main.py 
Scanning host: 10.12.0.10
Host : 10.12.0.10, Port : 80 is open
Time taken : 17.055407524108887
Scanning host: 10.12.0.20
Host : 10.12.0.20, Port : 5353 is open
Time taken : 48.71262764930725
Scanning host: 10.12.0.30
Host : 10.12.0.30, Port : 123 is open
Time taken : 52.727622270584106
Scanning host: 10.12.0.40
Host : 10.12.0.40, Port : 21 is open
Time taken : 55.34472131729126
```

### Protection

To launch the protection, use the following command in mininet : `source protections/network_port_scan/commands_network_port_scan.py`.

To protect against network port scan, we need to keep track of the number of SYN/UDP packets sent by a host that enters to the company netwok then if the rate of these packets exceeds a certain threshold, the concerned host is blacklisted for 1 hour.

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

        # Add the source IP to the blacklist if it exceeds the connection rate limit
        ip protocol udp limit rate over 5/second burst 1 packets add @blacklist { ip saddr timeout 1h }
```

To confirm that the network connectivity was functioning as expected, the `pingall` command was executed. The output matched the basic enterprise network protection, indicating that the network connectivity was not affected by the protection.

### Validation of the protection

After implementing the security measures, the attacker was not able to get a single port on the mininet topology since he was blacklisted instantly after scanning 50 ports. The command `nft list set inet filter blacklist` can be used to display the IP address, as shown in the following output : 
```bash
root@mininet-vm:~# nft list set inet filter blacklist
table inet filter {
        set blacklist {
                type ipv4_addr
                size 65535
                flags dynamic,timeout
                timeout 1h
                elements = { 10.2.0.2 expires 59m52s636ms }
        }
}
```

And also, after opening the terminal of `r2` using `xterm r2`, the output of the following command `tcpdump -i r2-eth12 && date` indicates that no further packets were received after the 50 packets and the `date` command confirms that no manipulation occurred. The output of the command is shown below :
```bash
root@mininet-vm:~# tcpdump -i r2-eth12 && date
.
.
.
.
08:42:43.549316 IP 10.12.0.10.echo > 10.2.0.2.51736: Flags [R.], seq 0, ack 2576174796, win 0, length 0
08:42:43.549797 IP 10.12.0.10.8 > 10.2.0.2.44356: Flags [R.], seq 0, ack 264977070, win 0, length 0
08:42:43.550304 IP 10.12.0.10.discard > 10.2.0.2.48632: Flags [R.], seq 0, ack 2658341580, win 0, length 0
08:42:43.550446 IP 10.2.0.2.44386 > 10.12.0.10.12: Flags [S], seq 1660961166, win 42340, options [mss 1460,sackOK,TS val 3671439964 ecr 0,nop,wscale 9], length 0
08:42:43.550596 IP 10.2.0.2.50108 > 10.12.0.10.systat: Flags [S], seq 2559427937, win 42340, options [mss 1460,sackOK,TS val 3671439964 ecr 0,nop,wscale 9], length 0
08:42:43.551320 IP 10.12.0.10.12 > 10.2.0.2.44386: Flags [R.], seq 0, ack 1660961167, win 0, length 0
08:42:43.551636 IP 10.12.0.10.systat > 10.2.0.2.50108: Flags [R.], seq 0, ack 2559427938, win 0, length 0
^C
22 packets captured
22 packets received by filter
0 packets dropped by kernel
Thu May 11 08:43:21 PDT 2023
```

**Remark** : As we said ealier, after this protection, you will need to restart the entire topology. To do so, exit the topology with the command `exit`, then use the command `sudo mn -c` to clear the mininet cache and finally relaunch the topology with the command `sudo -E python3 ~/LINFO2347/topo.py`. You are now ready to test the future attacks and protections !

[comment]: <> (###########################################)
[comment]: <> (###########################################)

## FTP brute-force attack
The attack scripts can be found in the `attacks/ftp_brute_force` directory.

Our script performs a threaded brute-force attack against an FTP server using a list of commonly used passwords (stored in `10k-most-common.txt`).

To launch the attack on `FTP` (in the `DMZ`) from `internet` (like a real attacker would do), follow these steps :

1) Open a new terminal window using the command `xterm internet`.
2) Move to the `attacks/ftp_brute_force/` directory.
3) Run the command `python3 main.py`.
4) Enjoy.


### Attack

We use the `ftplib` library to connect to the FTP server with the specified host IP address, username and password. It reads in a wordlist file of commonly used passwords that we found on the internet and attempts to log in with each password in the list using a separate thread for each login attempt.

**Remark** : We manually added the password `mininet` to this list so that the attack could be successful.

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

To launch the protection, use the following command in mininet : `source protections/ftp_brute_force/commands_ftp_brute_force.py`.

To protect against `FTP` brute-force attacks, we need to keep track of the number of new which means not-yet-established connection packets sent to the destination port `21`. If the rate of these packets exceeds a certain threshold, we drop them.

To implement these changes, we added these rules to the `firewall_r2.nft` file.
```
    ...
    chain forward {
        type filter hook forward priority 0; policy drop;

        tcp dport 21 ct state new counter packets 1 jump block_ftp_bruteforce
    ...
    }
    ...
    chain block_ftp_bruteforce {
        ct state new tcp dport 21 limit rate over 10/minute burst 5 packets counter drop
    }
```

To confirm that the network connectivity was functioning as expected, the `pingall` command was executed. The output matched the basic enterprise network protection, indicating that the network connectivity was not affected by the protection.

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

The time taken might be a bit surprising since we limit the traffic to 10 packets per minute. However, do not forget that the attack uses multiple threads so we cannot really predict the time taken. The important thing is that the attack is taking significantly longer now.

**Remark** : As we said ealier, after this protection, you will need to restart the entire topology. To do so, exit the topology with the command `exit`, then use the command `sudo mn -c` to clear the mininet cache and finally relaunch the topology with the command `sudo -E python3 ~/LINFO2347/topo.py`. You are now ready to test the future attacks and protections !

[comment]: <> (###########################################)
[comment]: <> (###########################################)

## Reflected DDoS
The attack scripts can be found in the `attacks/reflected_ddos` directory. By default, the attack is launched from `internet` to `http`.  

It uses the return values of `dns` and `ntp` servers to perform a reflected DDoS attack against the target IP address. The attacker sends DNS and NTP requests to the DNS and NTP servers, respectively, with the target IP address as the source IP address. The DNS and NTP servers will then send their responses, which usually are bigger than the requests, to the target IP address, causing a reflected DDoS attack.

To launch the DDoS attack from `internet` (like a real attacker would do), follow these steps :

1) Open a new terminal window using the command `xterm internet`.
2) Move to the `attacks/reflected_ddos/` directory.
3) Run the command `python3 main.py`.
4) Enjoy.

### Attack

We use the `scapy` library to craft DNS and NTP packets with the specified target IP address as the source IP. As explained earlier, the script performs a reflected DDoS attack by alternating between DNS and NTP requests which are submitted to separate threads for each attack attempt.

The `concurrent.futures.ThreadPoolExecutor` is used to manage a thread pool of up to 1000 worker threads, allowing multiple DDoS attack attempts to be processed concurrently.

For each attack attempt, the script submits either a `dns_ddos` or `ntp_ddos` function call with the specified target IP address and DNS server or NTP server (depending on the funtion called) to the thread pool using `executor.submit()`. If any of the attack attempts complete, the program checks the result and if it does not return a `None` value, the script shuts down the executor, prints the time taken and exits.

**Note** : for the DNS DDoS part, we used query type 255 `qtype=255` which is a request for all records that the DNS server has available.


### Validation of the attack

In a separate host (`ws2` for example), we measured the time for getting a response from the `http` server :

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

**Note** : the delay that the attack will produce is proportionate to the resources that you gave to the VM in Virtual Box. If you want the attack to be more effective, you can increase the number of `number_of_processes` in the `run_reflected_ddos` of the `attacks/reflected_ddos/main.py` file.

### Protection

To launch the protection, use the following command in mininet : `source protections/reflected_ddos/commands_reflected_ddos.py`.

Initially, we attempted to implement `rate limiting` and `packet dropping` rules only on `r2`. But after a while, we thought that it was a better idea to solve this issue, by implementing some `load balancing`. We applied a rate limiter to the `r2`, while implementing packet dropping on the `DMZ-servers`.

For `r2`, we added the following rules to the `firewall_r2.nft` file. The values we used for the rate limiter are not typical real-world values, but they were chosen to validate the effectiveness of our protection and easily demonstrate it to you.
The first rule is added to the chain `forward` :
```
    ...
    chain forward {
        type filter hook forward priority 0; policy drop;

        iif "r2-eth0" ip protocol udp ip daddr { 10.12.0.20, 10.12.0.30 } jump protect_services
    ...
    }
    ...
    chain protect_services {
        udp dport 5353 limit rate 3/second burst 5 packets accept
        udp dport 123 limit rate 3/second burst 5 packets accept
    }
}
```

For `DMZ-servers`, we added the following rules to the `firewall_DMZ.nft` file.
The first rule is added to the chain `input` :
```
    chain input {
        type filter hook input priority 0; policy accept;

        ip protocol udp ip daddr {10.12.0.20, 10.12.0.30} ip saddr {10.2.0.0/24} jump protect_services
    }
    ...
    chain protect_services {
        ip saddr != { 10.2.0.0/24 } drop
    }
}
```

To confirm that the network connectivity was functioning as expected, the `pingall` command was executed. The output matched the basic enterprise network protection, indicating that the network connectivity was not affected by the protection.

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

**Remark** : As we said ealier, after this protection, you will need to restart the entire topology. To do so, exit the topology with the command `exit`, then use the command `sudo mn -c` to clear the mininet cache and finally relaunch the topology with the command `sudo -E python3 ~/LINFO2347/topo.py`. You are now ready to test the future attacks and protections !

[comment]: <> (###########################################)
[comment]: <> (###########################################)


## BONUS : ARP cache poisoning

The attack script for ARP can be found in the `attacks/arp_cache_poisoning` folder. The script performs an ARP cache poisoning attack by sending forged ARP packets (with the ip of the router for example) to the target, therefore, the packets will be redirected to the attacker's computer instead of the router. 

To launch the `ARP` attack from `ws2` (to target `ws3`), follow these steps :

1) Open a new terminal window using the command `xterm ws2`.
2) Move to the `attacks/arp_cache_poisoning/` directory.
3) Run the command `python3 main.py`.
4) Once the victim (`ws3`) attempts to make a request, the request will first go through `ws2` before reaching its final destination.
5) Enjoy.
   
[comment]: <> (###########################################)

### Attack on ARP
The `get_mac()` function takes a `target_ip` argument and creates an ARP request packet using the `Ether()` and `ARP()` functions with the destination MAC address set to the broadcast address (`ff:ff:ff:ff:ff:ff`). The `srp()` function is used to send the ARP request and wait for a response. If a response is received, the function returns the MAC address of the target IP address.

The `spoof_arp_cache()` function takes `target_ip`, `target_mac` and `source_ip` arguments and creates a spoofed ARP response packet using the `ARP()` function with the operation code set to 2 (ARP reply), the target IP address set to the `target_ip` value, the source IP address set to the `source_ip` value and the destination MAC address set to the `target_mac` value.

The `craft_packet_target_ip()` function takes `host_ip` and `target_ip` parameters and constructs a packet with a spoofed source IP address to transmit to the intended machine. The IP function is used to set the destination IP address to `host_ip` and the source IP address to `target_ip`. The TCP function is used to create a TCP segment with the destination port set to `80`, the source port assigned to a random short value and the flags attribute set to `S` (which indicates the type SYN). The packet is assembled by combining the IP and TCP layers.

### Validation of the attack

For the validation, we will monitor the packets going through `ws2` using the command `tcpdump`. 

Note that when running `tcpdump`, it will show a lot of `ARP` packets which are the packets forged for cache poisoning. To easily find the packets that are sent from `ws3` to the gateway via `ws2`, we stopped the attack script after a few seconds to prevent further packet transmission, allowing for a thorough analysis.

Result on the `ws3` when performing a ping to `http` :
```
root@mininet-vm:~# ping 10.12.0.10
PING 10.12.0.10 (10.12.0.10) 56(84) bytes of data.
From 10.1.0.2: icmp_seq=1 Redirect Host(New nexthop: 10.1.0.1)
64 bytes from 10.12.0.10: icmp_seq=1 ttl=61 time=2.36 ms
```

Result on the `ws2` when using `tcpdump` :
```
root@mininet-vm:~# tcpdump
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on ws2-eth0, link-type EN10MB (Ethernet), capture size 262144 bytes
09:52:46.513125 IP 10.1.0.3 > 10.12.0.10: ICMP echo request, id 2805, seq 11, length 64
09:52:46.513179 IP 10.1.0.2 > 10.1.0.3: ICMP redirect 10.12.0.10 to host 10.1.0.1, length 92
```


### Protection on ARP

Before enabling the protection, we need to clear the corrupted ARP table of the victim (ws3) and more specifically, the corrupted address of the router. This can be done by using the following command : 
```
arp -d 10.1.0.1
arp -d 10.1.0.2
```

To launch the protection, use the following command in mininet : `source protections/arp_cache_poisoning/commands_arp_cache_poisoning.py`.

To be honest, implementing a good protection for this attack was really tough. We considered several solutions including : 
- Static table : This would be an ideal solution if we were in a private network where MAC and IP addresses were designed to be static. However, in practice, it is not feasible because the mininet topology randomizes the MAC addresses of each host.
- Rate-limiting and timeouts : While this solution would not **completely prevent** an attack, it would provide an early warning that the host is under attack and allow us for a response.

Our protection limits the rate of incoming ARP request for each source MAC address. It is done by using a meter `per-mac` that tracks the rate of incoming ARP requests per MAC address. The rate is limited to 1 ARP request per minute with a burst of 1. If the rate is exceeded, the packet is dropped.

A key point that allowed us to implement our solution is that the attacker's script needs to get the MAC address of the target using the function `get_mac`. When doing this, it burns his only attempt to get the MAC address. However, we are aware that this solution does not prevent completely the attack because an attacker who knows our protection table could :
- Use the `get_mac` function
- Wait for 1 minute
- Proceed with ARP cache poisoning

And he would successfully bypass the protection that we made.

Despite the limitations, this is the best solution that we could think of and that offers a reasonable level of protection.

For this attack, we need to create a new file named `firewall_wsx.nft` that is put on both workstations.

```
table arp filter {
    chain input {
        type filter hook input priority filter; policy accept;

        # Limit ARP requests per MAC address
        arp operation request meter per-mac { ether saddr limit rate 1/minute burst 1 packets } counter accept

        # Drop other ARP requests
        arp operation request counter drop
        }
}
```


### Validation of the protection

In our scenario, `ws2` attacks `ws3`.

After executing the attack, we can see that the ARP table of `ws3` is still empty. Therefore, whenever the attacker tries to send ARP packets, it will be blocked for 1 minute.

![ARP_cache_poisoning](/img/validation_arp/validation_arp_attack.png)

When trying to ping `ws3` from `ws2` before the 1 minute timeout, we can see that the packets are dropped.

![ARP_cache_poisoning](/img/validation_arp/validation_arp_ping.png)

After 1 minute, `ws2` is able to ping `ws3` again (the MAC address of `ws2` will be added to the arp table of `ws3`).

![ARP_cache_poisoning](/img/validation_arp/validation_arp_after_rate_limit.png)


To confirm that the network connectivity was functioning as expected, the `pingall` command was executed **after one minute**. The output matched the basic enterprise network protection, indicating that the network connectivity was not affected by the protection.


[comment]: <> (###########################################)
[comment]: <> (###########################################)

**Remark** : As we said ealier, after this protection, you will need to restart the entire topology. To do so, exit the topology with the command `exit`, then use the command `sudo mn -c` to clear the mininet cache and finally relaunch the topology with the command `sudo -E python3 ~/LINFO2347/topo.py`. You are now ready to test the future attacks and protections !

## BONUS : SYN Flooding
The attack scripts can be found in the `attacks/syn_flood` directory.

We want to flood the target IP with a large number of SYN packets. This type of attack is intended to overwhelm the target's ability to respond to legitimate network requests, causing it to become unavailable or slow to respond.

To launch the attack on `http` from `internet` (like a real attacker would do), follow these steps :

1) Open a new terminal window using the command `xterm internet`.
2) Move to the `attacks/syn_flood/` directory.
3) Run the command `python3 main.py`.
4) Enjoy.

### Attack

The script creates an IP packet using the `IP()` function with the destination IP address set to the `target_ip` value. The `TCP()` function is then used to create a TCP SYN packet with a random source port and the destination port set to the `target_port` value. The `flags` parameter is set to "S" to indicate that this is a SYN packet.

Finally, the script creates a `Raw` packet with a payload of 1024 bytes, consisting of the letter "A" repeated 1024 times. The `packet` variable is then created by concatenating the `IP`, `TCP` and `Raw` packets together.


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

**Note** : the delay that the attack will produce is proportionate to the resources that you gave to the VM in Virtual Box. If you want the attack to be more effective, you can increase the number of `number_of_processes` in the `run_syn_flood` of the `attacks/syn_flood/main.py` file.

### Protection

To launch the protection, use the following command in mininet : `source protections/syn_flood/commands_syn_flood.py`.

To implement these changes, we added some rules to the `firewall_r2.nft` file.

The first rule filters incoming `TCP` packets with only the `SYN` flag set. The `SYN` flag is set in the initial packet of the `TCP` handshake process which is used to establish a connection between two hosts. The rule counts the number of packets that match these conditions using the `counter` keyword and, if a packet matches, it jumps to the `syn_flood_protection` chain.

A chain block is defined for processing the `SYN` packets that match the rule. The `ct state new` keyword is used to match packets that are part of a new connection. The `limit rate 3/second burst 5 packets` keywords are used to limit the number of packets that are accepted to 3 per second with a burst of 5 packets. This means that up to 5 packets can be processed in a short burst without triggering the rule. However, if the incoming packet rate consistently exceeds 3 packets per second, the rule will be triggered and the specified action will be taken. We estimate that a legitimate number of connections per second is 3 with temporary spikes of 5 connections. The `counter` keyword is used to count the number of packets that are accepted and dropped by the rule. If the number of packets exceeds the limit, the `drop` keyword is used to drop the packet. Otherwise, the `accept` keyword is used to accept the packet.

**Remark** : When too many threads are launched, the VM is **overloaded** and the results are not necessarily reliable. In a real situation, the server would be more powerful and would be able to handle more requests.
We can see that the time is not constant and that it is not necessarily longer than before the attack. 
```
    ...
    chain forward {
        type filter hook forward priority 0; policy drop;

        # SYN flood protection
        tcp flags syn tcp flags == syn counter jump syn_flood_protection
    ...
    }
    chain syn_flood_protection {
        ct state new limit rate 3/second burst 5 packets counter accept
        counter drop
    }
```

To confirm that the network connectivity was functioning as expected, the `pingall` command was executed. The output matched the basic enterprise network protection, indicating that the network connectivity was not affected by the protection.

### Validation of the protection

To validate our protection, we measured the time for getting a response from the `http` server and we compared it with the time before the attack. We can see that it is pretty much the same.
```
real    0m0.023s
user    0m0.000s
sys     0m0.007s
``` 

[comment]: <> (###########################################)
[comment]: <> (###########################################)
