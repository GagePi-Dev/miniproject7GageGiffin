# Practice Hub MCP Server

**INF601 - Advanced Programming in Python | Mini Project 7 | Gage Giffin**

A [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that wraps the Practice Hub REST API, so that Claude Code can read, create, edit and delete your own posts on [practice.fhsucyber.com](https://practice.fhsucyber.com) through it. It is the API client from Mini Project 1, exposed to an AI agent as tools.

The server is built with **FastMCP** from the official `mcp` Python SDK and talks to the API with **httpx**. It runs over the stdio transport, which is what `claude mcp add` expects.

## Tools

Each tool calls one Practice Hub endpoint. The docstrings are written for the model, since Claude reads them to decide which tool to call.

| Tool | API call | What it does |
|---|---|---|
| `list_posts(mine=True, tag=None, limit=20)` | `GET /api/v1/posts` | Lists posts, newest first. Only your own posts by default (`mine`); can filter by tag. |
| `get_post(post_id)` | `GET /api/v1/posts/{id}` | Gets one post with its title, body, tags and author. |
| `create_post(title, body, tags=[])` | `POST /api/v1/posts` | Creates a post and returns it, including its new id. |
| `update_post(post_id, title=None, body=None, tags=None)` | `PATCH /api/v1/posts/{id}` | Edits one of your posts. Only the fields you pass are changed. |
| `delete_post(post_id)` | `DELETE /api/v1/posts/{id}` | Permanently deletes one of your posts. |

## Error Handling

Every request goes through one helper, `_request()`, which never raises. When something goes wrong the tool returns a clear message instead of crashing the server:

| Situation | Message the tool returns |
|---|---|
| 401 bad or missing token | `Error 401: the API rejected the token. Check PRACTICE_API_TOKEN (set with --env or in .env).` |
| 403 post isn't yours | `Error 403: post 12 belongs to another user. You can only change or delete your own posts.` |
| 404 post doesn't exist | `Error 404: post 12 does not exist.` |
| 422 invalid input | `Error 422: the API rejected the input: <the API's validation message>` |
| Any other HTTP error | `Error <code>: <the API's detail message>` |
| API too slow (10 s timeout) | `Error: the Practice Hub API did not respond within 10 seconds.` |
| API unreachable | `Error: could not reach the Practice Hub API at <url> (ConnectError).` |

If `PRACTICE_API_TOKEN` is not set at all, the server refuses to start and prints why.

## Project Structure

```text
miniproject7GageGiffin/
├── server.py                  # the MCP server: config, error handling and the five tools
├── requirements.txt
├── .env.example               # template for the private .env file
├── .gitignore                 # keeps .env and the virtual environment out of Git
└── docs/
    └── acceptance-test.md     # Claude Code transcript of the acceptance test
```

## Requirements

- Python 3.10 or newer (developed on 3.15.2)
- [Claude Code](https://docs.claude.com/en/docs/claude-code)
- A Practice Hub account and API token
- Python packages (in `requirements.txt`):
  - `mcp` 1.30.0 (the official MCP Python SDK, which provides FastMCP)
  - `httpx` 0.28.1
  - `python-dotenv` 1.2.4

`mcp` is pinned to 1.30.0 on purpose. In `mcp` 2.x, `FastMCP` was renamed to `MCPServer`, so `from mcp.server.fastmcp import FastMCP` no longer works there.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/GagePi-Dev/miniproject7GageGiffin.git
cd miniproject7GageGiffin
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\Activate.ps1       # Windows (PowerShell)
```

### 3. Install the requirements

```bash
pip install -r requirements.txt
```

## Setting the Environment Variables

The server reads two environment variables. Nothing is hard-coded in `server.py`.

| Variable | Value |
|---|---|
| `PRACTICE_API_URL` | `https://practice.fhsucyber.com` (used as the default if not set) |
| `PRACTICE_API_TOKEN` | Your personal Practice Hub API token (required) |

**When registering with Claude Code (recommended):** pass both with `--env`, as shown in the next section. Claude Code then sets them every time it starts the server.

**In your shell (for running or testing the server yourself):**

```bash
export PRACTICE_API_URL="https://practice.fhsucyber.com"     # macOS / Linux
export PRACTICE_API_TOKEN="your-token"
```

```powershell
$env:PRACTICE_API_URL = "https://practice.fhsucyber.com"     # Windows PowerShell
$env:PRACTICE_API_TOKEN = "your-token"
```

**Optional fallback: a `.env` file.** If a variable isn't set in the environment, `server.py` looks for it in a `.env` file next to `server.py`:

```bash
cp .env.example .env            # macOS / Linux
copy .env.example .env          # Windows
```

Then paste your token into `.env`. Real environment variables always take priority over `.env`. `.env` is listed in `.gitignore` and is never committed.

If `PRACTICE_API_TOKEN` isn't set in either place, the server refuses to start and prints why.

## Registering with Claude Code

Register the server with both environment variables and the **absolute** path to `server.py`. Use the virtual environment's Python, so the packages from `requirements.txt` are found.

**macOS / Linux:**

```bash
claude mcp add practice-hub \
  --env PRACTICE_API_URL=https://practice.fhsucyber.com \
  --env PRACTICE_API_TOKEN=your-token \
  -- /absolute/path/to/miniproject7GageGiffin/.venv/bin/python /absolute/path/to/miniproject7GageGiffin/server.py
```

**Windows PowerShell** (the line-continuation character is a backtick):

```powershell
claude mcp add practice-hub `
  --env PRACTICE_API_URL=https://practice.fhsucyber.com `
  --env PRACTICE_API_TOKEN=your-token `
  -- C:\absolute\path\to\miniproject7GageGiffin\.venv\Scripts\python.exe C:\absolute\path\to\miniproject7GageGiffin\server.py
```

If the line continuations give you trouble, put the whole command on one line, which works in every shell:

```bash
claude mcp add practice-hub --env PRACTICE_API_URL=https://practice.fhsucyber.com --env PRACTICE_API_TOKEN=your-token -- /absolute/path/to/miniproject7GageGiffin/.venv/bin/python /absolute/path/to/miniproject7GageGiffin/server.py
```

`--env` stores the token in Claude Code's own config file (`~/.claude.json`), outside this repository.

**Alternative: registering with a `.env` file.** If your token is in `.env`, leave out the `--env` flags. This is the command used for this project's acceptance test:

```bash
claude mcp add practice-hub -- /home/ggiffin/Projects/FHSU/miniproject7GageGiffin/.venv/bin/python /home/ggiffin/Projects/FHSU/miniproject7GageGiffin/server.py
```

Check that it connected:

```bash
claude mcp list
# practice-hub: .../.venv/bin/python .../server.py - ✔ Connected
```

The server is registered in the default **local** scope, so it is only available inside this project folder. To remove it: `claude mcp remove practice-hub -s local`.

## Running the Acceptance Test

The acceptance test is: Claude Code, using this server, **reads** your posts, **creates** a new post and **modifies** an existing post.

1. Start a **new** Claude Code session in the project folder (a session that was already open won't see a newly added server):
   ```bash
   cd miniproject7GageGiffin
   claude
   ```
2. Run `/mcp` and confirm `practice-hub` is connected with 5 tools.
3. Give Claude these prompts one at a time, approving each tool call:
   1. `Using the practice-hub MCP server, list my posts.`
   2. `Create a post titled "MCP Server Test" with the body "Created by Claude Code through my Mini Project 7 MCP server." and the tags mcp and python.`
   3. `Update that post's title to "MCP Server Test (edited)" and add the tag inf601.`
   4. `Get that post by its id to confirm the change.`
   5. `Get post 9999999999.` (shows the 404 error handling)
4. Save the transcript with `/export docs/acceptance-test.md`.
5. Optionally, check the post on [practice.fhsucyber.com](https://practice.fhsucyber.com).

### Results

The full transcript is in [`docs/acceptance-test.md`](docs/acceptance-test.md). In it, Claude Code:

- **Read:** listed my posts (none yet), then listed everyone's posts to confirm the token worked.
- **Created:** post **#61**, "MCP Server Test", tagged `mcp` and `python`.
- **Modified:** changed post #61's title to "MCP Server Test (edited)" and added the `inf601` tag, then fetched it with `get_post` to confirm the change was saved.
- **Handled an error:** `get_post(9999999999)` returned `Error 404: post 9999999999 does not exist.` and the server kept running.

## AI Usage

This project was built with help from **Claude Code** (Anthropic's AI coding assistant), using the **Claude Opus 5.5** model, running in the terminal. I set the requirements and the build order. For each step, Claude proposed what it would build, I approved or adjusted it, and then Claude wrote and tested the code. Every commit was made at my direction after I reviewed the step.

### What the AI Did

- **Planning:** reviewed the assignment and my earlier mini projects on GitHub (for the README and AI Usage style), read the Practice Hub API's OpenAPI schema to confirm the endpoints and the `mine` filter, and proposed a step-by-step build plan.
- **Explaining options:** explained the differences between `httpx` and `requests` and recommended `httpx`.
- **Scaffold:** wrote `.gitignore`, `requirements.txt` and `.env.example`.
- **Server setup:** wrote the start of `server.py` with the required header, imports and configuration read from the environment / `.env` file.
- **Version problem:** while installing the packages, found that `mcp` 2.x no longer includes `FastMCP` (it was renamed to `MCPServer`). It stopped and asked me how to proceed instead of choosing for me, then pinned `mcp==1.30.0` when I chose that option.
- **Tools and error handling:** wrote the `_request()` helper and the five tools with their docstrings.
- **Testing:** wrote throwaway test scripts (not part of the repo) that started the server over stdio with a dummy token and listed its tools, ran every tool against a fake API returning 200, 201, 204, 401, 403, 404, 422 and 500 responses plus a timeout and a refused connection, and checked the startup message when the token is missing. With my approval, it ran one live, read-only `list_posts` call to confirm my token worked.
- **Acceptance test help:** explained how to run the acceptance test and reviewed the exported transcript for coverage and leaked secrets.
- **Acceptance test session:** the transcript in `docs/acceptance-test.md` comes from a separate, fresh Claude Code session (Claude Opus 5.5) that called my server's tools in response to my prompts. In that session Claude also suggested raising exceptions instead of returning error strings; I decided to keep returning clear messages, which matches the assignment.
- **Tool-call table:** extracted the tool calls from the acceptance-test session's log and added them as a table to `docs/acceptance-test.md`, leaving out other users' post details.
- **Documentation:** drafted this README.
- **Matching the course instructions:** after I found the course page's `claude mcp add --env ...` command, confirmed that `server.py` already reads real environment variables first (they override `.env`, and the server starts with no `.env` at all), then updated the README to make the `--env` registration the main method and `.env` an optional fallback.

### What I Did Myself

- Set the project requirements and build order, and reviewed and approved every step and commit.
- Chose `httpx` as the HTTP client, a git-ignored `.env` file for the token, the commit style, and pinning `mcp` to 1.30.0.
- Created my `.env` file with my API token, so the token was never shown to the AI.
- Registered the server with Claude Code using `claude mcp add`.
- Ran the acceptance test myself in a new Claude Code session and exported the transcript.

### What I Changed In AI Code

- I made no manual edits to AI code. All changes were made by explaining what I wanted to Claude Code and approving the result.
