py r1.cmd("sudo nft -f protections/basic_network_protection/firewall_r1.nft")
py r2.cmd("sudo nft -f protections/basic_network_protection/firewall_r2.nft")
py dns.cmd("sudo nft -f protections/basic_network_protection/firewall_DMZ.nft")
py http.cmd("sudo nft -f protections/basic_network_protection/firewall_DMZ.nft")
py ftp.cmd("sudo nft -f protections/basic_network_protection/firewall_DMZ.nft")
py ntp.cmd("sudo nft -f protections/basic_network_protection/firewall_DMZ.nft")