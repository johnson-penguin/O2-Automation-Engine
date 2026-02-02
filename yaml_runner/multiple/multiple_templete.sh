#!/bin/bash

# --- 路徑配置 ---
CHART_ROOT="/home/johnson/O2-Automation-Engine/Mutated Configuration Generator/charts/oai-5g-ran"
# 變異測試案來源
TEST_CASE_DIR="/home/johnson/O2-Automation-Engine/yaml_runner/multiple/multiple_templete_yaml"
# 標準配置來源
STD_VAL_DIR="/home/johnson/O2-Automation-Engine/Mutated Configuration Generator/workable_yaml"
# 日誌存儲路徑
BASE_LOG_DIR="/home/johnson/O2-Automation-Engine/yaml_runner/multiple/multiple_templete_logs/$(date +%Y%m%d_%H%M%S)"

NAMESPACE="johnson-ns"

# 定義標準配置檔案名
STD_CU="$STD_VAL_DIR/cu_values.yaml"
STD_DU="$STD_VAL_DIR/du_values.yaml"
STD_UE="$STD_VAL_DIR/ue_values.yaml"

# 顏色與樣式
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

mkdir -p "$BASE_LOG_DIR"

# 清理環境函數
cleanup() {
    echo -e "${YELLOW}>> 正在執行環境清理與重置...${NC}"
    helm uninstall oai-cu oai-du oai-nr-ue -n $NAMESPACE 2>/dev/null || true
    kill $STERN_CU_PID $STERN_DU_PID $STERN_UE_PID 2>/dev/null || true
    pkill -9 stern 2>/dev/null || true
    sleep 5
}

# 取得所有變異測試檔
TEST_FILES=($(ls "$TEST_CASE_DIR"/*.yaml))
TOTAL_CASES=${#TEST_FILES[@]}
CURRENT_COUNT=0

echo -e "${GREEN}檢測到 $TOTAL_CASES 個測試案例。日誌將存於: $BASE_LOG_DIR${NC}"



for CASE_FILE in "${TEST_FILES[@]}"; do
    ((CURRENT_COUNT++))
    FILENAME=$(basename "$CASE_FILE")
    CURRENT_CASE="${FILENAME%.*}"
    CASE_LOG_DIR="$BASE_LOG_DIR/$CURRENT_CASE"
    mkdir -p "$CASE_LOG_DIR"
    
    # 初始化配置：預設全部使用 Standard 路徑下的檔案
    target_cu=$STD_CU
    target_du=$STD_DU
    target_ue=$STD_UE
    subject="Unknown"

    # 動態判定邏輯：如果測試檔名符合組件名稱，則替換該組件為變異版
    if [[ "$FILENAME" == oai-cu* ]]; then
        target_cu="$CASE_FILE"
        subject="CU (Mutated)"
    elif [[ "$FILENAME" == oai-du* ]]; then
        target_du="$CASE_FILE"
        subject="DU (Mutated)"
    fi

    # --- 顯示目前執行的排列組合與進度 ---
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

    # 1. 啟動背景 Stern 日誌監控
    # 對 CU/DU 使用 sed 過濾雜訊，UE 則全量記錄
    stern "oai-cu" -n $NAMESPACE --output raw > "$CASE_LOG_DIR/cu.log" 2>/dev/null &
    STERN_CU_PID=$!
    stern "oai-du" -n $NAMESPACE --output raw > "$CASE_LOG_DIR/du.log" 2>/dev/null &
    STERN_DU_PID=$!
    stern "oai-nr-ue" -n $NAMESPACE --output raw > "$CASE_LOG_DIR/ue.log" 2>/dev/null &
    STERN_UE_PID=$!

    # 2. 部署流程 (固定等待時間以採集錯誤狀態)
    echo -e "${BLUE}Deploying CU (Waiting 10s)...${NC}"
    helm install oai-cu "$CHART_ROOT/oai-cu" -n $NAMESPACE -f "$target_cu"
    sleep 10

    echo -e "${BLUE}Deploying DU (Waiting 20s)...${NC}"
    helm install oai-du "$CHART_ROOT/oai-du" -n $NAMESPACE -f "$target_du"
    sleep 20

    echo -e "${BLUE}Deploying UE (Waiting 20s)...${NC}"
    helm install oai-nr-ue "$CHART_ROOT/oai-nr-ue" -n $NAMESPACE -f "$target_ue"
    sleep 20

    # 3. 清理並準備下一輪
    cleanup
done

echo -e "\n${GREEN}✔ 所有 $TOTAL_CASES 個測試案例執行完畢！${NC}"
echo -e "${GREEN}總日誌路徑: $BASE_LOG_DIR${NC}"