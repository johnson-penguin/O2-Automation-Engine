#!/bin/bash

helm install oai-cu \
  "/home/johnson/O2-Automation-Engine/Mutated_Configuration_Generator/charts/oai-5g-ran/oai-cu" \
  -n johnson-ns \
  -f "/home/johnson/O2-Automation-Engine/Mutated_Configuration_Generator/charts/oai-5g-ran/oai-cu/values.yaml"

echo "Deploying CU"


helm install oai-cu \
  "/home/johnson/O2-Automation-Engine/Mutated_Configuration_Generator/charts/oai-5g-ran/oai-cu" \
  -n johnson-ns \
  --set-file customConfigData="/home/johnson/O2-Automation-Engine/yaml_runner/testing_place/oai_cu_config.yaml"