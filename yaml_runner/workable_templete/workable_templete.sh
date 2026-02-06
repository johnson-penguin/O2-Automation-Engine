#!/bin/bash

# --- Configuration ---
QUIET_MODE=true  
CHART_ROOT="/home/johnson/O2-Automation-Engine/Mutated_Configuration_Generator/charts/oai-5g-ran"
VALUES_DIR="/home/johnson/O2-Automation-Engine/Mutated_Configuration_Generator/workable_yaml"
NAMESPACE="johnson-ns"
LOG_DIR="./workable_templete_logs/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

# ----------------




set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

pkill -9 stern || true


trap "kill $STERN_CU_PID $STERN_DU_PID $STERN_UE_PID 2>/dev/null || true" EXIT

# Define a monitoring function to handle the switch logic
wait_for_log() {
    local label=$1
    local keyword=$2
    if [ "$QUIET_MODE" = true ]; then
        # Quiet mode: redirect stern output to a black hole, relying only on grep to determine
        (stern -l "$label" -n $NAMESPACE --tail 0 --output raw | grep -m 1 "$keyword") > /dev/null
    else
        # Display mode: directly output to the screen
        (stern -l "$label" -n $NAMESPACE --tail 0 --output raw | grep -m 1 "$keyword")
    fi
}
# 1. Start background continuous archiving (fix Label to ensure UE can be captured)
echo -e "${CYAN}--- Starting Stern Log Capture ---${NC}"
# Use name matching, which is the most reliable
# stern "oai-cu" -c "cu" -n $NAMESPACE --output raw > "$LOG_DIR/cu.log" 2>/dev/null &
stern "oai-cu" -c "cu" -n $NAMESPACE --output raw | sed -n '/Starting gNB soft modem/,$p' > "$LOG_DIR/cu.log" 2>/dev/null &
STERN_CU_PID=$!
# stern "oai-du" -c "du" -n $NAMESPACE --output raw > "$LOG_DIR/du.log" 2>/dev/null &
stern "oai-du" -c "du" -n $NAMESPACE --output raw | sed -n '/Starting gNB soft modem/,$p' > "$LOG_DIR/du.log" 2>/dev/null &
STERN_DU_PID=$!
stern "oai-nr-ue" -n $NAMESPACE --output raw > "$LOG_DIR/ue.log" 2>/dev/null &
STERN_UE_PID=$!


# 1. Deploy CU
echo -e "${YELLOW}--- Deploying CU ---${NC}"
helm install oai-cu $CHART_ROOT/oai-cu -n $NAMESPACE -f $VALUES_DIR/cu_values.yaml

echo -e "${BLUE}Waiting for CU GTPU instance...${NC}"
wait_for_log "app=oai-cu" "Created gtpu instance id"
echo -e "${GREEN}✔ CU GTPU is Ready.${NC}"

# 2. Deploy DU
echo -e "${YELLOW}--- Deploying DU ---${NC}"
helm install oai-du $CHART_ROOT/oai-du -n $NAMESPACE -f $VALUES_DIR/du_values.yaml
echo -e "${BLUE}Waiting for DU Frame.Slot synchronization...${NC}"
wait_for_log "app=oai-du" "\[NR_MAC\] I Frame.Slot"
echo -e "${GREEN}✔ DU Synchronization detected.${NC}"



# 3. Deploy UE
echo -e "${YELLOW}--- Deploying UE ---${NC}"
helm install oai-nr-ue $CHART_ROOT/oai-nr-ue -n $NAMESPACE -f $VALUES_DIR/ue_values.yaml

echo -e "${BLUE}System is UP. Collecting logs for 20s...${NC}"
sleep 10

# 4. Uninstall
echo -e "${YELLOW}--- Uninstalling ---${NC}"
helm uninstall oai-cu -n $NAMESPACE
helm uninstall oai-du -n $NAMESPACE
helm uninstall oai-nr-ue -n $NAMESPACE
sleep 2

echo -e "${GREEN}Test completed. Logs are saved in: $LOG_DIR${NC}"