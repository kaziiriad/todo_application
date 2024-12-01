"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws 

from alb import create_alb
from user_data import get_frontend_user_data, get_backend_user_data, get_database_user_data
from asg import create_asg

config = pulumi.Config()


from ec2 import EC2Instance
from security_groups import SecurityGroup
from vpc import VPC

KEY_PAIR_NAME = 'MyNewKeyPair'

USER_DATA = """
#!/bin/bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
sudo systemctl start docker
sudo systemctl enable docker
newgrp docker
mkdir -p /home/ubuntu/app
"""

# lb_docker_compose = """
# version: '3'
# services:
#   nginx:
#     image: nginx:alpine
#     ports:
#       - "80:80"
#       - "443:443"
#     volumes:
#       - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
#     restart: always
# """


# create a VPC
vpc_module = VPC('my-vpc', cider_block='10.0.0.0/16')

# create subnets
public_subnets_1 = vpc_module.create_subnet( # public subnets
    cidr_block='10.0.1.0/24',
    availability_zone='ap-southeast-1a',
    name='public-subnet-1'
)

public_subnets_2 = vpc_module.create_subnet( # public subnets
    cidr_block='10.0.3.0/24',
    availability_zone='ap-southeast-1b',
    name='public-subnet-2'
)

private_subnets_1 = vpc_module.create_subnet( # private subnets
    cidr_block='10.0.2.0/24',
    availability_zone='ap-southeast-1a',
    name='private-subnet-1'
)

private_subnets_2 = vpc_module.create_subnet( # private subnets
    cidr_block='10.0.4.0/24',
    availability_zone='ap-southeast-1b',
    name='private-subnet-2'
)

# create route tables
public_route_table = vpc_module.create_route_table( # public route table
    name='public-route-table'

)
private_route_table = vpc_module.create_route_table( # private route table
    name='private-route-table'
)

# create gateways
internet_gateway = vpc_module.create_internet_gateway( # internet gateway
    name='my-internet-gateway'
)


nat_gateway_1 = vpc_module.create_nat_gateway( # nat gateway
    name="my-nat-gateway",
    subnet_id=public_subnets_1.id
)
nat_gateway_2 = vpc_module.create_nat_gateway( # nat gateway
    name="my-nat-gateway-2",
    subnet_id=public_subnets_2.id
)

# create route table associations
vpc_module.create_route_table_association( # associate public route table with public subnets
    route_table_id=public_route_table.id,
    subnet_id=public_subnets_1.id
)

vpc_module.create_route_table_association( # associate public route table with public subnets
    route_table_id=public_route_table.id,
    subnet_id=public_subnets_2.id
)

vpc_module.create_route_table_association( # associate private route table with private subnets
    route_table_id=private_route_table.id,
    subnet_id=private_subnets_1.id
)

vpc_module.create_route_table_association( # associate private route table with private subnets
    route_table_id=private_route_table.id,
    subnet_id=private_subnets_2.id
)

# create routes
igw_route = vpc_module.create_route( # route to internet gateway
    route_table_id=public_route_table.id,
    destination_cidr_block='0.0.0.0/0',
    gateway_id=internet_gateway.id
)

nat_gw_route_1 = vpc_module.create_route( # route to nat gateway
    route_table_id=private_route_table.id,
    destination_cidr_block='0.0.0.0/0',
    nat_gateway_id=nat_gateway_1.id
)

nat_gw_route_2 = vpc_module.create_route( # route to nat gateway
    route_table_id=private_route_table.id,
    destination_cidr_block='0.0.0.0/0',
    nat_gateway_id=nat_gateway_2.id
)

# create security groups
backend_security_group = SecurityGroup('backend-security-group', vpc_id=vpc_module.vpc.id)
frontend_security_group = SecurityGroup('frontend-security-group', vpc_id=vpc_module.vpc.id)
lb_security_group = SecurityGroup('lb-security-group', vpc_id=vpc_module.vpc.id)
db_security_group = SecurityGroup('db-security-group', vpc_id=vpc_module.vpc.id)

lb_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=80,
    to_port=80,
    cidr_blocks=['0.0.0.0/0'],
    description='Allow HTTP traffic'
)
lb_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=443,
    to_port=443,
    cidr_blocks=['0.0.0.0/0'],
    description='Allow HTTPS traffic'

)
lb_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=22,
    to_port=22,
    cidr_blocks=['0.0.0.0/0'],
    description='Allow SSH traffic'
)

