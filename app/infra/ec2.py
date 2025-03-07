import pulumi_aws as aws

class EC2Instance:

    def __init__(self):
        self.instance_type = 't2.micro' # Replace with your desired instance type
        self.ami_id = 'ami-047126e50991d067b' # Replace with your AMI ID
        self.instances = []
    
    def create(self, name, number, security_groups, key_name, subnet_id, user_data, associate_public_ip_address=False):
        instance_args = {
            "instance_type": self.instance_type,  # or your desired instance type
            "ami": self.ami_id,  # your AMI ID
            "vpc_security_group_ids": security_groups,  # Changed from security_group_ids
            "key_name": key_name,
            "subnet_id": subnet_id,
            "user_data": user_data,
            "associate_public_ip_address": associate_public_ip_address,
            "tags": {
                "Name": name
            }
        }

        if number == 1:
            instance = aws.ec2.Instance(
                name,
                **instance_args
            )
            self.instances.append(instance)
            return instance
        else:
            instances = []
            for i in range(number):
                instance = aws.ec2.Instance(
                    f"{name}-{i+1}",
                    **instance_args
                )
                instances.append(instance)
                self.instances.extend(instances)
            return instances
    

    

    

    


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