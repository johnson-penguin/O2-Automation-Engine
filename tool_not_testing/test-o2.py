import requests

url = "http://192.168.8.35:8080/api/o2dms/v2/vnf_instances/"

payload = {
    "name": "oai-cu-test-01",
    "description": "Another VNF Descriptor",
    "profile_type": "kubernetes",
    "artifact_repo_url": "https://gitlab.eurecom.fr/oai/orchestration/charts.git",
    "artifact_name": "oai-5g-ran/oai-cu",
    "artifact_repo_branch": "main",
    "target_cluster": "0b9afde5-d8bb-4f91-956b-fdd424e5b766",
    "namespace": "johnson-ns",
    "values": {
        "config.amfHost": "192.168.8.108",
        "serviceAccount.create": "false",
        "serviceAccount.name": "default"
        }
}
headers = {
    "Content-Type": "application/json",
    "User-Agent": "insomnia/11.3.0"
}

response = requests.request("POST", url, json=payload, headers=headers)
dump = response.json()

print(response.text)

#---

url = "http://192.168.8.35:8080/api/o2dms/v2/deployments/"

payload = {
    "descriptor": dump['descriptor_id'],
    "name": "post-test-01",
    "namespace": "johnson-ns"
}
headers = {
    "Content-Type": "application/json",
    "User-Agent": "insomnia/11.3.0"
}

response = requests.request("POST", url, json=payload, headers=headers)
dump = response.json()

print(response.text)

#---

url = f"http://192.168.8.35:8080/api/o2dms/v2/deployments/{dump['instance_id']}/instantiate/"

payload = {"instantiation_params": {"replicas": 2, "namespace":"johnson-ns"}}
headers = {
    "Content-Type": "application/json",
    "User-Agent": "insomnia/11.3.0"
}

response = requests.request("POST", url, json=payload, headers=headers)

print(response.text)

#--------------------
# TERMINATE
#--------------------
# url = f"http://192.168.8.35:8080/api/o2dms/v2/deployments/{dump['instance_id']}/terminate/"
# 
# payload = {
#     "graceful": True,
#     "cleanup_namespace": True
# }
# headers = {
#     "Content-Type": "application/json",
#     "User-Agent": "insomnia/11.3.0"
# }
# 
# response = requests.request("POST", url, json=payload, headers=headers)
# 
# print(response.text)
