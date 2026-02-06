#!/usr/bin/env python3
import os
import json
import yaml
import glob

# 1. Configuration Paths
JSON_INPUT_DIR = "/home/johnson/O2-Automation-Engine/Mutated_Configuration_Generator/yaml_generator/output/cms"
BASE_YAML_DIR = "/home/johnson/O2-Automation-Engine/Mutated_Configuration_Generator/workable_yaml"
YAML_OUTPUT_DIR = "/home/johnson/O2-Automation-Engine/Mutated_Configuration_Generator/yaml_generator/output/yaml"

os.makedirs(YAML_OUTPUT_DIR, exist_ok=True)

def update_nested_dict(d, key_path, value, original_val):
    """
    Update value and append comment tag to the value
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
    
    # Format the modified content: value + comment tag
    # We temporarily use a unique string symbol to wrap the comment
    comment_tag = f" # Modified: {original_val} -> {value}"
    
    if '[' in last_key and ']' in last_key:
        list_name = last_key.split('[')[0]
        index = int(last_key.split('[')[1].split(']')[0])
        # Append comment tag when storing
        d[list_name][index] = f"{value}__COMMENT_HERE__{comment_tag}"
    else:
        d[last_key] = f"{value}__COMMENT_HERE__{comment_tag}"

def process_json_to_yaml():
    json_files = glob.glob(os.path.join(JSON_INPUT_DIR, "*.json"))
    
    for json_file in json_files:
        # 1. Build sub-folder
        json_basename = os.path.basename(json_file)
        folder_name = os.path.splitext(json_basename)[0]
        target_sub_dir = os.path.join(YAML_OUTPUT_DIR, folder_name)
        os.makedirs(target_sub_dir, exist_ok=True)

        print(f"\n>>> 正在處理來源檔案: {json_basename}")
        
        with open(json_file, 'r') as f:
            try:
                cases = json.load(f)
            except Exception as e:
                print(f"    [錯誤] JSON 解析失敗: {e}")
                continue

        for case in cases:
            target_filename = case.get('filename', '')
            changes = case.get('changes', [])
            
            # 2. Determine template (Corrected comparison logic to ensure base file is found)
            fname_lower = target_filename.lower()
            if "du" in fname_lower: 
                base_name = "du_values.yaml"
            elif "cu" in fname_lower: 
                base_name = "cu_values.yaml"
            elif "ue" in fname_lower: 
                base_name = "ue_values.yaml"
            else:
                print(f"    [Skip] Cannot identify type: {target_filename}")
                continue
            
            base_path = os.path.join(BASE_YAML_DIR, base_name)
            if not os.path.exists(base_path):
                print(f"    [Error] Cannot find base template: {base_path}")
                continue

            # 3. Read and modify
            with open(base_path, 'r') as f_yaml:
                yaml_data = yaml.safe_load(f_yaml)

            for change in changes:
                try:
                    update_nested_dict(yaml_data, change['key'], change['error_value'], change['original_value'])
                except Exception as e:
                    print(f"    [Warning] Failed to modify field {change['key']}: {e}")

            # 4. Output file to sub-folder
            yaml_str = yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)
            final_yaml = yaml_str.replace("__COMMENT_HERE__", "").replace("'", "")
            
            output_path = os.path.join(target_sub_dir, target_filename)
            
            with open(output_path, 'w') as f_out:
                f_out.write(final_yaml)
            
            print(f"    [Success] Generate file: {target_sub_dir}/{target_filename}")

            
if __name__ == "__main__":
    process_json_to_yaml()