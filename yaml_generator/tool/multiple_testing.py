#!/usr/bin/env python3
import os, time, subprocess, glob, sys
from datetime import datetime

# --- 參數設定 ---
YAML_INPUT_DIR = "/home/johnson/O2-Automation-Engine/yaml_generator/output/yaml"
CHARTS_BASE = "/home/johnson/O2-Automation-Engine/charts/oai-5g-ran"
WORKABLE_YAML_DIR = "/home/johnson/O2-Automation-Engine/yaml_generator/workable_yaml"
NAMESPACE = "johnson-ns"
CU_WAIT_TIME = 10
DU_WAIT_TIME = 15
UE_WAIT_TIME = 15

# ----------------

# 顏色定義
GREEN, YELLOW, CYAN, RED, NC = '\033[0;32m', '\033[1;33m', '\033[0;36m', '\033[0;31m', '\033[0m'

def progress_bar(seconds, message="Wait"):
    """在同一行顯示動態進度條，避免洗版"""
    for i in range(seconds):
        percent = (i + 1) / seconds
        bar = '█' * int(20 * percent) + '-' * (20 - int(20 * percent))
        sys.stdout.write(f"\r   {CYAN}[{message}]{NC} |{bar}| {i+1}/{seconds}s ")
        sys.stdout.flush()
        time.sleep(1)
    print()

def run_command(cmd):
    """執行指令並擷取錯誤訊息"""
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"{RED}❌ 執行失敗: {cmd}{NC}")
        print(f"{YELLOW}錯誤內容:{NC}\n{e.stderr}")
        sys.exit(1)

def start_stern(component, log_path):
    """將 stdout 與 stderr 全部導向檔案，徹底靜音 Terminal"""
    f = open(log_path, 'w')
    cmd = ["stern", component, "-n", NAMESPACE, "--output", "raw", "--only-log-lines"]
    # stderr=subprocess.STDOUT 確保所有的 + / - 標籤都進檔案
    return subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, preexec_fn=os.setsid), f

def main():
    yaml_files = sorted(glob.glob(os.path.join(YAML_INPUT_DIR, "*.yaml")))
    print(f"{CYAN}找到 {len(yaml_files)} 個測試案例。開始自動化測試...{NC}")

    for yaml_file in yaml_files:
        case_name = os.path.basename(yaml_file)
        log_dir = f"./logs/test_{datetime.now().strftime('%m%d_%H%M%S')}_{case_name.replace('.yaml', '')}"
        os.makedirs(log_dir, exist_ok=True)

        print(f"\n{YELLOW}🚀 [Testing Case] {case_name}{NC}")
        
        # 1. 啟動背景 Stern (靜音模式)
        p_cu, f_cu = start_stern("oai-cu", f"{log_dir}/cu.log")
        p_du, f_du = start_stern("oai-du", f"{log_dir}/du.log")
        p_ue, f_ue = start_stern("oai-nr-ue", f"{log_dir}/ue.log")

        # 2. 判定 Value 檔案
        v = {k: os.path.join(WORKABLE_YAML_DIR, f"{k}_values.yaml") for k in ['cu', 'du', 'ue']}
        target = next((k for k in v if k in case_name.lower()), None)
        if target: v[target] = yaml_file

        # 3. 部署
        print(f"   {GREEN}Deploying components...{NC}")
        run_command(f"helm install oai-cu {CHARTS_BASE}/oai-cu -n {NAMESPACE} -f {v['cu']}")
        progress_bar(CU_WAIT_TIME, "CU Waiting")
        run_command(f"helm install oai-du {CHARTS_BASE}/oai-du -n {NAMESPACE} -f {v['du']}")
        progress_bar(DU_WAIT_TIME, "DU Waiting")
        run_command(f"helm install oai-nr-ue {CHARTS_BASE}/oai-nr-ue -n {NAMESPACE} -f {v['ue']}")
        progress_bar(UE_WAIT_TIME, "UE Waiting")

        # 5. 清理
        print(f"   {YELLOW}Uninstalling and cleaning...{NC}")
        run_command(f"helm uninstall oai-cu oai-du oai-nr-ue -n {NAMESPACE}")
        
        # 關閉 Stern 並關閉檔案
        for p, f in [(p_cu, f_cu), (p_du, f_du), (p_ue, f_ue)]:
            os.killpg(os.getpgid(p.pid), 9)
            f.close()

        # 強制等待 K8s 釋放資源，避免下一個案例衝突
        progress_bar(10, "Cooling down")
        print(f"{GREEN}   [Finished] Case {case_name} done.{NC}")

if __name__ == "__main__":
    main()