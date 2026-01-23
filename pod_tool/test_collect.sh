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

# Wait for pods to be ready and collect logs
echo -e "${YELLOW}--- Waiting for pods to be ready before collecting logs ---${NC}"
sleep 5

# Create log directory with timestamp
LOG_DIR="/home/johnson/O2-Automation-Engine/test_log"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p "${LOG_DIR}"

echo -e "${GREEN}Collecting pod logs to ${LOG_DIR}...${NC}"

# Function to collect logs for a pod
collect_pod_logs() {
    local APP_LABEL=$1
    local INSTANCE_LABEL=$2
    local LOG_PREFIX=$3
    
    echo -e "${BLUE}  Collecting logs for ${LOG_PREFIX}...${NC}"
    POD_NAME=$(kubectl get pods -n johnson-ns -l "app.kubernetes.io/name=${APP_LABEL},app.kubernetes.io/instance=${INSTANCE_LABEL}" -o jsonpath="{.items[0].metadata.name}" 2>/dev/null)
    
    if [ -n "$POD_NAME" ]; then
        kubectl logs -n johnson-ns "$POD_NAME" > "${LOG_DIR}/${LOG_PREFIX}_${TIMESTAMP}.log" 2>&1
        echo -e "${GREEN    }    ✓ Saved to ${LOG_PREFIX}_${TIMESTAMP}.log${NC}"
    else
        echo -e "${YELLOW}    ⚠ Pod not found for ${LOG_PREFIX}${NC}"
    fi
}

# Collect logs for all deployed pods
collect_pod_logs "oai-cu" "oai-cu" "oai-cu"
collect_pod_logs "oai-du" "oai-du" "oai-du"
collect_pod_logs "oai-nr-ue-5gs-1" "oai-ue-1" "oai-ue-1"
collect_pod_logs "oai-nr-ue-5gs-2" "oai-ue-2" "oai-ue-2"

echo -e "${CYAN}--- Log collection completed ---${NC}"
echo -e "Logs saved in: ${LOG_DIR}"
