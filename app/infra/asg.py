import pulumi
import pulumi_aws as aws

def create_cpu_policy(asg, base_name):
    return aws.autoscaling.Policy(
        f"{base_name}-cpu-policy",  # Use the base name directly
        autoscaling_group_name=asg.name,
        policy_type="TargetTrackingScaling",
        target_tracking_configuration={
            "predefined_metric_specification": {
                "predefined_metric_type": "ASGAverageCPUUtilization",
            },
            "target_value": 75.0
        }
    )

def create_asg(name, launch_template_id, vpc_zone_identifiers, target_group_arns=None, health_check_type="EC2", health_check_grace_period=300, min_size=1, max_size=3, desired_capacity=2):
    asg = aws.autoscaling.Group(f"{name}-asg",
        vpc_zone_identifiers=vpc_zone_identifiers,
        target_group_arns=target_group_arns,  # This might be None
        health_check_type=health_check_type,
        health_check_grace_period=health_check_grace_period,
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
    cpu_policy = create_cpu_policy(asg, name)
    memory_policy = aws.autoscaling.Policy(f"{name}-memory-policy",
        autoscaling_group_name=asg.name,
        policy_type="TargetTrackingScaling",
        target_tracking_configuration={
            "customized_metric_specification": {
                "metric_name": "MemoryUtilization",
                "namespace": "System/Linux",
                "statistic": "Average",
                "unit": "Percent",
            },
            "target_value": 70.0
        }
    )

    return {
        "asg": asg,
        "cpu_policy": cpu_policy,
        "memory_policy": memory_policy
    }