#!/bin/bash
# Script to test SSH connections through the bastion host

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KEY_PATH="$HOME/.ssh/MyKeyPair.pem"
BASTION_IP="47.128.246.148"  # Update with your bastion IP

echo -e "${YELLOW}Testing SSH connections through bastion host...${NC}"
echo -e "${YELLOW}Using key: $KEY_PATH${NC}"
echo -e "${YELLOW}Bastion IP: $BASTION_IP${NC}"

# Test direct connection to bastion
echo -e "${YELLOW}Testing direct connection to bastion...${NC}"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=5 ubuntu@$BASTION_IP "echo 'Successfully connected to bastion!'; hostname; id"

# Test connection to a private instance through bastion
echo -e "${YELLOW}Testing connection to a private instance through bastion...${NC}"
PRIVATE_IP="10.0.2.181"  # Update with one of your private instance IPs
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o ProxyCommand="ssh -i $KEY_PATH -o StrictHostKeyChecking=no -W %h:%p ubuntu@$BASTION_IP" ubuntu@$PRIVATE_IP "echo 'Successfully connected to private instance!'; hostname; id" || echo -e "${RED}Failed to connect to private instance${NC}"

# Test SSH configuration on bastion
echo -e "${YELLOW}Testing SSH configuration on bastion...${NC}"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ubuntu@$BASTION_IP "ls -la ~/.ssh/; cat ~/.ssh/id_rsa.pub || echo 'No public key found'"

# Check if bastion can connect to private instances
echo -e "${YELLOW}Testing if bastion can connect to private instances...${NC}"
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ubuntu@$BASTION_IP "ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 ubuntu@$PRIVATE_IP 'echo Successfully connected from bastion to private instance!; hostname' || echo 'Failed to connect from bastion to private instance'"

echo -e "${GREEN}SSH connection tests completed!${NC}"