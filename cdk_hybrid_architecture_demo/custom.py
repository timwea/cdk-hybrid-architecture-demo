#pylint: disable-all
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

class Subnet(Construct):
    """
    A helper class to create a new subnet in a VPC and avoid code duplication.
    
    :param scope: The construct's parent.
    :param id: The construct ID.
    :param vpc_id: The ID of the VPC where the subnet should be created.
    :param cidr: The IPv4 network range for the subnet.
    :param az: The availability zone where the subnet should be created.
    :param kwargs: Additional keyword arguments to pass to the construct.
    """
    
    @property
    def subnet(self):
        """
        The underlying AWS CloudFormation subnet resource.
        """
        return self._subnet

    @property
    def subnet_id(self):
        """
        The ID of the subnet.
        """
        return self._subnet.subnet_id
    
    def __init__(self, scope: Construct, id: str, vpc_id: str, cidr: str, az: str, **kwargs):
        """
        Initializes a new instance of the Subnet class.
        """
        super().__init__(scope, id, **kwargs)
    
        self._subnet = ec2.Subnet(
            scope=self,
            id=id,
            cidr_block=cidr,
            vpc_id=vpc_id,
            availability_zone=az,
            map_public_ip_on_launch=False
        )
        # Unfortunately when using the CDK subnets create their own route tables
        # and associations by default, so we have to call this experimental method
        # for both resources to remove them  at transpilation time.
        self._subnet.node.try_remove_child("RouteTable")
        self._subnet.node.try_remove_child("RouteTableAssociation")