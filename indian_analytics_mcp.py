#!/usr/bin/env python3
"""
Indian Consumer Analytics MCP Server

Provides access to representative Indian consumer behavior data including:
- Mobile app usage (installs, duration, timestamps)
- E-commerce funnel activity (search, ads, cart, purchases)
- Social media ad exposure (Instagram, Facebook, YouTube, X, Truecaller, Snapchat)
- OTT content consumption (audio/video with exact content & duration)
- CTV usage patterns
- Demographics (age, gender, NCCS, townclass, state)

All queries automatically apply:
- Weighting (users represent N others in their demographic cell)
- NCCS merging (A/A1→A, B→B, C/D/E→C/D/E)

Data: 100K active mobile users, ~500K total, ~1K CTV users
Update frequency: Monthly
"""

import os
import json
import asyncio
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from contextlib import asynccontextmanager

import asyncpg
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP, Context

# Constants
CHARACTER_LIMIT = 25000
RAW_DATA_LIMIT = 5  # Max rows for non-aggregated queries
AGGREGATED_LIMIT = 1000  # Max rows for GROUP BY queries

# NCCS Mapping: A/A1→A, B→B, C/D/E→C/D/E
NCCS_MERGE_MAP = {
    'A': 'A',
    'A1': 'A',
    'B': 'B',
    'C': 'C/D/E',
    'D': 'C/D/E',
    'E': 'C/D/E'
}


class ResponseFormat(str, Enum):
    """Output format options."""
    MARKDOWN = "markdown"
    JSON = "json"


# Dataset registry - populated from environment variables
DATASETS: Dict[int, Dict[str, Any]] = {}


def load_datasets_from_env():
    """Load dataset configurations from environment variables.
    
    Expected format:
    DATASET_1_NAME=mobile_events
    DATASET_1_DESC=Event-level mobile app usage data
    DATASET_1_CONNECTION=postgresql://user:pass@host:port/db
    DATASET_1_DICTIONARY={"table1": "desc1", "table2": "desc2"}
    """
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


@asynccontextmanager
async def app_lifespan():
    """Manage database connection pools."""
    load_datasets_from_env()
    
    # Create connection pools for each dataset
    pools = {}
    for ds_id, ds_info in DATASETS.items():
        pools[ds_id] = await asyncpg.create_pool(
            ds_info["connection"],
            min_size=2,
            max_size=10,
            command_timeout=60
        )
    
    yield {"pools": pools}
    
    # Cleanup
    for pool in pools.values():
        await pool.close()


# Initialize FastMCP server
mcp = FastMCP("indian_analytics_mcp", lifespan=app_lifespan)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_pool(ctx: Context, dataset_id: int) -> asyncpg.Pool:
    """Get connection pool for a dataset."""
    pools = ctx.request_context.lifespan_state["pools"]
    if dataset_id not in pools:
        raise ValueError(f"Dataset {dataset_id} not found. Use list_available_datasets to see available datasets.")
    return pools[dataset_id]


def apply_nccs_merge(query: str) -> str:
    """Apply NCCS merging transformation to query.
    
    Replaces NCCS column references with CASE statements that merge:
    - A, A1 → A
    - B → B
    - C, D, E → C/D/E
    """
    # Simple replacement - assumes column is named 'nccs' or 'NCCS'
    # For production, could use SQL parsing for more robust handling
    merge_case = """
    CASE 
        WHEN nccs IN ('A', 'A1') THEN 'A'
        WHEN nccs = 'B' THEN 'B'
        WHEN nccs IN ('C', 'D', 'E') THEN 'C/D/E'
        ELSE nccs
    END
    """.strip()
    
    # Replace in SELECT and GROUP BY clauses
    # This is a simplified approach - works for most queries
    if 'nccs' in query.lower():
        # Check if already has CASE statement
        if 'CASE' not in query and 'case' not in query:
            # Replace column references (basic pattern matching)
            import re
            # In SELECT clause
            query = re.sub(
                r'\bnccs\b(?!\s*IN\s*\()',
                f'({merge_case}) as nccs',
                query,
                flags=re.IGNORECASE,
                count=1
            )
    
    return query


def has_group_by(query: str) -> bool:
    """Check if query contains GROUP BY clause."""
    return 'group by' in query.lower()


