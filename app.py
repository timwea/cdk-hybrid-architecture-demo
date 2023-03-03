#pylint: disable-all
#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import Environment

from vpc_architecture_demos.site_to_site_vpn.site_to_site_vpn_stack import SiteToSiteVpnStack
from vpc_architecture_demos.private_access.private_access_demo_stack import PrivateAccessDemoStack

app = cdk.App()

# SiteToSiteVpnStack(
#     scope=app, 
#     construct_id="SiteToSiteVpnStack",
#     stack_name="site-to-site-vpn-stack",
#     env=Environment(region="us-east-1")
# )

PrivateAccessDemoStack(
    scope=app,
    construct_id='NatGatewayStack',
    stack_name="vpc-architecture-demos-nat-gateway",
    env=Environment(region='us-east-1')
)

app.synth()
