# OpenSorus - AI Maintainer Agent for GitHub Issues
<p align="center"><img width="65%" src="https://res.cloudinary.com/ivolve/image/upload/v1749392337/opensorus-banner_wel6po.jpg"/></p>

> The OSS Copilot for automated triage & instant GitHub issue support with helpful context aware replies.

OpenSorus is an AI Agent distributed as a GitHub App that reads your GitHub issues, understands your codebase, and responds with a comment to help your users/contributors. It acts like a first-level dev support assistant of your project that never sleeps and actually understands your codebase.

## Features

Once installed and triggered on a GitHub issue (either via @mention or through the Gradio interface), OpenSorus autonomously:

- Pulls issue context from GitHub

- Indexes relevant parts of your codebase to match with the issue using semantic similarity search mechanisms.

- Retrieves relevant code snippets or docs from the repo.

- Crafts a useful, relevant reply by using the context from the codebase and generative capabilities of its own.

- Posts the response back as a GitHub comment.

## Goal
Open source projects often get overwhelmed with open issues, thanks to their inclusive and collaborative nature. But that openness should feel empowering, not exhausting, for all, including maintainers & contributors.

OpenSorus aims to make the life of open-source projects a little easier by handling the P1-level issues.
Built for open source maintainers & teams who want to reduce issue backlog, increase community engagement and free up time to focus on critical issues.

## Demo Video
🎥 Watch the [Demo Video here](https://www.loom.com/share/d39697a60b944dbb938c3952d66cdc62?sid=1e730996-c912-4089-b717-a42ac9fbfe25).


## Usage
-  Install the [OpenSorus GitHub App](https://github.com/apps/opensorus).

-  Configure this app for a particular repository by giving access to the repo from the dropdown.

> Follow this guide to learn more about how to [install GitHub apps](https://docs.github.com/en/apps/using-github-apps/installing-a-github-app-from-a-third-party#installing-a-github-app).

Once, you're done installing, there are primarily two ways to use the agent:
### 🔁 Option 1 (Quicker): Auto-trigger via GitHub mention
1. In any issue, simply comment `@opensorus`.

2. The agent reads your issue, understands your repo, and replies back within seconds.

### 💻 Option 2: Use the Gradio UI on HF Spaces
1. Visit this [space](https://huggingface.co/spaces/Agents-MCP-Hackathon/OpenSorus).
2. Paste your GitHub issue URL.

3. Enter the primary branch name (e.g., main or master).

4. Click Run Agent 🚀.
5. Agent logs back a success message, & you're done!

(Check back the issue's comments for updates).

## Tech Stack

Here’s the tech stack that made it all possible:

🧠 LLM: Devstral (via Mistral API 🧡)

🧬 Embeddings Generation: Codestral-Embed (via Mistral API 🧡)

🗂️ Indexing, Embeddings storage & retrieval: LlamaIndex 🦙

🔎 Querying Context: Codestral (via Mistral API 🧡) + LlamaIndex 🦙

🧱 Infra Provider: Modal Labs

🛠️ GitHub Integration:	GitHub REST API + GitHub Actions

✨ Web Interface: Gradio UI + Hugging Face Spaces


## Limitations
- Expects a well defined issue description for a better response. Vague descriptions may result in unhelpful/vague/irrelevant comment.

- Rate limits may apply if too many requests come frequently.

- Currently optimized for small-mid scale repositories. Might lag or take longer on large/heavy codebases. 

- Only reads issue description as a context, not any further comments on the issue.

- Doesn’t handle PRs or other discussions yet (only issues for now).

## Support
For any feedback, support or bug report:
- Feel free to [open a discussion](https://huggingface.co/spaces/Agents-MCP-Hackathon/OpenSorus/discussions?status=open&type=discussion&sort=recently-created) on HF.

- You can also [open an issue](https://github.com/aditi-dsi/opensorus) on GitHub.

- Or feel free to reach out via DM on [X](https://x.com/halfacupoftea_) or [LinkedIn](https://www.linkedin.com/in/aditi-bindal/).


## Acknowledgements
Made with ❤️ by [Aditi Bindal](https://huggingface.co/halfacupoftea)

Big Thanks to Mistral AI & LlamaIndex for incredible LLMs and Agentic tools and to Hugging Face for providing the opportunitiy to build this agent.

And special shoutout to ChatGPT for designing such a cute logo!


## License
This project is licensed under the MIT License – see the LICENSE file for details.
