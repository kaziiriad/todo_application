import pulumi_aws as aws

# Define AWS resources
class VPC:
    def __init__(self, name, cider_block):
        self.name = name
        self.vpc = self.create(cider_block)
        self.subnets = []
        self.route_tables = []
        self.security_groups = []
        self.internet_gateways = []
        self.nat_gateways = []
    
    def create(self, cider_block):
        self.vpc = aws.ec2.Vpc(
            self.name,
            cidr_block=cider_block,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            tags={
                "Name": self.name,
            },
        )
        return self.vpc
    
    def create_subnet(self, cidr_block, availability_zone, name, map_public_ip_on_launch=False):
        subnet = aws.ec2.Subnet(
            name,  # Use the provided name directly
            vpc_id=self.vpc.id,
            cidr_block=cidr_block,
            availability_zone=availability_zone,
            map_public_ip_on_launch=map_public_ip_on_launch,  # Enable or disable mapping public IP on launch
            tags={
                "Name": f"{self.name}-{name}",
            },
        )
        self.subnets.append(subnet)
        return subnet

    
    def create_route_table(self, name):
        route_table = aws.ec2.RouteTable(
            f"{name}",
            vpc_id=self.vpc.id,
            tags={
                "Name": f"{name}",
            },
        )
        self.route_tables.append(route_table)
        return route_table
    
    def create_internet_gateway(self, name):
        internet_gateway = aws.ec2.InternetGateway(
            f"{name}",
            vpc_id=self.vpc.id,
            tags={
                "Name": f"{name}",
            },
        )
        self.internet_gateways.append(internet_gateway)
        return internet_gateway

    def create_nat_gateway(self, name, subnet_id):
        eip = self.create_eip_allocation(f"{name}-eip", "vpc")
        nat_gateway = aws.ec2.NatGateway(
            name,
            allocation_id=eip.id,  # Use eip.id instead of creating new allocation
            subnet_id=subnet_id,
            tags={
                "Name": name,
            },
        )
        self.nat_gateways.append(nat_gateway)
        return nat_gateway
    
    def create_route_table_association(self, name, route_table_id, subnet_id):
          # Use static name instead of Output value

        return aws.ec2.RouteTableAssociation(
            f"rt-association-{name}",
            route_table_id=route_table_id,
            subnet_id=subnet_id,
        )


    def create_route(self, name, route_table_id, destination_cidr_block, gateway_id=None, nat_gateway_id=None):
        route_args = {
            "route_table_id": route_table_id,
            "destination_cidr_block": destination_cidr_block,
        }
        if gateway_id:
            route_args["gateway_id"] = gateway_id
        if nat_gateway_id:
            route_args["nat_gateway_id"] = nat_gateway_id
            
        return aws.ec2.Route(f"route-{name}", **route_args)
    
    def create_eip_allocation(self, name, domain):
        eip_allocation = aws.ec2.Eip(
            name,
            domain=domain,
            tags={
                "Name": f"{name}",
            },
        )
        return eip_allocation
    


# def create_vpc():
#     #vpc
#     vpc = aws.ec2.Vpc(
#         "my-vpc",
#         cidr_block="10.0.0.0/16",
#         enable_dns_hostnames=True,
#         enable_dns_support=True,
#         tags={
#             "Name": "My VPC",
#         },
#     )

#     # subnet
#     public_subnet = aws.ec2.Subnet(
#         "my-public-subnet",
#         vpc_id=vpc.id,
#         cidr_block="10.0.1.0/24",
#         map_public_ip_on_launch=True,
#         availability_zone="ap-southeast-1a",
#         tags={
#             "Name": "My Public Subnet",
#         },
#     )

#     private_subnet = aws.ec2.Subnet(
#         "my-private-subnet",
#         vpc_id=vpc.id,
#         cidr_block="10.0.2.0/24",
#         availability_zone="ap-southeast-1a",
#         tags={
#             "Name": "My Private Subnet",
#         },
#     )

#     # internet gateway
#     internet_gateway = aws.ec2.InternetGateway(
#         "my-igw",
#         vpc_id=vpc.id,
#         tags={
#             "Name": "My Internet Gateway",
#         },
#     )

#     # elastic ip address
#     eip = aws.ec2.Eip(
#         "my-nat-eip",
#         domain="vpc",
#         tags={
#             "Name": "My NAT Elastic IP Address",
#         },
#     )
#     #nat gateway
#     nat_gateway = aws.ec2.NatGateway(
#         "my-nat-gw",
#         subnet_id=public_subnet.id,
#         allocation_id=eip.allocation_id,
#         tags={
#             "Name": "My NAT Gateway",
#         },
#     )
    

#     # route table
#     public_route_table = aws.ec2.RouteTable(
#         "my-public-route-table",
#         vpc_id=vpc.id,
#         tags={
#             "Name": "My Public Route Table",
#         },
#     )
#     # Add a route to the route table
#     aws.ec2.Route(
#         "my-public-route",
#         route_table_id=public_route_table.id,
#         destination_cidr_block="0.0.0.0/0",
#         gateway_id=internet_gateway.id,
#     )
#     # Associate the public subnet with the route table
#     aws.ec2.RouteTableAssociation(
#         "my-public-route-table-association",
#         route_table_id=public_route_table.id,
#         subnet_id=public_subnet.id,
#     )

#     private_route_table = aws.ec2.RouteTable(
#         "my-private-route-table",
#         vpc_id=vpc.id,
#         tags={
#             "Name": "My Private Route Table",
#         }
#     )
#     # Add a route to the route table
#     aws.ec2.Route(
#         "my-private-route",
#         route_table_id=private_route_table.id,
#         destination_cidr_block="0.0.0.0/0",
#         nat_gateway_id=nat_gateway.id,
#     )

#     # Associate the private subnet with the route table
#     aws.ec2.RouteTableAssociation(
#         "my-private-route-table-association",
#         route_table_id=private_route_table.id,
#         subnet_id=private_subnet.id,
#     )

#     return {
#         "vpc": vpc,
#         "public_subnet": public_subnet,
#         "private_subnet": private_subnet,
#         "internet_gateway": internet_gateway,
#         "nat_gateway": nat_gateway,
#         "public_route_table": public_route_table,
#         "private_route_table": private_route_table,
#     }