#!/bin/bash
# Deployment script for the application

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
INFRA_DIR="$PROJECT_ROOT/infra"
DEPLOY_DIR="$PROJECT_ROOT/deploy"
ANSIBLE_DIR="$DEPLOY_DIR/ansible"
INVENTORY_DIR="$ANSIBLE_DIR/inventory"
PLAYBOOKS_DIR="$ANSIBLE_DIR/playbooks"

echo -e "${YELLOW}Starting deployment process...${NC}"
echo -e "${YELLOW}Script directory: $SCRIPT_DIR${NC}"
echo -e "${YELLOW}Project root: $PROJECT_ROOT${NC}"
echo -e "${YELLOW}Infrastructure directory: $INFRA_DIR${NC}"

# Step 1: Fix SSH key permissions by copying to Linux filesystem
echo -e "${YELLOW}Fixing SSH key permissions...${NC}"
ORIGINAL_KEY_PATH="$DEPLOY_DIR/MyKeyPair.pem"  # Key is now in deploy directory
LINUX_KEY_PATH="$HOME/.ssh/MyKeyPair.pem"

if [ -f "$ORIGINAL_KEY_PATH" ]; then
    echo -e "${YELLOW}Found key at $ORIGINAL_KEY_PATH${NC}"
    echo -e "${YELLOW}Copying key to $LINUX_KEY_PATH to fix WSL permission issues${NC}"
    
    # Create .ssh directory if it doesn't exist
    mkdir -p "$HOME/.ssh"
    
    # Copy the key to Linux filesystem
    cp "$ORIGINAL_KEY_PATH" "$LINUX_KEY_PATH"
    
    # Set proper permissions on the Linux filesystem
    chmod 600 "$LINUX_KEY_PATH"
    
    # Use the Linux path for SSH
    KEY_PATH="$LINUX_KEY_PATH"
    echo -e "${GREEN}Fixed permissions for $KEY_PATH${NC}"
else
    echo -e "${YELLOW}Warning: MyKeyPair.pem not found at $ORIGINAL_KEY_PATH${NC}"
    # Try to find the key in common locations
    possible_locations=(
        "$SCRIPT_DIR/MyKeyPair.pem"  # Also check in the script directory itself
        "$PROJECT_ROOT/MyKeyPair.pem"
        "$HOME/MyKeyPair.pem"
        "$HOME/.ssh/MyKeyPair.pem"
    )
    
    for location in "${possible_locations[@]}"; do
        if [ -f "$location" ]; then
            echo -e "${YELLOW}Found key at $location${NC}"
            
            # If the key is already in the Linux filesystem
            if [[ "$location" == "$HOME/.ssh/"* ]]; then
                chmod 600 "$location"
                KEY_PATH="$location"
                echo -e "${GREEN}Fixed permissions for $KEY_PATH${NC}"
            else
                # Copy to Linux filesystem
                cp "$location" "$LINUX_KEY_PATH"
                chmod 600 "$LINUX_KEY_PATH"
                KEY_PATH="$LINUX_KEY_PATH"
                echo -e "${GREEN}Copied key to $KEY_PATH and fixed permissions${NC}"
            fi
            break
        fi
    done
fi

if [ ! -f "$KEY_PATH" ]; then
    echo -e "${RED}Could not find SSH key file. Please specify the correct path.${NC}"
    exit 1
fi

# Verify permissions
ls -la "$KEY_PATH"

# Step 2: Deploy infrastructure with Pulumi
echo -e "${YELLOW}Deploying infrastructure with Pulumi...${NC}"
cd "$INFRA_DIR"

# Check if Pulumi stack exists, if not create it
pulumi stack ls | grep -q "dev" || pulumi stack init dev

pulumi stack select dev
pulumi up --yes

if [ $? -ne 0 ]; then
    echo -e "${RED}Pulumi deployment failed. Exiting.${NC}"
    exit 1
fi

echo -e "${GREEN}Infrastructure deployed successfully!${NC}"

# Step 3: Generate Ansible inventory
echo -e "${YELLOW}Generating Ansible inventory...${NC}"
cd "$DEPLOY_DIR"
python3 generate_ansible_inventory.py

if [ $? -ne 0 ]; then
    echo -e "${RED}Ansible inventory generation failed. Exiting.${NC}"
    exit 1
fi

echo -e "${GREEN}Ansible inventory generated successfully!${NC}"

# Step 4: Get the bastion IP from Pulumi outputs
echo -e "${YELLOW}Getting bastion IP from Pulumi outputs...${NC}"
cd "$INFRA_DIR"
BASTION_IP=$(pulumi stack output bastion_host_ip)

if [ -z "$BASTION_IP" ]; then
    echo -e "${RED}Could not get bastion IP from Pulumi outputs. Exiting.${NC}"
    exit 1
fi

echo -e "${GREEN}Bastion IP: $BASTION_IP${NC}"

# Step 5: Update inventory files with correct key path and bastion IP
echo -e "${YELLOW}Updating inventory files with correct key path and bastion IP...${NC}"

# Create inventory directory if it doesn't exist
mkdir -p "$INVENTORY_DIR"

