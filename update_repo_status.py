import os
import requests
import json
from datetime import datetime

# Get the GitHub token from environment variables
GITHUB_TOKEN = os.environ.get('MY_GITHUB_TOKEN')  # Use your personal access token

# Get the current repository information dynamically
CURRENT_REPO = os.environ.get('GITHUB_REPOSITORY')  # Should be in the format "owner/repo"

WORKFLOW_NAME = "refresh_repo.yml"  # The workflow to monitor

def get_last_workflow_run():
    """Fetch the most recent workflow run."""
    url = f"https://api.github.com/repos/{CURRENT_REPO}/actions/workflows/{WORKFLOW_NAME}/runs"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',  # Use PAT for authentication
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch workflow runs: {response.status_code} - {response.text}")
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
        "id": latest_run["id"]                   # ID of the run to fetch details
    }

def fetch_modified_files():
    """Fetches the files modified in the latest commit."""
    url = f"https://api.github.com/repos/{CURRENT_REPO}/commits?per_page=1"
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',  # Use PAT for authentication
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch commits: {response.status_code} - {response.text}")
        return []
    
    commits = response.json()
    
    if not commits:
        print("No commits found.")
        return []
    
    commit_sha = commits[0]['sha']
    files_url = f"https://api.github.com/repos/{CURRENT_REPO}/commits/{commit_sha}"
    
    files_response = requests.get(files_url, headers=headers)
    
    if files_response.status_code != 200:
        print(f"Failed to fetch commit details: {files_response.status_code} - {files_response.text}")
        return []
    
    changed_files = files_response.json().get('files', [])
    
    return [file['filename'] for file in changed_files]

def update_repo_status(action_status, modified_files):
    """Updates the repo_status.json with workflow status and modified files."""
    try:
        with open('repo_status.json', 'r') as json_file:
            status_info = json.load(json_file)
    except FileNotFoundError:
        print("repo_status.json not found. Creating a new one.")
        status_info = {"news": []}

    tint_color = "#00FF00" if action_status == "failure" else "#FF0000"  # Red for failure, green for success

    caption = f"Workflow {'failed' if action_status == 'failure' else 'succeeded'}.\n"
    caption += f"List of files modified by last action:\n {', '.join(modified_files)}"

    status_info["news"] = [
        {
            "title": f"Last repo refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "identifier": "repo_status",
            "caption": caption,
            "date": datetime.now().isoformat(),
            "tintColor": tint_color
        }
    ]

    with open('repo_status.json', 'w') as json_file:
        json.dump(status_info, json_file, indent=4)
    
    print("repo_status.json updated successfully.")
    print(caption)  # Display the modified files and workflow status

if __name__ == "__main__":
    last_run_info = get_last_workflow_run()  # Fetch last workflow run info
    
    if last_run_info:
        action_status = last_run_info["status"]  # Get action status
        
        modified_files = fetch_modified_files()  # Fetch modified files
        
        update_repo_status(action_status, modified_files)  # Update with action status and modified files
