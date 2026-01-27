#!/bin/bash

# --- 參數設定 ---
QUIET_MODE=true  # 設定為 true 則隱藏監控時的 Log 輸出，false 則顯示
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

# 定義一個監控函數來處理開關邏輯
wait_for_log() {
    local label=$1
    local keyword=$2
    if [ "$QUIET_MODE" = true ]; then
        # 安靜模式：將 stern 輸出導向黑洞，僅靠 grep 判斷
        (stern -l "$label" -n johnson-ns --tail 0 --output raw | grep -m 1 "$keyword") > /dev/null
    else
        # 顯示模式：直接輸出到螢幕
        (stern -l "$label" -n johnson-ns --tail 0 --output raw | grep -m 1 "$keyword")
    fi
}
# 1. 啟動背景持續存檔 (修正 Label 確保 UE 抓得到)
echo -e "${CYAN}--- Starting Stern Log Capture ---${NC}"
# 使用名稱包含匹配，最保險
stern "oai-cu" -n johnson-ns --output raw > "$LOG_DIR/cu.log" &
STERN_CU_PID=$!
stern "oai-du" -n johnson-ns --output raw > "$LOG_DIR/du.log" &
STERN_DU_PID=$!
stern "oai-nr-ue" -n johnson-ns --output raw > "$LOG_DIR/ue.log" &
STERN_UE_PID=$!


# 1. Deploy CU
echo -e "${YELLOW}--- Deploying CU ---${NC}"
helm install oai-cu /home/johnson/O2-Automation-Engine/charts/oai-5g-ran/oai-cu -n johnson-ns

echo -e "${BLUE}Waiting for CU GTPU instance...${NC}"
wait_for_log "app=oai-cu" "Created gtpu instance id"
echo -e "${GREEN}✔ CU GTPU is Ready.${NC}"

# 2. Deploy DU
echo -e "${YELLOW}--- Deploying DU ---${NC}"
helm install oai-du /home/johnson/O2-Automation-Engine/charts/oai-5g-ran/oai-du -n johnson-ns

echo -e "${BLUE}Waiting for DU Frame.Slot synchronization...${NC}"
wait_for_log "app=oai-du" "\[NR_MAC\] I Frame.Slot 128.0"
echo -e "${GREEN}✔ DU Synchronization detected.${NC}"



# 3. Deploy UE
echo -e "${YELLOW}--- Deploying UE ---${NC}"
helm install oai-nr-ue /home/johnson/O2-Automation-Engine/charts/oai-5g-ran/oai-nr-ue -n johnson-ns

echo -e "${BLUE}System is UP. Collecting logs for 20s...${NC}"
sleep 10

# 4. Uninstall
echo -e "${YELLOW}--- Uninstalling ---${NC}"
helm uninstall oai-cu -n johnson-ns
helm uninstall oai-du -n johnson-ns
helm uninstall oai-nr-ue -n johnson-ns

echo -e "${GREEN}Test completed. Logs are saved in: $LOG_DIR${NC}"