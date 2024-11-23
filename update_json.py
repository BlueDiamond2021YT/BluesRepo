import requests
import json

# Constants
REPO_OWNER = 'SideStore'
REPO_NAME = 'SideStore'
GITHUB_TOKEN = 'your_github_token'  # Store this securely as a secret

# Headers for authentication
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

# Fetch the latest workflow runs
response = requests.get(
    f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/nightly.yml/runs',
    headers=headers
)
runs = response.json()

# Get the latest successful run
latest_run = next(run for run in runs['workflow_runs'] if run['conclusion'] == 'success')

# Extract version and date information
version = latest_run['head_commit']['id'][:7]  # Example for versioning using commit hash
version_date = latest_run['created_at'].split('T')[0]

# Load existing JSON file
with open('sidestore_repo.json', 'r') as file:
    data = json.load(file)

# Update version and date fields in JSON
data['apps'][0]['version'] = version
data['apps'][0]['versionDate'] = version_date

# Save updated JSON file
with open('sidestore_repo.json', 'w') as file:
    json.dump(data, file, indent=4)