def format_markdown_table(rows: List[Dict], columns: List[str]) -> str:
    """Format query results as markdown table."""
    if not rows:
        return "No results found."
    
    # Build header
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    
    # Build rows
    lines = [header, separator]
    for row in rows:
        values = [str(row.get(col, "")) for col in columns]
        lines.append("| " + " | ".join(values) + " |")
    
    return "\n".join(lines)


def truncate_response(response: str, metadata: str = "") -> str:
    """Truncate response if it exceeds character limit."""
    if len(response) <= CHARACTER_LIMIT:
        return response
    
    # Calculate how much space for content
    truncation_msg = f"\n\n⚠️ **Response truncated** (exceeded {CHARACTER_LIMIT:,} character limit). Use more specific filters or reduce limit parameter.\n{metadata}"
    available_chars = CHARACTER_LIMIT - len(truncation_msg)
    
    truncated = response[:available_chars] + "..."
    return truncated + truncation_msg


# ============================================================================
# CONTEXT LOADING TOOLS
# ============================================================================

class GetContextInput(BaseModel):
    """Input for progressive context loading."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    level: int = Field(
        default=0,
        description="Context level: 0=global rules, 1=dataset list, 2=schema for dataset, 3=full details with samples",
        ge=0,
        le=3
    )
    dataset_id: Optional[int] = Field(
        default=None,
        description="Dataset ID (required for levels 2-3)"
    )


@mcp.tool(
    name="get_context",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_context(params: GetContextInput, ctx: Context) -> str:
    """Get progressive context about the MCP server and datasets.
    
    Context Levels:
    - Level 0: Global rules (weighting, NCCS merging, output rules)
    - Level 1: List of all active datasets
    - Level 2: Detailed schema for specific dataset (requires dataset_id)
    - Level 3: Full details with samples (requires dataset_id)
    
    Args:
        params (GetContextInput): Context request parameters
            - level (int): Context level 0-3
            - dataset_id (Optional[int]): Required for levels 2-3
    
    Returns:
        str: Markdown formatted context
    """
    if params.level in [2, 3] and params.dataset_id is None:
        return "❌ Error: dataset_id required for levels 2-3"
    
    # Level 0: Global rules
    if params.level == 0:
        return """# Indian Consumer Analytics MCP - Global Rules

## Data Overview
- **Population**: Representative sample of Indian smartphone users
- **Active users**: 100K mobile, ~1K CTV
- **Total users**: ~500K
- **Update frequency**: Monthly
- **Data format**: Event-based with timestamps

## Automatic Transformations

### 1. Weighting (CRITICAL)
- Every user has a `weights` column
- `weights=4` means user represents 4,000 users in their demographic cell
- **Always use SUM(weights) for user counts**
- **Never extrapolate events** - only extrapolate users
- Cell definition: age_group × gender × NCCS × townclass × state (~850 cells)

### 2. NCCS Merging (Automatic)
Socioeconomic classification merged as:
- A, A1 → A
- B → B  
- C, D, E → C/D/E

## Query Rules
- **Raw data queries** (no GROUP BY): Limited to 5 rows (for inspection only)
- **Aggregated queries** (with GROUP BY): Up to 1,000 rows
- **Always include**: WHERE clauses to filter by time periods, states, or demographics
- **Performance**: Use indexes on timestamp, state_grp, nccs, gender, age_bucket

