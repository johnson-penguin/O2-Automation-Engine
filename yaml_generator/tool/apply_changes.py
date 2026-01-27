#!/usr/bin/env python3
import os
import json
import yaml
import glob

# 1. 配置路徑
JSON_INPUT_DIR = "/home/johnson/O2-Automation-Engine/yaml_generator/output/cms"
BASE_YAML_DIR = "/home/johnson/O2-Automation-Engine/yaml_generator/workable_yaml"
YAML_OUTPUT_DIR = "/home/johnson/O2-Automation-Engine/yaml_generator/output/yaml"

os.makedirs(YAML_OUTPUT_DIR, exist_ok=True)

def update_nested_dict(d, key_path, value, original_val):
    """
    更新數值並在值後面強行掛載註解標記
    """
    keys = key_path.split('.')
    for key in keys[:-1]:
        if '[' in key and ']' in key:
            list_name = key.split('[')[0]
            index = int(key.split('[')[1].split(']')[0])
            d = d[list_name][index]
        else:
            d = d.setdefault(key, {})
    
    last_key = keys[-1]
    
    # 格式化修改後的內容： value + 註解標記
    # 我們先暫時用一個獨特的字串符號包裹註解
    comment_tag = f" # Modified: {original_val} -> {value}"
    
    if '[' in last_key and ']' in last_key:
        list_name = last_key.split('[')[0]
        index = int(last_key.split('[')[1].split(']')[0])
        # 存入時帶入標記
        d[list_name][index] = f"{value}__COMMENT_HERE__{comment_tag}"
    else:
        d[last_key] = f"{value}__COMMENT_HERE__{comment_tag}"

def process_json_to_yaml():
    json_files = glob.glob(os.path.join(JSON_INPUT_DIR, "*.json"))
    
    for json_file in json_files:
        print(f"Processing: {os.path.basename(json_file)}")
        with open(json_file, 'r') as f:
            cases = json.load(f)

        for case in cases:
            target_filename = case['filename']
            changes = case['changes']
            
            # 決定基底檔
            fname_lower = target_filename.lower()
            if "du" in fname_lower: base_name = "du_values.yaml"
            elif "cu" in fname_lower: base_name = "cu_values.yaml"
            elif "ue" in fname_lower: base_name = "ue_values.yaml"
            else: continue
            
            base_path = os.path.join(BASE_YAML_DIR, base_name)
            if not os.path.exists(base_path): continue

            with open(base_path, 'r') as f_yaml:
                # safe_load 會移除所有原始註解，符合你的需求
                yaml_data = yaml.safe_load(f_yaml)

            for change in changes:
                try:
                    update_nested_dict(yaml_data, change['key'], change['error_value'], change['original_value'])
                except Exception as e:
                    print(f"  Error applying {change['key']}: {e}")

            # 5. 生成 YAML 字串並處理註解
            # sort_keys=False 保持原始順序，不產生多餘註解
            yaml_str = yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)
            
            # 移除 PyYAML 自動幫字串加上的單引號，並將標記轉換為真正的註解
            final_yaml = yaml_str.replace("__COMMENT_HERE__", "").replace("'", "")
            
            output_path = os.path.join(YAML_OUTPUT_DIR, target_filename)
            with open(output_path, 'w') as f_out:
                f_out.write(final_yaml)
            
            print(f"  [Created] {output_path}")

if __name__ == "__main__":
    process_json_to_yaml()