import asyncio
import base64
from datetime import datetime, timezone, timedelta
import jwt
import threading
import time
from typing import List
import requests
from config import APP_ID, APP_PRIVATE_KEY


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

async def fetch_repo_files(owner: str, repo: str, ref: str = "main") -> List[str]:
    """
    Lists all files in the repository by recursively fetching the Git tree from GitHub API.
    Returns a list of file paths.
    """
    installation_id = get_installation_id(owner, repo)
    token = get_installation_token(installation_id)
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{ref}?recursive=1"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = await asyncio.to_thread(github_request, "GET", url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to list repository files: {response.status_code} {response.text}")

    tree = response.json().get("tree", [])
    file_paths = [item["path"] for item in tree if item["type"] == "blob"]
    return file_paths

# print(fetch_repo_files("aditi-dsi", "EvalAI-Starters", "master"))

async def fetch_file_content(owner: str, repo: str, path: str, ref: str = "main") -> str:
    """
    Fetches the content of a file from the GitHub repository.
    """
    installation_id = get_installation_id(owner, repo)
    token = await asyncio.to_thread(get_installation_token, installation_id)

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = await asyncio.to_thread(github_request, "GET", url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch file content {path}: {response.status_code} {response.text}")

    content_json = response.json()
    content = base64.b64decode(content_json["content"]).decode("utf-8", errors="ignore")
    return content

# print(fetch_file_content("aditi-dsi", "testing-cryptope", "frontend/src/lib/buildSwap.ts", "main"))

