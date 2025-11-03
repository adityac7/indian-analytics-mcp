#!/usr/bin/env python3
"""
HTTP wrapper for Indian Analytics MCP Server
Exposes MCP server via HTTP/SSE for web access
"""

import os
import json
import asyncio
from typing import Optional
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import the MCP server
from indian_analytics_mcp import mcp, DATASETS, load_datasets_from_env

# Load environment variables
load_datasets_from_env()

# Create FastAPI app
app = FastAPI(title="Indian Analytics MCP Server")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connection pools
pools = {}

@app.on_event("startup")
async def startup():
    """Initialize database connection pools."""
    global pools
    for ds_id, ds_info in DATASETS.items():
        pools[ds_id] = await asyncpg.create_pool(
            ds_info["connection"],
            min_size=2,
            max_size=10,
            command_timeout=60
        )
    print(f"✅ Initialized {len(pools)} database connection pool(s)")

@app.on_event("shutdown")
async def shutdown():
    """Close database connection pools."""
    for pool in pools.values():
        await pool.close()
    print("✅ Closed all database connections")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Indian Analytics MCP Server",
        "datasets": len(DATASETS),
        "version": "1.0"
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/datasets")
async def list_datasets():
    """List available datasets."""
    return {
        "datasets": [
            {
                "id": ds_id,
                "name": ds_info["name"],
                "description": ds_info["description"],
                "tables": list(ds_info["dictionary"].keys())
            }
            for ds_id, ds_info in DATASETS.items()
        ]
    }

@app.get("/mcp/sse")
async def mcp_sse(request: Request):
    """SSE endpoint for MCP protocol."""
    # This would require implementing the full MCP SSE transport
    # For now, return a simple response
    return JSONResponse({
        "error": "SSE endpoint not yet implemented",
        "message": "Use the Python MCP client to connect to this server"
    })

# Test query endpoint
@app.post("/query")
async def execute_query(request: Request):
    """Execute a SQL query (for testing purposes)."""
    try:
        data = await request.json()
        dataset_id = data.get("dataset_id", 1)
        query = data.get("query", "")
        
        if dataset_id not in pools:
            return JSONResponse(
                {"error": f"Dataset {dataset_id} not found"},
                status_code=404
            )
        
        pool = pools[dataset_id]
        async with pool.acquire() as conn:
            results = await conn.fetch(query)
            
            # Convert to JSON-serializable format
            rows = [dict(row) for row in results]
            
            return {
                "success": True,
                "rows": rows,
                "count": len(rows)
            }
    
    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
