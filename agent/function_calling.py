import requests
from urllib.parse import urlparse
from config import APP_ID, APP_PRIVATE_KEY
import time
import jwt
from datetime import datetime, timezone, timedelta
import threading

installation_tokens = {}
token_lock = threading.Lock()

def generate_jwt():
    """Generate a JWT signed with GitHub App private key."""
    now = int(time.time())
    payload = {
        "iat": now,
        "exp": now + (10 * 60),
        "iss": APP_ID,
    }
    encoded_jwt = jwt.encode(payload, APP_PRIVATE_KEY, algorithm="RS256")
    return encoded_jwt


def github_request(method, url, headers=None, **kwargs):
    if headers is None:
        jwt_token = generate_jwt()
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
        }
    while True:
        response = requests.request(method, url, headers=headers, **kwargs)
        
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset_time = response.headers.get("X-RateLimit-Reset")

        if remaining is None or reset_time is None:
            return response
        
        remaining = int(remaining)
        reset_time = int(reset_time)

        print(f"[GitHub] Remaining: {remaining}, Reset: {reset_time}")

        if response.status_code == 403 and "rate limit" in response.text.lower():
            wait = reset_time - int(time.time()) + 5
            print(f"Hit rate limit. Sleeping for {wait} seconds.")
            time.sleep(max(wait, 0))
            continue
        if remaining <= 2:
            wait = reset_time - int(time.time()) + 5
            print(f"Approaching rate limit ({remaining} left). Sleeping for {wait} seconds.")
            time.sleep(max(wait, 0))
            continue

        return response

    
def get_installation_id(owner, repo):
    """Fetch the installation ID for the app on a repo."""
    url = f"https://api.github.com/repos/{owner}/{repo}/installation"
    response = github_request("GET", url)
    if response.status_code == 200:
        data = response.json()
        return data["id"]
    else:
        raise Exception(f"Failed to get installation ID for {owner}/{repo}: {response.status_code} {response.text}")
    
# print(get_installation_id("aditi-dsi", "testing-cryptope"))


def get_installation_token(installation_id):
    """Return a valid installation token, fetch new if expired or missing."""
    with token_lock:
        token_info = installation_tokens.get(installation_id)
        if token_info and token_info["expires_at"] > datetime.now(timezone.utc) + timedelta(seconds=30):
            return token_info["token"]

        url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        response = github_request("POST", url)
        if response.status_code != 201:
            raise Exception(f"Failed to fetch installation token: {response.status_code} {response.text}")

        token_data = response.json()
        token = token_data["token"]
        expires_at = datetime.strptime(token_data["expires_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

        installation_tokens[installation_id] = {"token": token, "expires_at": expires_at}
        return token

# print(get_installation_token(69452220))

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
        return response.json()
    else:
        raise Exception(f"Failed to fetch issue: {response.status_code} {response.text}")

# print(get_issue_details("aditi-dsi", "testing-cryptope", "3"))

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

# tools = [
#     {
#         "type": "function",
#         "function": {
#             "name": "fetch_github_issue",
#             "description": "Fetch GitHub issue details",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "issue_url": {
#                         "type": "string",
#                         "description": "The full URL of the GitHub issue"
#                     }
#                 },
#                 "required": ["issue_url"]
#             },
#         },
#     },
# {
#         "type": "function",
#         "function": {
#             "name": "get_issue_details",
#             "description": "Get details of a GitHub issue",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "owner": {
#                         "type": "string",
#                         "description": "The owner of the repository."
#                     },
#                     "repo": {
#                         "type": "string",
#                         "description": "The name of the repository."
#                     },
#                     "issue_num": {
#                         "type": "string",
#                         "description": "The issue number."
#                     }
#                 },
#                 "required": ["owner", "repo", "issue_num"],
#             },
#         },
#     },
# {
#         "type": "function",
#         "function": {
#             "name": "post_comment",
#             "description": "Post a comment on a GitHub issue",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "owner": {
#                         "type": "string",
#                         "description": "The owner of the repository."
#                     },
#                     "repo": {
#                         "type": "string",
#                         "description": "The name of the repository."
#                     },
#                     "issue_num": {
#                         "type": "string",
#                         "description": "The issue number."
#                     },
#                     "comment_body": {
#                         "type": "string",
#                         "description": "The body of the comment."
#                     }
#                 },
#                 "required": ["owner", "repo", "issue_num", "comment_body"],
#             },
#         },
#     },
# ]
