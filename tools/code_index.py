import asyncio
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity
import time
from typing import List, Dict
from llama_index.core import VectorStoreIndex, Document, Settings, get_response_synthesizer
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.embeddings.mistralai import MistralAIEmbedding
from llama_index.llms.mistralai import MistralAI
from mistralai import Mistral
from config import MISTRAL_API_KEY
from tools.utils import fetch_repo_files, fetch_file_content


INCLUDE_FILE_EXTENSIONS = {".py", ".js", ".ts", ".json", ".md", ".txt"}

def safe_normalize(vec: np.ndarray) -> np.ndarray:
    vec = np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)
    norm = np.linalg.norm(vec)
    if norm == 0 or np.isnan(norm) or np.isinf(norm):
        return None
    return vec / norm

def select_relevant_files_semantic(issue_description: str, file_paths: List[str]) -> List[str]:
    embed_model = MistralAIEmbedding(model_name="codestral-embed", api_key=MISTRAL_API_KEY)

    issue_embedding = np.array(embed_model.get_text_embedding(issue_description), dtype=np.float64)
    issue_embedding = safe_normalize(issue_embedding)
    if issue_embedding is None:
        print("[Warning] Issue description embedding invalid (zero or NaN norm). Returning empty list.")
        return []

    scored_files = []

    for path in file_paths:
        try:
            file_embedding = np.array(embed_model.get_text_embedding(path), dtype=np.float64)
            file_embedding = safe_normalize(file_embedding)
            if file_embedding is None:
                print(f"[Warning] Skipping {path} due to zero or invalid embedding norm.")
                continue
            
            with np.errstate(divide='ignore', invalid='ignore', over='ignore'):
                score = cosine_similarity([issue_embedding], [file_embedding])[0][0]

            if np.isnan(score) or np.isinf(score):
                print(f"[Warning] Skipping {path} due to invalid similarity score.")
                continue

            scored_files.append((path, score))
        except Exception as e:
            print(f"[Warning] Skipping {path} due to error: {e}")

    top_files = [f[0] for f in sorted(scored_files, key=lambda x: x[1], reverse=True)[:2]]

    if "README.md" in file_paths:
        if "README.md" not in top_files:
            top_files.insert(0, "README.md")

    return top_files


# print(select_relevant_files_semantic(
# '''
# 🛠️ Configuration Error: Placeholder values detected in host_config.json
# This file still includes default placeholders like:

# <evalai_user_auth_token>
# <host_team_pk>
# <evalai_host_url>
# Please replace them with real values to proceed.
# ''',
# ['.github/FUNDING.yml', '.github/workflows/process_challenge.yml', '.gitignore', 'README.md', 'annotations/test_annotations_devsplit.json', 'annotations/test_annotations_testsplit.json', 'challenge_config.yaml', 'challenge_data/__init__.py', 'challenge_data/challenge_1/__init__.py', 'challenge_data/challenge_1/main.py', 'evaluation_script/__init__.py', 'evaluation_script/main.py', 'github/challenge_processing_script.py', 'github/config.py', 'github/host_config.json', 'github/requirements.txt', 'github/utils.py', 'logo.jpg', 'remote_challenge_evaluation/README.md', 'remote_challenge_evaluation/eval_ai_interface.py', 'remote_challenge_evaluation/evaluate.py', 'remote_challenge_evaluation/main.py', 'remote_challenge_evaluation/requirements.txt', 'run.sh', 'submission.json', 'templates/challenge_phase_1_description.html', 'templates/challenge_phase_2_description.html', 'templates/description.html', 'templates/evaluation_details.html', 'templates/submission_guidelines.html', 'templates/terms_and_conditions.html', 'worker/__init__.py', 'worker/run.py']))


# Assuming these are async now or wrapped appropriately
# async def fetch_repo_files(...)
# async def fetch_file_content(...)
# async def VectorStoreIndex.from_documents(...)

async def async_retry_on_429(func, *args, max_retries=3, delay=1, **kwargs):
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            status = getattr(e, 'response', None) and getattr(e.response, 'status_code', None)
            if status == 429:
                print(f"[Retry] Rate limit hit while calling {func.__name__}. Attempt {attempt+1}/{max_retries}. Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                delay *= 2
            else:
                raise

async def build_repo_index(owner: str, repo: str, ref: str = "main", issue_description: str = "") -> VectorStoreIndex:
    model_name = "codestral-embed"
    embed_model = MistralAIEmbedding(model_name=model_name, api_key=MISTRAL_API_KEY)
    print(f"[Indexing] Starting to index repository: {owner}/{repo} at ref {ref}...")

    file_paths = await async_retry_on_429(fetch_repo_files, owner, repo, ref)

    if issue_description:
        file_paths = select_relevant_files_semantic(issue_description, file_paths)  # stays sync unless heavy

    documents = []

    for path in file_paths:
        _, ext = os.path.splitext(path)
        if ext.lower() not in INCLUDE_FILE_EXTENSIONS:
            continue

        try:
            content = await async_retry_on_429(fetch_file_content, owner, repo, path, ref)
            documents.append(Document(text=content, metadata={"file_path": path}))
            print(f"[Indexing] Added file: {path}")
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"[Warning] Skipping file {path} due to error: {e}")

    try:
        index = await async_retry_on_429(VectorStoreIndex.from_documents, documents, embed_model=embed_model)
    except Exception as e:
        print(f"[Error] Failed to build index due to: {e}")
        raise

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


async def retrieve_context(owner: str, repo: str, ref: str, issue_description: str) -> List[str]:
    print("Issue Description:", issue_description)
    index = await build_repo_index(owner, repo, ref, issue_description)
    Settings.llm = MistralAI(model="codestral-latest", api_key=MISTRAL_API_KEY)
    Settings.embed_model = MistralAIEmbedding(model_name="codestral-embed", api_key=MISTRAL_API_KEY)

    retriever = index.as_retriever(similarity_top_k=3)

    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=get_response_synthesizer(),
        node_postprocessors=[
            SimilarityPostprocessor(similarity_top_k=3, similarity_cutoff=0.75)
        ],
    )

    query = (
        f"Please give relevant information from the codebase that highly matches the keywords of this issue and is useful for solving or understanding this issue: {issue_description}\n"
        "STRICT RULES:\n"
        "- ONLY use information available in the retriever context.\n"
        "- DO NOT generate or assume any information outside the given context.\n"
        f"- ONLY include context that is highly relevant and clearly useful for understanding or solving this issue: {issue_description}\n"
        "- DO NOT include generic, loosely related, or unrelated content.\n"
    )

    print("Query:", query)

    # If query_engine.query is sync, wrap it in a thread
    response = await asyncio.to_thread(query_engine.query, query)

    print(response)
    return response

# print(retrieve_context("aditi-dsi", "EvalAI-Starters", "master",
#     '''
#     🛠️ Configuration Error: Placeholder values detected in host_config.json
#     This file still includes default placeholders like:

#     <evalai_user_auth_token>
#     <host_team_pk>
#     <evalai_host_url>
#     Please replace them with real values to proceed.
#     '''))