#!/usr/bin/env python3
"""
Generate Ansible inventory from Pulumi stack outputs.
Run this after pulumi up to create an inventory file for Ansible.
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

def generate_inventory(outputs):
    """Generate Ansible inventory from Pulumi outputs"""
    inventory = defaultdict(list)
    
    # Process each output and organize by role
    for key, value in outputs.items():
        if key == "bastion_host_ip":
            inventory["bastion"].append({
                "host": value,
                "ansible_user": "ubuntu",
                "ansible_ssh_private_key_file": "~/.ssh/id_rsa"  # Adjust path as needed
            })
        elif key.startswith("db_master"):
            inventory["db_masters"].append({
                "host": value,
                "ansible_user": "ubuntu",
                "ansible_ssh_common_args": "-o ProxyCommand=\"ssh -W %h:%p -q ubuntu@" + outputs["bastion_host_ip"] + "\""
            })
        elif key.startswith("db_replica"):
            inventory["db_replicas"].append({
                "host": value,
                "ansible_user": "ubuntu",
                "ansible_ssh_common_args": "-o ProxyCommand=\"ssh -W %h:%p -q ubuntu@" + outputs["bastion_host_ip"] + "\""
            })
        elif key.startswith("redis_master"):
            inventory["redis_masters"].append({
                "host": value,
                "ansible_user": "ubuntu",
                "ansible_ssh_common_args": "-o ProxyCommand=\"ssh -W %h:%p -q ubuntu@" + outputs["bastion_host_ip"] + "\""
            })
        elif key.startswith("redis_replica"):
            inventory["redis_replicas"].append({
                "host": value,
                "ansible_user": "ubuntu",
                "ansible_ssh_common_args": "-o ProxyCommand=\"ssh -W %h:%p -q ubuntu@" + outputs["bastion_host_ip"] + "\""
            })
        elif key.startswith("redis_sentinel"):
            inventory["redis_sentinels"].append({
                "host": value,
                "ansible_user": "ubuntu",
                "ansible_ssh_common_args": "-o ProxyCommand=\"ssh -W %h:%p -q ubuntu@" + outputs["bastion_host_ip"] + "\""
            })
        elif key.startswith("backend_instance") and key.endswith("_ip"):
            inventory["backend_servers"].append({
                "host": value,
                "ansible_user": "ubuntu",
                "ansible_ssh_common_args": "-o ProxyCommand=\"ssh -W %h:%p -q ubuntu@" + outputs["bastion_host_ip"] + "\""
            })
        elif key.startswith("frontend_instance") and key.endswith("_ip") and not key.endswith("_private_ip"):
            inventory["frontend_servers"].append({
                "host": value,
                "ansible_user": "ubuntu",
                "ansible_ssh_common_args": "-o ProxyCommand=\"ssh -W %h:%p -q ubuntu@" + outputs["bastion_host_ip"] + "\""
            })
    
    # Create combined groups
    inventory["database_servers"] = inventory["db_masters"] + inventory["db_replicas"]
    inventory["redis_servers"] = inventory["redis_masters"] + inventory["redis_replicas"] + inventory["redis_sentinels"]
    inventory["app_servers"] = inventory["backend_servers"] + inventory["frontend_servers"]
    
    return inventory

def write_inventory_file(inventory, filename="inventory.yml"):
    """Write the inventory to a YAML file for Ansible"""
    # Create absolute path for the inventory file
    inventory_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ansible")
    os.makedirs(inventory_dir, exist_ok=True)  # Create directory if it doesn't exist
    inventory_path = os.path.join(inventory_dir, filename)
    
    with open(inventory_path, "w") as f:
        f.write("---\n")
        for group, hosts in inventory.items():
            f.write(f"{group}:\n")
            f.write("  hosts:\n")
            for i, host_data in enumerate(hosts):
                host = host_data.pop("host")
                f.write(f"    {group}-{i+1}:\n")
                f.write(f"      ansible_host: {host}\n")
                for key, value in host_data.items():
                    f.write(f"      {key}: {value}\n")
            f.write("\n")
    
    print(f"Inventory file created: {inventory_path}")

    
def main():
    outputs = get_pulumi_outputs()
    inventory = generate_inventory(outputs)
    write_inventory_file(inventory)

if __name__ == "__main__":
    main()
