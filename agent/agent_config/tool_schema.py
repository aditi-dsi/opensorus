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
                        "description": "The exact issue description from the issue the agent is resolving. Must be passed without rephrasing."
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