import os
import requests
import json
from datetime import datetime

# Get the GitHub token from environment variables
GITHUB_TOKEN = os.environ.get('MY_GITHUB_TOKEN')  # Use your personal access token

# Get the current repository information dynamically
CURRENT_REPO = os.environ.get('GITHUB_REPOSITORY')  # Should be in the format "owner/repo"

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

def update_repo_status(modified_files):
    """Updates the repo_status.json with the list of modified files."""
    try:
        with open('repo_status.json', 'r') as json_file:
            status_info = json.load(json_file)
    except FileNotFoundError:
        print("repo_status.json not found. Creating a new one.")
        status_info = {"news": []}

    caption = f"List of files modified by last action: {', '.join(modified_files)}"

    status_info["news"] = [
        {
            "title": f"Last repo refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "identifier": "repo_status",
            "caption": caption,
            "date": datetime.now().isoformat(),
            "tintColor": "#27AE60"  # Green for success
        }
    ]

    with open('repo_status.json', 'w') as json_file:
        json.dump(status_info, json_file, indent=4)
    
    print("repo_status.json updated successfully.")
    print(caption)  # Display the modified files

if __name__ == "__main__":
    modified_files = fetch_modified_files()  # Fetch modified files
    if modified_files:
        update_repo_status(modified_files)  # Update with modified files
