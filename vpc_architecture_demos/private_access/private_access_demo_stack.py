#pylint: disable-all

from aws_cdk import (
    Stack,
    CfnTag,
    aws_ec2 as ec2,
    aws_iam as iam,
)

from constructs import Construct
from vpc_architecture_demos.custom import Subnet

class PrivateAccessDemoStack(Stack):
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
    
        # create the vpc
        self._vpc = ec2.Vpc(
            scope=self,
            id="Vpc",
            vpc_name="private_access_demo_vpc",
            ip_addresses=ec2.IpAddresses.cidr('10.16.0.0/16'),
            enable_dns_support=True,
            enable_dns_hostnames=True,
            subnet_configuration=[]
        )
        
        # create a public subnet
        self._public_subnet = Subnet(
            scope=self,
            id='PublicSubnet',
            cidr='10.16.96.0/20',
            vpc_id=self._vpc.vpc_id,
            az=self.availability_zones[0]
        )
        
        # create a private subnet
        self._private_subnet = Subnet(
            scope=self,
            id='PrivateSubnet',
            cidr='10.16.32.0/20',
            vpc_id=self._vpc.vpc_id,
            az=self.availability_zones[0]
        )
        
        # create the internet gateway
        self._internet_gateway = ec2.CfnInternetGateway(
            scope=self,
            id="IGW",
            tags=[CfnTag(
                key="Name",
                value="private_access_demo_igw"
            )]
        )
        
        # attach the internet gateway to the vpc
        self._internet_gateway_attach = ec2.CfnVPCGatewayAttachment(
            scope=self,
            id="IGWAttach",
            vpc_id=self._vpc.vpc_id,
            internet_gateway_id=self._internet_gateway.attr_internet_gateway_id
        )
        
        # create elastic IP for the nat gateway
        self._eip = ec2.CfnEIP(
            scope=self,
            id="EIP",
            tags=[CfnTag(
                key="Name",
                value="private_access_demo_eip"
            )]
        )
        
        # create the nat gateway for the public subnet
        self._nat_gateway = ec2.CfnNatGateway(
            scope=self,
            id="NatGateway",
            allocation_id=self._eip.attr_allocation_id,
            subnet_id=self._public_subnet.subnet_id,
            tags=[CfnTag(
                key="Name",
                value="private_access_demo_ngw"
            )]
        )
        
        # create the route table for the private subnet
        self._private_subnet_route_table = ec2.CfnRouteTable(
            scope=self,
            id="PrivateSubnetARouteTable",
            vpc_id=self._vpc.vpc_id,
            tags=[CfnTag(
                key="Name",
                value="private_access_demo_private_subnet_route_table"
            )]
        )
        
        # add a route to the private subnet's route table that targets 
        # the nat gateway 
        self._private_subnet_route_table_route = ec2.CfnRoute(
            scope=self,
            id="PrivateSubnetRouteTableRoute",
            route_table_id=self._private_subnet_route_table.attr_route_table_id,
            nat_gateway_id=self._nat_gateway.attr_nat_gateway_id,
            destination_cidr_block='0.0.0.0/0'
        )
        
        # associate the route table with the private subnet
        self._private_subnet_route_table_assoc = ec2.CfnSubnetRouteTableAssociation(
            scope=self,
            id="PrivateSubnetRTAssoc",
            subnet_id=self._private_subnet.subnet_id,
            route_table_id=self._private_subnet_route_table.attr_route_table_id
        )
        
        # create a route table for the public subnet
        self._public_subnet_route_table = ec2.CfnRouteTable(
            scope=self,
            id="PublicSubnetRouteTable",
            vpc_id=self._vpc.vpc_id,
            tags=[CfnTag(
                key="Name",
                value="private_access_demo_public_subnet_route_table"
            )]
        )
        
        # add a route for the public subnet's route table that targets
        # the igw
        self._public_subnet_route_table_route = ec2.CfnRoute(
            scope=self,
            id="PublicSubnetRouteTableRoute",
            route_table_id=self._public_subnet_route_table.attr_route_table_id,
            gateway_id=self._internet_gateway.attr_internet_gateway_id,
            destination_cidr_block='0.0.0.0/0'
        )
        self._public_subnet_route_table_route.add_dependency(target=self._internet_gateway_attach)
        
        # associate the route table with the public subnet
        self._public_subnet_route_table_assoc = ec2.CfnSubnetRouteTableAssociation(
            scope=self,
            id="PublicSubnetRTAssoc",
            subnet_id=self._public_subnet.subnet_id,
            route_table_id=self._public_subnet_route_table.attr_route_table_id
        )
        
        # create a iam role for the ec2
        self._ec2_iam_role = iam.Role(
            scope=self,
            id="EC2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            path="/",
            role_name="private-access-demo-ec2-iam-role",
            inline_policies={
                "root": iam.PolicyDocument(
                    statements=[
                        # broad policy just for demo purposes
                        iam.PolicyStatement(
                            actions=["*"],
                            resources=["*"],
                            effect=iam.Effect.ALLOW
                        )
                    ]
                )
            }
        )
        
        # create the instance profile for ec2
        self._ec2_instance_profile = iam.CfnInstanceProfile(
            scope=self,
            id="EC2InstanceProfile",
            path="/",
            roles=[self._ec2_iam_role.role_name]
        )
        
        # create the security group for ec2
        self._ec2_security_group = ec2.CfnSecurityGroup(
            scope=self,
            id="EC2SecurityGroup",
            group_description="private access demo security group",
            group_name="private-access-demo-ec2-sg",
            vpc_id=self._vpc.vpc_id,
            security_group_ingress=[
                ec2.CfnSecurityGroup.IngressProperty(
                    description="Allow SSH IPv4 IN",
                    ip_protocol="tcp",
                    from_port=22,
                    to_port=22,
                    cidr_ip="0.0.0.0/0"
                ) 
            ]
        )
        
        # create ec2 instance in for the private subnet
        self._ec2_instance = ec2.CfnInstance(
            scope=self,
            id="EC2",
            instance_type="t2.micro",
            image_id=ec2.MachineImage.latest_amazon_linux().get_image(self).image_id,
            subnet_id=self._private_subnet.subnet_id,
            iam_instance_profile=self._ec2_instance_profile.ref,
            security_group_ids=[self._ec2_security_group.attr_group_id],
            tags=[CfnTag(
                key="Name",
                value="private-access-demo-ec2"
            )]
        )