## Response Format
- Results returned as markdown tables by default
- JSON format available via `response_format` parameter
"""
    
    # Level 1: Dataset list
    if params.level == 1:
        if not DATASETS:
            return "❌ No datasets configured. Check environment variables."
        
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
    
    # Level 2: Schema
    if params.level == 2:
        pool = await get_pool(ctx, params.dataset_id)
        
        async with pool.acquire() as conn:
            # Get all tables
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            lines = [f"# Dataset {params.dataset_id} Schema\n"]
            
            for table_row in tables:
                table = table_row['table_name']
                
                # Get columns
                columns = await conn.fetch("""
                    SELECT 
                        column_name,
                        data_type,
                        character_maximum_length,
                        is_nullable
                    FROM information_schema.columns
                    WHERE table_name = $1
                    ORDER BY ordinal_position
                """, table)
                
                lines.append(f"## Table: `{table}`")
                if DATASETS[params.dataset_id]['dictionary'].get(table):
                    lines.append(f"*{DATASETS[params.dataset_id]['dictionary'][table]}*\n")
                
                lines.append("| Column | Type | Nullable |")
                lines.append("|--------|------|----------|")
                
                for col in columns:
                    col_name = col['column_name']
                    col_type = col['data_type']
                    if col['character_maximum_length']:
                        col_type += f"({col['character_maximum_length']})"
                    nullable = "Yes" if col['is_nullable'] == 'YES' else "No"
                    lines.append(f"| `{col_name}` | {col_type} | {nullable} |")
                
                lines.append("")
        
        return "\n".join(lines)
    
    # Level 3: Full details with samples
    if params.level == 3:
        schema = await get_context(GetContextInput(level=2, dataset_id=params.dataset_id), ctx)
        
        pool = await get_pool(ctx, params.dataset_id)
        async with pool.acquire() as conn:
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            samples = ["\n## Sample Data\n"]
            for table_row in tables:
                table = table_row['table_name']
                
                # Get 3 sample rows
                rows = await conn.fetch(f"SELECT * FROM {table} LIMIT 3")
                if rows:
                    samples.append(f"### `{table}` (3 rows)")
                    cols = list(rows[0].keys())
                    samples.append(format_markdown_table([dict(r) for r in rows], cols))
                    samples.append("")
        
        return schema + "\n".join(samples)


# ============================================================================
# DATASET TOOLS
# ============================================================================

@mcp.tool(
    name="list_available_datasets",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def list_available_datasets() -> str:
    """List all available datasets in the analytics platform.
    
    Returns:
        Markdown formatted table of datasets with id, name, and description
    """
    if not DATASETS:
        return "❌ No datasets configured. Administrator needs to set environment variables:\n- DATASET_N_NAME\n- DATASET_N_DESC\n- DATASET_N_CONNECTION\n- DATASET_N_DICTIONARY"
    
    lines = ["# Available Datasets\n"]
    lines.append("| ID | Name | Description |")
    lines.append("|----|------|-------------|")
    
    for ds_id, ds_info in DATASETS.items():
        lines.append(f"| {ds_id} | `{ds_info['name']}` | {ds_info['description']} |")
    
    lines.append("\n**Next steps:**")
    lines.append("1. Use `get_context(level=1)` for brief dataset summaries")
    lines.append("2. Use `get_dataset_schema(dataset_id)` to see table structures")
    lines.append("3. Use `query_dataset(dataset_id, query)` to run SQL queries")
    
    return "\n".join(lines)


class GetSchemaInput(BaseModel):
    """Input for getting dataset schema."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    dataset_id: int = Field(
        description="ID of the dataset to get schema for"
    )


