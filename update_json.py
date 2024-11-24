import os
import requests
import json
import zipfile
import io

# Get the GitHub token from environment variables
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

# Get the current repository information dynamically
CURRENT_REPO = os.environ.get('GITHUB_REPOSITORY')

# Headers for authentication
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def process_app(app_config):
    SOURCE_REPO_OWNER = app_config['repo_owner']
    SOURCE_REPO_NAME = app_config['repo_name']
    WORKFLOW_ID = app_config['workflow_id']
    
    # Fetch the latest workflow runs from the source repository
    response = requests.get(
        f'https://api.github.com/repos/{SOURCE_REPO_OWNER}/{SOURCE_REPO_NAME}/actions/workflows/{WORKFLOW_ID}/runs',
        headers=headers
    )

    if response.status_code != 200:
        print(f"Failed to fetch workflow runs for {app_config['name']}: {response.status_code}")
        return None

    runs = response.json()

    # Get the latest successful run
    try:
        latest_run = next(run for run in runs['workflow_runs'] if run['conclusion'] == 'success')
    except StopIteration:
        print(f"No successful runs found for {app_config['name']}.")
        return None

    run_id = latest_run['id']

    # Fetch artifacts for the latest successful run from the source repository
    artifacts_response = requests.get(
        f'https://api.github.com/repos/{SOURCE_REPO_OWNER}/{SOURCE_REPO_NAME}/actions/runs/{run_id}/artifacts',
        headers=headers
    )

    if artifacts_response.status_code != 200:
        print(f"Failed to fetch artifacts for {app_config['name']}: {artifacts_response.status_code}")
        return None

    artifacts = artifacts_response.json()

    if not artifacts['artifacts']:
        print(f"No artifacts found for {app_config['name']}.")
        return None

    artifact = artifacts['artifacts'][0]
    artifact_url = artifact['archive_download_url']

    # Download the artifact zip file
    zip_response = requests.get(artifact_url, headers=headers)
    if zip_response.status_code != 200:
        print(f"Failed to download artifact for {app_config['name']}: {zip_response.status_code}")
        return None

    # Create downloads directory if it doesn't exist
    os.makedirs('./downloads', exist_ok=True)

    # Extract the .ipa file from the downloaded zip and save it in ./downloads/
    with zipfile.ZipFile(io.BytesIO(zip_response.content)) as z:
        ipa_files = [f for f in z.namelist() if f.endswith('.ipa')]
        
        if not ipa_files:
            print(f"No .ipa files found in the artifact for {app_config['name']}.")
            return None
        
        ipa_file_name = ipa_files[0]
        
        # Define version for naming and save path
        version = latest_run['head_commit']['id'][:7]
        save_path = f"./downloads/{ipa_file_name[:-4]}-{version}.ipa"

        # Extract and save .ipa file to specified path
        with open(save_path, 'wb') as ipa_file:
            ipa_file.write(z.read(ipa_file_name))

    print(f"Extracted and saved IPA File for {app_config['name']}: {save_path}")

    # Construct the download URL dynamically based on current repo info
    download_url = f"https://raw.githubusercontent.com/{CURRENT_REPO}/main/downloads/{os.path.basename(save_path)}"

    return {
        "name": app_config['name'],
        "bundleIdentifier": app_config['bundle_identifier'],
        "version": version,
        "versionDate": latest_run['created_at'].split('T')[0],
        "versionDescription": f"Latest build from {latest_run['name']}",
        "downloadURL": download_url
    }

# Load app configurations
with open('app_config.json', 'r') as config_file:
    app_configs = json.load(config_file)['apps']

# Process each app
updated_apps = []
for app_config in app_configs:
    app_data = process_app(app_config)
    if app_data:
        updated_apps.append(app_data)

# Load existing JSON file and update it with new information
try:
    with open('sidestore_repo.json', 'r') as file:
        if os.stat('sidestore_repo.json').st_size == 0:
            raise ValueError("JSON file is empty.")
        data = json.load(file)
except (FileNotFoundError, ValueError) as e:
    print(f"Error loading JSON file: {e}")
    exit(1)

# Update or add new apps in the JSON data using unique keys (e.g., name + repo_owner)
for updated_app in updated_apps:
    unique_key = (updated_app["name"], updated_app["bundleIdentifier"])
    
    existing_app_index = next((index for (index, d) in enumerate(data['apps']) 
                               if (d["name"], d["bundleIdentifier"]) == unique_key), None)
    
    if existing_app_index is not None:
        data['apps'][existing_app_index] = updated_app  # Update existing entry
    else:
        data['apps'].append(updated_app)  # Add new entry

# Save updated JSON file and print its contents to the console
try:
    with open('sidestore_repo.json', 'w') as file:
        json.dump(data, file, indent=4)
        print("Updated JSON content:")
        print(json.dumps(data, indent=4))
except Exception as e:
    print(f"Error writing to JSON file: {e}")
