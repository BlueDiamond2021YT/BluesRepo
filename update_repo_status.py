import json
from datetime import datetime

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

# Example usage
if __name__ == "__main__":
    # Replace with actual status and modified files
    last_action_status = "Success"  # or "Failure"
    modified_files_list = ["file1.json", "file2.json"]  # Example list of modified files
    update_repo_status(last_action_status, modified_files_list)