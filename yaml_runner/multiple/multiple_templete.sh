#!/bin/bash

# --- Configuration ---
# 1. 定義路徑變數
YAML_INPUT_DIR="/home/johnson/O2-Automation-Engine/yaml_runner/multiple/multiple_templete_yaml"
CHARTS_BASE="/home/johnson/O2-Automation-Engine/charts/oai-5g-ran"
WORKABLE_YAML_DIR="/home/johnson/O2-Automation-Engine/workable_yaml"
LOG_BASE_DIR="/home/johnson/O2-Automation-Engine/yaml_runner/multiple/multiple_templete_logs"
NAMESPACE="johnson-ns"

# 確保基礎 Log 目錄存在
mkdir -p "$LOG_BASE_DIR"

# 設定全域變數
QUIET_MODE=true
# ----------------

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# 清理舊的 stern (保險起見)
pkill -9 stern || true

# --- Functions ---

# 定義監控函數 (與之前相同)
wait_for_log() {
    local label=$1
    local keyword=$2
    if [ "$QUIET_MODE" = true ]; then
        (stern -l "$label" -n $NAMESPACE --tail 0 --output raw | grep -m 1 "$keyword") > /dev/null
    else
        (stern -l "$label" -n $NAMESPACE --tail 0 --output raw | grep -m 1 "$keyword")
    fi
}

# 定義卸載函數
uninstall_all() {
    echo -e "${YELLOW}--- Uninstalling All Components ---${NC}"
    helm uninstall oai-cu -n $NAMESPACE 2>/dev/null || true
    helm uninstall oai-du -n $NAMESPACE 2>/dev/null || true
    helm uninstall oai-nr-ue -n $NAMESPACE 2>/dev/null || true
    # 等待 Pod 完全終止，避免影響下一個 Case
    echo -e "${BLUE}Waiting for pods to terminate...${NC}"
    sleep 5
}

# --- Main Loop ---

# 檢查是否有檔案，並按自然順序排序 (case_1, case_2, ... case_10)
count=$(ls -1 "$YAML_INPUT_DIR"/oai-du_case_*.yaml 2>/dev/null | wc -l)
if [ "$count" -eq 0 ]; then
    echo -e "${RED}Error: No yaml files found in $YAML_INPUT_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}Found $count test cases. Starting automation...${NC}"

# 使用 find 和 sort -V 進行自然排序迭代
find "$YAML_INPUT_DIR" -name "oai-du_case_*.yaml" | sort -V | while read DU_YAML_FILE; do
    
    # 提取檔名作為 Case ID (例如: oai-du_case_1)
    CASE_NAME=$(basename "$DU_YAML_FILE" .yaml)
    
    # 建立該 Case 的 Log 資料夾
    CURRENT_LOG_DIR="$LOG_BASE_DIR/${CASE_NAME}_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$CURRENT_LOG_DIR"

    echo -e "\n=================================================="
    echo -e "${GREEN}Running Test Case: $CASE_NAME${NC}"
    echo -e "Config: $DU_YAML_FILE"
    echo -e "Logs:   $CURRENT_LOG_DIR"
    echo -e "=================================================="

    # 0. 啟動 Log 收集 (針對當前 Case)
    echo -e "${CYAN}--- Starting Stern Log Capture ---${NC}"
    
    stern "oai-cu" -c "cu" -n $NAMESPACE --output raw | sed -n '/Starting gNB soft modem/,$p' > "$CURRENT_LOG_DIR/cu.log" 2>/dev/null &
    PID_CU=$!
    
    stern "oai-du" -c "du" -n $NAMESPACE --output raw | sed -n '/Starting gNB soft modem/,$p' > "$CURRENT_LOG_DIR/du.log" 2>/dev/null &
    PID_DU=$!
    
    stern "oai-nr-ue" -n $NAMESPACE --output raw > "$CURRENT_LOG_DIR/ue.log" 2>/dev/null &
    PID_UE=$!

    # 1. 部署 CU (固定使用 workable_yaml 下的設定)
    echo -e "${YELLOW}--- Deploying Default CU ---${NC}"
    helm install oai-cu "$CHARTS_BASE/oai-cu" -n $NAMESPACE -f "$WORKABLE_YAML_DIR/cu_values.yaml"

    echo -e "${BLUE}Waiting for CU GTPU instance...${NC}"
    wait_for_log "app=oai-cu" "Created gtpu instance id"
    echo -e "${GREEN}✔ CU Ready.${NC}"

    # 2. 部署 DU (使用 Loop 當前的 Case YAML)
    echo -e "${YELLOW}--- Deploying DU ($CASE_NAME) ---${NC}"
    helm install oai-du "$CHARTS_BASE/oai-du" -n $NAMESPACE -f "$DU_YAML_FILE"

    echo -e "${BLUE}Waiting for DU Synchronization...${NC}"
    # 加入一個超時機制或錯誤處理通常比較好，但這裡維持原邏輯
    wait_for_log "app=oai-du" "\[NR_MAC\] I Frame.Slot"
    echo -e "${GREEN}✔ DU Ready.${NC}"

    # 3. 部署 UE (固定使用 workable_yaml 下的設定)
    echo -e "${YELLOW}--- Deploying Default UE ---${NC}"
    helm install oai-nr-ue "$CHARTS_BASE/oai-nr-ue" -n $NAMESPACE -f "$WORKABLE_YAML_DIR/ue_values.yaml"

    echo -e "${BLUE}System UP. Collecting logs for 20s...${NC}"
    sleep 20

    # 4. 清理環境
    uninstall_all

    # 5. 停止當前的 Log 收集程序
    kill $PID_CU $PID_DU $PID_UE 2>/dev/null || true
    
    echo -e "${GREEN}Case $CASE_NAME Completed.${NC}"
    sleep 2 # 稍微緩衝，讓 namespace 乾淨
done

echo -e "\n${GREEN}All test cases finished successfully!${NC}"