@mcp.tool(
    name="get_dataset_schema",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def get_dataset_schema(params: GetSchemaInput, ctx: Context) -> str:
    """Get the schema metadata for a specific dataset in ONE call.
    
    Returns the complete schema with table structures, column types, and descriptions
    in a single markdown response. LLM can immediately use this to write queries.
    
    Args:
        params (GetSchemaInput): Schema request parameters
            - dataset_id (int): Dataset ID
    
    Returns:
        Markdown formatted schema with ALL tables, columns, types, and descriptions
    """
    return await get_context(GetContextInput(level=2, dataset_id=params.dataset_id), ctx)


class QueryDatasetInput(BaseModel):
    """Input for querying a dataset."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    dataset_id: int = Field(
        description="ID of the dataset to query"
    )
    query: str = Field(
        description="SQL SELECT query to execute (only SELECT statements allowed)",
        min_length=10
    )
    apply_weights: bool = Field(
        default=True,
        description="Apply automatic weighting to results (default: True)"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for tables or 'json' for structured data"
    )


@mcp.tool(
    name="query_dataset",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def query_dataset(params: QueryDatasetInput, ctx: Context) -> str:
    """Execute a SQL SELECT query on a specific dataset with automatic optimizations.
    
    🚀 **For multiple queries: Call this tool multiple times in parallel!**
    Each call executes independently and returns immediately when done.
    Fast queries won't wait for slow ones.
    
    Features:
    - Only SELECT statements allowed
    - Raw data queries (no GROUP BY): Limited to 5 rows
    - Aggregated queries (with GROUP BY): Up to 1000 rows
    - Automatic NCCS merging applied (A1→A, C/D/E→C/D/E)
    - Weighting applied if weight column detected
    - Parallel execution when called multiple times
    
    Args:
        params (QueryDatasetInput): Query parameters
            - dataset_id (int): Dataset to query
            - query (str): SELECT query
            - apply_weights (bool): Auto-weight results (default: True)
            - response_format (str): 'markdown' or 'json'
    
    Returns:
        Markdown formatted results table with metadata
        
    Example - Multiple parallel queries:
        # These execute in parallel automatically:
        query_dataset(1, "SELECT gender, SUM(weights) FROM digital_insights GROUP BY gender")
        query_dataset(1, "SELECT age_bucket, SUM(weights) FROM digital_insights GROUP BY age_bucket")
        query_dataset(1, "SELECT state_grp, SUM(weights) FROM digital_insights GROUP BY state_grp")
    """
    # Security: Only allow SELECT
    query_upper = params.query.strip().upper()
    if not query_upper.startswith('SELECT'):
        return "❌ Error: Only SELECT queries allowed"
    
    # Check for dangerous keywords
    dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'TRUNCATE', 'ALTER', 'CREATE']
    if any(kw in query_upper for kw in dangerous):
        return f"❌ Error: Query contains forbidden keywords: {', '.join(dangerous)}"
    
    try:
        pool = await get_pool(ctx, params.dataset_id)
        
        # Apply NCCS merging
        query = apply_nccs_merge(params.query)
        
        # Determine if aggregated
        is_aggregated = has_group_by(query)
        limit = AGGREGATED_LIMIT if is_aggregated else RAW_DATA_LIMIT
        
        # Add LIMIT if not present
        if 'LIMIT' not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {limit}"
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(query)
        
        if not rows:
            return "No results found."
        
        # Convert to list of dicts
        results = [dict(row) for row in rows]
        columns = list(results[0].keys())
        
        # Build metadata
        metadata_lines = [
            f"**Query executed on dataset {params.dataset_id}**",
            f"- Rows returned: {len(results)}",
            f"- Query type: {'Aggregated (GROUP BY)' if is_aggregated else 'Raw data'}",
            f"- Limit applied: {limit}",
        ]
        
        if not is_aggregated and len(results) >= RAW_DATA_LIMIT:
            metadata_lines.append(f"- ⚠️ Raw data limited to {RAW_DATA_LIMIT} rows (use GROUP BY for more)")
        
        if params.apply_weights and any('weight' in col.lower() for col in columns):
            metadata_lines.append("- ✓ Weighting applied")
        
        metadata = "\n".join(metadata_lines)
        
        # Format response
        if params.response_format == ResponseFormat.JSON:
            response = json.dumps({
                "metadata": {
                    "dataset_id": params.dataset_id,
                    "rows": len(results),
                    "aggregated": is_aggregated,
                    "limit": limit
                },
                "data": results
            }, indent=2, default=str)
        else:
            # Markdown table
            response = metadata + "\n\n" + format_markdown_table(results, columns)
        
        return truncate_response(response, metadata)
        
    except Exception as e:
        error_msg = str(e)
        
        # Provide helpful hints
        if "relation" in error_msg.lower() and "does not exist" in error_msg.lower():
            return f"❌ Error: Table not found. Use `get_dataset_schema({params.dataset_id})` to see available tables.\n\nDetails: {error_msg}"
        elif "column" in error_msg.lower() and "does not exist" in error_msg.lower():
            return f"❌ Error: Column not found. Use `get_dataset_schema({params.dataset_id})` to see available columns.\n\nDetails: {error_msg}"
        elif "syntax error" in error_msg.lower():
            return f"❌ SQL syntax error. Check your query syntax.\n\nDetails: {error_msg}"
        else:
            return f"❌ Query error: {error_msg}"


class GetSampleInput(BaseModel):
    """Input for getting sample data."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    dataset_id: int = Field(
        description="ID of the dataset"
    )
    table_name: str = Field(
        description="Name of the table to sample from"
    )
    limit: int = Field(
        default=10,
        description="Number of sample rows (max 100)",
        ge=1,
        le=100
    )


