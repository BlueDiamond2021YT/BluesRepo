import os
import requests
import json
import zipfile
import io
from pathlib import Path

# Get the GitHub token from environment variables
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

# Get the current repository information dynamically
CURRENT_REPO = os.environ.get('GITHUB_REPOSITORY')

# Headers for authentication
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def extract_icon_and_metadata(ipa_path, app_name):
    with zipfile.ZipFile(ipa_path, 'r') as z:
        payload_path = [name for name in z.namelist() if name.startswith('Payload/') and name.endswith('.app/')][0]
        app_icons = [name for name in z.namelist() if payload_path in name and 'AppIcon' in name and name.endswith('.png')]
        entitlements = [name for name in z.namelist() if payload_path in name and 'Entitlements.plist' in name]
        
        # Extract the largest icon
        if app_icons:
            largest_icon = max(app_icons, key=lambda x: int(x.split('@')[1].split('x')[0]) if '@' in x else 1)
            icon_data = z.read(largest_icon)
            icons_dir = Path(f'./resources/icons')
            icons_dir.mkdir(parents=True, exist_ok=True)
            icon_path = icons_dir / f"{app_name}_icon.png"
            with open(icon_path, 'wb') as icon_file:
                icon_file.write(icon_data)
        
        # Extract entitlements (if any)
        permissions = []
        if entitlements:
            entitlements_data = z.read(entitlements[0])
            # Assuming plistlib or similar is used to parse entitlements data
            # permissions = parse_entitlements(entitlements_data)
        
        return str(icon_path), permissions

def process_app(app_config):
    SOURCE_REPO_OWNER = app_config['repo_owner']
    SOURCE_REPO_NAME = app_config['repo_name']
    WORKFLOW_ID = app_config['workflow_id']
    
    response = requests.get(
        f'https://api.github.com/repos/{SOURCE_REPO_OWNER}/{SOURCE_REPO_NAME}/actions/workflows/{WORKFLOW_ID}/runs',
        headers=headers
    )

    if response.status_code != 200:
        print(f"Failed to fetch workflow runs for {app_config['name']}: {response.status_code}")
        return None

    runs = response.json()

    try:
        latest_run = next(run for run in runs['workflow_runs'] if run['conclusion'] == 'success')
    except StopIteration:
        print(f"No successful runs found for {app_config['name']}.")
        return None

    run_id = latest_run['id']

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

    zip_response = requests.get(artifact_url, headers=headers)
    if zip_response.status_code != 200:
        print(f"Failed to download artifact for {app_config['name']}: {zip_response.status_code}")
        return None

    downloads_dir = Path(f'./downloads/{app_config["name"]}')
    downloads_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(zip_response.content)) as z:
        ipa_files = [f for f in z.namelist() if f.endswith('.ipa')]
        
        if not ipa_files:
            print(f"No .ipa files found in the artifact for {app_config['name']}.")
            return None
        
        ipa_file_name = ipa_files[0]
        
        version = latest_run['head_commit']['id'][:7]
        save_path = downloads_dir / f"{ipa_file_name[:-4]}-{version}.ipa"

        with open(save_path, 'wb') as ipa_file:
            ipa_file.write(z.read(ipa_file_name))

        icon_path, permissions = extract_icon_and_metadata(save_path, app_config['name'])

    print(f"Extracted and saved IPA File for {app_config['name']}: {save_path}")

    download_url = f"https://raw.githubusercontent.com/{CURRENT_REPO}/main/downloads/{app_config['name']}/{os.path.basename(save_path)}"

    return {
        "beta": True,
        "name": app_config['name'],
        "bundleIdentifier": app_config['bundle_identifier'],
        "developerName": SOURCE_REPO_OWNER,
        "version": version,
        "versionDate": latest_run['created_at'].split('T')[0],
        "versionDescription": f"Latest build from {latest_run['name']}",
        "downloadURL": download_url,
        "iconURL": f"https://raw.githubusercontent.com/{CURRENT_REPO}/main/resources/icons/{os.path.basename(icon_path)}",
        "localizedDescription": "Run iOS app without actually installing it!",
        "tintColor": "#0784FC",
        "category": "utilities",
        "size": os.path.getsize(save_path),
        "screenshotURLs": [],
        "appPermissions": {
            "entitlements": permissions,
            "privacy": {}
        }
    }

with open('app_config.json', 'r') as config_file:
    app_configs = json.load(config_file)['apps']

updated_apps = []
for app_config in app_configs:
    app_data = process_app(app_config)
    if app_data:
        updated_apps.append(app_data)

try:
    with open('sidestore_repo.json', 'r') as file:
        if os.stat('sidestore_repo.json').st_size == 0:
            raise ValueError("JSON file is empty.")
        data = json.load(file)
except (FileNotFoundError, ValueError) as e:
    print(f"Error loading JSON file: {e}")
    exit(1)

for updated_app in updated_apps:
    unique_key = (updated_app["name"], updated_app["bundleIdentifier"])
    
    existing_app_index = next((index for (index, d) in enumerate(data['apps']) 
                               if (d["name"], d["bundleIdentifier"]) == unique_key), None)
    
    if existing_app_index is not None:
        data['apps'][existing_app_index] = updated_app
    else:
        data['apps'].append(updated_app)

try:
    with open('sidestore_repo.json', 'w') as file:
        json.dump(data, file, indent=4)
except Exception as e:
    print(f"Error writing to JSON file: {e}")
