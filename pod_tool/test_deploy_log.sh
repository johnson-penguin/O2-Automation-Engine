#!/bin/bash

# Ensure script stops on command failure (optional, recommended)
set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

# Deploy OAI Components
echo -e "${YELLOW}--- Deploying OAI Components ---${NC}"

# Deploy CU
echo -e "${GREEN}[1/3] Entering oai-cu and installing...${NC}"
helm install oai-cu /home/johnson/O2-Automation-Engine/charts/oai-5g-ran/oai-cu -n johnson-ns
sleep 10

# Deploy DU
echo -e "${GREEN}[2/3] Entering oai-du and installing...${NC}"
helm install oai-du /home/johnson/O2-Automation-Engine/charts/oai-5g-ran/oai-du -n johnson-ns
sleep 10

# Deploy UE
echo -e "${GREEN}[3/3] Entering oai-ue and installing...${NC}"
helm install oai-ue /home/johnson/O2-Automation-Engine/charts/oai-5g-ran/oai-nr-ue -n johnson-ns



