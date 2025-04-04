import os
import pulumi

def create_ssh_config(args):
    """
    Create an SSH config file for easy access to all instances.
    
    This function takes a list of arguments where:
    - The first element is the bastion host IP
    - The remaining elements are dictionaries with instance details
    """
    bastion_ip = args[0]
    instances = args[1:]
    
    config_content = f"""# SSH Config for Infrastructure
# Generated automatically - do not edit manually

# Bastion host configuration
Host bastion
    HostName {bastion_ip}
    User ubuntu
    IdentityFile ~/.ssh/dev_deploy.id_rsa
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ServerAliveInterval 30
    ServerAliveCountMax 3

"""
    
    # Add configurations for all other instances
    for instance in instances:
        name = instance["name"]
        ip = instance["ip"]
        is_public = instance.get("is_public", False)
        
        config_content += f"Host {name}\n"
        config_content += f"    HostName {ip}\n"
        config_content += "    User ubuntu\n"
        config_content += "    IdentityFile ~/.ssh/dev_deploy.id_rsa\n"
        
        # All instances should be accessed through the bastion, including frontend
        config_content += "    ProxyJump bastion\n"
        
        config_content += "    StrictHostKeyChecking no\n"
        config_content += "    UserKnownHostsFile /dev/null\n"
        config_content += "    ServerAliveInterval 30\n"
        config_content += "    ServerAliveCountMax 3\n\n"
    
    # Write the content to the SSH config file
    config_path = os.path.expanduser("~/.ssh/config")
    
    # Backup existing config if it exists
    if os.path.exists(config_path):
        backup_path = os.path.expanduser("~/.ssh/config.bak")
        try:
            with open(config_path, "r") as src, open(backup_path, "w") as dst:
                dst.write(src.read())
            print(f"Backed up existing SSH config to {backup_path}")
        except Exception as e:
            print(f"Warning: Could not backup existing SSH config: {e}")
    
    # Write new config
    try:
        with open(config_path, "w") as config_file:
            config_file.write(config_content)
        print(f"SSH config written to {config_path}")
        
        # Make sure the permissions are correct
        os.chmod(config_path, 0o600)
    except Exception as e:
        print(f"Error writing SSH config: {e}")
        return False
    
    return True

def setup_ssh_config(bastion_host, db_master, db_replicas, redis_master, redis_replicas, 
                    redis_sentinels, backend_instances, frontend_instances):
    """
    Set up SSH config for all infrastructure components
    """
    # Create a list of instance configurations
    instances = []
    
    # Add DB instances
    instances.append({
        "name": "db-master",
        "ip": db_master.private_ip,
        "is_public": False
    })
    
    for i, replica in enumerate(db_replicas):
        instances.append({
            "name": f"db-replica-{i+1}",
            "ip": replica.private_ip,
            "is_public": False
        })
    
    # Add Redis instances
    instances.append({
        "name": "redis-master",
        "ip": redis_master.private_ip,
        "is_public": False
    })
    
    for i, replica in enumerate(redis_replicas):
        instances.append({
            "name": f"redis-replica-{i+1}",
            "ip": replica.private_ip,
            "is_public": False
        })
    
    for i, sentinel in enumerate(redis_sentinels):
        instances.append({
            "name": f"redis-sentinel-{i+1}",
            "ip": sentinel.private_ip,
            "is_public": False
        })
    
    # Add backend instances
    for i, instance in enumerate(backend_instances):
        instances.append({
            "name": f"backend-{i+1}",
            "ip": instance.private_ip,
            "is_public": False
        })
    
    # Add frontend instances - now using private IPs since they'll be accessed through bastion
    for i, instance in enumerate(frontend_instances):
        instances.append({
            "name": f"frontend-{i+1}",
            "ip": instance.private_ip,  # Changed to private_ip
            "is_public": False  # Changed to False
        })
    
    # Convert all instance data to Pulumi outputs
    instance_outputs = []
    for instance in instances:
        instance_output = {
            "name": instance["name"],
            "ip": instance["ip"],
            "is_public": instance["is_public"]
        }
        instance_outputs.append(instance_output)
    
    # Apply the function once all outputs are available
    pulumi.Output.all(bastion_host.public_ip, *instance_outputs).apply(
        lambda args: create_ssh_config(args)
    )
