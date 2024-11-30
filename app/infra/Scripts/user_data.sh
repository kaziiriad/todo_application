#!/bin/bash

sudo apt update
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker $USER
