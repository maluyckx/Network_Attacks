py r1.cmd("sudo nft -f protections/ftp_brute_force/firewall_r1.nft")
py r2.cmd("sudo nft -f protections/ftp_brute_force/firewall_r2.nft")
py dns.cmd("sudo nft -f protections/ftp_brute_force/firewall_DMZ.nft")
py http.cmd("sudo nft -f protections/ftp_brute_force/firewall_DMZ.nft")
py ftp.cmd("sudo nft -f protections/ftp_brute_force/firewall_DMZ.nft")
py ntp.cmd("sudo nft -f protections/ftp_brute_force/firewall_DMZ.nft")