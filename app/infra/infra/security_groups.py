import pulumi_aws as aws

class SecurityGroup:
    def __init__(self, name, vpc_id):
        self.sg = aws.ec2.SecurityGroup(name, vpc_id=vpc_id)
        self.name = name

    def create_ingress_rule(self, from_port, to_port, protocol, cidr_blocks, description, **kwargs):
        self.sg.ingress.add(aws.ec2.SecurityGroupRuleArgs(
            from_port=from_port,
            to_port=to_port,
            protocol=protocol,
            cidr_blocks=cidr_blocks,
            description=description,
            **kwargs
        ))
    def create_egress_rule(self, from_port, to_port, protocol, cidr_blocks, description, **kwargs):
        self.sg.egress.add(aws.ec2.SecurityGroupRuleArgs(
            from_port=from_port,
            to_port=to_port,
            protocol=protocol,
            cidr_blocks=cidr_blocks,
            description=description,
            **kwargs
        ))

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