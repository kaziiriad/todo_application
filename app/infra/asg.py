import pulumi
import pulumi_aws as aws



def create_asg(name, launch_template_id, vpc_zone_identifiers, target_group_arns, min_size=1, max_size=3, desired_capacity=2):
    asg = aws.autoscaling.Group(f"{name}-asg",
        vpc_zone_identifiers=vpc_zone_identifiers,
        target_group_arns=target_group_arns,
        health_check_type="ELB",
        health_check_grace_period=300,
        min_size=min_size,
        max_size=max_size,
        desired_capacity=desired_capacity,
        launch_template={
            "id": launch_template_id,
            "version": "$Latest"
        },
        tags=[{
            "key": "Name",
            "value": f"{name}-asg",
            "propagateAtLaunch": True
        }]
    )

    # Create scaling policies
    cpu_policy = aws.autoscaling.Policy(f"{name}-cpu-policy",
        autoscaling_group_name=asg.name,
        policy_type="TargetTrackingScaling",
        target_tracking_configuration={
            "predefined_metric_specification": {
                "predefined_metric_type": "ASGAverageCPUUtilization",
            },
            "target_value": 75.0
        }
    )

    return {
        "asg": asg,
        "cpu_policy": cpu_policy,
        "target_group_arn": asg.target_group_arns[0]  # Get the ARN of the target group for the load balancer listener
    }
