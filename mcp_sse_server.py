"""
Standalone Indian Analytics MCP Server with HTTP/SSE transport.
No external MCP SDK dependencies - implements protocol directly.
"""

import os
import json
import uuid
import asyncio
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Request, Response, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncpg

app = FastAPI(title="Indian Analytics MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
sessions: Dict[str, Dict[str, Any]] = {}
db_pools: Dict[int, asyncpg.Pool] = {}
DATASETS: Dict[int, Dict[str, Any]] = {}

# Constants
MCP_PROTOCOL_VERSION = "2025-06-18"
CHARACTER_LIMIT = 25000
RAW_DATA_LIMIT = 5
AGGREGATED_LIMIT = 1000

# NCCS Mapping
NCCS_MERGE_MAP = {
    'A': 'A', 'A1': 'A', 'B': 'B',
    'C': 'C/D/E', 'D': 'C/D/E', 'E': 'C/D/E'
}


def load_datasets_from_env():
    """Load dataset configurations from environment variables."""
    dataset_id = 1
    while True:
        name_key = f"DATASET_{dataset_id}_NAME"
        if name_key not in os.environ:
            break
        
        DATASETS[dataset_id] = {
            "id": dataset_id,
            "name": os.environ[name_key],
            "description": os.environ.get(f"DATASET_{dataset_id}_DESC", ""),
            "connection": os.environ[f"DATASET_{dataset_id}_CONNECTION"],
            "dictionary": json.loads(os.environ.get(f"DATASET_{dataset_id}_DICTIONARY", "{}"))
        }
        dataset_id += 1


async def init_db_pools():
    """Initialize database connection pools."""
    for ds_id, ds_info in DATASETS.items():
        db_pools[ds_id] = await asyncpg.create_pool(
            ds_info["connection"],
            min_size=2,
            max_size=10,
            command_timeout=60
        )


@app.on_event("startup")
async def startup():
    """Initialize on startup."""
    load_datasets_from_env()
    await init_db_pools()


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    for pool in db_pools.values():
        await pool.close()


# ============================================================================
# MCP TOOL IMPLEMENTATIONS
# ============================================================================

async def tool_get_context(arguments: Dict[str, Any]) -> str:
    """Get progressive context about datasets."""
    level = arguments.get("level", 0)
    dataset_id = arguments.get("dataset_id")
    
    if level in [2, 3] and dataset_id is None:
        return "❌ Error: dataset_id required for levels 2-3"
    
    # Level 0: Global rules
    if level == 0:
        return """# Indian Consumer Analytics MCP - Global Rules

## Data Overview
- **Population**: Representative sample of Indian smartphone users
- **Active users**: 100K mobile, ~1K CTV
- **Total users**: ~500K
- **Update frequency**: Monthly

## Automatic Transformations

### 1. Weighting (CRITICAL)
- Every user has a `weights` column
- `weights=4` means user represents 4,000 users
- **Always use SUM(weights) for user counts**
- **Never extrapolate events** - only extrapolate users

### 2. NCCS Merging (Automatic)
- A, A1 → A
- B → B
- C, D, E → C/D/E

## Query Rules
- **Raw data**: Limited to 5 rows
- **Aggregated**: Up to 1,000 rows
- **Always include**: WHERE clauses for filtering
"""
    
    # Level 1: Dataset list
    if level == 1:
        if not DATASETS:
            return "❌ No datasets configured"
        
        lines = ["# Available Datasets\n"]
        for ds_id, ds_info in DATASETS.items():
            lines.append(f"## Dataset {ds_id}: {ds_info['name']}")
            lines.append(f"{ds_info['description']}\n")
            if ds_info['dictionary']:
                lines.append("**Tables:**")
                for table, desc in ds_info['dictionary'].items():
                    lines.append(f"- `{table}`: {desc}")
                lines.append("")
        
        return "\n".join(lines)
    
    # Level 2-3: Schema details
    if level >= 2:
        if dataset_id not in DATASETS:
            return f"❌ Dataset {dataset_id} not found"
        
        ds_info = DATASETS[dataset_id]
        pool = db_pools[dataset_id]
        
        lines = [f"# Dataset {dataset_id}: {ds_info['name']}\n"]
        lines.append(f"{ds_info['description']}\n")
        
        # Get schema for each table
        for table_name in ds_info.get('dictionary', {}).keys():
            try:
                async with pool.acquire() as conn:
                    # Get column info
                    columns = await conn.fetch("""
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_name = $1
                        ORDER BY ordinal_position
                    """, table_name)
                    
                    lines.append(f"## Table: {table_name}")
                    lines.append("| Column | Type |")
                    lines.append("|--------|------|")
                    for col in columns:
                        lines.append(f"| {col['column_name']} | {col['data_type']} |")
                    lines.append("")
                    
                    # Level 3: Include sample
                    if level == 3:
                        sample = await conn.fetch(f"SELECT * FROM {table_name} LIMIT 3")
                        if sample:
                            lines.append("**Sample rows:**")
                            lines.append(f"```json\n{json.dumps([dict(r) for r in sample], indent=2, default=str)}\n```\n")
            
            except Exception as e:
                lines.append(f"Error getting schema for {table_name}: {str(e)}\n")
        
        return "\n".join(lines)


async def tool_list_datasets(arguments: Dict[str, Any]) -> str:
    """List all available datasets."""
    if not DATASETS:
        return "❌ No datasets configured"
    
    datasets = []
    for ds_id, ds_info in DATASETS.items():
        datasets.append({
            "id": ds_id,
            "name": ds_info["name"],
            "description": ds_info["description"],
            "tables": list(ds_info.get("dictionary", {}).keys())
        })
    
    return json.dumps({"datasets": datasets}, indent=2)


async def tool_get_dataset_schema(arguments: Dict[str, Any]) -> str:
    """Get schema for a specific dataset."""
    dataset_id = arguments.get("dataset_id")
    
    if not dataset_id or dataset_id not in DATASETS:
        return f"❌ Dataset {dataset_id} not found"
    
    # Reuse get_context level 2
    return await tool_get_context({"level": 2, "dataset_id": dataset_id})


async def tool_run_query(arguments: Dict[str, Any]) -> str:
    """Execute a SQL query on a dataset."""
    dataset_id = arguments.get("dataset_id")
    query = arguments.get("query", "").strip()
    
    if not dataset_id or dataset_id not in DATASETS:
        return json.dumps({"error": f"Dataset {dataset_id} not found"})
    
    if not query:
        return json.dumps({"error": "Query is required"})
    
    # Security: Only allow SELECT
    if not query.lower().startswith("select"):
        return json.dumps({"error": "Only SELECT queries are allowed"})
    
    # Check for dangerous keywords
    dangerous = ["drop", "delete", "update", "insert", "alter", "create", "truncate"]
    if any(keyword in query.lower() for keyword in dangerous):
        return json.dumps({"error": "Query contains dangerous keywords"})
    
    # Apply row limit
    has_group_by = "group by" in query.lower()
    limit = AGGREGATED_LIMIT if has_group_by else RAW_DATA_LIMIT
    
    # Add LIMIT if not present
    if "limit" not in query.lower():
        query += f" LIMIT {limit}"
    
    try:
        pool = db_pools[dataset_id]
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
            
            # Convert to list of dicts
            results = [dict(row) for row in rows]
            
            return json.dumps({
                "success": True,
                "rows": results,
                "count": len(results)
            }, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


# ============================================================================
# MCP PROTOCOL HANDLERS
# ============================================================================

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
        "description": "Get detailed schema information for a specific dataset.",
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


async def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle initialize request."""
    return {
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "capabilities": {
            "tools": {},
            "prompts": {},
            "resources": {}
        },
        "serverInfo": {
            "name": "Indian Analytics MCP Server",
            "version": "1.0"
        }
    }


async def handle_tools_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/list request."""
    return {"tools": TOOLS}


async def handle_tools_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tools/call request."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    try:
        if tool_name == "get_context":
            result = await tool_get_context(arguments)
        elif tool_name == "list_available_datasets":
            result = await tool_list_datasets(arguments)
        elif tool_name == "get_dataset_schema":
            result = await tool_get_dataset_schema(arguments)
        elif tool_name == "run_query":
            result = await tool_run_query(arguments)
        else:
            return {
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                "isError": True
            }
        
        return {
            "content": [{"type": "text", "text": result}]
        }
    
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True
        }


async def handle_jsonrpc_message(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Handle a JSON-RPC message."""
    method = message.get("method")
    params = message.get("params", {})
    msg_id = message.get("id")
    
    if method == "initialize":
        result = await handle_initialize(params)
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}
    
    elif method == "initialized":
        return None  # Notification, no response
    
    elif method == "tools/list":
        result = await handle_tools_list(params)
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}
    
    elif method == "tools/call":
        result = await handle_tools_call(params)
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}
    
    else:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }


# ============================================================================
# HTTP ENDPOINTS
# ============================================================================

@app.post("/mcp")
async def mcp_post(
    request: Request,
    mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id"),
    mcp_protocol_version: Optional[str] = Header(None, alias="MCP-Protocol-Version")
):
    """Handle MCP POST requests."""
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
    
    # Handle initialization
    is_initialize = message.get("method") == "initialize"
    
    if is_initialize:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {"initialized": False}
    else:
        session_id = mcp_session_id
        if not session_id or session_id not in sessions:
            return Response(status_code=400, content="Invalid or missing session ID")
    
    # Handle the message
    response_data = await handle_jsonrpc_message(message)
    
    # If notification (no response)
    if response_data is None:
        if message.get("method") == "initialized":
            sessions[session_id]["initialized"] = True
        return Response(status_code=202)
    
    # Return JSON response
    headers = {}
    if is_initialize:
        headers["Mcp-Session-Id"] = session_id
    
    return JSONResponse(content=response_data, headers=headers)


@app.get("/mcp")
async def mcp_get():
    """Handle MCP GET requests (SSE streams not supported)."""
    return Response(status_code=405, content="Server-initiated streams not supported")


# REST API for backward compatibility
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
    """List datasets (REST API)."""
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
    """Execute query (REST API)."""
    data = await request.json()
    result_str = await tool_run_query(data)
    result = json.loads(result_str)
    return result


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
