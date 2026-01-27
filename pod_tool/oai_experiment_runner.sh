#!/bin/bash

# --- Configuration ---
QUIET_MODE=true  # Set to true to hide Stern log output, false to show
# ----------------

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

LOG_DIR="./logs/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"



trap "kill $STERN_CU_PID $STERN_DU_PID $STERN_UE_PID 2>/dev/null || true" EXIT

# 1. Execute Helm Install
echo -e "${CYAN}--- Starting Stern Log Capture ---${NC}"
stern "oai-cu" -n johnson-ns --output raw > "$LOG_DIR/cu.log" &
STERN_CU_PID=$!
stern "oai-du" -n johnson-ns --output raw > "$LOG_DIR/du.log" &
STERN_DU_PID=$!
stern "oai-nr-ue" -n johnson-ns --output raw > "$LOG_DIR/ue.log" &
STERN_UE_PID=$!


# 1. Deploy CU
echo -e "${YELLOW}--- Deploying CU ---${NC}"
helm install oai-cu /home/johnson/O2-Automation-Engine/charts/oai-5g-ran/oai-cu -n johnson-ns
sleep 10

# 2. Deploy DU
echo -e "${YELLOW}--- Deploying DU ---${NC}"
helm install oai-du /home/johnson/O2-Automation-Engine/charts/oai-5g-ran/oai-du -n johnson-ns
sleep 15



# 3. Deploy UE
echo -e "${YELLOW}--- Deploying UE ---${NC}"
helm install oai-nr-ue /home/johnson/O2-Automation-Engine/charts/oai-5g-ran/oai-nr-ue -n johnson-ns
sleep 10

# 4. Uninstall
echo -e "${YELLOW}--- Uninstalling ---${NC}"
helm uninstall oai-cu -n johnson-ns
helm uninstall oai-du -n johnson-ns
helm uninstall oai-nr-ue -n johnson-ns

echo -e "${GREEN}Test completed. Logs are saved in: $LOG_DIR${NC}"