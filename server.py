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

HEADERS = {"Authorization": f"Bearer {PRACTICE_API_TOKEN}"}
TIMEOUT = 10.0  # seconds; a hung request would leave Claude Code waiting

# MCP Server
mcp = FastMCP("practice-hub")


# Error Handling
def _error_detail(resp: httpx.Response) -> str:
    """Pull the API's error message out of a failed response."""
    try:
        detail = resp.json().get("detail", resp.text)
    except ValueError:
        detail = resp.text
    if isinstance(detail, list) and detail:
        detail = detail[0].get("msg", str(detail[0]))  # 422 sends a list of validation errors
    return str(detail or resp.reason_phrase)


def _error_message(resp: httpx.Response, post_id: int | None) -> str:
    """Turn a failed response into a clear message for the model."""
    code = resp.status_code
    detail = _error_detail(resp)
    if code == 401:
        return "Error 401: the API rejected the token. Check PRACTICE_API_TOKEN (set with --env or in .env)."
    if code == 403:
        if post_id is not None:
            return f"Error 403: post {post_id} belongs to another user. You can only change or delete your own posts."
        return f"Error 403: not allowed ({detail})."
    if code == 404:
        if post_id is not None:
            return f"Error 404: post {post_id} does not exist."
        return f"Error 404: not found ({detail})."
    if code == 422:
        return f"Error 422: the API rejected the input: {detail}"
    return f"Error {code}: {detail}"


async def _request(method: str, path: str, *, params=None, json=None, post_id=None):
    """Call the Practice Hub API.

    Returns (data, None) on success or (None, error_message) on failure.
    It never raises, so one bad request can't crash the server.
    """
    try:
        async with httpx.AsyncClient(base_url=PRACTICE_API_URL, headers=HEADERS, timeout=TIMEOUT) as client:
            resp = await client.request(method, path, params=params, json=json)
    except httpx.TimeoutException:
        return None, f"Error: the Practice Hub API did not respond within {TIMEOUT:g} seconds."
    except httpx.HTTPError as exc:
        return None, f"Error: could not reach the Practice Hub API at {PRACTICE_API_URL} ({type(exc).__name__})."

    if not resp.is_success:
        return None, _error_message(resp, post_id)
    if resp.status_code == 204 or not resp.content:
        return None, None  # success with no body (delete)
    try:
        return resp.json(), None
    except ValueError:
        return None, f"Error: the API returned a non-JSON response (status {resp.status_code})."


# Tools
@mcp.tool()
async def list_posts(mine: bool = True, tag: str | None = None, limit: int = 20) -> list[dict] | str:
    """List posts on Practice Hub, newest first.

    Use this to see the user's posts or to find a post's id before reading,
    editing or deleting it. By default only the user's own posts are returned.

    Args:
        mine: True for only the user's own posts, False for posts from everyone.
        tag: Only return posts with this tag (optional).
        limit: Maximum number of posts to return, 1 to 100.
    """
    params = {"mine": mine, "limit": limit}
    if tag:
        params["tag"] = tag
    data, error = await _request("GET", "/api/v1/posts", params=params)
    return error or data


@mcp.tool()
async def get_post(post_id: int) -> dict | str:
    """Get one Practice Hub post by its id, including its title, body, tags and author.

    Args:
        post_id: The id of the post.
    """
    data, error = await _request("GET", f"/api/v1/posts/{post_id}", post_id=post_id)
    return error or data


@mcp.tool()
async def create_post(title: str, body: str, tags: list[str] | None = None) -> dict | str:
    """Create a new post on Practice Hub as the user. Returns the new post, including its id.

    Args:
        title: The post's title.
        body: The post's text.
        tags: Optional list of tags, for example ["python", "mcp"].
    """
    payload = {"title": title, "body": body, "tags": tags or []}
    data, error = await _request("POST", "/api/v1/posts", json=payload)
    return error or data


@mcp.tool()
async def update_post(
    post_id: int,
    title: str | None = None,
    body: str | None = None,
    tags: list[str] | None = None,
) -> dict | str:
    """Edit one of the user's own Practice Hub posts. Returns the updated post.

    Only the fields you pass are changed; the others stay as they are.
    Passing tags replaces the post's whole tag list. Posts owned by other
    users can't be edited.

    Args:
        post_id: The id of the post to edit.
        title: New title (optional).
        body: New body text (optional).
        tags: New list of tags (optional).
    """
    payload = {key: value for key, value in {"title": title, "body": body, "tags": tags}.items() if value is not None}
    if not payload:
        return "Nothing to update: pass at least one of title, body or tags."
    data, error = await _request("PATCH", f"/api/v1/posts/{post_id}", json=payload, post_id=post_id)
    return error or data


@mcp.tool()
async def delete_post(post_id: int) -> str:
    """Permanently delete one of the user's own Practice Hub posts. This can't be undone.

    Posts owned by other users can't be deleted.

    Args:
        post_id: The id of the post to delete.
    """
    _, error = await _request("DELETE", f"/api/v1/posts/{post_id}", post_id=post_id)
    return error or f"Post {post_id} was deleted."

if __name__ == "__main__":
    mcp.run()  # stdio transport, which is what `claude mcp add ... -- python server.py` expects
