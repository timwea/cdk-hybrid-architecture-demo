#pylint: disable-all

from aws_cdk import (
    CfnTag,
    aws_ec2 as ec2,
    aws_iam as iam,
)

from constructs import Construct

from vpc_architecture_demos.custom import Subnet
from vpc_architecture_demos.site_to_site_vpn import cidr_config

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
        super().__init__(scope, id, **kwargs)
        
        self._vpc = ec2.Vpc(
            scope=self,
            id="AWSVpc",
            vpc_name="aws-private-network",
            ip_addresses=ec2.IpAddresses.cidr(cidr_config.AWS_VPC_CIDR),
            enable_dns_support=True,
            enable_dns_hostnames=True,
            subnet_configuration=[]
        )
        
        self._private_subnet_A = Subnet(
            scope=self,
            id="AWSPrivateSubnetA",
            cidr=cidr_config.AWS_PRIVATE_SUBNET_A_CIDR,
            vpc_id=self._vpc.vpc_id,
            az=azs[0]
        )
        
        self._private_subnet_B = Subnet(
            scope=self,
            id="AWSPrivateSubnetB",
            cidr=cidr_config.AWS_PRIVATE_SUBNET_B_CIDR,
            vpc_id=self._vpc.vpc_id,
            az=azs[1]
        )
        
        self._custom_route_table = ec2.CfnRouteTable(
            scope=self,
            id="AWSCustomRouteTable",
            vpc_id=self._vpc.vpc_id,
            tags=[CfnTag(
                key="Name",
                value="aws-private-network-custom_route_table"
            )]
        )
        
        self._transit_gateway = ec2.CfnTransitGateway(
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
        
        self._transit_gateway_attach = ec2.CfnTransitGatewayAttachment(
            scope=self,
            id="AWSTGWAttachment",
            subnet_ids=[
                self._private_subnet_A.subnet_id,
                self._private_subnet_B.subnet_id
            ],
            transit_gateway_id=self._transit_gateway.attr_id,
            vpc_id=self._vpc.vpc_id,
            tags=[CfnTag(
                key="Name",
                value="aws-private-network-transit-gateway-attach"
            )]
        )
        
        self._transit_gateway_default_route = ec2.CfnRoute(
            scope=self,
            id="AWSTGWDefaultRoute",
            transit_gateway_id=self._transit_gateway.attr_id,
            route_table_id=self._custom_route_table.attr_route_table_id,
            destination_cidr_block=cidr_config.ALL_IP_CIDR
        )
        self._transit_gateway_default_route.add_dependency(target=self._transit_gateway_attach)
        
        self._private_subnet_A_route_table_assoc = ec2.CfnSubnetRouteTableAssociation(
            scope=self,
            id="AWSPrivateSubnetARTAssoc",
            subnet_id=self._private_subnet_A.subnet_id,
            route_table_id=self._custom_route_table.attr_route_table_id
        )
        
        self._private_subnet_B_route_table_assoc = ec2.CfnSubnetRouteTableAssociation(
            scope=self,
            id="AWSPrivateSubnetBRTAssoc",
            subnet_id=self._private_subnet_B.subnet_id,
            route_table_id=self._custom_route_table.attr_route_table_id
        )
        
        self._ec2_security_group = ec2.CfnSecurityGroup(
            scope=self,
            id="AWSEC2SecurityGroup",
            group_description="AWS private network default security group",
            group_name="aws-vpc-ec2-sg",
            vpc_id=self._vpc.vpc_id,
            security_group_ingress=[
                ec2.CfnSecurityGroup.IngressProperty(
                    description="Allow SSH IPv4 IN",
                    ip_protocol="tcp",
                    from_port=22,
                    to_port=22,
                    cidr_ip=cidr_config.ALL_IP_CIDR
                ),
                ec2.CfnSecurityGroup.IngressProperty(
                    description="Allow ALL from ONPREM Networks",
                    ip_protocol="-1",
                    cidr_ip=cidr_config.ONPREM_CIDR
                ),   
            ]
        )
        self._ec2_security_group_self_reference_rule = ec2.CfnSecurityGroupIngress(
            scope= self,
            id="AWSEC2SecurityGroupSelfReferenceRule",
            group_id=self._ec2_security_group.attr_group_id,
            ip_protocol="-1",
            source_security_group_id=self._ec2_security_group.attr_group_id
        )
    
        self._s3_interface_endpoint = ec2.CfnVPCEndpoint(
            scope=self,
            id="AWSEC2MessagesInterfaceEndpoint",
            vpc_id=self._vpc.vpc_id,
            service_name="com.amazonaws.us-east-1.ec2messages",
            private_dns_enabled=True,
            vpc_endpoint_type="Interface",
            subnet_ids=[self._private_subnet_A.subnet_id,self._private_subnet_B.subnet_id],
            security_group_ids=[self._ec2_security_group.attr_group_id]
        )

        self._s3_interface_endpoint = ec2.CfnVPCEndpoint(
            scope=self,
            id="AWSSSMMessagesInterfaceEndpoint",
            vpc_id=self._vpc.vpc_id,
            service_name="com.amazonaws.us-east-1.ssmmessages",
            private_dns_enabled=True,
            vpc_endpoint_type="Interface",
            subnet_ids=[self._private_subnet_A.subnet_id,self._private_subnet_B.subnet_id],
            security_group_ids=[self._ec2_security_group.attr_group_id]
        )
        
        self._s3_interface_endpoint = ec2.CfnVPCEndpoint(
            scope=self,
            id="AWSSSMInterfaceEndpoint",
            vpc_id=self._vpc.vpc_id,
            service_name="com.amazonaws.us-east-1.ssm",
            private_dns_enabled=True,
            vpc_endpoint_type="Interface",
            subnet_ids=[self._private_subnet_A.subnet_id,self._private_subnet_B.subnet_id],
            security_group_ids=[self._ec2_security_group.attr_group_id]
        )
        
        self._ec2_iam_role = iam.Role(
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
        
        self._ec2_instance_profile = iam.CfnInstanceProfile(
            scope=self,
            id="AWSEC2InstanceProfile",
            path="/",
            roles=[self._ec2_iam_role.role_name]
        )
        
        self._ec2_instance_A = ec2.CfnInstance(
            scope=self,
            id="AWSEC2A",
            instance_type="t2.micro",
            image_id=ec2.MachineImage.latest_amazon_linux().get_image(self).image_id,
            iam_instance_profile=self._ec2_instance_profile.ref,
            subnet_id=self._private_subnet_A.subnet_id,
            security_group_ids=[self._ec2_security_group.attr_group_id],
            tags=[CfnTag(
                key="Name",
                value="aws-private-network-ec2-a"
            )]
        )
        
        self._ec2_instance_B = ec2.CfnInstance(
            scope=self,
            id="AWSEC2B",
            instance_type="t2.micro",
            image_id=ec2.MachineImage.latest_amazon_linux().get_image(self).image_id,
            iam_instance_profile=self._ec2_instance_profile.ref,
            subnet_id=self._private_subnet_B.subnet_id,
            security_group_ids=[self._ec2_security_group.attr_group_id],
            tags=[CfnTag(
                key="Name",
                value="aws-private-network-ec2-b"
            )]
        )