lb_security_group.create_egress_rule(
    protocol='-1',
    from_port=0,
    to_port=0,
    cidr_blocks=["0.0.0.0/0"],
    description='Allow outbound traffic'
)

frontend_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=80,
    to_port=80,
    description='Allow HTTP traffic',
    source_security_group_id=lb_security_group.id
)

frontend_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=443,
    to_port=443,
    description='Allow HTTPS traffic',
    source_security_group_id=lb_security_group.id
)

frontend_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=22,
    to_port=22,
    cidr_blocks=['0.0.0.0/0'],
    description='Allow SSH traffic',
)

frontend_security_group.create_egress_rule(
    protocol='-1',
    from_port=0,
    to_port=0,
    cidr_blocks=["0.0.0.0/0"],
    description='Allow outbound traffic'
)

backend_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=8000,
    to_port=8000,
    description='Allow HTTP traffic',
    source_security_group_id=lb_security_group.id
)

backend_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=22,
    to_port=22,
    description='Allow HTTP traffic',
    source_security_group_id=lb_security_group.id
)

backend_security_group.create_egress_rule(
    protocol='-1',
    from_port=0,
    to_port=0,
    cidr_blocks=["0.0.0.0/0"],
    description='Allow outbound traffic'
)

backend_security_group.create_egress_rule(
    protocol='tcp',
    from_port=5432,
    to_port=5432,
    description='Allow PostgreSQL traffic',
    source_security_group_id=db_security_group.id
)

db_security_group.create_ingress_rule(
    protocol='tcp',
    from_port=5432,
    to_port=5432,
    description='Allow PostgreSQL traffic',
    source_security_group_id=backend_security_group.id
)

db_security_group.create_egress_rule(
    protocol='-1',
    from_port=0,
    to_port=0,
    cidr_blocks=["0.0.0.0/0"],
    description='Allow outbound traffic'
)


# create instances
instance_module = EC2Instance()


# create load balancer


# create frontend instances

database_instance = instance_module.create(
    name='database_instance',
    number=1,
    security_groups=[db_security_group.id],
    key_name=KEY_PAIR_NAME,
    subnet_id=private_subnets_1.id,
    user_data=get_database_user_data(
        "myuser",
        "mypassword",
        "mydb"
    )
)


alb_instance = create_alb(
    vpc_id=vpc_module.vpc.id,
    name='app-alb_instance',
    security_group_ids=[lb_security_group.id],
    subnets=[public_subnets_1.id, public_subnets_2.id],
)
alb = alb_instance['alb']
pulumi.export("alb_dns_name", alb.dns_name)

frontend_tg = alb_instance['frotned_tg']
backend_tg = alb_instance['backend_tg']
frontend_listener = alb_instance['frontend_listener']
backend_listener = alb_instance['backend_listener']

frontend_lt = aws.ec2.LaunchTemplate("frontend-lt",
    name_prefix="frontend-",
    image_id="ami-047126e50991d067b",  # Use your AMI ID
    instance_type="t2.micro",
    vpc_security_group_ids=[frontend_security_group.id],
    user_data=get_frontend_user_data(alb.dns_name),
    key_name=KEY_PAIR_NAME
)
pulumi.export("database_instance_ip", database_instance.private_ip)


backend_lt = aws.ec2.LaunchTemplate("backend-lt",
    name_prefix="backend-",
    image_id="ami-047126e50991d067b",  # Use your AMI ID
    instance_type="t2.micro",
    vpc_security_group_ids=[backend_security_group.id],
    user_data=get_backend_user_data(
        database_instance.private_ip,
        "myuser",
        "mypassword",
        "mydb"
    ),
    key_name=KEY_PAIR_NAME
)


frontend_asg = create_asg(
    name="frontend-asg",
    launch_template_id=frontend_lt.id,
    vpc_zone_identifier=[public_subnets_1.id, public_subnets_2.id],
    target_group_arns=[frontend_tg.arn]

)

backend_asg = create_asg(
    name="backend-asg",
    launch_template_id=backend_lt.id,
    vpc_zone_identifier=[private_subnets_1.id, private_subnets_2.id],
    target_group_arns=[backend_tg.arn]
)

pulumi.export("frontend_asg_name", frontend_asg['asg'].id)
pulumi.export("backend_asg_name", backend_asg['asg'].id)
pulumi.export("frontend_listener_arn", frontend_listener.arn)
pulumi.export("backend_listener_arn", backend_listener.arn)
