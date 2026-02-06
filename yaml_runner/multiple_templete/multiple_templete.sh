#!/bin/bash

# --- Configuration ---
CHART_ROOT="/home/johnson/O2-Automation-Engine/Mutated_Configuration_Generator/charts/oai-5g-ran"
# Mutation test case source
TEST_CASE_DIR="/home/johnson/O2-Automation-Engine/yaml_runner/multiple_templete/multiple_templete_yaml"
# Standard configuration source
STD_VAL_DIR="/home/johnson/O2-Automation-Engine/Mutated_Configuration_Generator/workable_yaml"
# Log storage path
BASE_LOG_DIR="/home/johnson/O2-Automation-Engine/yaml_runner/multiple_templete/multiple_templete_output/$(date +%Y%m%d_%H%M%S)"

NAMESPACE="johnson-ns"

# Define standard configuration file names
STD_CU="$STD_VAL_DIR/cu_values.yaml"
STD_DU="$STD_VAL_DIR/du_values.yaml"
STD_UE="$STD_VAL_DIR/ue_values.yaml"

# Colors and styles
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

mkdir -p "$BASE_LOG_DIR"

# Environment cleanup function
cleanup() {
    echo -e "${YELLOW}>> Executing environment cleanup and reset...${NC}"
    helm uninstall oai-cu oai-du oai-nr-ue -n $NAMESPACE 2>/dev/null || true
    kill $STERN_CU_PID $STERN_DU_PID $STERN_UE_PID 2>/dev/null || true
    pkill -9 stern 2>/dev/null || true
    sleep 5
}

# Get all mutation test files
TEST_FILES=($(ls "$TEST_CASE_DIR"/*.yaml))
TOTAL_CASES=${#TEST_FILES[@]}
CURRENT_COUNT=0

echo -e "${GREEN}Detected $TOTAL_CASES test cases. Logs will be stored at: $BASE_LOG_DIR${NC}"



for CASE_FILE in "${TEST_FILES[@]}"; do
    ((CURRENT_COUNT++))
    FILENAME=$(basename "$CASE_FILE")
    CURRENT_CASE="${FILENAME%.*}"
    CASE_LOG_DIR="$BASE_LOG_DIR/$CURRENT_CASE"
    
    mkdir -p "$CASE_LOG_DIR/logs"
    mkdir -p "$CASE_LOG_DIR/conf"

    # Initialize configuration: Use all files from Standard path by default
    target_cu=$STD_CU
    target_du=$STD_DU
    target_ue=$STD_UE
    subject="Unknown"

    # Dynamic determination logic: If test filename matches component name, replace that component with mutated version
    if [[ "$FILENAME" == oai-cu* ]]; then
        target_cu="$CASE_FILE"
        subject="CU (Mutated)"
        cp "$target_cu" "$CASE_LOG_DIR/conf/mutated_cu.yaml"
        cp "$target_du" "$CASE_LOG_DIR/conf/default_du.yaml"
        cp "$target_ue" "$CASE_LOG_DIR/conf/default_ue.yaml"
    elif [[ "$FILENAME" == oai-du* ]]; then
        target_du="$CASE_FILE"
        subject="DU (Mutated)"
        cp "$target_cu" "$CASE_LOG_DIR/conf/default_cu.yaml"
        cp "$target_du" "$CASE_LOG_DIR/conf/mutated_du.yaml"
        cp "$target_ue" "$CASE_LOG_DIR/conf/default_ue.yaml"
    fi



    # --- Display current execution combination and progress ---
    echo -e "\n${CYAN}================================================================${NC}"
    echo -e "${GREEN}[Progress: $CURRENT_COUNT / $TOTAL_CASES]${NC}"
    echo -e "${YELLOW}CASE ID:${NC} $CURRENT_CASE"
    echo -e "${CYAN}----------------------------------------------------------------${NC}"
    printf "  %-10s | %-45s\n" "${BLUE}Component${NC}" "${BLUE}Source Path${NC}"
    echo -e "  ----------|-----------------------------------------------------"
    printf "  OAI-CU     | %-35s %b\n" "$(basename "$target_cu")" "$([[ "$subject" == *"CU"* ]] && echo -e "${RED}<<< TARGET${NC}")"
    printf "  OAI-DU     | %-35s %b\n" "$(basename "$target_du")" "$([[ "$subject" == *"DU"* ]] && echo -e "${RED}<<< TARGET${NC}")"
    printf "  OAI-UE     | %-35s\n" "$(basename "$target_ue")"
    echo -e "${CYAN}================================================================${NC}"

    # 1. Start background Stern log monitoring
    # Use sed to filter noise for CU/DU, while UE logs everything
    stern "oai-cu" -n $NAMESPACE --output raw > "$CASE_LOG_DIR/logs/cu.log" 2>/dev/null &
    STERN_CU_PID=$!
    stern "oai-du" -n $NAMESPACE --output raw > "$CASE_LOG_DIR/logs/du.log" 2>/dev/null &
    STERN_DU_PID=$!
    stern "oai-nr-ue" -n $NAMESPACE --output raw > "$CASE_LOG_DIR/logs/ue.log" 2>/dev/null &
    STERN_UE_PID=$!

    # 2. Deployment process (fixed wait time to capture error states)
    echo -e "${BLUE}Deploying CU (Waiting 10s)...${NC}"
    helm install oai-cu "$CHART_ROOT/oai-cu" -n $NAMESPACE -f "$target_cu"
    sleep 10

    echo -e "${BLUE}Deploying DU (Waiting 20s)...${NC}"
    helm install oai-du "$CHART_ROOT/oai-du" -n $NAMESPACE -f "$target_du"
    sleep 20

    echo -e "${BLUE}Deploying UE (Waiting 20s)...${NC}"
    helm install oai-nr-ue "$CHART_ROOT/oai-nr-ue" -n $NAMESPACE -f "$target_ue"
    sleep 20

    # 3. Cleanup and prepare for next round
    cleanup
    sleep 1
done

echo -e "\n${GREEN}✔ All $TOTAL_CASES test cases completed!${NC}"
echo -e "${GREEN}Total log path: $BASE_LOG_DIR${NC}"