"""
This config file contains constants used for setting up a VPC and its associated subnets.
"""

ALL_IP_CIDR = "0.0.0.0/0"
"""
A CIDR block that represents all IP addresses.

:type: str
"""

AWS_VPC_CIDR = "10.16.0.0/16"
"""
The CIDR block for the VPC. This specifies the IP address range for the VPC.

:type: str
"""

AWS_PRIVATE_SUBNET_A_CIDR = "10.16.32.0/20"
"""
The CIDR block for the first private subnet in the VPC.

:type: str
"""

AWS_PRIVATE_SUBNET_B_CIDR = "10.16.96.0/20"
"""
The CIDR block for the second private subnet in the VPC.

:type: str
"""

ONPREM_CIDR = "192.168.8.0/21"
"""
The CIDR block for the simulated on-premises network.

:type: str
"""
ONPREM_PUBLIC_SUBNET_CIDR = "192.168.12.0/24"
ONPREM_PRIVATE_SUBNET_A_CIDR = "192.168.10.0/24"
ONPREM_PRIVATE_SUBNET_B_CIDR = "192.168.11.0/24"
