import pulumi
import pulumi_aws as aws


def create_alb(
        vpc_id,
        name,
        security_group_ids,
        subnets,
):
    
    # Create an Application Load Balancer
    alb = aws.lb.LoadBalancer(
        name,
        load_balancer_type="application",
        security_groups=security_group_ids,
        subnets=subnets,
    )

    frontend_tg = aws.lb.TargetGroup(
        "frontend-tg",
        port=80,
        protocol="HTTP",
        target_type="instance",
        vpc_id=vpc_id,
        health_check={
            "enabled": True,
            "healthy_threshold": 2,
            "interval": 30,
            "path": "/",
            "port": "80",
            "protocol": "HTTP",
            "timeout": 5,
            "unhealthy_threshold": 2
        }
    )

    backend_tg = aws.lb.TargetGroup(
        "backend-tg",
        port=8000,
        protocol="HTTP",
        target_type="instance",
        vpc_id=vpc_id,
        health_check={
            "enabled": True,
            "healthy_threshold": 2,
            "interval": 30,
            "path": "/tasks",
            "port": "8000",
            "protocol": "HTTP",
            "timeout": 5,
            "unhealthy_threshold": 2
        }
    )


    frontend_listnener = aws.lb.Listener(
        resource_name="frontend-listener",
        load_balancer_arn=alb.arn,
        port=80,
        protocol="HTTP",
        default_actions=[     # List of actions
            {                 # Each action is a dictionary
                "type": "forward",
                "target_group_arn": frontend_tg.arn,
            },
        ]
    )

    backend_listener = aws.lb.Listener(
        resource_name="backend-listener",
        load_balancer_arn=alb.arn,
        port=8000,
        protocol="HTTP",
        default_actions=[     # List of actions
            {                 # Each action is a dictionary
                "type": "forward",
                "target_group_arn": backend_tg.arn,
            },
        ]

    )


    return {
        "alb": alb,
        "frontend_tg": frontend_tg,
        "backend_tg": backend_tg,
        "frontend_listener": frontend_listnener,
        "backend_listener": backend_listener,
    }