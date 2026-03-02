#!/usr/bin/env python3

"""
WordPress MCP SSE Server for OpenAI and ChatGPT.

This server exposes a Model Context Protocol (MCP) tools interface over
HTTP(S) + Server-Sent Events (SSE), allowing ChatGPT to manage posts
on a WordPress site via the WordPress REST API.
"""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from mcp.server import Server
from mcp.types import TextContent, Tool
from sse_starlette.sse import EventSourceResponse


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

WORDPRESS_URL: str = "https://your-wordpress-site.com/"
WORDPRESS_USERNAME: str = "your-username"
WORDPRESS_PASSWORD: str = "your-password"


# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("wordpress-mcp-sse-server")


# ---------------------------------------------------------------------------
# WordPress MCP client
# ---------------------------------------------------------------------------


class WordPressMCP:
    """
    Async client wrapper around the WordPress REST API.
    """

    def __init__(self, base_url: str, username: str, password: str) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.username = username
        self.password = password
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            auth=(self.username, self.password),
            timeout=httpx.Timeout(30.0),
        )
        logger.info("Initialized WordPressMCP with base_url=%s", self.base_url)

    async def create_post(
        self,
        title: str,
        content: str,
        excerpt: str = "",
        status: str = "publish",
    ) -> Dict[str, Any]:
        """
        Create a new WordPress post.
        """
        url = "wp-json/wp/v2/posts"
        payload: Dict[str, Any] = {
            "title": title,
            "content": content,
            "excerpt": excerpt,
            "status": status,
        }
        logger.info("Creating WordPress post: %s", title)
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            post_id = data.get("id")
            post_url = data.get("link") or data.get("guid", {}).get("rendered")
            logger.info("Created WordPress post id=%s url=%s", post_id, post_url)
            return {
                "success": True,
                "post_id": post_id,
                "url": post_url,
                "message": "Post created successfully.",
                "raw": data,
            }
        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to create post (status error): %s - %s",
                e.response.status_code,
                e.response.text,
            )
            return {
                "success": False,
                "post_id": None,
                "url": None,
                "message": f"HTTP error creating post: {e.response.status_code}",
                "error": e.response.text,
            }
        except httpx.RequestError as e:
            logger.error("Failed to create post (request error): %s", str(e))
            return {
                "success": False,
                "post_id": None,
                "url": None,
                "message": "Network error creating post.",
                "error": str(e),
            }
        except Exception as e:
            logger.exception("Unexpected error creating post")
            return {
                "success": False,
                "post_id": None,
                "url": None,
                "message": "Unexpected error creating post.",
                "error": str(e),
            }

    async def update_post(
        self,
        post_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        excerpt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing WordPress post.
        """
        url = f"wp-json/wp/v2/posts/{post_id}"
        payload: Dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if content is not None:
            payload["content"] = content
        if excerpt is not None:
            payload["excerpt"] = excerpt

        logger.info("Updating WordPress post id=%s with fields=%s", post_id, list(payload.keys()))
        if not payload:
            return {
                "success": False,
                "post_id": post_id,
                "url": None,
                "message": "No fields provided to update.",
            }

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            post_url = data.get("link") or data.get("guid", {}).get("rendered")
            logger.info("Updated WordPress post id=%s url=%s", post_id, post_url)
            return {
                "success": True,
                "post_id": data.get("id", post_id),
                "url": post_url,
                "message": "Post updated successfully.",
                "raw": data,
            }
        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to update post id=%s (status error): %s - %s",
                post_id,
                e.response.status_code,
                e.response.text,
            )
            return {
                "success": False,
                "post_id": post_id,
                "url": None,
                "message": f"HTTP error updating post: {e.response.status_code}",
                "error": e.response.text,
            }
        except httpx.RequestError as e:
            logger.error("Failed to update post id=%s (request error): %s", post_id, str(e))
            return {
                "success": False,
                "post_id": post_id,
                "url": None,
                "message": "Network error updating post.",
                "error": str(e),
            }
        except Exception as e:
            logger.exception("Unexpected error updating post id=%s", post_id)
            return {
                "success": False,
                "post_id": post_id,
                "url": None,
                "message": "Unexpected error updating post.",
                "error": str(e),
            }

    async def get_posts(
        self,
        per_page: int = 10,
        page: int = 1,
    ) -> Dict[str, Any]:
        """
        Get a list of WordPress posts.
        """
        url = "wp-json/wp/v2/posts"
        params: Dict[str, Any] = {"per_page": per_page, "page": page}
        logger.info("Fetching WordPress posts per_page=%s page=%s", per_page, page)
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            total_header = response.headers.get("X-WP-Total")
            try:
                total_count: Optional[int] = int(total_header) if total_header is not None else None
            except ValueError:
                total_count = None
            logger.info(
                "Fetched %s posts (reported total=%s)",
                len(data) if isinstance(data, list) else "unknown",
                total_count,
            )
            return {
                "success": True,
                "posts": data,
                "count": len(data) if isinstance(data, list) else 0,
                "total": total_count,
                "message": "Posts fetched successfully.",
            }
        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to fetch posts (status error): %s - %s",
                e.response.status_code,
                e.response.text,
            )
            return {
                "success": False,
                "posts": [],
                "count": 0,
                "total": None,
                "message": f"HTTP error fetching posts: {e.response.status_code}",
                "error": e.response.text,
            }
        except httpx.RequestError as e:
            logger.error("Failed to fetch posts (request error): %s", str(e))
            return {
                "success": False,
                "posts": [],
                "count": 0,
                "total": None,
                "message": "Network error fetching posts.",
                "error": str(e),
            }
        except Exception as e:
            logger.exception("Unexpected error fetching posts")
            return {
                "success": False,
                "posts": [],
                "count": 0,
                "total": None,
                "message": "Unexpected error fetching posts.",
                "error": str(e),
            }

    async def delete_post(self, post_id: int) -> Dict[str, Any]:
        """
        Delete a WordPress post.
        """
        url = f"wp-json/wp/v2/posts/{post_id}"
        logger.info("Deleting WordPress post id=%s", post_id)
        try:
            response = await self.client.delete(url, params={"force": True})
            response.raise_for_status()
            data = response.json()
            logger.info("Deleted WordPress post id=%s", post_id)
            return {
                "success": True,
                "post_id": post_id,
                "message": "Post deleted successfully.",
                "raw": data,
            }
        except httpx.HTTPStatusError as e:
            logger.error(
                "Failed to delete post id=%s (status error): %s - %s",
                post_id,
                e.response.status_code,
                e.response.text,
            )
            return {
                "success": False,
                "post_id": post_id,
                "message": f"HTTP error deleting post: {e.response.status_code}",
                "error": e.response.text,
            }
        except httpx.RequestError as e:
            logger.error("Failed to delete post id=%s (request error): %s", post_id, str(e))
            return {
                "success": False,
                "post_id": post_id,
                "message": "Network error deleting post.",
                "error": str(e),
            }
        except Exception as e:
            logger.exception("Unexpected error deleting post id=%s", post_id)
            return {
                "success": False,
                "post_id": post_id,
                "message": "Unexpected error deleting post.",
                "error": str(e),
            }

    async def close(self) -> None:
        """
        Close the underlying HTTP client.
        """
        logger.info("Closing WordPressMCP HTTP client")
        await self.client.aclose()


# ---------------------------------------------------------------------------
# MCP Server setup: tools
# ---------------------------------------------------------------------------

mcp_server = Server("wordpress-mcp-server")


@mcp_server.list_tools()
async def list_tools_handler() -> List[Tool]:
    """
    Return the list of MCP tools supported by this server.
    """
    tools: List[Tool] = [
        Tool(
            name="create_post",
            description="Create a new WordPress post on your site",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Post title",
                    },
                    "content": {
                        "type": "string",
                        "description": "Post content in HTML",
                    },
                    "excerpt": {
                        "type": "string",
                        "description": "Post excerpt",
                        "default": "",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["publish", "draft", "private"],
                        "default": "publish",
                    },
                },
                "required": ["title", "content"],
            },
        ),
        Tool(
            name="update_post",
            description="Update an existing WordPress post",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_id": {
                        "type": "integer",
                        "description": "ID of the post to update",
                    },
                    "title": {
                        "type": "string",
                        "description": "New title of the post",
                    },
                    "content": {
                        "type": "string",
                        "description": "New content of the post in HTML",
                    },
                    "excerpt": {
                        "type": "string",
                        "description": "New excerpt of the post",
                    },
                },
                "required": ["post_id"],
            },
        ),
        Tool(
            name="get_posts",
            description="Get list of WordPress posts",
            inputSchema={
                "type": "object",
                "properties": {
                    "per_page": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10,
                        "description": "Number of posts per page (1-100)",
                    },
                    "page": {
                        "type": "integer",
                        "minimum": 1,
                        "default": 1,
                        "description": "Page number to fetch",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="delete_post",
            description="Delete a WordPress post",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_id": {
                        "type": "integer",
                        "description": "ID of the post to delete",
                    },
                },
                "required": ["post_id"],
            },
        ),
    ]
    return tools


@mcp_server.call_tool()
async def call_tool_handler(
    name: str,
    arguments: Dict[str, Any],
    request: Optional[Request] = None,
) -> List[TextContent]:
    """
    Handle MCP tool invocations and dispatch to WordPressMCP.

    This handler is intended to be used by higher-level transport
    integrations, such as the JSON-RPC /mcp endpoint below.
    """
    # Retrieve the WordPressMCP instance from the FastAPI app state.
    if request is None:
        raise RuntimeError("Request object is required to access app state.")

    wp: WordPressMCP = request.app.state.wp_client  # type: ignore[attr-defined]

    logger.info("MCP tool call: %s with args=%s", name, arguments)

    if name == "create_post":
        result = await wp.create_post(
            title=str(arguments.get("title", "")),
            content=str(arguments.get("content", "")),
            excerpt=str(arguments.get("excerpt", "")),
            status=str(arguments.get("status", "publish")),
        )
    elif name == "update_post":
        post_id_val = arguments.get("post_id")
        try:
            post_id_int = int(post_id_val)
        except (TypeError, ValueError):
            result = {
                "success": False,
                "post_id": post_id_val,
                "url": None,
                "message": "Invalid post_id; must be an integer.",
            }
        else:
            result = await wp.update_post(
                post_id=post_id_int,
                title=arguments.get("title"),
                content=arguments.get("content"),
                excerpt=arguments.get("excerpt"),
            )
    elif name == "get_posts":
        per_page = arguments.get("per_page", 10)
        page = arguments.get("page", 1)
        try:
            per_page_int = int(per_page)
            page_int = int(page)
        except (TypeError, ValueError):
            result = {
                "success": False,
                "posts": [],
                "count": 0,
                "total": None,
                "message": "per_page and page must be integers.",
            }
        else:
            result = await wp.get_posts(
                per_page=per_page_int,
                page=page_int,
            )
    elif name == "delete_post":
        post_id_val = arguments.get("post_id")
        try:
            post_id_int = int(post_id_val)
        except (TypeError, ValueError):
            result = {
                "success": False,
                "post_id": post_id_val,
                "message": "Invalid post_id; must be an integer.",
            }
        else:
            result = await wp.delete_post(post_id=post_id_int)
    else:
        logger.warning("Unknown MCP tool requested: %s", name)
        result = {
            "success": False,
            "message": f"Unknown tool: {name}",
        }

    content_text = json.dumps(result, ensure_ascii=False)
    return [TextContent(type="text", text=content_text)]


# ---------------------------------------------------------------------------
# FastAPI application with lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context for FastAPI to manage startup and shutdown.
    """
    logger.info("Starting FastAPI app with WordPressMCP client")
    wp_client = WordPressMCP(
        base_url=WORDPRESS_URL,
        username=WORDPRESS_USERNAME,
        password=WORDPRESS_PASSWORD,
    )
    app.state.wp_client = wp_client
    try:
        yield
    finally:
        logger.info("Shutting down FastAPI app and closing WordPressMCP client")
        await wp_client.close()


app = FastAPI(lifespan=lifespan, title="WordPress MCP SSE Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helper: build tool description for root endpoint and tools/list
# ---------------------------------------------------------------------------


async def get_tool_schemas() -> List[Dict[str, Any]]:
    """
    Return tools as plain dicts suitable for JSON responses.
    """
    tools = await list_tools_handler()
    # mcp.types.Tool is a Pydantic model; use model_dump if available.
    tool_dicts: List[Dict[str, Any]] = []
    for t in tools:
        if hasattr(t, "model_dump"):
            tool_dicts.append(t.model_dump())
        else:
            tool_dicts.append(
                {
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.inputSchema,
                }
            )
    return tool_dicts


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/")
async def root() -> Dict[str, Any]:
    """
    Basic information about the server and available endpoints.
    """
    logger.info("GET / - server info requested")
    tools = await get_tool_schemas()
    return {
        "name": "WordPress MCP SSE Server",
        "version": "1.0.0",
        "protocol": "MCP over SSE",
        "endpoints": {
            "health": "/health",
            "sse": "/sse",
            "mcp": "/mcp",
        },
        "tools": tools,
    }


@app.get("/health")
async def health() -> Dict[str, Any]:
    """
    Health check endpoint.
    """
    logger.info("GET /health - health check")
    return {
        "status": "healthy",
        "service": "wordpress-mcp-sse-server",
    }


@app.get("/sse")
async def sse_endpoint(request: Request) -> EventSourceResponse:
    """
    SSE endpoint for ChatGPT.

    Sends an initial "endpoint" event pointing to /mcp and then
    periodic "heartbeat" events every 15 seconds while the
    connection is open.
    """

    async def event_generator() -> AsyncGenerator[Dict[str, str], None]:
        logger.info("New SSE connection from %s", request.client)

        # Initial endpoint event
        endpoint_payload = {"url": str(request.url.replace(path="/mcp", query=""))}
        yield {
            "event": "endpoint",
            "data": json.dumps(endpoint_payload),
        }

        # Periodic heartbeat
        try:
            while True:
                if await request.is_disconnected():
                    logger.info("SSE client disconnected")
                    break
                heartbeat_payload = {"status": "alive"}
                yield {
                    "event": "heartbeat",
                    "data": json.dumps(heartbeat_payload),
                }
                await asyncio.sleep(15)
        except asyncio.CancelledError:
            logger.info("SSE generator cancelled (client disconnected)")
            raise
        except Exception as e:
            logger.exception("Unexpected error in SSE generator: %s", e)

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    }
    return EventSourceResponse(event_generator(), headers=headers)


@app.post("/mcp")
async def mcp_endpoint(request: Request) -> Dict[str, Any]:
    """
    MCP JSON-RPC endpoint.

    Supports:
      - "initialize"
      - "tools/list"
      - "tools/call"
    """
    try:
        body = await request.json()
    except Exception as e:
        logger.error("Failed to parse JSON body for /mcp: %s", e)
        return {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": "Parse error",
            },
        }

    logger.info("POST /mcp - request body: %s", body)

    jsonrpc = body.get("jsonrpc", "2.0")
    method = body.get("method")
    params = body.get("params", {}) or {}
    req_id = body.get("id")

    if method == "initialize":
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
            },
            "serverInfo": {
                "name": "WordPress MCP SSE Server",
                "version": "1.0.0",
            },
        }
        logger.info("MCP initialize called")
        return {
            "jsonrpc": jsonrpc,
            "id": req_id,
            "result": result,
        }

    if method == "tools/list":
        tools = await get_tool_schemas()
        logger.info("MCP tools/list called; returning %s tools", len(tools))
        return {
            "jsonrpc": jsonrpc,
            "id": req_id,
            "result": {
                "tools": tools,
            },
        }

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {}) or {}
        logger.info("MCP tools/call for tool=%s args=%s", tool_name, arguments)

        if not tool_name:
            return {
                "jsonrpc": jsonrpc,
                "id": req_id,
                "error": {
                    "code": -32602,
                    "message": "Missing tool name in params.name",
                },
            }

        try:
            contents = await call_tool_handler(
                name=str(tool_name),
                arguments=arguments,
                request=request,
            )
        except Exception as e:
            logger.exception("Error during MCP tool call for %s", tool_name)
            return {
                "jsonrpc": jsonrpc,
                "id": req_id,
                "error": {
                    "code": -32000,
                    "message": f"Tool call failed: {e}",
                },
            }

        # Convert TextContent objects to plain dicts
        serialized_contents: List[Dict[str, Any]] = []
        for c in contents:
            if hasattr(c, "model_dump"):
                serialized_contents.append(c.model_dump())
            else:
                serialized_contents.append(
                    {
                        "type": c.type,
                        "text": c.text,
                    }
                )

        return {
            "jsonrpc": jsonrpc,
            "id": req_id,
            "result": {
                "content": serialized_contents,
            },
        }

    logger.warning("Unknown MCP method requested: %s", method)
    return {
        "jsonrpc": jsonrpc,
        "id": req_id,
        "error": {
            "code": -32601,
            "message": f"Method not found: {method}",
        },
    }


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    logger.info("Starting WordPress MCP SSE Server on 0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

