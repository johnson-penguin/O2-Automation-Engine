#!/usr/bin/env python3

import yaml
import json
import os

# 定義檔案路徑
file_path = '/home/johnson/O2-Automation-Engine/yaml_generator/workable_yaml/cu_values.yaml'

def print_yaml_config(path):
    # 檢查檔案是否存在
    if not os.path.exists(path):
        print(f"錯誤：找不到檔案 {path}")
        return

    try:
        with open(path, 'r', encoding='utf-8') as file:
            # 讀取 YAML 內容
            data = yaml.safe_load(file)
            
            # 提取 config 結構
            config_data = data.get('config')
            
            if config_data:
                print("--- 找到 config 結構 ---")
                # 使用 json.dumps 加上 indent 來美化 print 出來的結構
                print(json.dumps(config_data, indent=4, ensure_ascii=False))
            else:
                print("檔案中找不到 'config:' 鍵值。")
                
    except yaml.YAMLError as exc:
        print(f"YAML 解析錯誤: {exc}")
    except Exception as e:
        print(f"發生非預期錯誤: {e}")

if __name__ == "__main__":
    print_yaml_config(file_path)