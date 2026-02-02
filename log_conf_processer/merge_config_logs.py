#!/usr/bin/env python3
"""
合併 YAML 配置與日誌檔案到 JSON 格式
Merge YAML configurations and log files into JSON format

此程式會讀取 templete_yaml 目錄中的 YAML 配置檔案，
以及 templete_logs 目錄中對應的日誌檔案，
並合併為 JSON 格式輸出。

This program reads YAML configuration files from the templete_yaml directory,
and corresponding log files from the templete_logs directory,
and merges them into JSON format.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any


def read_yaml_file(yaml_path: str) -> Dict[str, Any]:
    """讀取 YAML 檔案並返回字典"""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def read_log_file(log_path: str) -> list:
    """讀取日誌檔案並返回內容（按行分割）"""
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            return f.read().splitlines()
    return []


def merge_configs_and_logs(yaml_dir: str, logs_dir: str, output_file: str = None) -> Dict[str, Any]:
    """
    合併 YAML 配置與日誌檔案
    
    Args:
        yaml_dir: YAML 配置檔案目錄
        logs_dir: 日誌檔案目錄
        output_file: 輸出 JSON 檔案路徑 (可選)
    
    Returns:
        合併後的字典
    """
    yaml_dir_path = Path(yaml_dir)
    logs_dir_path = Path(logs_dir)
    
    # 結果字典
    result = {}
    
    # 遍歷所有 YAML 檔案
    for yaml_file in yaml_dir_path.glob("*.yaml"):
        case_name = yaml_file.stem  # 例如：oai-cu_case_1
        
        # 讀取 YAML 配置
        yaml_data = read_yaml_file(str(yaml_file))
        
        # 確定組件類型 (cu 或 du)
        component_type = "cu" if "cu_" in case_name else "du" if "du_" in case_name else "unknown"
        
        # 讀取對應的日誌檔案
        log_folder = logs_dir_path / case_name
        
        cu_log = read_log_file(str(log_folder / "cu.log"))
        du_log = read_log_file(str(log_folder / "du.log"))
        ue_log = read_log_file(str(log_folder / "ue.log"))
        
        # 構建此 case 的資料結構
        # yaml_content 只包含 config 部分
        result[case_name] = {
            "config": {
                "type": component_type,
                "yaml_content": yaml_data.get("config", {})
            },
            "logs": {
                "cu": cu_log,
                "du": du_log,
                "ue": ue_log
            }
        }
    
    # 如果指定了輸出檔案，則寫入
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✓ 成功輸出到: {output_file}")
        print(f"✓ Successfully exported to: {output_file}")
    
    return result


def main():
    """主函數"""
    # 設定路徑
    base_dir = Path(__file__).parent
    yaml_dir = base_dir / "templete_yaml"
    logs_dir = base_dir / "templete_logs"
    output_file = base_dir / "merged_config_logs.json"
    
    print("=" * 60)
    print("合併配置與日誌檔案 / Merging configs and logs")
    print("=" * 60)
    print(f"YAML 目錄 / YAML directory: {yaml_dir}")
    print(f"日誌目錄 / Logs directory: {logs_dir}")
    print(f"輸出檔案 / Output file: {output_file}")
    print("=" * 60)
    
    # 執行合併
    result = merge_configs_and_logs(str(yaml_dir), str(logs_dir), str(output_file))
    
    # 顯示統計資訊
    print(f"\n處理的案例數 / Cases processed: {len(result)}")
    for case_name, data in result.items():
        config_type = data["config"]["type"]
        cu_log_size = len(data["logs"]["cu"])
        du_log_size = len(data["logs"]["du"])
        ue_log_size = len(data["logs"]["ue"])
        print(f"  • {case_name} ({config_type})")
        print(f"    - CU log: {cu_log_size:,} bytes")
        print(f"    - DU log: {du_log_size:,} bytes")
        print(f"    - UE log: {ue_log_size:,} bytes")
    
    print("\n✅ 完成 / Done!")


if __name__ == "__main__":
    main()
