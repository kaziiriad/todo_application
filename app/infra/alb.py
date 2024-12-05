import pulumi
import pulumi_aws as aws
import json

nginx_role = aws.iam.Role("nginx-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            }
        }]
    })
)

nginx_policy = aws.iam.RolePolicy("nginx-policy",
    role=nginx_role.id,
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "autoscaling:DescribeAutoScalingGroups",
                "ec2:DescribeInstances"
            ],
            "Resource": "*"
        }]
    })
)

nginx_instance_profile = aws.iam.InstanceProfile("nginx-profile",
    role=nginx_role.name
)

