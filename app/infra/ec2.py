import pulumi_aws as aws

class EC2Instance:

    def __init__(self):
        self.instance_type = 't2.micro' # Replace with your desired instance type
        self.ami_id = 'ami-047126e50991d067b' # Replace with your AMI ID
        self.instances = []
    
    def create(self, name, number, security_group_ids, subnet_id, key_name, user_data=None, **kwargs):
        instances = []
        for i in range(1, number+1): # Create multiple instances based on the count parameter
            instance = aws.ec2.Instance(
                f'{name}-{i}',
                ami=self.ami_id, # Replace with your AMI ID
                instance_type=self.instance_type,
                security_group_ids=security_group_ids,
                subnet_id=subnet_id,
                key_name=key_name,
                user_data=user_data,  # Replace with your user data script
                **kwargs,  # Additional parameters for the instance creation
                tags={
                    'Name': self.name,
                },
            )
            instances.append(instance)
        
        self.instances.extend(instances)
        return self.instances
    

    

    

    


# # Create an AWS EC2 instance
# def create_aws_ec2(subnet_id, security_group, user_data, key_name, instance_type='t3.micro', count=1, name='instance', **kwargs):
#     instances = [] #

#     for i in range(1, count+1): #

#         instance = aws.ec2.Instance(
#             f'{name}-{i}',
#             ami='ami-047126e50991d067b', # Replace with your AMI ID
#             subnet_id=subnet_id,
#             security_groups=[security_group.id],
#             instance_type=instance_type, 
#             user_data=user_data, # Replace with your user data script
#             key_name=key_name,# Replace with your key pair name
#             **kwargs,
#             tags={
#                 'Name': f'{name}-{i}',
#             },
#         )
#         instances.append(instance)

#     return instances