"""
FastAPI server with MCP Streamable HTTP/SSE transport support.
Wraps the Indian Analytics MCP server for remote access via Claude Desktop.
"""

import os
import json
import uuid
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Response, Header
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncpg

# Import the original MCP server
import sys
sys.path.append('/home/ubuntu/mcp-server-deploy')
from indian_analytics_mcp import (
    get_context,
    list_available_datasets,
    get_dataset_schema,
    run_query,
    DATASETS
)

app = FastAPI(title="Indian Analytics MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session storage (in-memory for simplicity)
sessions: Dict[str, Dict[str, Any]] = {}

# MCP Protocol Version
MCP_PROTOCOL_VERSION = "2025-06-18"

# Server capabilities
SERVER_CAPABILITIES = {
    "tools": {},
    "prompts": {},
    "resources": {}
}

# Tool definitions
TOOLS = [
    {
        "name": "get_context",
        "description": "Get progressive context about available datasets. Use level 0 for global rules, 1 for dataset list, 2 for schema, 3 for full details.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "level": {
                    "type": "integer",
                    "description": "Context level (0-3)",
                    "minimum": 0,
                    "maximum": 3
                },
                "dataset_id": {
                    "type": "integer",
                    "description": "Dataset ID (required for levels 2-3)",
                    "minimum": 1
                }
            },
            "required": ["level"]
        }
    },
    {
        "name": "list_available_datasets",
        "description": "List all available datasets with their IDs, names, and descriptions.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_dataset_schema",
        "description": "Get detailed schema information for a specific dataset including tables, columns, and sample data.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dataset_id": {
                    "type": "integer",
                    "description": "Dataset ID",
                    "minimum": 1
                }
            },
            "required": ["dataset_id"]
        }
    },
    {
        "name": "run_query",
        "description": "Execute a SQL query on a dataset. Queries are automatically weighted. Use GROUP BY for aggregations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dataset_id": {
                    "type": "integer",
                    "description": "Dataset ID",
                    "minimum": 1
                },
                "query": {
                    "type": "string",
                    "description": "SQL SELECT query"
                }
            },
            "required": ["dataset_id", "query"]
        }
    }
]


def create_session_id() -> str:
    """Create a new session ID."""
    return str(uuid.uuid4())


def create_jsonrpc_response(id: Any, result: Any) -> Dict[str, Any]:
    """Create a JSON-RPC response."""
    return {
        "jsonrpc": "2.0",
        "id": id,
        "result": result
    }


def create_jsonrpc_error(id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
    """Create a JSON-RPC error response."""
    error = {
        "code": code,
        "message": message
    }
    if data is not None:
        error["data"] = data
    
    return {
        "jsonrpc": "2.0",
        "id": id,
        "error": error
    }


async def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle initialize request."""
    return {
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "capabilities": SERVER_CAPABILITIES,
        "serverInfo": {
            "name": "Indian Analytics MCP Server",
            "version": "1.0"
        }
    }


async def handle_tools_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/list request."""
    return {
        "tools": TOOLS
    }


async def handle_tools_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/call request."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    try:
        if tool_name == "get_context":
            result = await get_context(arguments)
        elif tool_name == "list_available_datasets":
            result = await list_available_datasets(arguments)
        elif tool_name == "get_dataset_schema":
            result = await get_dataset_schema(arguments)
        elif tool_name == "run_query":
            result = await run_query(arguments)
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown tool: {tool_name}"
                    }
                ],
                "isError": True
            }
        
        # Format result as MCP tool response
        if isinstance(result, str):
            content_text = result
        else:
            content_text = json.dumps(result, indent=2)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": content_text
                }
            ]
        }
    
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error executing tool: {str(e)}"
                }
            ],
            "isError": True
        }


