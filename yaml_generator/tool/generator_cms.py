#!/usr/bin/env python3
import os, re, random
import json
import yaml
import glob
from openai import OpenAI
from dotenv import load_dotenv

# 1. Configuration
WORKABLE_YAML_DIR = "/home/johnson/O2-Automation-Engine/yaml_generator/workable_yaml"
PROMPT_FILE = "/home/johnson/O2-Automation-Engine/yaml_generator/tool/prompt.md"
OUTPUT_DIR = "/home/johnson/O2-Automation-Engine/yaml_generator/output/cms"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Ensure API Key is set
load_dotenv()
api_key = os.environ.get("NVIDIA_API_KEY")

if not api_key:
    print("Warning: NVIDIA_API_KEY not found in environment variables.")

def get_random_yaml_file(directory):
    """Selects a random YAML file from the directory."""
    yaml_files = glob.glob(os.path.join(directory, "*.yaml"))
    if not yaml_files:
        raise FileNotFoundError(f"No YAML files found in {directory}")
    return random.choice(yaml_files)

def load_prompt(prompt_path):
    """Loads the prompt template."""
    with open(prompt_path, 'r') as f:
        return f.read()

def generate_modifications(yaml_subset, filename, prompt_template, component_name, gen_number):
    """
    將過濾後的 yaml_subset 傳送給 LLM 進行修改建議生成。
    """
    formatted_prompt = prompt_template.replace("{component_name}", component_name) \
                                      .replace("{filename}", os.path.basename(filename)) \
                                      .replace("{num_cases}", str(gen_number)) \
                                      .replace("{random_id}", str(random.randint(100, 999)))

    client = OpenAI(
        base_url = "https://integrate.api.nvidia.com/v1",
        api_key = os.environ.get("NVIDIA_API_KEY")
    )
    
    try:
        response = client.chat.completions.create(
            model="meta/llama-3.1-8b-instruct",
            messages=[
                {"role": "system", "content": formatted_prompt},
                {"role": "user", "content": f"Here is the YAML 'config' section content:\n\n{yaml_subset}"}
            ],
            temperature=0.2,
            top_p=0.7,
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling LLM: {str(e)}"

def main():
    print(f"Searching for YAML files in: {WORKABLE_YAML_DIR}")
    
    try:
        # 1. 隨機選取一個 YAML 原始檔案
        selected_file = get_random_yaml_file(WORKABLE_YAML_DIR)
        base_name = os.path.basename(selected_file)
        print(f"Selected file: {selected_file}")
        
        # 2. 讀取並僅提取 'config' 區塊
        with open(selected_file, 'r') as f:
            full_data = yaml.safe_load(f)
        
        # 取得 config 內容，若不存在則給予空字典
        config_data = full_data.get('config', {})
        if not config_data:
            print("Warning: No 'config' section found in the selected YAML.")
        
        # 將 config 區塊轉回 YAML 字串，只餵這個部分給 LLM
        config_yaml_subset = yaml.dump(config_data, default_flow_style=False)
            
        prompt_template = load_prompt(PROMPT_FILE)
        
        # 3. 自動判定組件名稱 (根據檔名關鍵字)
        base_name_lower = base_name.lower()
        if "du" in base_name_lower:
            comp_name = "oai-du"
        elif "cu" in base_name_lower:
            comp_name = "oai-cu"
        elif "ue" in base_name_lower:
            comp_name = "oai-ue"
        else:
            comp_name = random.choice(["oai-du", "oai-cu"])
            
        print(f"Matched component for LLM: {comp_name}")

        if api_key:
            print(f"Generating {5} cases specifically for 'config' section...")
            current_gen_number = 5
            
            # 呼叫 LLM 產生修改建議 (僅針對 config 子集)
            result = generate_modifications(config_yaml_subset, selected_file, prompt_template, comp_name, current_gen_number)
            
            # --- 4. 解析與儲存機制 ---
            try:
                # 使用 Regex 提取 JSON，忽略前後文字
                json_match = re.search(r'(\[.*\]|\{.*\})', result, re.DOTALL)
                
                if json_match:
                    clean_result = json_match.group(1)
                    # 修正可能的 JSON 結尾多餘逗號
                    clean_result = re.sub(r',\s*([\]}])', r'\1', clean_result)
                else:
                    clean_result = result.replace("```json", "").replace("```", "").strip()

                json_data = json.loads(clean_result)
                
                # 移除副檔名 (.yaml 或 .yml)
                file_stem = os.path.splitext(base_name)[0]
                output_filename = f"mod_{file_stem}.json"
                output_path = os.path.join(OUTPUT_DIR, output_filename)
                
                with open(output_path, 'w', encoding='utf-8') as f_out:
                    json.dump(json_data, f_out, indent=4, ensure_ascii=False)
                
                print(f"\n[Success] Output saved to: {output_path}")
                
            except (json.JSONDecodeError, Exception) as e:
                print(f"\nWarning: Parsing failed. Error: {e}")
                # 解析失敗時儲存原始文字以便除錯
                error_raw_path = os.path.join(OUTPUT_DIR, f"debug_raw_{base_name}.txt")
                with open(error_raw_path, 'w') as f_err:
                    f_err.write(result)
                print(f"Raw response saved to: {error_raw_path}")
        else:
            print("\n[Dry Run] No API Key provided.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()