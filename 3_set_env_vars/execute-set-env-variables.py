import subprocess
import cmlapi
import os
import json

client = cmlapi.default_client(url=os.getenv("CDSW_API_URL").replace("/api/v1", ""), cml_api_key=os.getenv("CDSW_APIV2_KEY"))
# if os.getenv("UNIQUE_PROJECT_NAME") == "Healthcare Demo":
#     projects = client.list_projects(search_filter=json.dumps({"name": "Healthcare Demo"}))
# else:
#     projects = client.list_projects(search_filter=json.dumps({"name": os.getenv("DEMO_PROJECT_NAME")}))
# print(client.list_projects(search_filter=json.dumps({"name": "CML_AMP_Hybrid-Search-with-BM25-VDB-RAG"})))
# project = projects.projects[0]

project_id = os.getenv("CDSW_PROJECT_ID")
solr_applications = client.list_applications(project_id=project_id, search_filter=json.dumps({"script": "solr/02_start-solr-application.py"}))
solr_application = solr_applications.applications[0]
# print(solr_application)

solr_building_url = os.getenv("CDSW_API_URL")
solr_building_url = solr_building_url.replace('/api/v1', '')

# Check if the URL starts with 'https://' or 'http://'
if solr_building_url.startswith('https://'):
    # Add the subdomain after 'https://'
    solr_building_url = 'https://' + solr_application.subdomain + "." + solr_building_url[8:] + "/solr/"
elif solr_building_url.startswith('http://'):
    # Add the subdomain after 'http://'
    solr_building_url = 'http://' + solr_application.subdomain + "." + solr_building_url[7:] + "/solr/"
    
print(solr_building_url)

opensearch_applications = client.list_applications(project_id=project_id, search_filter=json.dumps({"script": "opensearch/run_opensearch.py"}))
opensearch_application = opensearch_applications.applications[0]
# print(opensearch_application)

opensearch_building_url = os.getenv("CDSW_API_URL")
opensearch_building_url = opensearch_building_url.replace('/api/v1', '')

# Check if the URL starts with 'https://' or 'http://'
if opensearch_building_url.startswith('https://'):
    # Add the subdomain after 'https://'
    opensearch_building_url = 'https://' + opensearch_application.subdomain + "." + opensearch_building_url[8:] + "/"
elif opensearch_building_url.startswith('http://'):
    # Add the subdomain after 'http://'
    opensearch_building_url = 'http://' + opensearch_application.subdomain + "." + opensearch_building_url[7:] + "/"
    
print(opensearch_building_url)

os.environ['SOLR_SERVER_URL'] = solr_building_url
os.environ['OPENSEARCH_SERVER_URL'] = opensearch_building_url

# Update coreconfigs.py with new Solr and OpenSearch URLs
coreconfigs_path = "coreconfigs.py"

# Read the current content of coreconfigs.py
with open(coreconfigs_path, "r") as f:
    config_lines = f.readlines()

# Modify the _FTBASE and _VECBASE lines
with open(coreconfigs_path, "w") as f:
    for line in config_lines:
        if line.strip().startswith("_FTBASE"):
            f.write(f'_FTBASE = ["{solr_building_url}"]\n')
        elif line.strip().startswith("_VECBASE"):
            f.write(f'_VECBASE = ["{opensearch_building_url}"]\n')
        else:
            f.write(line)

print(f"Updated coreconfigs.py with:\n_FTBASE = {solr_building_url}\n_VECBASE = {opensearch_building_url}")
