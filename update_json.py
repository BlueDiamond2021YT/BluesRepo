import os
import requests
import json

# Get the GitHub token from environment variables
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

# Constants for the SideStore repository
REPO_OWNER = 'SideStore'
REPO_NAME = 'SideStore'
WORKFLOW_ID = 'nightly.yml'

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

# Extract necessary details for updating JSON file
version = latest_run['head_commit']['id'][:7]  # Example using commit hash
version_date = latest_run['created_at'].split('T')[0]
download_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/download/nightly/SideStore.ipa"  # Adjust if needed

print(f"Latest Version: {version}")
print(f"Version Date: {version_date}")
print(f"Download URL: {download_url}")

# Load existing JSON file and update it with new information
try:
    with open('sidestore_repo.json', 'r') as file:
        if os.stat('sidestore_repo.json').st_size == 0:
            raise ValueError("JSON file is empty.")
        data = json.load(file)
except (FileNotFoundError, ValueError) as e:
    print(f"Error loading JSON file: {e}")
    exit(1)

data['apps'][0]['version'] = version
data['apps'][0]['versionDate'] = version_date
data['apps'][0]['downloadURL'] = download_url

# Save updated JSON file and print its contents to the console
try:
    with open('sidestore_repo.json', 'w') as file:
        json.dump(data, file, indent=4)
        print("Updated JSON content:")
        print(json.dumps(data, indent=4))
        print("JSON file updated successfully.")
except Exception as e:
    print(f"Error writing to JSON file: {e}")
