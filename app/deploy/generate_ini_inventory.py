#!/usr/bin/env python3
"""
Generate Ansible inventory in INI format from Pulumi stack outputs.
Run this after pulumi up to create inventory files for Ansible.
"""

import json
import subprocess
import os
from collections import defaultdict

def get_pulumi_outputs():
    """Get the outputs from the current Pulumi stack"""
    # Store the current directory
    original_dir = os.getcwd()
    
    try:
        # Change to the infrastructure directory
        infra_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "infra")
        os.chdir(infra_dir)
        
        # Run the Pulumi command
        result = subprocess.run(["pulumi", "stack", "output", "--json"], 
                               capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    finally:
        # Always change back to the original directory
        os.chdir(original_dir)

def generate_ini_inventory(outputs):
    """Generate Ansible inventory in INI format from Pulumi outputs"""
    # Get the bastion host IP
    bastion_ip = outputs.get("bastion_host_ip", "")
    if not bastion_ip:
        print("Warning: No bastion host IP found in Pulumi outputs")
    
    # Set the SSH key path - will be updated by the deployment script
    ssh_key_path = "~/.ssh/dev-deploy.id_rsa"
    
    # Common SSH arguments to bypass host key checking
    ssh_common_args_base = '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
    
    # SSH arguments for instances accessed through bastion
    proxy_command = f'-o ProxyCommand="ssh -i {ssh_key_path} {ssh_common_args_base} -o ConnectTimeout=30 -o ConnectionAttempts=5 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -W %h:%p ubuntu@{bastion_ip}"'
    ssh_common_args_proxy = f'{proxy_command} {ssh_common_args_base}'
    
    # Create inventory sections
    bastion_section = "[bastion]\n"
    db_masters_section = "[db_masters]\n"
    db_replicas_section = "[db_replicas]\n"
    redis_masters_section = "[redis_masters]\n"
    redis_replicas_section = "[redis_replicas]\n"
    redis_sentinels_section = "[redis_sentinels]\n"
    backend_servers_section = "[backend_servers]\n"
    frontend_servers_section = "[frontend_servers]\n"
    
    # Process each output and organize by role
    for key, value in outputs.items():
        if key == "bastion_host_ip":
            bastion_section += f"bastion-1 ansible_host={value} ansible_user=ubuntu ansible_ssh_private_key_file={ssh_key_path} ansible_ssh_common_args='{ssh_common_args_base}'\n"
        
        elif key.startswith("db_master"):
            db_masters_section += f"db_masters-1 ansible_host={value} ansible_user=ubuntu ansible_ssh_private_key_file={ssh_key_path} ansible_ssh_common_args='{ssh_common_args_proxy}'\n"
        
        elif key.startswith("db_replica"):
            # Extract the replica number from the key
            try:
                replica_num = int(key.split("_")[2])
                db_replicas_section += f"db_replicas-{replica_num} ansible_host={value} ansible_user=ubuntu ansible_ssh_private_key_file={ssh_key_path} ansible_ssh_common_args='{ssh_common_args_proxy}'\n"
            except (IndexError, ValueError):
                db_replicas_section += f"db_replicas-1 ansible_host={value} ansible_user=ubuntu ansible_ssh_private_key_file={ssh_key_path} ansible_ssh_common_args='{ssh_common_args_proxy}'\n"
        
        elif key.startswith("redis_master"):
            redis_masters_section += f"redis_masters-1 ansible_host={value} ansible_user=ubuntu ansible_ssh_private_key_file={ssh_key_path} ansible_ssh_common_args='{ssh_common_args_proxy}'\n"
        
        elif key.startswith("redis_replica"):
            # Extract the replica number from the key
            try:
                replica_num = int(key.split("_")[2])
                redis_replicas_section += f"redis_replicas-{replica_num} ansible_host={value} ansible_user=ubuntu ansible_ssh_private_key_file={ssh_key_path} ansible_ssh_common_args='{ssh_common_args_proxy}'\n"
            except (IndexError, ValueError):
                redis_replicas_section += f"redis_replicas-1 ansible_host={value} ansible_user=ubuntu ansible_ssh_private_key_file={ssh_key_path} ansible_ssh_common_args='{ssh_common_args_proxy}'\n"
        
        elif key.startswith("redis_sentinel"):
            # Extract the sentinel number from the key
            try:
                sentinel_num = int(key.split("_")[2])
                redis_sentinels_section += f"redis_sentinels-{sentinel_num} ansible_host={value} ansible_user=ubuntu ansible_ssh_private_key_file={ssh_key_path} ansible_ssh_common_args='{ssh_common_args_proxy}'\n"
            except (IndexError, ValueError):
                redis_sentinels_section += f"redis_sentinels-1 ansible_host={value} ansible_user=ubuntu ansible_ssh_private_key_file={ssh_key_path} ansible_ssh_common_args='{ssh_common_args_proxy}'\n"
        
        elif key.startswith("backend_instance") and key.endswith("_ip"):
            # Extract the instance number from the key
            try:
                instance_num = int(key.split("_")[2])
                backend_servers_section += f"backend_servers-{instance_num} ansible_host={value} ansible_user=ubuntu ansible_ssh_private_key_file={ssh_key_path} ansible_ssh_common_args='{ssh_common_args_proxy}'\n"
            except (IndexError, ValueError):
                backend_servers_section += f"backend_servers-1 ansible_host={value} ansible_user=ubuntu ansible_ssh_private_key_file={ssh_key_path} ansible_ssh_common_args='{ssh_common_args_proxy}'\n"
        
        elif key.startswith("frontend_instance") and key.endswith("_ip") and not key.endswith("_private_ip"):
            # Extract the instance number from the key
            try:
                instance_num = int(key.split("_")[2])
                frontend_servers_section += f"frontend_servers-{instance_num} ansible_host={value} ansible_user=ubuntu ansible_ssh_private_key_file={ssh_key_path} ansible_ssh_common_args='{ssh_common_args_proxy}'\n"
            except (IndexError, ValueError):
                frontend_servers_section += f"frontend_servers-1 ansible_host={value} ansible_user=ubuntu ansible_ssh_private_key_file={ssh_key_path} ansible_ssh_common_args='{ssh_common_args_proxy}'\n"
    
    # Create group relationships
    groups_section = """
[database_servers:children]
db_masters
db_replicas

[redis_servers:children]
redis_masters
redis_replicas
redis_sentinels

[app_servers:children]
backend_servers
frontend_servers
"""
    
    # Combine all sections
    all_inventory = "; Combined Inventory in INI format\n\n" + \
                   bastion_section + "\n" + \
                   db_masters_section + "\n" + \
                   db_replicas_section + "\n" + \
                   redis_masters_section + "\n" + \
                   redis_replicas_section + "\n" + \
                   redis_sentinels_section + "\n" + \
                   backend_servers_section + "\n" + \
                   frontend_servers_section + "\n" + \
                   groups_section
    
    # Create individual inventory files
    bastion_inventory = "; Bastion Inventory in INI format\n\n" + bastion_section
    
    database_inventory = "; Database Inventory in INI format\n\n" + \
                        db_masters_section + "\n" + \
                        db_replicas_section + "\n" + \
                        "[database_servers:children]\ndb_masters\ndb_replicas\n"
    
    redis_inventory = "; Redis Inventory in INI format\n\n" + \
                     redis_masters_section + "\n" + \
                     redis_replicas_section + "\n" + \
                     redis_sentinels_section + "\n" + \
                     "[redis_servers:children]\nredis_masters\nredis_replicas\nredis_sentinels\n"
    
    app_inventory = "; Application Inventory in INI format\n\n" + \
                   backend_servers_section + "\n" + \
                   frontend_servers_section + "\n" + \
                   "[app_servers:children]\nbackend_servers\nfrontend_servers\n"
    
    return {
        "all": all_inventory,
        "bastion": bastion_inventory,
        "database": database_inventory,
        "redis": redis_inventory,
        "app": app_inventory
    }

def write_inventory_files(inventories):
    """Write the inventory to INI files for Ansible"""
    # Create inventory directory
    inventory_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ansible", "inventory")
    os.makedirs(inventory_dir, exist_ok=True)
    
    # Write each inventory file
    for name, content in inventories.items():
        file_path = os.path.join(inventory_dir, f"{name}.ini")
        with open(file_path, "w") as f:
            f.write(content)
        print(f"Inventory file created: {file_path}")

def main():
    try:
        outputs = get_pulumi_outputs()
        inventories = generate_ini_inventory(outputs)
        write_inventory_files(inventories)
        print("INI inventory generation completed successfully.")
    except Exception as e:
        print(f"Error generating inventory: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
