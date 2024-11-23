import os
import requests
import json
import zipfile
import io

# Get the GitHub token from environment variables
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

# Constants for the repository
REPO_OWNER = 'khanhduytran0'
REPO_NAME = 'LiveContainer'
WORKFLOW_ID = 'build.yml'

# Headers for authentication
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# Fetch the latest workflow runs
response = requests.get(
    f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_ID}/runs',
    headers=headers
)

if response.status_code != 200:
    print(f"Failed to fetch workflow runs: {response.status_code}")
    exit(1)

runs = response.json()

# Get the latest successful run
try:
    latest_run = next(run for run in runs['workflow_runs'] if run['conclusion'] == 'success')
except StopIteration:
    print("No successful runs found.")
    exit(1)

run_id = latest_run['id']

# Fetch artifacts for the latest successful run
artifacts_response = requests.get(
    f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs/{run_id}/artifacts',
    headers=headers
)

if artifacts_response.status_code != 200:
    print(f"Failed to fetch artifacts: {artifacts_response.status_code}")
    exit(1)

artifacts = artifacts_response.json()

# Assume we want the first artifact; adjust logic as necessary
if not artifacts['artifacts']:
    print("No artifacts found.")
    exit(1)

artifact = artifacts['artifacts'][0]
artifact_url = artifact['archive_download_url']

# Download the artifact zip file
zip_response = requests.get(artifact_url, headers=headers)
if zip_response.status_code != 200:
    print(f"Failed to download artifact: {zip_response.status_code}")
    exit(1)

# Extract the .ipa file from the downloaded zip
with zipfile.ZipFile(io.BytesIO(zip_response.content)) as z:
    ipa_files = [f for f in z.namelist() if f.endswith('.ipa')]
    
    if not ipa_files:
        print("No .ipa files found in the artifact.")
        exit(1)
    
    # Assuming we take the first .ipa file found
    ipa_file_name = ipa_files[0]
    
    # Optionally extract it to a specific location or keep it in memory
    z.extract(ipa_file_name)  # This extracts it to current working directory

print(f"Extracted IPA File: {ipa_file_name}")

# Load existing JSON file and update it with new information
try:
    with open('sidestore_repo.json', 'r') as file:
        if os.stat('sidestore_repo.json').st_size == 0:
            raise ValueError("JSON file is empty.")
        data = json.load(file)
except (FileNotFoundError, ValueError) as e:
    print(f"Error loading JSON file: {e}")
    exit(1)

data['apps'][0]['version'] = latest_run['head_commit']['id'][:7]
data['apps'][0]['versionDate'] = latest_run['created_at'].split('T')[0]
data['apps'][0]['downloadURL'] = ipa_file_name  # Link to extracted IPA

# Save updated JSON file and print its contents to the console
try:
    with open('sidestore_repo.json', 'w') as file:
        json.dump(data, file, indent=4)
        print("Updated JSON content:")
        print(json.dumps(data, indent=4))
        print("JSON file updated successfully.")
except Exception as e:
    print(f"Error writing to JSON file: {e}")
