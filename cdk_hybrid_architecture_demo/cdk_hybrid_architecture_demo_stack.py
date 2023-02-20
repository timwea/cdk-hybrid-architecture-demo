#pylint: disable-all
from aws_cdk import (
    Stack,
    CfnTag,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct

import config

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

"""
This module defines an AWSPrivateNetwork construct, which creates a VPC and associated resources for a private AWS network.
"""

class AWSPrivateNetwork(Construct):
    """
    Creates a VPC and associated resources for a private AWS network.

    :param scope: The construct scope.
    :type scope: Construct
    :param id: The construct ID.
    :type id: str
    :param azs: A list of availability zones to use for the VPC subnets.
    :type azs: list
    """

    def __init__(self, scope: Construct, id: str, azs: list, **kwargs):
        """
        Initializes the AWSPrivateNetwork construct and creates the VPC and associated resources.

        :param scope: The construct scope.
        :type scope: Construct
        :param id: The construct ID.
        :type id: str
        :param azs: A list of availability zones to use for the VPC subnets.
        :type azs: list
        """
        
        self.vpc = ec2.Vpc(
            scope=self,
            id="AWSVpc",
            vpc_name="aws-private-network",
            ip_addresses=ec2.IpAddresses.cidr(config.VPC_CIDR),
            enable_dns_support=True,
            enable_dns_hostnames=True,
            subnet_configuration=[]
        )
        
        self.private_subnet_A = Subnet(
            scope=self,
            id="AWSPrivateSubnetA",
            cidr=config.PRIVATE_SUBNET_A_CIDR,
            vpc_id=self.vpc.vpc_id,
            az=azs[0]
        )
        
        self.private_subnet_B = Subnet(
            scope=self,
            id="AWSPrivateSubnetB",
            cidr=config.PRIVATE_SUBNET_B_CIDR,
            vpc_id=self.vpc.vpc_id,
            az=azs[1]
        )
        
        self.custom_route_table = ec2.CfnRouteTable(
            scope=self,
            id="AWSCustomRouteTable",
            vpc_id=self.vpc.vpc_id,
            tags=[CfnTag(
                key="Name",
                value="aws-private-network-custom_route_table"
            )]
        )
        
        self.transit_gateway = ec2.CfnTransitGateway(
            scope=self,
            id="AWSTransitGateway",
            description="Transit Gateway for the AWS private network",
            amazon_side_asn=64512,
            default_route_table_association="enable",
            dns_support="enable",
            vpn_ecmp_support="enable",
            tags=[CfnTag(
                key="Name",
                value="aws-private-network-transit-gateway"
            )]
        )
        
        self.transit_gateway_attach = ec2.CfnTransitGatewayAttachment(
            scope=self,
            id="AWSTGWAttachment",
            subnet_ids=[
                self.private_subnet_A.subnet_id,
                self.private_subnet_B.subnet_id
            ],
            transit_gateway_id=self.tgw.attr_id,
            vpc_id=self.vpc.vpc_id,
            tags=[CfnTag(
                key="Name",
                value="aws-private-network-transit-gateway-attach"
            )]
        )
        
        self.transit_gateway_default_route = ec2.CfnRoute(
            scope=self,
            id="AWSTGWDefaultRoute",
            transit_gateway_id=self.transit_gateway.attr_id,
            route_table_id=self.custom_route_table.attr_route_table_id,
            destination_cidr_block=config.ALL_IP_CIDR
        ).add_dependency(target=self.transit_gateway_attach)
        
        self.private_subnet_A_route_table_assoc = ec2.CfnSubnetRouteTableAssociation(
            scope=self,
            id="AWSPrivateSubnetARTAssoc",
            subnet_id=self.private_subnet_A.subnet_id,
            route_table_id=self.custom_route_table.attr_route_table_id
        )
        
        self.private_subnet_B_route_table_assoc = ec2.CfnSubnetRouteTableAssociation(
            scope=self,
            id="AWSPrivateSubnetBRTAssoc",
            subnet_id=self.private_subnet_B.subnet_id,
            route_table_id=self.custom_route_table.attr_route_table_id
        )
        
        self.ec2_security_group = ec2.SecurityGroup(
            scope=self,
            id="AWSEC2SecurityGroup",
            description="AWS private network default security group",
            security_group_name="aws-vpc-ec2-sg",
            vpc=self.vpc
        )
        
        self.ec2_security_group.add_ingress_rule(
            description="Allow SSH IPv4 IN",
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(22)
        )
        
        self.ec2_security_group.add_ingress_rule(
            description="Allow ALL from ONPREM Networks",
            peer=ec2.Peer.ipv4(config.ON_PREM_CIDR),
            connection=ec2.Port.all_traffic()
        )
        
        self.ec2_security_group_self_reference_rule = ec2.CfnSecurityGroupIngress(
            scope= self,
            id="AWSEC2SecurityGroupSelfReferenceRule",
            group_id=self.ec2_security_group.security_group_id,
            ip_protocol="-1",
            source_security_group_id=self.ec2_security_group.security_group_id
        )
        
        self.ec2_messages_interface_endpoint = ec2.InterfaceVpcEndpoint(
            scope=self,
            id="AWSEC2MessagesInterfaceEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.EC2_MESSAGES,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(
                subnets=[
                    self.private_subnet_A.subnet,
                    self.private_subnet_B.subnet
                ]
            ),
            security_groups=[self.ec2_security_group]
        )
        self.ssm_messages_interface_endpoint = ec2.InterfaceVpcEndpoint(
            scope=self,
            id="AWSSSMMessagesInterfaceEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.SSM_MESSAGES,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(
                subnets=[
                    self.private_subnet_A.subnet,
                    self.private_subnet_B.subnet
                ]
            ),
            security_groups=[self.ec2_security_group]
        )
        self.ssm_interface_endpoint = ec2.InterfaceVpcEndpoint(
            scope=self,
            id="AWSSSMInterfaceEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.SSM,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(
                subnets=[
                    self.private_subnet_A.subnet,
                    self.private_subnet_B.subnet
                ]
            ),
            security_groups=[self.ec2_security_group]
        )
        
        self.ec2_iam_role = iam.Role(
            scope=self,
            id="AWSEC2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            path="/",
            role_name="aws-private-network-ec2-iam-role",
            inline_policies={
                "root": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                "ssm:DescribeAssociation",
                                "ssm:GetDeployablePatchSnapshotForInstance",
                                "ssm:GetDocument",
                                "ssm:DescribeDocument",
                                "ssm:GetManifest",
                                "ssm:GetParameter",
                                "ssm:GetParameters",
                                "ssm:ListAssociations",
                                "ssm:ListInstanceAssociations",
                                "ssm:PutInventory",
                                "ssm:PutComplianceItems",
                                "ssm:PutConfigurePackageResult",
                                "ssm:UpdateAssociationStatus",
                                "ssm:UpdateInstanceAssociationStatus",
                                "ssm:UpdateInstanceInformation"
                            ],
                            resources=["*"],
                            effect=iam.Effect.ALLOW
                        ),
                        iam.PolicyStatement(
                            actions=[
                                "ssmmessages:CreateControlChannel",
                                "ssmmessages:CreateDataChannel",
                                "ssmmessages:OpenControlChannel",
                                "ssmmessages:OpenDataChannel",
                            ],
                            resources=["*"],
                            effect=iam.Effect.ALLOW
                        ),
                        iam.PolicyStatement(
                            actions=[
                                "ec2messages:AcknowledgeMessage",
                                "ec2messages:DeleteMessage",
                                "ec2messages:FailMessage",
                                "ec2messages:GetEndpoint",
                                "ec2messages:GetMessages",
                                "ec2messages:SendReply"
                            ],
                            resources=["*"],
                            effect=iam.Effect.ALLOW
                        ),
                        iam.PolicyStatement(
                            actions=["s3:*"],
                            resources=["*"],
                            effect=iam.Effect.ALLOW
                        ),
                        iam.PolicyStatement(
                            actions=["sns:*"],
                            resources=["*"],
                            effect=iam.Effect.ALLOW
                        )
                    ]
                )
            }
        )
        
        self.ec2_instance_profile = iam.CfnInstanceProfile(
            scope=self,
            id="AWSEC2InstanceProfile",
            path="/",
            roles=[self.ec2_iam_role.role_name]
        )
        
        self.ec2_instance_A = ec2.Instance(
            scope=self,
            id="AWSEC2A",
            instance_name="aws-private-network-ec2-a",
            instance_type=ec2.InstanceType.of(
                instance_class=ec2.InstanceClass.T2,
                instance_size=ec2.InstanceSize.MICRO
            ),
            machine_image=ec2.MachineImage.latest_amazon_linux(),
            role=self.ec2_instance_profile,
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=[self.private_subnet_A.subnet]),
            security_group=self.ec2_security_group
        )
        
        self.ec2_instance_B = ec2.Instance(
            scope=self,
            id="AWSEC2B",
            instance_name="aws-private-network-ec2-b",
            instance_type=ec2.InstanceType.of(
                instance_class=ec2.InstanceClass.T2,
                instance_size=ec2.InstanceSize.MICRO
            ),
            machine_image=ec2.MachineImage.latest_amazon_linux(),
            role=self.ec2_instance_profile,
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=[self.private_subnet_B.subnet]),
            security_group=self.ec2_security_group
        )

class CdkHybridArchitectureDemoStack(Stack):
    """
    A class that defines an AWS CloudFormation stack for the hybrid architecture demo.

    This stack creates an Amazon VPC with private subnets, transit gateway, security groups, and other resources.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        """
        Initializes a new instance of the `CdkHybridArchitectureDemoStack` class.

        :param scope: The parent construct of the stack.
        :param construct_id: A unique identifier for the stack.
        :param kwargs: Additional keyword arguments to pass to the parent constructor.
        """
        super().__init__(scope, construct_id, **kwargs)
        
        aws_private_network = AWSPrivateNetwork(
            scope=self,
            id="AWSPrivateNetwork",
            azs=self.availability_zones
        )
        
