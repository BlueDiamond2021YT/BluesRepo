import os
import requests
import json
from datetime import datetime

# GitHub repository details
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')  # Your GitHub token
REPO_OWNER = "BlueDiamond2021YT"  # Replace with your repo owner
REPO_NAME = "BluesRepo"  # Replace with your repo name
WORKFLOW_NAME = "refresh_repo.yml"  # The workflow to monitor

def get_last_workflow_run():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_NAME}/runs"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch workflow runs: {response.status_code}")
        return None
    
    runs = response.json()
    
    if runs['total_count'] == 0:
        print("No workflow runs found.")
        return None
    
    # Get the most recent run
    latest_run = runs['workflow_runs'][0]
    
    return {
        "status": latest_run["conclusion"],  # Success or Failure
        "date": latest_run["created_at"],      # ISO-8601 format date
        "modified_files": latest_run.get("head_commit", {}).get("modified", [])
    }

def update_repo_status(action_status, modified_files):
    # Define the status information
    status_info = {
        "news": [
            {
                "title": f"Last repo refresh: {datetime.now().isoformat()}",
                "identifier": "repo_status",
                "caption": f"Workflow: {action_status}\nList of files modified by last action: {', '.join(modified_files)}",
                "date": datetime.now().isoformat(),
                "tintColor": "#F54F32"
            }
        ]
    }

    # Write to repo_status.json
    with open('repo_status.json', 'w') as json_file:
        json.dump(status_info, json_file, indent=4)
    print("repo_status.json updated successfully.")

if __name__ == "__main__":
    last_run_info = get_last_workflow_run()
    
    if last_run_info:
        action_status = last_run_info["status"]
        modified_files = last_run_info.get("modified_files", [])
        
        update_repo_status(action_status, modified_files)