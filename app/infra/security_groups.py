import pulumi_aws as aws

class SecurityGroup:
    def __init__(self, name, vpc_id):
        self.sg = aws.ec2.SecurityGroup(
            name,
            vpc_id=vpc_id,
            description=f"Security group for {name}",
            ingress=[],  # Initialize empty ingress rules
            egress=[],   # Initialize empty egress rules
            tags={
                "Name": name
            }
        )
        self.name = name
        self.id = self.sg.id

    def create_ingress_rule(self, protocol, from_port, to_port, description, cidr_blocks=None, source_security_group_id=None):
        rule = {
            "protocol": protocol,
            "from_port": from_port,
            "to_port": to_port,
            "description": description
        }
        
        if cidr_blocks:
            rule["cidr_blocks"] = cidr_blocks
        if source_security_group_id:
            rule["source_security_group_id"] = source_security_group_id

        aws.ec2.SecurityGroupRule(
            f"{self.name}-ingress-{from_port}",
            type="ingress",
            security_group_id=self.sg.id,
            **rule
        )

    def create_egress_rule(self, protocol, from_port, to_port, description, cidr_blocks=None, source_security_group_id=None):
        rule = {
            "protocol": protocol,
            "from_port": from_port,
            "to_port": to_port,
            "description": description
        }

        if cidr_blocks:
            rule["cidr_blocks"] = cidr_blocks
        if source_security_group_id:
            rule["source_security_group_id"] = source_security_group_id

        aws.ec2.SecurityGroupRule(
            f"{self.name}-egress-{from_port}",
            type="egress",
            security_group_id=self.sg.id,
            **rule
        )

# Usage
# vpc_id = aws.ec2.get_vpc(id="vpc-0abcdef1234567890").id
# sg = SecurityGroup("master-sg", vpc_id)
# sg.create_ingress_rule(22, 22, "tcp", ["0.0.0.0/0"], "SSH access")
# sg.create_egress_rule(80, 80, "tcp", ["0.0.0.0/0"], "http access")
# sg.create_egress_rule(443, 443, "tcp", ["0.0.0.0/0"], "https access")
# inbound vs outbound rule differences:

# def create_security_group(vpc_id):  
    
#     alb_sg = aws.ec2.SecurityGroup(
#         "master-sg",
#         description="Security Group for master node",
#         vpc_id=vpc_id,
#         ingress=[
#             {
#                 "from_port": 22,
#                 "to_port": 22,
#                 "protocol": "tcp",
#                 "cidr_blocks": ["0.0.0.0/0"],
#                 "description" : "SSH access"
#             },
#             {
#                 "from_port": 80,
#                 "to_port": 80,
#                 "protocol": "tcp",
#                 "cidr_blocks": ["0.0.0.0/0"],
#                 "description" : "http access"
#             },
#             {
#                 "from_port": 443,
#                 "to_port": 443,
#                 "protocol": "tcp",
#                 "cidr_blocks": ["0.0.0.0/0"],
#                 "description" : "https access"
#             }
#         ],
#         egress=[
#             {
#                 "from_port": 8001,
#                 "to_port": 0,
#                 "protocol": "-1",
#                 "cidr_blocks": ["0.0.0.0/0"],
#                 "description" : "All outbound traffic"
#             }
#         ],
#         tags={
#             "Name": "Master Security Group",
#         },
#     )

#     app_ec2_sg = aws.ec2.SecurityGroup(
#         "app_ec2-sg",
#         description="Security Group for agent nodes",
#         vpc_id=vpc_id,
#         ingress=[
#             {
#                 "from_port": 22,
#                 "to_port": 22,
#                 "protocol": "tcp",
#                 "cidr_blocks": ["0.0.0.0/0"],
#                 "description" : "SSH access"

#             },
#             {
#                 "from_port": 8000,
#                 "to_port": 8000,
#                 "protocol": "tcp",
#                 "security_groups": [alb_sg.id],
#                 "description" : "FastAPI access"
#             },
#             {
#                 "from_port": 2375,
#                 "to_port": 2375,
#                 "protocol": "tcp",
#                 "security_groups": [alb_sg.id],
#                 "description" : "Docker access"
#             }
            
#         ],
#         egress=[
#             {
#                 "from_port": 0,
#                 "to_port": 0,
#                 "protocol": "-1",
#                 "cidr_blocks": ["0.0.0.0/0"],
#                 "description" : "All outbound traffic"
#             }
#         ],
#         tags={
#                 "Name": "Agent Security Group",
#         }
#     )
    
#     return {
#         "alb_sg": alb_sg,
#         "app_ec2_sg": app_ec2_sg
#     }

#     # Create a security group for our EC2 instances