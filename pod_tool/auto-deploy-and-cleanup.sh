#!/bin/bash
set -e

BASE_PATH=$(pwd)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="$BASE_PATH/oai_logs_$TIMESTAMP"
NAMESPACE="johnson-ns"

mkdir -p "$LOG_DIR"

CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_msg() {
    echo -e "${CYAN}[$(date +%H:%M:%S)] $1${NC}" | tee -a "$LOG_DIR/deploy_summary.log"
}

# --- 部署前清理 (確保環境乾淨) ---
log_msg "Cleaning up previous deployments..."
helm uninstall oai-cu oai-du oai-ue-1 -n $NAMESPACE 2>/dev/null || true
sleep 2

# --- 部署流程 ---
log_msg "Deploying OAI components..."
cd /home/johnson/O2-Automation-Engine/oai-cn5g-fed/charts/oai-5g-ran/oai-cu
helm install oai-cu . -n $NAMESPACE >> "$LOG_DIR/helm_install.log" 2>&1

cd /home/johnson/O2-Automation-Engine/oai-cn5g-fed/charts/oai-5g-ran/oai-du
helm install oai-du . -n $NAMESPACE >> "$LOG_DIR/helm_install.log" 2>&1

sleep 5

cd /home/johnson/O2-Automation-Engine/oai-cn5g-fed/charts/oai-5g-ran/oai-nr-ue
helm install oai-ue . -n $NAMESPACE >> "$LOG_DIR/helm_install.log" 2>&1

# --- 動態等待 Pods Ready ---
log_msg "Waiting for all Pods to be Ready..."
# 使用 wait 指令比 sleep 30s 更精準
kubectl wait --for=condition=Ready pods --all -n $NAMESPACE --timeout=60s || log_msg "Warning: Some pods are not ready yet."

# 額外留一點時間讓 UE 完成 RRC 連線程序，Log 才會完整
sleep 5

# --- 日誌擷取階段 ---
cd "$BASE_PATH"
log_msg "Exporting logs..."

# 修正：改用更寬鬆的選取方式，或同時檢查多個 Label
# 有些 OAI Chart 的 UE Label 可能是 app=oai-nr-ue
for comp in "oai-cu" "oai-du" "oai-ue"; do
    # 嘗試多種 Label 組合尋找 Pod 名稱
    POD_NAME=$(kubectl get pods -n $NAMESPACE -l "app.kubernetes.io/name=$comp" -o jsonpath="{.items[0].metadata.name}" 2>/dev/null || \
               kubectl get pods -n $NAMESPACE -l "app=$comp" -o jsonpath="{.items[0].metadata.name}" 2>/dev/null || true)
    
    if [ -n "$POD_NAME" ]; then
        # 增加 --all-containers 以防 UE 有多個 container (例如 wait-for-it)
        kubectl logs "$POD_NAME" -n $NAMESPACE --all-containers=true > "$LOG_DIR/${comp}.log" 2>&1
        log_msg "Saved log for $comp ($POD_NAME)"
    else
        log_msg "ERROR: Could not find Pod for $comp. Current pods in namespace:"
        kubectl get pods -n $NAMESPACE >> "$LOG_DIR/error_pods_state.log"
    fi
done

# --- 卸載 ---
log_msg "Uninstalling..."
helm uninstall oai-cu -n $NAMESPACE
helm uninstall oai-du -n $NAMESPACE
helm uninstall oai-ue -n $NAMESPACE

log_msg "Process finished. Directory: $LOG_DIR"