# Update all inventory files
for inventory_file in "$INVENTORY_DIR"/*.yml; do
    if [ -f "$inventory_file" ]; then
        # Update SSH key path
        sed -i "s|ansible_ssh_private_key_file:.*|ansible_ssh_private_key_file: $KEY_PATH|g" "$inventory_file"
        
        # Update bastion IP in ProxyCommand
        sed -i "s|ubuntu@[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}|ubuntu@$BASTION_IP|g" "$inventory_file"
        
        # Add SSH timeout and connection settings
        sed -i '/ansible_ssh_common_args/s/"ssh -W %h:%p -q/"ssh -o ConnectTimeout=30 -o ConnectionAttempts=5 -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -W %h:%p -q/g' "$inventory_file"
        
        echo -e "${GREEN}Updated inventory file $inventory_file with key path: $KEY_PATH and bastion IP: $BASTION_IP${NC}"
    fi
done

# Step 6: Wait for instances to be fully initialized
echo -e "${YELLOW}Waiting for instances to initialize (3 minutes)...${NC}"
echo -e "${YELLOW}This longer wait time ensures SSH services are fully started...${NC}"
sleep 180

# Step 7: Test SSH connection to bastion host
echo -e "${YELLOW}Testing SSH connection to bastion host...${NC}"
echo -e "${YELLOW}Bastion IP: $BASTION_IP${NC}"
echo -e "${YELLOW}Attempting to connect to bastion host...${NC}"

# Try to connect to the bastion host with a timeout
timeout 10 ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=5 ubuntu@$BASTION_IP exit 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Successfully connected to bastion host!${NC}"
else
    echo -e "${YELLOW}Could not connect to bastion host yet. Waiting another minute...${NC}"
    sleep 60
    
    # Try again
    timeout 10 ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=5 ubuntu@$BASTION_IP exit 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Successfully connected to bastion host!${NC}"
    else
        echo -e "${RED}Could not connect to bastion host. Please check your AWS console to ensure the instance is running and accessible.${NC}"
        echo -e "${YELLOW}Continuing anyway, but Ansible might fail...${NC}"
    fi
fi

# Step 8: Copy SSH key to bastion host for internal connections
echo -e "${YELLOW}Copying SSH key to bastion host for internal connections...${NC}"
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$KEY_PATH" ubuntu@$BASTION_IP:/home/ubuntu/.ssh/id_rsa

# Set proper permissions on the key
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ubuntu@$BASTION_IP "chmod 600 /home/ubuntu/.ssh/id_rsa"

# Generate public key from private key
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ubuntu@$BASTION_IP "ssh-keygen -y -f /home/ubuntu/.ssh/id_rsa > /home/ubuntu/.ssh/id_rsa.pub"

echo -e "${GREEN}SSH key copied to bastion host!${NC}"

# Step 9: Deploy components one by one with error handling
cd "$ANSIBLE_DIR"

# Function to run a playbook with proper error handling
run_playbook() {
    local playbook=$1
    local component=$2
    
    echo -e "${YELLOW}Deploying $component...${NC}"
    
    # First try to ping the hosts to verify connectivity
    echo -e "${YELLOW}Testing connectivity to $component hosts...${NC}"
    ansible -i "$INVENTORY_DIR" -m ping $component -vv || true
    
    # Run the playbook
    echo -e "${YELLOW}Running $playbook playbook...${NC}"
    ansible-playbook -i "$INVENTORY_DIR" "$playbook" --limit $component -vv
    
    local result=$?
    if [ $result -eq 0 ]; then
        echo -e "${GREEN}Successfully deployed $component!${NC}"
        return 0
    else
        echo -e "${RED}Failed to deploy $component. Error code: $result${NC}"
        return $result
    fi
}

# Deploy bastion first
run_playbook "playbooks/bastion.yml" "bastion"
if [ $? -ne 0 ]; then
    echo -e "${RED}Bastion deployment failed. Cannot continue without bastion host.${NC}"
    exit 1
fi

# Deploy database servers
run_playbook "playbooks/database.yml" "database_servers" || true

# Deploy Redis servers
run_playbook "playbooks/redis.yml" "redis_servers" || true

# Deploy backend servers
run_playbook "playbooks/backend.yml" "backend_servers" || true

# Deploy frontend servers
run_playbook "playbooks/frontend.yml" "frontend_servers" || true

# Step 10: Try to run the master playbook for any remaining configurations
echo -e "${YELLOW}Running master playbook to ensure all configurations are applied...${NC}"
ansible-playbook -i "$INVENTORY_DIR" "site.yml" -vv || true

# Step 11: Get the frontend URLs
echo -e "${YELLOW}Retrieving frontend URLs...${NC}"
cd "$INFRA_DIR"
FRONTEND_IPS=$(pulumi stack output | grep frontend_instance | grep public_ip | awk '{print $2}')

echo -e "${GREEN}Deployment completed!${NC}"
echo -e "${YELLOW}Your application is now available at:${NC}"
for ip in $FRONTEND_IPS; do
    echo -e "${GREEN}http://$ip${NC}"
done

echo -e "${YELLOW}Note: It may take a few minutes for all services to start up completely.${NC}"

# Provide instructions for individual component deployment
echo -e "${YELLOW}To deploy individual components, use:${NC}"
echo -e "${GREEN}cd $ANSIBLE_DIR${NC}"
echo -e "${GREEN}ansible-playbook -i inventory playbooks/bastion.yml # For bastion host${NC}"
echo -e "${GREEN}ansible-playbook -i inventory playbooks/database.yml # For database servers${NC}"
echo -e "${GREEN}ansible-playbook -i inventory playbooks/redis.yml # For Redis servers${NC}"
echo -e "${GREEN}ansible-playbook -i inventory playbooks/backend.yml # For backend servers${NC}"
echo -e "${GREEN}ansible-playbook -i inventory playbooks/frontend.yml # For frontend servers${NC}"
