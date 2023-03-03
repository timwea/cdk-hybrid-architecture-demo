#pylint: disable-all
from aws_cdk import (
    Fn,
    CfnTag,
    CfnOutput,
    aws_ec2 as ec2,
    aws_iam as iam,
    
)
from constructs import Construct

from vpc_architecture_demos.custom import Subnet 
from vpc_architecture_demos.site_to_site_vpn import cidr_config

class OnPremNetwork(Construct):
    
    def __init__(self, scope: Construct, id: str, azs: list, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        self._vpc = ec2.Vpc(
            scope=self,
            id="OnPremVpc",
            vpc_name="onprem-network",
            ip_addresses=ec2.IpAddresses.cidr(cidr_config.ONPREM_CIDR),
            enable_dns_support=True,
            enable_dns_hostnames=True,
            subnet_configuration=[]
        )
        
        self._public_subnet = Subnet(
            scope=self,
            id="OnPremPublicSubnet",
            cidr=cidr_config.ONPREM_PUBLIC_SUBNET_CIDR,
            vpc_id=self._vpc.vpc_id,
            az=azs[0]
        )
        
        self._private_subnet_A = Subnet(
            scope=self,
            id="OnPremPrivateSubnetA",
            cidr=cidr_config.ONPREM_PRIVATE_SUBNET_A_CIDR,
            vpc_id=self._vpc.vpc_id,
            az=azs[0]
        )
        
        self._private_subnet_B = Subnet(
            scope=self,
            id="OnPremPrivateSubnetB",
            cidr=cidr_config.ONPREM_PRIVATE_SUBNET_B_CIDR,
            vpc_id=self._vpc.vpc_id,
            az=azs[0]
        )
        
        self._public_subnet_route_table = ec2.CfnRouteTable(
            scope=self,
            id="OnPremPublicSubnetRouteTable",
            vpc_id=self._vpc.vpc_id,
            tags=[CfnTag(
                key="Name",
                value="onprem-network-public_subnet_route_table"
            )]
        )
        
        self._private_subnet_A_route_table = ec2.CfnRouteTable(
            scope=self,
            id="OnPremPrivateSubnetARouteTable",
            vpc_id=self._vpc.vpc_id,
            tags=[CfnTag(
                key="Name",
                value="onprem-network-private_subnet_A_route_table"
            )]
        )
        
        self._private_subnet_B_route_table = ec2.CfnRouteTable(
            scope=self,
            id="OnPremPrivateSubnetBRouteTable",
            vpc_id=self._vpc.vpc_id,
            tags=[CfnTag(
                key="Name",
                value="onprem-network-private_subnet_B_route_table"
            )]
        )
        
        self._ec2_security_group = ec2.CfnSecurityGroup(
            scope=self,
            id="OnPremEC2SecurityGroup",
            group_description="On-Prem network default security group",
            group_name="onprem-network-ec2-sg",
            vpc_id=self._vpc.vpc_id,
            security_group_ingress=[
                ec2.CfnSecurityGroup.IngressProperty(
                    description="Allow All from AWS Environment",
                    ip_protocol="-1",
                    cidr_ip=cidr_config.AWS_VPC_CIDR
                ),   
            ]
        )
        self._ec2_security_group_self_reference_rule = ec2.CfnSecurityGroupIngress(
            scope= self,
            id="OnPremiseEC2SecurityGroupSelfReferenceRule",
            group_id=self._ec2_security_group.attr_group_id,
            ip_protocol="-1",
            source_security_group_id=self._ec2_security_group.attr_group_id
        )
        
        self._router_A_private_network_interface = ec2.CfnNetworkInterface(
            scope=self,
            id="OnPremRouterAPrivateNetworkInterface",
            subnet_id=self._private_subnet_A.subnet_id,
            description="OnPrem RouterA Private Interface",
            source_dest_check=False,
            group_set=[self._ec2_security_group.attr_group_id],
            tags=[CfnTag(
                key="Name",
                value="onprem-routerA-private-network-interface"
            )]
        )
        
        self._router_A_public_network_interface = ec2.CfnNetworkInterface(
            scope=self,
            id="OnPremRouterAPublicNetworkInterface",
            subnet_id=self._public_subnet.subnet_id,
            description="OnPrem RouterA Public Interface",
            source_dest_check=False,
            group_set=[self._ec2_security_group.attr_group_id],
            tags=[CfnTag(
                key="Name",
                value="onprem-routerA-public-network-interface"
            )]
        )
        
        self._router_B_private_network_interface = ec2.CfnNetworkInterface(
            scope=self,
            id="OnPremRouterBPrivateNetworkInterface",
            subnet_id=self._private_subnet_B.subnet_id,
            description="OnPrem RouterB Private Interface",
            source_dest_check=False,
            group_set=[self._ec2_security_group.attr_group_id],
            tags=[CfnTag(
                key="Name",
                value="onprem-routerB-private-network-interface"
            )]
        )
        
        self._router_B_public_network_interface = ec2.CfnNetworkInterface(
            scope=self,
            id="OnPremRouterBPublicNetworkInterface",
            subnet_id=self._public_subnet.subnet_id,
            description="OnPrem RouterB Public Interface",
            source_dest_check=False,
            group_set=[self._ec2_security_group.attr_group_id],
            tags=[CfnTag(
                key="Name",
                value="onprem-routerB-public-network-interface"
            )]
        )
        
        self._internet_gateway = ec2.CfnInternetGateway(
            scope=self,
            id="OnPremIGW",
            tags=[CfnTag(
                key="Name",
                value="onprem-network-igw"
            )]
        )
        
        self._internet_gateway_attach = ec2.CfnVPCGatewayAttachment(
            scope=self,
            id="OnPremIGWAttach",
            vpc_id=self._vpc.vpc_id,
            internet_gateway_id=self._internet_gateway.attr_internet_gateway_id
        )
        
        self._public_subnet_route_table_default_route = ec2.CfnRoute(
            scope=self,
            id="OnPremPublicSubnetRouteTableDefaultRoute",
            route_table_id=self._public_subnet_route_table.attr_route_table_id,
            gateway_id=self._internet_gateway.attr_internet_gateway_id,
            destination_cidr_block=cidr_config.ALL_IP_CIDR
        )
        self._public_subnet_route_table_default_route.add_dependency(target=self._internet_gateway_attach)
        
        
        self._private_subnet_A_route_table_route = ec2.CfnRoute(
            scope=self,
            id="OnPremPrivateSubnetARouteTableRoute",
            route_table_id=self._private_subnet_A_route_table.attr_route_table_id,
            network_interface_id=self._router_A_private_network_interface.attr_id,
            destination_cidr_block=cidr_config.AWS_VPC_CIDR
        )
        
        self._private_subnet_B_route_table_route = ec2.CfnRoute(
            scope=self,
            id="OnPremPrivateSubnetBRouteTableRoute",
            route_table_id=self._private_subnet_B_route_table.attr_route_table_id,
            network_interface_id=self._router_B_private_network_interface.attr_id,
            destination_cidr_block=cidr_config.AWS_VPC_CIDR
        )
        
        self._public_subnet_route_table_assoc = ec2.CfnSubnetRouteTableAssociation(
            scope=self,
            id="OnPremPublicSubnetRTAssoc",
            subnet_id=self._public_subnet.subnet_id,
            route_table_id=self._public_subnet_route_table.attr_route_table_id
        )
        
        self._private_subnet_A_route_table_assoc = ec2.CfnSubnetRouteTableAssociation(
            scope=self,
            id="OnPremPrivateSubnetARTAssoc",
            subnet_id=self._private_subnet_A.subnet_id,
            route_table_id=self._private_subnet_A_route_table.attr_route_table_id
        )
        
        self._private_subnet_B_route_table_assoc = ec2.CfnSubnetRouteTableAssociation(
            scope=self,
            id="OnPremPrivateSubnetBRTAssoc",
            subnet_id=self._private_subnet_B.subnet_id,
            route_table_id=self._private_subnet_B_route_table.attr_route_table_id
        )
        
        self._router_A_elastic_ip = ec2.CfnEIP(scope=self, id="OnPremRouterAElasticIP")
        self._router_A_elastic_ip.add_dependency(target=self._internet_gateway_attach)
        self._router_A_elastic_ip_assoc = ec2.CfnEIPAssociation(
            scope=self,
            id="OnPremRouterAElasticIPAssoc",
            allocation_id=self._router_A_elastic_ip.attr_allocation_id,
            network_interface_id=self._router_A_public_network_interface.attr_id
        )
        
        self._router_B_elastic_ip = ec2.CfnEIP(scope=self, id="OnPremRouterBElasticIP")
        self._router_B_elastic_ip.add_dependency(target=self._internet_gateway_attach)
        self._router_B_elastic_ip_assoc = ec2.CfnEIPAssociation(
            scope=self,
            id="OnPremRouterBElasticIPAssoc",
            allocation_id=self._router_B_elastic_ip.attr_allocation_id,
            network_interface_id=self._router_B_public_network_interface.attr_id
        )
        
        self._s3_interface_endpoint = ec2.CfnVPCEndpoint(
            scope=self,
            id="OnPremEC2MessagesInterfaceEndpoint",
            vpc_id=self._vpc.vpc_id,
            service_name="com.amazonaws.us-east-1.ec2messages",
            private_dns_enabled=True,
            vpc_endpoint_type="Interface",
            subnet_ids=[self._public_subnet.subnet_id],
            security_group_ids=[self._ec2_security_group.attr_group_id]
        )
        # self._ssm_messages_interface_endpoint = ec2.InterfaceVpcEndpoint(
        #     scope=self,
        #     id="OnPremSSMMessagesInterfaceEndpoint",
        #     vpc=self._vpc,
        #     service=ec2.InterfaceVpcEndpointAwsService.SSM_MESSAGES,
        #     private_dns_enabled=True,
        #     subnets=ec2.SubnetSelection(subnets=[self._public_subnet]),
        #     security_groups=[self._ec2_security_group]
        # )
        self._s3_interface_endpoint = ec2.CfnVPCEndpoint(
            scope=self,
            id="OnPremSSMMessagesInterfaceEndpoint",
            vpc_id=self._vpc.vpc_id,
            service_name="com.amazonaws.us-east-1.ssmmessages",
            private_dns_enabled=True,
            vpc_endpoint_type="Interface",
            subnet_ids=[self._public_subnet.subnet_id],
            security_group_ids=[self._ec2_security_group.attr_group_id]
        )
        
        self._s3_interface_endpoint = ec2.CfnVPCEndpoint(
            scope=self,
            id="OnPremSSMInterfaceEndpoint",
            vpc_id=self._vpc.vpc_id,
            service_name="com.amazonaws.us-east-1.ssm",
            private_dns_enabled=True,
            vpc_endpoint_type="Interface",
            subnet_ids=[self._public_subnet.subnet_id],
            security_group_ids=[self._ec2_security_group.attr_group_id]
        )
        
        self._s3_interface_endpoint = ec2.CfnVPCEndpoint(
            scope=self,
            id="OnPremS3InterfaceEndpoint",
            vpc_id=self._vpc.vpc_id,
            vpc_endpoint_type="Gateway",
            service_name="com.amazonaws.us-east-1.s3",
            route_table_ids=[
                self._public_subnet_route_table.attr_route_table_id,
                self._private_subnet_A_route_table.attr_route_table_id,
                self._private_subnet_B_route_table.attr_route_table_id
            ],
        )
        
        self._ec2_iam_role = iam.Role(
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
        
        self._ec2_instance_profile = iam.CfnInstanceProfile(
            scope=self,
            id="OnPremEC2InstanceProfile",
            path="/",
            roles=[self._ec2_iam_role.role_name]
        )
        
        shell_commands = ec2.UserData.for_linux()
        shell_commands.add_commands(
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
        
        self._router_A_ec2 = ec2.CfnInstance(
            scope=self,
            id="OnPremRouterA",
            instance_type="t3.small",
            network_interfaces=[
                ec2.CfnInstance.NetworkInterfaceProperty(
                    device_index="0",
                    network_interface_id=self._router_A_public_network_interface.attr_id
                ),
                ec2.CfnInstance.NetworkInterfaceProperty(
                    device_index="1",
                    network_interface_id=self._router_A_private_network_interface.attr_id
                )
            ],
            availability_zone=azs[0],
            image_id="ami-0ac80df6eff0e70b5",
            iam_instance_profile=self._ec2_instance_profile.ref,
            tags=[CfnTag(
                key="Name",
                value="onprem-router-A"
            )],
            user_data=Fn.base64(shell_commands.render())
        )
        
        self._router_B_ec2 = ec2.CfnInstance(
            scope=self,
            id="OnPremRouterB",
            instance_type="t3.small",
            network_interfaces=[
                ec2.CfnInstance.NetworkInterfaceProperty(
                    device_index="0",
                    network_interface_id=self._router_B_public_network_interface.attr_id
                ),
                ec2.CfnInstance.NetworkInterfaceProperty(
                    device_index="1",
                    network_interface_id=self._router_B_private_network_interface.attr_id
                )
            ],
            availability_zone=azs[0],
            image_id="ami-0ac80df6eff0e70b5",
            iam_instance_profile=self._ec2_instance_profile.ref,
            tags=[CfnTag(
                key="Name",
                value="onprem-router-B"
            )],
            user_data=Fn.base64(shell_commands.render())
        )
        
        self._onprem_server_A = ec2.CfnInstance(
            scope=self,
            id="OnPremServerA",
            instance_type="t2.micro",
            security_group_ids=[self._ec2_security_group.attr_group_id],
            image_id=ec2.MachineImage.latest_amazon_linux().get_image(self).image_id,
            iam_instance_profile=self._ec2_instance_profile.ref,
            subnet_id=self._private_subnet_A.subnet_id,
            tags=[CfnTag(
                key="Name",
                value="onprem-server-a"
            )]
        )
        
        self._onprem_server_B = ec2.CfnInstance(
            scope=self,
            id="OnPremServerB",
            instance_type="t2.micro",
            security_group_ids=[self._ec2_security_group.attr_group_id],
            image_id=ec2.MachineImage.latest_amazon_linux().get_image(self).image_id,
            iam_instance_profile=self._ec2_instance_profile.ref,
            subnet_id=self._private_subnet_B.subnet_id,
            tags=[CfnTag(
                key="Name",
                value="onprem-server-b"
            )]
        )
        
        self._router_A_customer_gateway = ec2.CfnCustomerGateway(
            scope=self,
            id="OnPremRouterACGW",
            bgp_asn=65016,
            type='ipsec.1',
            ip_address=self._router_A_ec2.attr_public_ip,
            device_name="onprem-router-A-cgw",
            tags=[CfnTag(
                key="Name",
                value="onprem-router-A-cgw"
            )],
        )
        self._router_A_customer_gateway.add_dependency(target=self._router_A_ec2)
        self._router_A_customer_gateway.add_dependency(target=self._router_A_elastic_ip_assoc)
        
        self._router_B_customer_gateway = ec2.CfnCustomerGateway(
            scope=self,
            id="OnPremRouterBCGW",
            bgp_asn=65016,
            type='ipsec.1',
            ip_address=self._router_B_ec2.attr_public_ip,
            device_name="onprem-router-B-cgw",
            tags=[CfnTag(
                key="Name",
                value="onprem-router-B-cgw"
            )],
        )
        self._router_B_customer_gateway.add_dependency(target=self._router_B_ec2)
        self._router_B_customer_gateway.add_dependency(target=self._router_B_elastic_ip_assoc)
        
        CfnOutput(
            scope=self,
            id="RouterAPublicIP",
            description="Public IP of Router A",
            value=self._router_A_ec2.attr_public_ip
        )
        CfnOutput(
            scope=self,
            id="RouterAPrivateIP",
            description="Private IP of Router A",
            value=self._router_A_ec2.attr_private_ip
        )
        CfnOutput(
            scope=self,
            id="RouterBPublicIP",
            description="Public IP of Router B",
            value=self._router_B_ec2.attr_public_ip
        )
        CfnOutput(
            scope=self,
            id="RouterBPrivateIP",
            description="Private IP of Router B",
            value=self._router_B_ec2.attr_private_ip
        )