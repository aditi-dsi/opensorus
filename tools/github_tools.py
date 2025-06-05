from urllib.parse import urlparse
from tools.utils import get_installation_id, get_installation_token, github_request

def fetch_github_issue(issue_url):
    parsed = urlparse(issue_url)
    path_parts = parsed.path.strip('/').split('/')
    if len(path_parts) >= 4 and path_parts[2] == 'issues':
        owner = path_parts[0]
        repo = path_parts[1]
        issue_num = path_parts[3]
        return owner, repo, issue_num
    else:
        raise ValueError("Invalid GitHub Issue URL")
    

def get_issue_details(owner, repo, issue_num):
    installation_id = get_installation_id(owner, repo)
    token = get_installation_token(installation_id)
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = github_request("GET", url, headers=headers)
    if response.status_code == 200:
        return response.json().get("body")
    else:
        raise Exception(f"Failed to fetch issue: {response.status_code} {response.text}")

# print(get_issue_details("aditi-dsi", "testing-cryptope", "4"))

def post_comment(owner, repo, issue_num, comment_body):
    installation_id = get_installation_id(owner, repo)
    token = get_installation_token(installation_id)
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {"body": comment_body}
    response = github_request("POST", url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Failed to post comment: {response.status_code} {response.text}")

# print(post_comment("aditi-dsi", "testing-cryptope", "3", "This is a test comment from OpenSorus."))
