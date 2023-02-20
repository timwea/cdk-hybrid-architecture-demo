"""
This config file contains constants used for setting up a VPC and its associated subnets.
"""

ALL_IP_CIDR = "0.0.0.0/0"
"""
A CIDR block that represents all IP addresses.

:type: str
"""

VPC_CIDR = "10.16.0.0/16"
"""
The CIDR block for the VPC. This specifies the IP address range for the VPC.

:type: str
"""

PRIVATE_SUBNET_A_CIDR = "10.16.32.0/20"
"""
The CIDR block for the first private subnet in the VPC.

:type: str
"""

PRIVATE_SUBNET_B_CIDR = "10.16.96.0/20"
"""
The CIDR block for the second private subnet in the VPC.

:type: str
"""

ON_PREM_CIDR = "192.168.8.0/21"
"""
The CIDR block for the simulated on-premises network.

:type: str
"""
