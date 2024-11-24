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
        "log_url": latest_run["logs_url"]      # URL to fetch the logs
    }

def fetch_workflow_log(log_url):
    # Fetch the logs from the URL provided
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',  # Use PAT for authentication
        'Accept': 'application/vnd.github.v3+json'
    }
    
    response = requests.get(log_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch workflow logs: {response.status_code} - {response.text}")
        return "Unable to retrieve logs."
    
    return response.text  # Return the log content as a string

def update_repo_status(action_status, modified_files, log_content):
    # Load existing status info if it exists
    try:
        with open('repo_status.json', 'r') as json_file:
            status_info = json.load(json_file)
    except FileNotFoundError:
        print("repo_status.json not found. Exiting.")
        return

    # Determine background color based on status
    tint_color = "#C0392B" if action_status == "failure" else "#27AE60"  # Darker red for failure, darker green for success

    # Format the news entry based on action status
    if action_status == "failure":
        caption = f"Workflow: {action_status}\nLog:\n{log_content}"  # Use log content on failure
    else:
        caption = f"Workflow: {action_status}\nList of files modified by last action: {', '.join(modified_files)}"

    # Update only the news entry
    status_info["news"] = [
        {
            "title": f"Last repo refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",  # Human-readable format
            "identifier": "repo_status",
            "caption": caption,
            "date": datetime.now().isoformat(),  # ISO-8601 format for internal use
            "tintColor": tint_color
        }
    ]

    # Write updated status back to repo_status.json
    with open('repo_status.json', 'w') as json_file:
        json.dump(status_info, json_file, indent=4)
    
    print("repo_status.json updated successfully.")

if __name__ == "__main__":
    last_run_info = get_last_workflow_run()
    
    if last_run_info:
        action_status = last_run_info["status"]
        
        log_content = fetch_workflow_log(last_run_info["log_url"])
        
        update_repo_status(action_status, [], log_content)  # Pass empty list for modified files when fetching logs fails or on failure