async def handle_jsonrpc_message(message: Dict[str, Any], session_id: Optional[str] = None) -> Dict[str, Any]:
    """Handle a JSON-RPC message and return response."""
    method = message.get("method")
    params = message.get("params", {})
    msg_id = message.get("id")
    
    # Handle different methods
    if method == "initialize":
        result = await handle_initialize(params)
        return create_jsonrpc_response(msg_id, result)
    
    elif method == "initialized":
        # This is a notification, no response needed
        return None
    
    elif method == "tools/list":
        result = await handle_tools_list(params)
        return create_jsonrpc_response(msg_id, result)
    
    elif method == "tools/call":
        result = await handle_tools_call(params)
        return create_jsonrpc_response(msg_id, result)
    
    else:
        return create_jsonrpc_error(
            msg_id,
            -32601,
            f"Method not found: {method}"
        )


async def sse_generator(response_data: Dict[str, Any]):
    """Generate SSE events."""
    # Send the response as an SSE event
    event_data = json.dumps(response_data)
    yield f"data: {event_data}\n\n"


@app.get("/mcp")
async def mcp_get(
    request: Request,
    mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id"),
    mcp_protocol_version: Optional[str] = Header(None, alias="MCP-Protocol-Version")
):
    """
    Handle GET requests to open SSE stream for server-to-client communication.
    """
    # Validate protocol version
    if mcp_protocol_version and mcp_protocol_version != MCP_PROTOCOL_VERSION:
        return Response(status_code=400, content="Unsupported protocol version")
    
    # For now, return 405 as we don't need server-initiated streams
    return Response(status_code=405, content="Server-initiated streams not supported")


@app.post("/mcp")
async def mcp_post(
    request: Request,
    mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id"),
    mcp_protocol_version: Optional[str] = Header(None, alias="MCP-Protocol-Version")
):
    """
    Handle POST requests with JSON-RPC messages.
    Returns either JSON response or SSE stream.
    """
    # Validate protocol version
    if mcp_protocol_version and mcp_protocol_version != MCP_PROTOCOL_VERSION:
        return Response(status_code=400, content="Unsupported protocol version")
    
    # Parse JSON-RPC message
    try:
        message = await request.json()
    except Exception as e:
        return Response(status_code=400, content=f"Invalid JSON: {str(e)}")
    
    # Validate JSON-RPC format
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return Response(status_code=400, content="Invalid JSON-RPC message")
    
    # Check if this is an initialization request
    is_initialize = message.get("method") == "initialize"
    
    # Create or validate session
    if is_initialize:
        # Create new session for initialize
        session_id = create_session_id()
        sessions[session_id] = {"initialized": False}
    else:
        # Validate existing session
        session_id = mcp_session_id
        if not session_id or session_id not in sessions:
            return Response(status_code=400, content="Invalid or missing session ID")
    
    # Handle the message
    response_data = await handle_jsonrpc_message(message, session_id)
    
    # If this is a notification (no response needed)
    if response_data is None:
        # Mark session as initialized if this was the initialized notification
        if message.get("method") == "initialized":
            sessions[session_id]["initialized"] = True
        return Response(status_code=202)
    
    # For initialize, include session ID in header
    headers = {}
    if is_initialize:
        headers["Mcp-Session-Id"] = session_id
    
    # Return JSON response (simpler than SSE for most cases)
    return JSONResponse(
        content=response_data,
        headers=headers
    )


# Keep existing REST API endpoints for backward compatibility
@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Indian Analytics MCP Server",
        "datasets": len(DATASETS),
        "version": "1.0",
        "mcp_endpoint": "/mcp",
        "mcp_protocol_version": MCP_PROTOCOL_VERSION
    }


@app.get("/datasets")
async def list_datasets():
    """List available datasets (REST API)."""
    datasets = []
    for ds_id, ds_info in DATASETS.items():
        datasets.append({
            "id": ds_id,
            "name": ds_info["name"],
            "description": ds_info["description"],
            "tables": list(ds_info.get("dictionary", {}).keys())
        })
    return {"datasets": datasets}


@app.post("/query")
async def execute_query(request: Request):
    """Execute a query (REST API)."""
    data = await request.json()
    dataset_id = data.get("dataset_id")
    query = data.get("query")
    
    if not dataset_id or not query:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing dataset_id or query"}
        )
    
    try:
        result = await run_query({"dataset_id": dataset_id, "query": query})
        # Parse the result if it's a string
        if isinstance(result, str):
            result = json.loads(result)
        return result
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
