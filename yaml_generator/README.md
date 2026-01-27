# LLM-Based 5G RAN Configuration Fuzzing & Testing Tool

This directory contains a suite of tools designed to automate the process of "fuzzing" or "chaos testing" OAI 5G RAN (CU, DU, UE) configurations. It leverages Large Language Models (LLMs) to generate semantically relevant but erroneous/boundary/modified configuration values, applies them to base YAML files, and attempts to deploy them via Helm.

## 📂 Directory Structure

```text
yaml_generator/
├── tool/                                         # Core Python scripts
│   ├── generator_cms.py                          # Step 1: LLM-based Change Management System (CMS) generator
│   ├── apply_changes.py                          # Step 2: Applies LLM suggestions to YAML files
│   ├── multiple_testing.py                       # Step 3: Automated Batch Testing Runner
│   └── Configuration_Mutation_Prompt.md          # System prompt for the LLM
├── workable_yaml/                                # Base "Golden" Valid Configurations (CU/DU/UE)
└── output/                                       # Generated Artifacts
    ├── cms/                                      # Intermediate JSON Modification Requests
    └── yaml/                                     # Final Accessible Helm Value Files
```

## 🚀 Workflow

### Step 1: Generate Test Cases (`generator_cms.py`)
Uses the NVIDIA API to analyze base YAML files (`workable_yaml/`) and generate "Chaos" modification requests.
- **Input**: `workable_yaml/*.yaml`, `Configuration Mutation Prompt.md`
- **Output**: `output/cms/mod_*.json`
- **Details**: Generates 5 distinct test cases per run, targeting the `config` section with fuzzing strategies (Type Mismatch, Boundary Violations, etc.).

```bash
python3 tool/generator_cms.py
```
*Requires `NVIDIA_API_KEY` in your environment variables.*
### Output
```bash
[
    {
        "filename": "oai-du_case_1.yaml",
        "modified": "parameter_fuzzing",
        "changes": [
            {
                "key": "config.cuHost",
                "original_value": "oai-cu",
                "error_value": "true"
            },
            {
                "key": "config.plmn_list[0].mnc_length",
                "original_value": "2",
                "error_value": "null"
            }
        ]
    },
    {
        "filename": "oai-du_case_2.yaml",
        "modified": "parameter_fuzzing",
        "changes": [
            {
                "key": "config.enableE2",
                "original_value": "false",
                "error_value": "123"
            },
            {
                "key": "config.plmn_list[0].mnc",
                "original_value": "01",
                "error_value": "true"
            }
        ]
    },
```
### Step 2: Apply Changes (`apply_changes.py`)
Reads the generated JSON modification requests and applies them to the base YAML files to create deployable Helm values files.
- **Input**: `output/cms/*.json` + `workable_yaml/*.yaml`
- **Output**: `output/yaml/*.yaml`
- **Details**: Injects comments into the YAML indicating what was modified (e.g., `# Modified: old -> new`).

```bash
python3 tool/apply_changes.py
```

### Output
```bash
 config:
  timeZone: Europe/Paris
  useAdditionalOptions: -E --rfsim --log_config.global_log_options level,nocolor,time
  duName: oai-rfsim
  usrp: rfsim
  cuHost: true # Modified: oai-cu -> true
  enableE2: false
  f1duPort: 2153
  ricHost: oai-flexric
  gdbstack: 1
  tac: 1
  plmn_list:
  - mcc: 001
    mnc: 01
    mnc_length: null # Modified: 2 -> null
    snssaiList:
    - sst: 1
      sd: 0xffffff
```
```bash
  config:
  timeZone: Europe/Paris
  useAdditionalOptions: -E --rfsim --log_config.global_log_options level,nocolor,time
  duName: oai-rfsim
  usrp: rfsim
  cuHost: oai-cu
  enableE2: 123 # Modified: false -> 123
  f1duPort: 2153
  ricHost: oai-flexric
  gdbstack: 1
  tac: 1
  plmn_list:
  - mcc: 001
    mnc: true # Modified: 01 -> true
    mnc_length: 2
    snssaiList:
    - sst: 1
      sd: 0xffffff
```

### Step 3: Run Automated Tests (`multiple_testing.py`)
Iterates through all generated YAML files, deploys them using Helm, monitors logs with Stern, and cleans up afterwards.
- **Input**: `output/yaml/*.yaml`
- **Actions**:
    1.  `helm install` for CU, DU, and UE.
    2.  `stern` log capture (background).
    3.  Wait for defined cooling periods.
    4.  `helm uninstall` cleanup.
- **Logs**: Saved to `tool/logs/` with timestamps.

```bash
python3 tool/multiple_testing.py
```

## 🛠 Prerequisites

- **Python 3**
- **Helm**: For deploying charts.
- **Stern**: For log tailing/capture (`sudo snap install stern` or equivalent).
- **OAI 5G Charts**: Expected at `/home/johnson/O2-Automation-Engine/charts/oai-5g-ran`.
- **NVIDIA API Key**: Set `NVIDIA_API_KEY` for the LLM generation step.

## 📝 Configuration

- **`tool/prompt.md`**: Modify this file to change the strategy or instructions given to the LLM (e.g., change from "fuzzing" to "performance tuning").
- **Script Variables**: Check the top of each `.py` file for directory paths (defaulted to project absolute paths).
