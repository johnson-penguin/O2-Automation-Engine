#!/usr/bin/env python3
import os, re, random
import json
import yaml
import glob
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
timestamp = datetime.now().strftime("%m%d_%H%M")


# 1. Configuration
WORKABLE_YAML_DIR = "/home/johnson/O2-Automation-Engine/Mutated_Configuration_Generator/workable_yaml"
PROMPT_FILE = "/home/johnson/O2-Automation-Engine/Mutated_Configuration_Generator/yaml_generator/tool/Configuration_Mutation_Prompt.md"
OUTPUT_DIR = "/home/johnson/O2-Automation-Engine/Mutated_Configuration_Generator/yaml_generator/output/cms"
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
    Filter the yaml_subset and send it to LLM for modification suggestions.
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
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": formatted_prompt},
                {"role": "user", "content": f"Here is the YAML 'config' section content:\n\n{yaml_subset}"}
            ],
            temperature=1,
            top_p=0.7,
            max_tokens=8192
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error calling LLM: {str(e)}"

def main():
    print(f"Searching for YAML files in: {WORKABLE_YAML_DIR}")
    
    try:
        # 1. Randomly select a YAML file

        # selected_file = get_random_yaml_file(WORKABLE_YAML_DIR)

        selected_file = "/home/johnson/O2-Automation-Engine/Mutated_Configuration_Generator/workable_yaml/cu_values.yaml"

        base_name = os.path.basename(selected_file)
        print(f"Selected file: {selected_file}")
        
        # 2. Read and extract 'config' section
        with open(selected_file, 'r') as f:
            full_data = yaml.safe_load(f)
        
        # Get config section, if not exist then give empty dictionary
        config_data = full_data.get('config', {})
        if not config_data:
            print("Warning: No 'config' section found in the selected YAML.")
        
        # Convert config section back to YAML string, only feed this part to LLM
        config_yaml_subset = yaml.dump(config_data, default_flow_style=False)
            
        prompt_template = load_prompt(PROMPT_FILE)
        
        # 3. Automatically determine component name (based on file name keywords)
        base_name_lower = base_name.lower()
        if "du" in base_name_lower:
            comp_name = "oai-du"
        elif "cu" in base_name_lower:
            comp_name = "oai-cu"
        else:
            comp_name = random.choice(["oai-du", "oai-cu"])
            
        print(f"Matched component for LLM: {comp_name}")

        if api_key:
            current_gen_number = 100
            print(f"Generating {current_gen_number} cases specifically for 'config' section...")
            
            # Call LLM to generate modification (only for config subset)
            result = generate_modifications(config_yaml_subset, selected_file, prompt_template, comp_name, current_gen_number)
            
            # --- 4. Parsing and Storage Mechanism ---
            try:
                # Use Regex to extract JSON, ignore surrounding text
                json_match = re.search(r'(\[.*\]|\{.*\})', result, re.DOTALL)
                
                if json_match:
                    clean_result = json_match.group(1)
                    # Fix possible trailing commas in JSON
                    clean_result = re.sub(r',\s*([\]}])', r'\1', clean_result)
                else:
                    clean_result = result.replace("```json", "").replace("```", "").strip()

                json_data = json.loads(clean_result)
                file_stem = os.path.splitext(base_name)[0]
                output_filename = f"{timestamp}_{current_gen_number}_mod_{file_stem}.json"
                output_path = os.path.join(OUTPUT_DIR, output_filename)
                
                with open(output_path, 'w', encoding='utf-8') as f_out:
                    json.dump(json_data, f_out, indent=4, ensure_ascii=False)
                
                print(f"\n[Success] Output saved to: {output_path}")
                
            except (json.JSONDecodeError, Exception) as e:
                print(f"\nWarning: Parsing failed. Error: {e}")
                # Save raw response for debugging
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