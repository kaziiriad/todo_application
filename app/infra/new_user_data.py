import base64

def minimal_instance_user_data():
    """
    User data script for minimal instance
    """
    script = """#!/bin/bash
    # Update system
    sudo apt-get update
    # sudo apt-get upgrade -y
    
    # Install necessary packages
    sudo apt-get install -y python3-pip
    
    # Install AWS CLI
    pip3 install awscli --upgrade --user
    
    # Configure AWS CLI with IAM role
    aws configure set aws_access_key_id YOUR_ACCESS_KEY_ID
    aws configure set aws_secret_access_key YOUR_SECRET_ACCESS_KEY
    aws configure set default.region YOUR_REGION
    
    # # Create a simple Python script to test the setup
    # echo 'print("Hello, World!")' > hello.py
    
    # # Run the Python script
    # python3 hello.py
    """
    
    return base64.b64encode(script.encode()).decode()