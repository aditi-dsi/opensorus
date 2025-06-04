import base64
import os
import re
import time
from typing import List, Dict
from llama_index.core import VectorStoreIndex, Document, Settings, get_response_synthesizer
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.embeddings.mistralai import MistralAIEmbedding
from llama_index.llms.mistralai import MistralAI
from mistralai import Mistral
from agent.function_calling import github_request, get_installation_id, get_installation_token
from config import MISTRAL_API_KEY

repo_indices_cache: Dict[str, VectorStoreIndex] = {}
INCLUDE_FILE_EXTENSIONS = {".py", ".js", ".ts", ".json", ".md", ".txt"}

def fetch_repo_files(owner: str, repo: str, ref: str = "main") -> List[str]:
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
    response = github_request("GET", url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to list repository files: {response.status_code} {response.text}")

    tree = response.json().get("tree", [])
    file_paths = [item["path"] for item in tree if item["type"] == "blob"]
    return file_paths

# print(fetch_repo_files("aditi-dsi", "EvalAI-Starters", "master"))

def fetch_file_content(owner: str, repo: str, path: str, ref: str = "main") -> str:
    """
    Fetches the content of a file from the GitHub repository.
    """
    installation_id = get_installation_id(owner, repo)
    token = get_installation_token(installation_id)
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = github_request("GET", url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch file content {path}: {response.status_code} {response.text}")

    content_json = response.json()
    content = base64.b64decode(content_json["content"]).decode("utf-8", errors="ignore")
    return content

# print(fetch_file_content("aditi-dsi", "testing-cryptope", "frontend/src/lib/buildSwap.ts", "main"))

def clean_line(line: str) -> str:
    line = re.sub(r'^\s*\d+[\.\)]\s*', '', line)
    line = line.strip(' `"\'')

    return line.strip()

def select_relevant_files_mistral(issue_description: str, file_paths: List[str]) -> List[str]:

    model = "devstral-small-latest"
    client = Mistral(api_key=MISTRAL_API_KEY)
    
    system_prompt = '''
    You are a code reasoning assistant. Given a GitHub issue description and a list of file paths from a codebase, return a list of top 5 files that are most relevant to solving or understanding the issue, based on naming, possible associations, or inferred logic.

    DO NOT RETURN ANYTHING ELSE. 
    DO NOT RETURN ANY ADDITIONAL INFORMATION OR EXPLANATIONS. 
    ONLY RETURN THE FILE PATHS, ONE PER LINE, WITHOUT ANY ADDITIONAL TEXT OR FORMATTING.
    DO NOT HALLUCINATE.
    '''
    user_prompt = f"""Issue:
{issue_description}

Files:
{chr(10).join(file_paths)}

Return the list of most relevant files (only exact paths)."""

    response = client.chat.complete(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    reply = response.choices[0].message.content if hasattr(response.choices[0].message, "content") else str(response.choices[0].message)

    lines = [line.strip() for line in reply.strip().splitlines()]
    relevant_files = []

    for line in lines:
        cleaned = clean_line(line)
        if cleaned in file_paths:
            relevant_files.append(cleaned)
        # else:
        #     print(f"[Warning] Ignored unexpected line from LLM response: {line}")

    if not relevant_files:
        print("[Info] No valid file paths found in LLM response, defaulting to all files.")
        return file_paths
    else:
        # print("RELEVANT files selected by LLM:")
        return relevant_files

# print(select_relevant_files_mistral('''
# 🛠️ Configuration Error: Placeholder values detected in host_config.json
# This file still includes default placeholders like:

# <evalai_user_auth_token>
# <host_team_pk>
# <evalai_host_url>
# Please replace them with real values to proceed.
# ''',
# ['.github/FUNDING.yml', '.github/workflows/process_challenge.yml', '.gitignore', 'README.md', 'annotations/test_annotations_devsplit.json', 'annotations/test_annotations_testsplit.json', 'challenge_config.yaml', 'challenge_data/__init__.py', 'challenge_data/challenge_1/__init__.py', 'challenge_data/challenge_1/main.py', 'evaluation_script/__init__.py', 'evaluation_script/main.py', 'github/challenge_processing_script.py', 'github/config.py', 'github/host_config.json', 'github/requirements.txt', 'github/utils.py', 'logo.jpg', 'remote_challenge_evaluation/README.md', 'remote_challenge_evaluation/eval_ai_interface.py', 'remote_challenge_evaluation/evaluate.py', 'remote_challenge_evaluation/main.py', 'remote_challenge_evaluation/requirements.txt', 'run.sh', 'submission.json', 'templates/challenge_phase_1_description.html', 'templates/challenge_phase_2_description.html', 'templates/description.html', 'templates/evaluation_details.html', 'templates/submission_guidelines.html', 'templates/terms_and_conditions.html', 'worker/__init__.py', 'worker/run.py']))

def build_repo_index(owner: str, repo: str, ref: str = "main", issue_description: str = "") -> VectorStoreIndex:
    model_name = "codestral-embed"
    embed_model = MistralAIEmbedding(model_name=model_name, api_key=MISTRAL_API_KEY)
    print(f"[Indexing] Starting to index repository: {owner}/{repo} at ref {ref}...")
    file_paths = fetch_repo_files(owner, repo, ref)

    if issue_description:
        file_paths = select_relevant_files_mistral(issue_description, file_paths)

    documents = []
    for path in file_paths:
        _, ext = os.path.splitext(path)
        if ext.lower() not in INCLUDE_FILE_EXTENSIONS:
            continue

        try:
            content = fetch_file_content(owner, repo, path, ref)
            documents.append(Document(text=content, metadata={"file_path": path}))
            print(f"[Indexing] Added file: {path}")
            time.sleep(0.1)
        except Exception as e:
            print(f"[Warning] Skipping file {path} due to error: {e}")

    index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
    print(f"[Indexing] Finished indexing {len(documents)} files.")
    return index

# print(build_repo_index("aditi-dsi", "EvalAI-Starters", "master", 
# '''
# 🛠️ Configuration Error: Placeholder values detected in host_config.json
# This file still includes default placeholders like:

# <evalai_user_auth_token>
# <host_team_pk>
# <evalai_host_url>
# Please replace them with real values to proceed.
# '''))


def get_repo_index(owner: str, repo: str, ref: str, issue_description: str) -> VectorStoreIndex:
    cache_key = f"{owner}/{repo}:{hash(issue_description)}"
    if cache_key in repo_indices_cache:
        print(f"[Cache] Returning cached index for {cache_key}")
        return repo_indices_cache[cache_key]

    index = build_repo_index(owner, repo, ref, issue_description)
    repo_indices_cache[cache_key] = index
    return index


# print(get_repo_index("aditi-dsi", "EvalAI-Starters", "master", 
# '''
# 🛠️ Configuration Error: Placeholder values detected in host_config.json
# This file still includes default placeholders like:

# <evalai_user_auth_token>
# <host_team_pk>
# <evalai_host_url>
# Please replace them with real values to proceed.
# '''))


def retrieve_context(owner: str, repo: str, ref: str, issue_description: str) -> List[str]:
    index = get_repo_index(owner, repo, ref, issue_description)
    Settings.llm = MistralAI(model="codestral-latest", api_key=MISTRAL_API_KEY)
    Settings.embed_model = MistralAIEmbedding(model_name="codestral-embed", api_key=MISTRAL_API_KEY)
    retriever = index.as_retriever(similarity_top_k=5)
    query_engine = RetrieverQueryEngine(
    retriever=retriever,
    response_synthesizer=get_response_synthesizer(),
    node_postprocessors=[SimilarityPostprocessor(similarity_top_k=5)],
    )
    query = f"Please give relevant information from the codebase about that can help to solve or understand this issue:{issue_description}"
    response = query_engine.query(query)
    print(response)
    return None

# index_tools = [
#         {
#         "type": "function",
#         "function": {
#             "name": "retrieve_context",
#             "description": "Fetch relevant context from codebase for a GitHub issue",
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
#                     "ref": {
#                         "type": "string",
#                         "description": "The branch or commit reference to index from."
#                     },
#                     "issue_description": {
#                         "type": "string",
#                         "description": "The description of the issue to retrieve context for."
#                     }
#                 },
#                 "required": ["owner", "repo", "ref", "issue_description"]
#             },
#         },
#     },
# ]