#pylint: disable-all
from aws_cdk import (
    CfnTag,
    CfnOutput,
    aws_ec2 as ec2,
    aws_iam as iam,
    
)
from constructs import Construct

from cdk_hybrid_architecture_demo.custom import Subnet 
from cdk_hybrid_architecture_demo import config

class OnPremNetwork(Construct):
    
    def __init__(self, scope: Construct, id: str, azs: list, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        self.vpc = ec2.Vpc(
            scope=self,
            id="OnPremVpc",
            vpc_name="onprem-network",
            ip_addresses=ec2.IpAddresses.cidr(config.ONPREM_CIDR),
            enable_dns_support=True,
            enable_dns_hostnames=True,
            subnet_configuration=[]
        )
        
        self.public_subnet = Subnet(
            scope=self,
            id="OnPremPublicSubnet",
            cidr=config.ONPREM_PUBLIC_SUBNET_CIDR,
            vpc_id=self.vpc.vpc_id,
            az=azs[0]
        )
        
        self.private_subnet_A = Subnet(
            scope=self,
            id="OnPremPrivateSubnetA",
            cidr=config.ONPREM_PRIVATE_SUBNET_A_CIDR,
            vpc_id=self.vpc.vpc_id,
            az=azs[0]
        )
        
        self.private_subnet_B = Subnet(
            scope=self,
            id="OnPremPrivateSubnetB",
            cidr=config.ONPREM_PRIVATE_SUBNET_B_CIDR,
            vpc_id=self.vpc.vpc_id,
            az=azs[0]
        )
        
        self.public_subnet_route_table = ec2.CfnRouteTable(
            scope=self,
            id="OnPremPublicSubnetRouteTable",
            vpc_id=self.vpc.vpc_id,
            tags=[CfnTag(
                key="Name",
                value="onprem-network-public_subnet_route_table"
            )]
        )
        
        self.private_subnet_A_route_table = ec2.CfnRouteTable(
            scope=self,
            id="OnPremPrivateSubnetARouteTable",
            vpc_id=self.vpc.vpc_id,
            tags=[CfnTag(
                key="Name",
                value="onprem-network-private_subnet_A_route_table"
            )]
        )
        
        self.private_subnet_B_route_table = ec2.CfnRouteTable(
            scope=self,
            id="OnPremPrivateSubnetBRouteTable",
            vpc_id=self.vpc.vpc_id,
            tags=[CfnTag(
                key="Name",
                value="onprem-network-private_subnet_B_route_table"
            )]
        )
        
        self.ec2_security_group = ec2.SecurityGroup(
            scope=self,
            id="OnPremEC2SecurityGroup",
            description="On-Prem network default security group",
            security_group_name="onprem-network-ec2-sg",
            vpc=self.vpc
        )
        self.ec2_security_group.add_ingress_rule(
            description="Allow All from AWS Private Network",
            peer=ec2.Peer.ipv4(config.AWS_VPC_CIDR),
            connection=ec2.Port.all_traffic()
        )
        
        self.ec2_security_group_self_reference_rule = ec2.CfnSecurityGroupIngress(
            scope= self,
            id="OnPremiseEC2SecurityGroupSelfReferenceRule",
            group_id=self.ec2_security_group.security_group_id,
            ip_protocol="-1",
            source_security_group_id=self.ec2_security_group.security_group_id
        ) 
        
        self.router_A_private_network_interface = ec2.CfnNetworkInterface(
            scope=self,
            id="OnPremRouterAPrivateNetworkInterface",
            subnet_id=self.private_subnet_A.subnet_id,
            description="OnPrem RouterA Private Interface",
            source_dest_check=False,
            group_set=[self.ec2_security_group.security_group_id],
            tags=[CfnTag(
                key="Name",
                value="onprem-routerA-private-network-interface"
            )]
        )
        
        self.router_A_public_network_interface = ec2.CfnNetworkInterface(
            scope=self,
            id="OnPremRouterAPublicNetworkInterface",
            subnet_id=self.public_subnet.subnet_id,
            description="OnPrem RouterA Public Interface",
            source_dest_check=False,
            group_set=[self.ec2_security_group.security_group_id],
            tags=[CfnTag(
                key="Name",
                value="onprem-routerA-public-network-interface"
            )]
        )
        
        self.router_B_private_network_interface = ec2.CfnNetworkInterface(
            scope=self,
            id="OnPremRouterBPrivateNetworkInterface",
            subnet_id=self.private_subnet_B.subnet_id,
            description="OnPrem RouterB Private Interface",
            source_dest_check=False,
            group_set=[self.ec2_security_group.security_group_id],
            tags=[CfnTag(
                key="Name",
                value="onprem-routerB-private-network-interface"
            )]
        )
        
        self.router_B_public_network_interface = ec2.CfnNetworkInterface(
            scope=self,
            id="OnPremRouterBPublicNetworkInterface",
            subnet_id=self.public_subnet.subnet_id,
            description="OnPrem RouterB Public Interface",
            source_dest_check=False,
            group_set=[self.ec2_security_group.security_group_id],
            tags=[CfnTag(
                key="Name",
                value="onprem-routerB-public-network-interface"
            )]
        )
        
        self.internet_gateway = ec2.CfnInternetGateway(
            scope=self,
            id="OnPremIGW",
            tags=[CfnTag(
                key="Name",
                value="onprem-network-igw"
            )]
        )
        
        self.internet_gateway_attach = ec2.CfnVPCGatewayAttachment(
            scope=self,
            id="OnPremIGWAttach",
            vpc_id=self.vpc.vpc_id,
            internet_gateway_id=self.internet_gateway.attr_internet_gateway_id
        )
        
        self.public_subnet_route_table_default_route = ec2.CfnRoute(
            scope=self,
            id="OnPremPublicSubnetRouteTableDefaultRoute",
            route_table_id=self.public_subnet_route_table.attr_route_table_id,
            gateway_id=self.internet_gateway.attr_internet_gateway_id,
            destination_cidr_block=config.ALL_IP_CIDR
        ).add_depends_on(target=self.internet_gateway_attach)
        
        self.private_subnet_A_route_table_route = ec2.CfnRoute(
            scope=self,
            id="OnPremPrivateSubnetARouteTableRoute",
            route_table_id=self.private_subnet_A_route_table.attr_route_table_id,
            network_interface_id=self.router_A_private_network_interface.attr_id,
            destination_cidr_block=config.AWS_VPC_CIDR
        )
        
        self.private_subnet_B_route_table_route = ec2.CfnRoute(
            scope=self,
            id="OnPremPrivateSubnetBRouteTableRoute",
            route_table_id=self.private_subnet_B_route_table.attr_route_table_id,
            network_interface_id=self.router_B_private_network_interface.attr_id,
            destination_cidr_block=config.AWS_VPC_CIDR
        )
        
        self.public_subnet_route_table_assoc = ec2.CfnSubnetRouteTableAssociation(
            scope=self,
            id="OnPremPublicSubnetRTAssoc",
            subnet_id=self.public_subnet.subnet_id,
            route_table_id=self.public_subnet_route_table.attr_route_table_id
        )
        
        self.private_subnet_A_route_table_assoc = ec2.CfnSubnetRouteTableAssociation(
            scope=self,
            id="OnPremPrivateSubnetARTAssoc",
            subnet_id=self.private_subnet_A.subnet_id,
            route_table_id=self.private_subnet_A_route_table.attr_route_table_id
        )
        
        self.private_subnet_B_route_table_assoc = ec2.CfnSubnetRouteTableAssociation(
            scope=self,
            id="OnPremPrivateSubnetBRTAssoc",
            subnet_id=self.private_subnet_B.subnet_id,
            route_table_id=self.private_subnet_B_route_table.attr_route_table_id
        )
        
        self.router_A_elastic_ip = ec2.CfnEIP(scope=self, id="OnPremRouterAElasticIP")
        self.router_A_elastic_ip.add_dependency(target=self.internet_gateway_attach)
        self.router_A_elastic_ip_assoc = ec2.CfnEIPAssociation(
            scope=self,
            id="OnPremRouterAElasticIPAssoc",
            allocation_id=self.router_A_elastic_ip.attr_allocation_id,
            network_interface_id=self.router_A_public_network_interface.attr_id
        )
        
        self.router_B_elastic_ip = ec2.CfnEIP(scope=self, id="OnPremRouterBElasticIP")
        self.router_B_elastic_ip.add_dependency(target=self.internet_gateway_attach)
        self.router_B_elastic_ip_assoc = ec2.CfnEIPAssociation(
            scope=self,
            id="OnPremRouterBElasticIPAssoc",
            allocation_id=self.router_B_elastic_ip.attr_allocation_id,
            network_interface_id=self.router_B_public_network_interface.attr_id
        )
        
        self.ec2_messages_interface_endpoint = ec2.InterfaceVpcEndpoint(
            scope=self,
            id="OnPremEC2MessagesInterfaceEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.EC2_MESSAGES,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(subnets=[self.public_subnet]),
            security_groups=[self.ec2_security_group]
        )
        self.ssm_messages_interface_endpoint = ec2.InterfaceVpcEndpoint(
            scope=self,
            id="OnPremSSMMessagesInterfaceEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.SSM_MESSAGES,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(subnets=[self.public_subnet]),
            security_groups=[self.ec2_security_group]
        )
        self.ssm_interface_endpoint = ec2.InterfaceVpcEndpoint(
            scope=self,
            id="OnPremSSMInterfaceEndpoint",
            vpc=self.vpc,
            service=ec2.InterfaceVpcEndpointAwsService.SSM,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(subnets=[self.public_subnet]),
            security_groups=[self.ec2_security_group]
        )
        
        self.s3_interface_endpoint = ec2.CfnVPCEndpoint(
            scope=self,
            id="OnPremS3InterfaceEndpoint",
            vpc_id=self.vpc.vpc_id,
            service_name="com.amazonaws.us-east-1.s3",
            private_dns_enabled=False,
            route_table_ids=[
                self.public_subnet_route_table.attr_route_table_id,
                self.private_subnet_A_route_table.attr_route_table_id,
                self.private_subnet_B_route_table.attr_route_table_id
            ],
        )
        
        self.ec2_iam_role = iam.Role(
            scope=self,
            id="OnPremEC2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            path="/",
            role_name="onprem-network-ec2-iam-role",
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
            id="OnPremEC2InstanceProfile",
            path="/",
            roles=[self.ec2_iam_role.role_name]
        )
        
        self.router_A_ec2 = ec2.CfnInstance(
            scope=self,
            id="OnPremRouterA",
            instance_type="t3.small",
            network_interfaces=[
                ec2.CfnInstance.NetworkInterfaceProperty(
                    device_index="0",
                    network_interface_id=self.router_A_public_network_interface.attr_id
                ),
                ec2.CfnInstance.NetworkInterfaceProperty(
                    device_index="1",
                    network_interface_id=self.router_A_private_network_interface.attr_id
                )
            ],
            availability_zone=azs[0],
            image_id="ami-0ac80df6eff0e70b5",
            iam_instance_profile=self.ec2_instance_profile.instance_profile_name,
            tags=[CfnTag(
                key="Name",
                value="onprem-router-A"
            )],
            user_data=ec2.UserData.for_linux().add_commands(
                "apt-get update && apt-get install -y strongswan wget",
                "mkdir /home/ubuntu/demo_assets",
                "cd /home/ubuntu/demo_assets",
                "wget https://raw.githubusercontent.com/acantril/learn-cantrill-io-labs/master/aws-hybrid-bgpvpn/OnPremRouter1/ipsec-vti.sh",
                "wget https://raw.githubusercontent.com/acantril/learn-cantrill-io-labs/master/aws-hybrid-bgpvpn/OnPremRouter1/ipsec.conf",
                "wget https://raw.githubusercontent.com/acantril/learn-cantrill-io-labs/master/aws-hybrid-bgpvpn/OnPremRouter1/ipsec.secrets",
                "wget https://raw.githubusercontent.com/acantril/learn-cantrill-io-labs/master/aws-hybrid-bgpvpn/OnPremRouter1/51-eth1.yaml",
                "wget https://raw.githubusercontent.com/acantril/learn-cantrill-io-labs/master/aws-hybrid-bgpvpn/OnPremRouter1/ffrouting-install.sh",
                "chown ubuntu:ubuntu /home/ubuntu/demo_assets -R",
                "cp /home/ubuntu/demo_assets/51-eth1.yaml /etc/netplan",
                "netplan --debug apply"
            )
        )
        self.router_B_ec2 = ec2.CfnInstance(
            scope=self,
            id="OnPremRouterB",
            instance_type="t3.small",
            network_interfaces=[
                ec2.CfnInstance.NetworkInterfaceProperty(
                    device_index="0",
                    network_interface_id=self.router_B_public_network_interface.attr_id
                ),
                ec2.CfnInstance.NetworkInterfaceProperty(
                    device_index="1",
                    network_interface_id=self.router_B_private_network_interface.attr_id
                )
            ],
            availability_zone=azs[0],
            image_id="ami-0ac80df6eff0e70b5",
            iam_instance_profile=self.ec2_instance_profile.instance_profile_name,
            tags=[CfnTag(
                key="Name",
                value="onprem-router-B"
            )],
            user_data=ec2.UserData.for_linux().add_commands(
                "apt-get update && apt-get install -y strongswan wget",
                "mkdir /home/ubuntu/demo_assets",
                "cd /home/ubuntu/demo_assets",
                "wget https://raw.githubusercontent.com/acantril/learn-cantrill-io-labs/master/aws-hybrid-bgpvpn/OnPremRouter1/ipsec-vti.sh",
                "wget https://raw.githubusercontent.com/acantril/learn-cantrill-io-labs/master/aws-hybrid-bgpvpn/OnPremRouter1/ipsec.conf",
                "wget https://raw.githubusercontent.com/acantril/learn-cantrill-io-labs/master/aws-hybrid-bgpvpn/OnPremRouter1/ipsec.secrets",
                "wget https://raw.githubusercontent.com/acantril/learn-cantrill-io-labs/master/aws-hybrid-bgpvpn/OnPremRouter1/51-eth1.yaml",
                "wget https://raw.githubusercontent.com/acantril/learn-cantrill-io-labs/master/aws-hybrid-bgpvpn/OnPremRouter1/ffrouting-install.sh",
                "chown ubuntu:ubuntu /home/ubuntu/demo_assets -R",
                "cp /home/ubuntu/demo_assets/51-eth1.yaml /etc/netplan",
                "netplan --debug apply"
            )
        )
        
        self.onprem_server_A = ec2.Instance(
            scope=self,
            id="OnPremServerA",
            instance_name="onprem-server-a",
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
        self.onprem_server_B = ec2.Instance(
            scope=self,
            id="OnPremServerB",
            instance_name="onprem-server-b",
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
        
        CfnOutput(
            scope=self,
            id="RouterAPublicIP",
            description="Public IP of Router A",
            value=self.router_A_ec2.attr_public_ip
        )
        CfnOutput(
            scope=self,
            id="RouterAPrivateIP",
            description="Public IP of Router A",
            value=self.router_A_ec2.attr_private_ip
        )
        CfnOutput(
            scope=self,
            id="RouterBPublicIP",
            description="Public IP of Router B",
            value=self.router_B_ec2.attr_public_ip
        )
        CfnOutput(
            scope=self,
            id="RouterBPrivateIP",
            description="Private IP of Router B",
            value=self.router_B_ec2.attr_private_ip
        )