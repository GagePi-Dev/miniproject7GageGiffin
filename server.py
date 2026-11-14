# INF601 - Advanced Programming in Python
# Gage Giffin
# Mini Project 7

# Imports
import os

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Configuration
# Values come from the environment, or from a git-ignored .env file.
# Nothing secret is hard-coded here.
load_dotenv()

PRACTICE_API_URL = os.environ.get("PRACTICE_API_URL", "https://practice.fhsucyber.com").rstrip("/")
PRACTICE_API_TOKEN = os.environ.get("PRACTICE_API_TOKEN")

if not PRACTICE_API_TOKEN:
    # SystemExit prints to stderr, which keeps stdout clean for the MCP stdio transport.
    raise SystemExit(
        "PRACTICE_API_TOKEN is not set. Add it to your .env file "
        "(see .env.example) or export it in your shell."
    )

# MCP Server
mcp = FastMCP("practice-hub")

# Tools go here (next step)

if __name__ == "__main__":
    mcp.run()  # stdio transport, which is what `claude mcp add ... -- python server.py` expects