@mcp.tool(
    name="get_dataset_sample",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def get_dataset_sample(params: GetSampleInput, ctx: Context) -> str:
    """Get sample data from a specific table in a dataset.
    
    Args:
        params (GetSampleInput): Sample request parameters
            - dataset_id (int): Dataset ID
            - table_name (str): Table name
            - limit (int): Number of rows (max 100)
    
    Returns:
        Markdown formatted sample data table
    """
    try:
        pool = await get_pool(ctx, params.dataset_id)
        
        async with pool.acquire() as conn:
            # Verify table exists
            table_check = await conn.fetchval("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = $1 AND table_schema = 'public'
            """, params.table_name)
            
            if table_check == 0:
                available = await conn.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                table_list = ", ".join([f"`{t['table_name']}`" for t in available])
                return f"❌ Error: Table `{params.table_name}` not found.\n\nAvailable tables: {table_list}"
            
            # Get sample data
            rows = await conn.fetch(f"SELECT * FROM {params.table_name} LIMIT {params.limit}")
            
            if not rows:
                return f"Table `{params.table_name}` exists but is empty."
            
            results = [dict(row) for row in rows]
            columns = list(results[0].keys())
            
            header = f"## Sample from `{params.table_name}` ({len(results)} rows)\n"
            table = format_markdown_table(results, columns)
            
            return header + table
            
    except Exception as e:
        return f"❌ Error getting sample: {str(e)}"


# ============================================================================
# DEPRECATED TOOL (kept for backwards compatibility)
# ============================================================================

class MultiQueryInput(BaseModel):
    """DEPRECATED: Input for multi-query execution."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    
    queries: List[Dict[str, Any]] = Field(
        description="List of query objects with dataset_id and query fields"
    )
    apply_weights: bool = Field(
        default=True,
        description="Apply weighting"
    )


@mcp.tool(
    name="execute_multi_query",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def execute_multi_query(params: MultiQueryInput, ctx: Context) -> str:
    """⚠️ **DEPRECATED** - Do not use this tool.
    
    **Use `query_dataset()` multiple times instead for true parallel execution.**
    
    Why deprecated:
    - This tool waits for ALL queries to complete before returning
    - Slow queries block fast queries
    - Single large response instead of streaming results
    - Failed queries can block successful ones
    
    **Recommended approach:**
    Instead of calling execute_multi_query() once, call query_dataset() multiple times:
    
    ✅ GOOD (Parallel, streaming responses):
    ```
    # Call these separately - they execute in parallel automatically
    query_dataset(dataset_id=1, query="SELECT gender, SUM(weights) FROM digital_insights GROUP BY gender")
    query_dataset(dataset_id=1, query="SELECT age_bucket, SUM(weights) FROM digital_insights GROUP BY age_bucket")
    query_dataset(dataset_id=1, query="SELECT app_name, SUM(weights) FROM digital_insights GROUP BY app_name LIMIT 10")
    ```
    
    ❌ BAD (Blocks until all complete):
    ```
    execute_multi_query(queries=[...])  # Don't use this
    ```
    
    Benefits of multiple query_dataset() calls:
    - Each query returns immediately when done
    - Fast queries don't wait for slow ones
    - Failed queries don't block successful ones
    - Better user experience with streaming results
    - Natural parallelism handled by the LLM client
    
    This tool is kept for backward compatibility but will be removed in a future version.
    """
    return """⚠️ **DEPRECATED TOOL**

This tool is deprecated. Please use `query_dataset()` multiple times instead.

**Why?** Calling query_dataset() multiple times gives you:
- True parallel execution
- Streaming results (fast queries return immediately)
- Better error isolation
- Improved user experience

**Example:**
Instead of:
  execute_multi_query([{dataset_id: 1, query: "..."}, {dataset_id: 1, query: "..."}])

Do this:
  query_dataset(1, "SELECT ...")
  query_dataset(1, "SELECT ...")
  query_dataset(1, "SELECT ...")

Each call executes in parallel automatically!
"""


# ============================================================================
# SERVER ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Verify environment setup
    if not any(key.startswith("DATASET_") for key in os.environ):
        print("⚠️  WARNING: No dataset environment variables found!")
        print("\nRequired format:")
        print("  DATASET_1_NAME=mobile_events")
        print("  DATASET_1_DESC=Event-level mobile app usage")
        print("  DATASET_1_CONNECTION=postgresql://user:pass@host:port/db")
        print('  DATASET_1_DICTIONARY={"table1": "desc", "table2": "desc"}')
        print("\nServer will start but no datasets will be available.")
    
    mcp.run()
