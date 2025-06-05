import gradio as gr
from agent.core import run_agent

def respond_to_issue(issue_url, branch_name):
    try:
        result = run_agent(issue_url, branch_name)
        response = "Agent has successfully processed the issue and posted an update in the comments. Check the GitHub issue for updates."
    except Exception as e:
        response = f"Something went wrong: {str(e)}"
    return response

iface = gr.Interface(
    fn=respond_to_issue,
    inputs=[
        gr.Textbox(label="GitHub Issue URL", placeholder="https://github.com/user/repo/issues/123"),
        gr.Textbox(label="Branch Name", placeholder="main or dev or feature/xyz")
    ],
    outputs=gr.Textbox(label="Agent Response"),
    title="OpenSorus – AI Copilot for Timely Dev Support in GitHub Issues",
    description="Running short on time? Just paste the URL of the issue and let the Agent take care of the rest!",
)

if __name__ == "__main__":
    iface.launch()

