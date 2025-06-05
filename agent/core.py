import json
from mistralai import Mistral
from agent.agent_config import prompts
from agent.agent_config import tool_schema
from config import MISTRAL_API_KEY
from tools.code_index import retrieve_context
from tools.github_tools import fetch_github_issue, get_issue_details, post_comment

tools = tool_schema.tools
names_to_functions = {
    "fetch_github_issue": fetch_github_issue,
    "get_issue_details": get_issue_details,
    "retrieve_context": retrieve_context,
    "post_comment": post_comment,
}

allowed_tools = set(names_to_functions.keys())

system_message = prompts.system_message

api_key = MISTRAL_API_KEY
model = "devstral-small-latest"
client = Mistral(api_key=api_key)

def run_agent(issue_url: str, branch_name: str = "main") -> str:
    """
    Run the agent workflow on a given GitHub issue URL.
    """

    MAX_STEPS = 5
    tool_calls = 0
    issue_description_cache = None
    
    user_message = {
        "role": "user",
        "content": f"Please suggest a fix on this issue {issue_url} and use {branch_name} branch for retrieving code context."
    }
    messages = [system_message, user_message]

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

                    if function_name == "get_issue_details" and isinstance(function_result, dict):
                        issue_title = function_result.get("title")
                        issue_body = function_result.get("body")
                        issue_description_cache = issue_title + "\n" + issue_body if issue_title or issue_body else None
                        print("ISSUE DESCRIPTION CACHE ✨:", issue_description_cache)

                    if function_name == "retrieve_context":
                        if "issue_description" in function_params:
                            if (
                                issue_description_cache
                                and (function_params["issue_description"] != issue_description_cache)
                            ):
                                print("🔁 Overriding incorrect issue_description with correct one from cache.")
                                function_params["issue_description"] = issue_description_cache
                                function_result = names_to_functions[function_name](**function_params)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(function_result)
                    })

                    if function_name == "post_comment":
                        print("OpenSorus (final): ✅ Comment posted successfully. No further action needed.")
                        return "Task Completed"

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
    return "Task Completed"