#!/usr/bin/env python3
import os, time, subprocess, glob, sys
from datetime import datetime

# --- Configuration ---
YAML_INPUT_DIR = "/home/johnson/O2-Automation-Engine/yaml_generator/output/yaml"
CHARTS_BASE = "/home/johnson/O2-Automation-Engine/charts/oai-5g-ran"
WORKABLE_YAML_DIR = "/home/johnson/O2-Automation-Engine/yaml_generator/workable_yaml"
NAMESPACE = "johnson-ns"
CU_WAIT_TIME = 10
DU_WAIT_TIME = 15
UE_WAIT_TIME = 15

# ----------------

# Color definition
GREEN, YELLOW, CYAN, RED, NC = '\033[0;32m', '\033[1;33m', '\033[0;36m', '\033[0;31m', '\033[0m'

def progress_bar(seconds, message="Wait"):
    """Display dynamic progress bar in the same line to avoid screen washing"""
    for i in range(seconds):
        percent = (i + 1) / seconds
        bar = '█' * int(20 * percent) + '-' * (20 - int(20 * percent))
        sys.stdout.write(f"\r   {CYAN}[{message}]{NC} |{bar}| {i+1}/{seconds}s ")
        sys.stdout.flush()
        time.sleep(1)
    print()

def run_command(cmd):
    """Execute command and capture error message"""
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"{RED}❌ Execution failed: {cmd}{NC}")
        print(f"{YELLOW}Error content:{NC}\n{e.stderr}")
        sys.exit(1)

def start_stern(component, log_path):
    f = open(log_path, 'w')
    cmd = ["stern", component, "-n", NAMESPACE, "--output", "raw", "--only-log-lines"]
    return subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, preexec_fn=os.setsid), f

def main():
    yaml_files = sorted(glob.glob(os.path.join(YAML_INPUT_DIR, "*.yaml")))
    print(f"{CYAN}Found {len(yaml_files)} test cases. Starting automated testing...{NC}")

    for yaml_file in yaml_files:
        case_name = os.path.basename(yaml_file)
        log_dir = f"./logs/test_{datetime.now().strftime('%m%d_%H%M%S')}_{case_name.replace('.yaml', '')}"
        os.makedirs(log_dir, exist_ok=True)

        print(f"\n{YELLOW}🚀 [Testing Case] {case_name}{NC}")
        
        # 1. Start Stern in background
        p_cu, f_cu = start_stern("oai-cu", f"{log_dir}/cu.log")
        p_du, f_du = start_stern("oai-du", f"{log_dir}/du.log")
        p_ue, f_ue = start_stern("oai-nr-ue", f"{log_dir}/ue.log")

        # 2. Determine Value file
        v = {k: os.path.join(WORKABLE_YAML_DIR, f"{k}_values.yaml") for k in ['cu', 'du', 'ue']}
        target = next((k for k in v if k in case_name.lower()), None)
        if target: v[target] = yaml_file

        # 3. Deploy
        print(f"   {GREEN}Deploying components...{NC}")
        run_command(f"helm install oai-cu {CHARTS_BASE}/oai-cu -n {NAMESPACE} -f {v['cu']}")
        progress_bar(CU_WAIT_TIME, "CU Waiting")
        run_command(f"helm install oai-du {CHARTS_BASE}/oai-du -n {NAMESPACE} -f {v['du']}")
        progress_bar(DU_WAIT_TIME, "DU Waiting")
        run_command(f"helm install oai-nr-ue {CHARTS_BASE}/oai-nr-ue -n {NAMESPACE} -f {v['ue']}")
        progress_bar(UE_WAIT_TIME, "UE Waiting")

        # 5. Clean
        print(f"   {YELLOW}Uninstalling and cleaning...{NC}")
        run_command(f"helm uninstall oai-cu oai-du oai-nr-ue -n {NAMESPACE}")
        
        # Close Stern and file
        for p, f in [(p_cu, f_cu), (p_du, f_du), (p_ue, f_ue)]:
            os.killpg(os.getpgid(p.pid), 9)
            f.close()

        # Force wait for release resources, avoid conflict with the next case
        progress_bar(10, "Cooling down")
        print(f"{GREEN}   [Finished] Case {case_name} done.{NC}")

if __name__ == "__main__":
    main()