import json
from mistralai import Mistral
from agent.function_calling import fetch_github_issue, get_issue_details, post_comment
from agent.code_index import retrieve_context
from config import MISTRAL_API_KEY

tools = [
    {
        "type": "function",
        "function": {
            "name": "fetch_github_issue",
            "description": "Fetch GitHub issue details",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_url": {
                        "type": "string",
                        "description": "The full URL of the GitHub issue"
                    }
                },
                "required": ["issue_url"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_issue_details",
            "description": "Get details of a GitHub issue",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "The owner of the repository."
                    },
                    "repo": {
                        "type": "string",
                        "description": "The name of the repository."
                    },
                    "issue_num": {
                        "type": "string",
                        "description": "The issue number."
                    }
                },
                "required": ["owner", "repo", "issue_num"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_context",
            "description": "Fetch relevant context from codebase for a GitHub issue",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "The owner of the repository."
                    },
                    "repo": {
                        "type": "string",
                        "description": "The name of the repository."
                    },
                    "ref": {
                        "type": "string",
                        "description": "The branch reference from either master or main to index from."
                    },
                    "issue_description": {
                        "type": "string",
                        "description": "The description of the issue to retrieve context for."
                    }
                },
                "required": ["owner", "repo", "ref", "issue_description"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "post_comment",
            "description": "Post a comment on a GitHub issue",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "The owner of the repository."
                    },
                    "repo": {
                        "type": "string",
                        "description": "The name of the repository."
                    },
                    "issue_num": {
                        "type": "string",
                        "description": "The issue number."
                    },
                    "comment_body": {
                        "type": "string",
                        "description": "The body of the comment."
                    }
                },
                "required": ["owner", "repo", "issue_num", "comment_body"],
            },
        },
    },
]

names_to_functions = {
    "fetch_github_issue": fetch_github_issue,
    "get_issue_details": get_issue_details,
    "retrieve_context": retrieve_context,
    "post_comment": post_comment,
}

allowed_tools = set(names_to_functions.keys())

system_message = {
    "role": "system",
    "content": (
        "You are a senior developer assistant bot for GitHub issues.\n\n"

        "Your job is to respond to GitHub issues **professionally** and **helpfully**, but never repeat the issue description verbatim.\n\n"
        "First, classify the issue as one of the following:\n"
        "- Bug report\n"
        "- Implementation question\n"
        "- Feature request\n"
        "- Incomplete or unclear\n\n"

        "Then, based on the classification, write a clear, concise, and friendly response.\n\n"
        "The comment should be well formatted and readable, using Markdown for code blocks and lists where appropriate.\n\n"
        "DO NOT paste or repeat the issue description. DO NOT quote it. Respond entirely in your own words.\n"
        "You can only use the following tools: fetch_github_issue, get_issue_details, retrieve_context, post_comment.\n"
        "Do not attempt to use any other tools such as web_search."
        "DO NOT HALLUCINATE OR MAKE UP TOOLS."
    )
}

user_message = {
    "role": "user",
    "content": "Please suggest a fix on this issue https://github.com/aditi-dsi/testing-cryptope/issues/4."
}

messages = [system_message, user_message]

api_key = MISTRAL_API_KEY
model = "devstral-small-latest"
client = Mistral(api_key=api_key)

MAX_STEPS = 5
tool_calls = 0

while True:
    response = client.chat.complete(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="any",
    )
    msg = response.choices[0].message
    messages.append(msg)

    if hasattr(msg, "tool_calls") and msg.tool_calls:
        for tool_call in msg.tool_calls:
            function_name = tool_call.function.name
            function_params = json.loads(tool_call.function.arguments)
            if function_name in allowed_tools:
                function_result = names_to_functions[function_name](**function_params)
                print(f"Agent is calling tool: {function_name}")
                tool_calls += 1
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(function_result)
                })

                if function_name == "post_comment":
                    print("OpenSorus (final): ✅ Comment posted successfully. No further action needed.")
                    exit(0)

            else:
                print(f"LLM tried to call unknown tool: {function_name}")
                tool_error_msg = (
                    f"Error: Tool '{function_name}' is not available. "
                    "You can only use the following tools: fetch_github_issue, get_issue_details, post_comment."
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_error_msg
                })
        if tool_calls >= MAX_STEPS:
            print(f"Agent stopped after {MAX_STEPS} tool calls to protect against rate limiting.")
            break
    else:
        print("OpenSorus (final):", msg.content)
        break
