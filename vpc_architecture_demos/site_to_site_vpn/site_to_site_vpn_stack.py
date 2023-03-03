#pylint: disable-all
from aws_cdk import Stack
    
from constructs import Construct

from vpc_architecture_demos.site_to_site_vpn.aws_network import AWSPrivateNetwork
from vpc_architecture_demos.site_to_site_vpn.onprem_network import OnPremNetwork

class SiteToSiteVpnStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        
        aws_private_network = AWSPrivateNetwork(
            scope=self,
            id="AWSPrivateNetwork",
            azs=self.availability_zones
        )
        
        onprem_network = OnPremNetwork(
            scope=self,
            id="OnPremNetwork",
            azs=self.availability_zones
        )
        
