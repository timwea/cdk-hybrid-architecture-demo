#pylint: disable-all
from aws_cdk import Stack
    
from constructs import Construct

from cdk_hybrid_architecture_demo.aws_network import AWSPrivateNetwork
from cdk_hybrid_architecture_demo.onprem_network import OnPremNetwork

class CdkHybridArchitectureDemoStack(Stack):

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
        
