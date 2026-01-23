#!/bin/bash

# Ensure script stops on command failure (optional, recommended)
set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}--- Starting OAI Deployment Sequence ---${NC}"

# Step 1: Deploy CU
echo -e "${GREEN}[1/3] Entering oai-cu and installing...${NC}"
cd /home/johnson/O2-Automation-Engine/oai-cn5g-fed/charts/oai-5g-ran/oai-cu
helm install oai-cu . -n johnson-ns

# Step 2: Deploy DU
echo -e "${GREEN}[2/3] Entering oai-du and installing...${NC}"
cd /home/johnson/O2-Automation-Engine/oai-cn5g-fed/charts/oai-5g-ran/oai-du
helm install oai-du . -n johnson-ns
sleep 8

# Step 3: Deploy UE
echo -e "${GREEN}[3/3] Entering oai-nr-ue-1 and installing...${NC}"
cd /home/johnson/O2-Automation-Engine/oai-cn5g-fed/charts/oai-5g-ran/oai-nr-ue-open5gs-1
helm install oai-ue-1 . -n johnson-ns
sleep 1

echo -e "${BLUE}[3/3] Entering oai-nr-ue-2 and installing...${NC}"
cd /home/johnson/O2-Automation-Engine/oai-cn5g-fed/charts/oai-5g-ran/oai-nr-ue-open5gs-2
helm install oai-ue-2 . -n johnson-ns
sleep 1


# Return to home directory
cd ~
echo -e "${CYAN}--- All installation commands completed ---${NC}"
