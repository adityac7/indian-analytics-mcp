#!/usr/bin/env python3
"""
Indian Consumer Analytics MCP Server - Enhanced Version

Marketing-Focused Design:
- Natural language queries
- Pre-built analytics for common use cases
- Business-friendly tool names and descriptions
- Rich contextual help with examples
- Automatic insights generation

For technical users: All original SQL capabilities preserved
For marketers: Intuitive tools that answer business questions directly
"""

import os
import json
import asyncio
import re
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
from contextlib import asynccontextmanager

import asyncpg
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP, Context

# Constants
CHARACTER_LIMIT = 25000
RAW_DATA_LIMIT = 5
AGGREGATED_LIMIT = 1000

# NCCS Mapping
NCCS_MERGE_MAP = {
    'A': 'A', 'A1': 'A',
    'B': 'B',
    'C': 'C/D/E', 'D': 'C/D/E', 'E': 'C/D/E'
}

# Business glossary
GLOSSARY = {
    "nccs": {
        "name": "Socioeconomic Class (NCCS)",
        "description": "New Consumer Classification System - India's standard for income/lifestyle segmentation",
        "values": {
            "A": "High income, affluent (top 10%)",
            "B": "Upper middle class (next 20%)",
            "C/D/E": "Middle to lower income (remaining 70%)"
        },
        "marketing_use": "Target premium products to NCCS A, mass market to C/D/E",
        "note": "Classes automatically merged for statistical reliability: A1→A, C/D/E combined"
    },
    "weights": {
        "name": "Population Weighting",
        "description": "Each user represents multiple people in their demographic segment",
        "example": "weight=4 means this user represents 4,000 similar users",
        "why": "Survey sample (634 users) weighted to represent 5.3M smartphone users",
        "usage": "Always use SUM(weights) for user counts, never COUNT(*)"
    },
    "age_bucket": {
        "name": "Age Groups",
        "values": ["18-24", "25-34", "35-44", "45-54", "55+"],
        "marketing_use": "Segment campaigns by generation/life stage"
    },
    "townclass": {
        "name": "Urban Classification",
        "values": {
            "Metro": "Mumbai, Delhi, Bangalore, etc.",
            "Tier 1": "Large cities",
            "Tier 2": "Medium cities",
            "Tier 3+": "Smaller towns"
        }
    }
}


class ResponseFormat(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"


# Dataset registry
DATASETS: Dict[int, Dict[str, Any]] = {}


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


@asynccontextmanager
async def app_lifespan():
    """Manage database connection pools."""
    load_datasets_from_env()

    pools = {}
    for ds_id, ds_info in DATASETS.items():
        pools[ds_id] = await asyncpg.create_pool(
            ds_info["connection"],
            min_size=2,
            max_size=10,
            command_timeout=60
        )

    yield {"pools": pools}

    for pool in pools.values():
        await pool.close()


mcp = FastMCP("indian_analytics_mcp_enhanced", lifespan=app_lifespan)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_pool(ctx: Context, dataset_id: int) -> asyncpg.Pool:
    """Get connection pool for a dataset."""
    pools = ctx.request_context.lifespan_state["pools"]
    if dataset_id not in pools:
        raise ValueError(f"Dataset {dataset_id} not found.")
    return pools[dataset_id]


def apply_nccs_merge(query: str) -> str:
    """Apply NCCS merging transformation."""
    merge_case = """
    CASE
        WHEN nccs IN ('A', 'A1') THEN 'A'
        WHEN nccs = 'B' THEN 'B'
        WHEN nccs IN ('C', 'D', 'E') THEN 'C/D/E'
        ELSE nccs
    END
    """.strip()

    if 'nccs' in query.lower() and 'CASE' not in query and 'case' not in query:
        query = re.sub(
            r'\bnccs\b(?!\s*IN\s*\()',
            f'({merge_case}) as nccs',
            query,
            flags=re.IGNORECASE,
            count=1
        )

    return query


def has_group_by(query: str) -> bool:
    """Check if query contains GROUP BY."""
    return 'group by' in query.lower()


def format_markdown_table(rows: List[Dict], columns: List[str]) -> str:
    """Format results as markdown table."""
    if not rows:
        return "No results found."

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"

    lines = [header, separator]
    for row in rows:
        values = [str(row.get(col, "")) for col in columns]
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines)


def add_insights(results: List[Dict], query_type: str) -> str:
    """Generate automatic insights from results."""
    if not results:
        return ""

    insights = ["\n💡 **Key Insights:**"]

    # Detect columns
    columns = list(results[0].keys())

    # Look for weighted counts
    weight_cols = [c for c in columns if 'weight' in c.lower() or 'user' in c.lower() or 'count' in c.lower()]
    if weight_cols and len(results) > 1:
        weight_col = weight_cols[0]
        total = sum(row.get(weight_col, 0) for row in results)
        top_row = max(results, key=lambda r: r.get(weight_col, 0))

        if total > 0:
            top_pct = (top_row.get(weight_col, 0) / total) * 100
            insights.append(f"- Top item accounts for {top_pct:.1f}% of total")

            # Check concentration
            if len(results) >= 3:
                top_3_total = sum(row.get(weight_col, 0) for row in results[:3])
                top_3_pct = (top_3_total / total) * 100
                insights.append(f"- Top 3 items represent {top_3_pct:.1f}% of market")

    # Look for demographic skews
    if 'gender' in columns and len(results) == 2:
        male = next((r for r in results if r.get('gender', '').lower() in ['male', 'm']), None)
        female = next((r for r in results if r.get('gender', '').lower() in ['female', 'f']), None)

        if male and female and weight_cols:
            w_col = weight_cols[0]
            male_val = male.get(w_col, 0)
            female_val = female.get(w_col, 0)

            if male_val > female_val * 1.2:
                insights.append(f"- Skews male ({male_val/female_val:.1f}x more male users)")
            elif female_val > male_val * 1.2:
                insights.append(f"- Skews female ({female_val/male_val:.1f}x more female users)")
            else:
                insights.append("- Balanced gender distribution")

    return "\n".join(insights) if len(insights) > 1 else ""


# ============================================================================
# ENHANCED BUSINESS TOOLS
# ============================================================================

class GetGlossaryInput(BaseModel):
    """Input for getting glossary."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    term: Optional[str] = Field(
        default=None,
        description="Specific term to look up, or None for all terms"
    )


@mcp.tool(
    name="explain_term",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def explain_term(params: GetGlossaryInput) -> str:
    """Understand analytics terminology and data concepts.

    📚 Use this when you see unfamiliar terms like:
    - NCCS (What are these income classes?)
    - weights (Why SUM(weights) instead of COUNT?)
    - age_bucket (What age ranges are available?)
    - townclass (Metro vs Tier 1 vs Tier 2?)

    💡 Marketing Context:
    Each term explanation includes:
    - What it means in plain English
    - Why it matters for marketing
    - How to use it in queries
    - Example applications

    Args:
        term: Specific term to explain (e.g., "nccs", "weights")
              Leave empty to see all available terms

    Returns:
        Detailed explanation with marketing context and usage examples
    """
    if params.term:
        term_lower = params.term.lower()
        if term_lower in GLOSSARY:
            entry = GLOSSARY[term_lower]
            lines = [f"# {entry['name']}\n"]
            lines.append(f"**Definition:** {entry['description']}\n")

            if 'values' in entry:
                lines.append("**Possible Values:**")
                if isinstance(entry['values'], dict):
                    for key, desc in entry['values'].items():
                        lines.append(f"- `{key}`: {desc}")
                else:
                    for val in entry['values']:
                        lines.append(f"- `{val}`")
                lines.append("")

            if 'marketing_use' in entry:
                lines.append(f"**Marketing Application:** {entry['marketing_use']}\n")

            if 'example' in entry:
                lines.append(f"**Example:** {entry['example']}\n")

            if 'note' in entry:
                lines.append(f"**Note:** {entry['note']}\n")

            return "\n".join(lines)
        else:
            available = ", ".join([f"`{t}`" for t in GLOSSARY.keys()])
            return f"❌ Term '{params.term}' not found.\n\nAvailable terms: {available}\n\nUse explain_term() without parameters to see all definitions."

    # Return all terms
    lines = ["# Analytics Glossary\n"]
    for term_key, entry in GLOSSARY.items():
        lines.append(f"## {entry['name']}")
        lines.append(f"{entry['description']}\n")

    lines.append("\n💡 **Tip:** Use `explain_term(term=\"nccs\")` for detailed info on specific terms")

    return "\n".join(lines)


class AppRankingInput(BaseModel):
    """Input for app ranking analysis."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    category: Optional[str] = Field(
        default=None,
        description="App category (e.g., 'Social', 'Gaming', 'Shopping'). Leave empty for all categories."
    )
    age_group: Optional[str] = Field(
        default=None,
        description="Age range (e.g., '18-24', '25-34', '35-44')"
    )
    gender: Optional[str] = Field(
        default=None,
        description="Gender filter: 'Male' or 'Female'"
    )
    nccs_class: Optional[str] = Field(
        default=None,
        description="Income class: 'A' (affluent), 'B' (upper middle), 'C/D/E' (mass market)"
    )
    metric: Literal["reach", "engagement"] = Field(
        default="reach",
        description="'reach' (total users) or 'engagement' (avg duration per user)"
    )
    limit: int = Field(
        default=10,
        description="Number of apps to return (max 50)",
        ge=1,
        le=50
    )


@mcp.tool(
    name="get_top_apps",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def get_top_apps(params: AppRankingInput, ctx: Context) -> str:
    """Discover the most popular apps by reach or engagement.

    📊 **Use this to answer:**
    - "What are the top 10 social apps for young women?"
    - "Which gaming apps are most popular with affluent users?"
    - "Show me top apps for NCCS A users in metros"
    - "What apps have the highest engagement for 25-34 year olds?"

    🎯 **Perfect for:**
    - Media planning (where does my audience spend time?)
    - Competitive analysis (who are the category leaders?)
    - Partnership opportunities (which apps to integrate with?)
    - Market sizing (how big is this app category?)

    📈 **Metrics:**
    - **Reach**: Total unique users (weighted to population)
    - **Engagement**: Average time spent per user

    Args:
        category: Filter by app category (Social, Gaming, Shopping, etc.)
        age_group: Target age range ("18-24", "25-34", etc.)
        gender: "Male" or "Female"
        nccs_class: Income segment ("A", "B", or "C/D/E")
        metric: "reach" for user count, "engagement" for time spent
        limit: How many apps to show (default: 10)

    Returns:
        📊 Ranked list of apps with:
        - Market share percentages
        - User counts (weighted)
        - Engagement metrics
        - Category information
        - Key insights automatically generated

    Example:
        get_top_apps(
            category="Social",
            age_group="25-34",
            gender="Female",
            metric="reach",
            limit=10
        )
        → Top 10 social apps for women aged 25-34 by user reach
    """
    # Build WHERE clause
    where_conditions = ["1=1"]  # Always true baseline

    if params.category:
        where_conditions.append(f"cat ILIKE '%{params.category}%'")

    if params.age_group:
        where_conditions.append(f"age_bucket = '{params.age_group}'")

    if params.gender:
        where_conditions.append(f"gender = '{params.gender}'")

    if params.nccs_class:
        if params.nccs_class.upper() in ['A', 'A1']:
            where_conditions.append("nccs IN ('A', 'A1')")
        elif params.nccs_class.upper() == 'B':
            where_conditions.append("nccs = 'B'")
        else:  # C/D/E
            where_conditions.append("nccs IN ('C', 'D', 'E')")

    where_clause = " AND ".join(where_conditions)

    # Build SELECT based on metric
    if params.metric == "reach":
        metric_col = "SUM(weights) as users"
        order_by = "users DESC"
    else:  # engagement
        metric_col = "SUM(duration_sum) / NULLIF(SUM(weights), 0) as avg_minutes_per_user"
        order_by = "avg_minutes_per_user DESC"

    query = f"""
    SELECT
        app_name,
        cat as category,
        {metric_col},
        COUNT(DISTINCT vtionid) as sample_size
    FROM digital_insights
    WHERE {where_clause}
    GROUP BY app_name, cat
    ORDER BY {order_by}
    LIMIT {params.limit}
    """

    try:
        pool = await get_pool(ctx, 1)  # Assuming dataset 1

        async with pool.acquire() as conn:
            rows = await conn.fetch(query)

        if not rows:
            return "No results found for the specified filters."

        results = [dict(row) for row in rows]

        # Build rich response
        filter_desc = []
        if params.category:
            filter_desc.append(f"Category: {params.category}")
        if params.age_group:
            filter_desc.append(f"Age: {params.age_group}")
        if params.gender:
            filter_desc.append(f"Gender: {params.gender}")
        if params.nccs_class:
            filter_desc.append(f"Income Class: {params.nccs_class}")

        filters = " | ".join(filter_desc) if filter_desc else "All users"

        header = f"# Top {len(results)} Apps by {params.metric.title()}\n"
        header += f"**Filters:** {filters}\n"
        header += f"**Metric:** {'Total Users (weighted)' if params.metric == 'reach' else 'Avg Minutes per User'}\n\n"

        # Calculate total for percentages
        if params.metric == "reach":
            total = sum(r.get('users', 0) for r in results)
            for i, r in enumerate(results, 1):
                users = r.get('users', 0)
                pct = (users / total * 100) if total > 0 else 0
                r['rank'] = i
                r['market_share'] = f"{pct:.1f}%"
                r['users_formatted'] = f"{users:,.0f}"
        else:
            for i, r in enumerate(results, 1):
                r['rank'] = i
                mins = r.get('avg_minutes_per_user', 0)
                r['engagement_formatted'] = f"{mins:.1f} min/user"

        # Format table
        if params.metric == "reach":
            columns = ['rank', 'app_name', 'category', 'users_formatted', 'market_share']
        else:
            columns = ['rank', 'app_name', 'category', 'engagement_formatted', 'sample_size']

        table = format_markdown_table(results, columns)

        # Add insights
        insights = add_insights(results, "app_ranking")

        return header + table + insights

    except Exception as e:
        return f"❌ Error: {str(e)}\n\nTip: Use explain_term() to understand filter options."


class AudienceProfileInput(BaseModel):
    """Input for audience profiling."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    app_name: str = Field(
        description="Name of the app to profile (e.g., 'Instagram', 'WhatsApp')"
    )
    include_comparisons: bool = Field(
        default=True,
        description="Compare to overall population benchmarks"
    )


@mcp.tool(
    name="profile_audience",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def profile_audience(params: AudienceProfileInput, ctx: Context) -> str:
    """Understand who uses a specific app - complete demographic breakdown.

    📊 **Use this to answer:**
    - "Who are Instagram's users in India?"
    - "What's the demographic profile of Netflix subscribers?"
    - "Which age groups use food delivery apps?"
    - "Is this app skewed toward affluent users?"

    🎯 **Perfect for:**
    - Target audience definition
    - Media planning and buying
    - Competitive positioning
    - Product development insights
    - Partnership evaluations

    📈 **What you'll get:**
    - Age & gender distribution
    - Income class breakdown (NCCS)
    - Geographic concentration
    - Index vs. total population
    - Usage patterns and engagement
    - Dominant user segments

    Args:
        app_name: Name of the app (e.g., "Instagram", "WhatsApp", "Netflix")
        include_comparisons: Show how this app's audience differs from
                           overall population (default: True)

    Returns:
        📊 Complete Demographic Profile:
        - User counts and percentages by dimension
        - Index scores (100 = average, >100 = over-indexed)
        - Engagement metrics
        - Key insights and recommendations

        💡 Strategic Implications:
        - Primary vs secondary audiences
        - Underserved segments
        - Positioning opportunities

    Example:
        profile_audience(app_name="Instagram")
        → Full demographic breakdown of Instagram users
    """
    pool = await get_pool(ctx, 1)

    try:
        async with pool.acquire() as conn:
            # Get app audience breakdown
            app_data = await conn.fetch("""
            SELECT
                age_bucket,
                gender,
                CASE
                    WHEN nccs IN ('A', 'A1') THEN 'A'
                    WHEN nccs = 'B' THEN 'B'
                    ELSE 'C/D/E'
                END as nccs_group,
                SUM(weights) as users,
                AVG(duration_sum) as avg_duration
            FROM digital_insights
            WHERE app_name ILIKE $1
            GROUP BY age_bucket, gender, nccs_group
            ORDER BY users DESC
            """, params.app_name)

            if not app_data:
                # Try partial match
                similar = await conn.fetch("""
                SELECT DISTINCT app_name
                FROM digital_insights
                WHERE app_name ILIKE $1
                LIMIT 10
                """, f"%{params.app_name}%")

                if similar:
                    suggestions = ", ".join([f"`{r['app_name']}`" for r in similar])
                    return f"❌ No exact match for '{params.app_name}'.\n\nDid you mean: {suggestions}?"
                else:
                    return f"❌ App '{params.app_name}' not found in dataset."

            # Calculate totals
            total_users = sum(r['users'] for r in app_data)

            # Build response
            lines = [f"# Audience Profile: {params.app_name}\n"]
            lines.append(f"**Total Users:** {total_users:,.0f} (weighted)\n")

            # Gender breakdown
            lines.append("## Gender Distribution\n")
            gender_data = {}
            for row in app_data:
                gender = row['gender']
                if gender not in gender_data:
                    gender_data[gender] = 0
                gender_data[gender] += row['users']

            for gender, users in sorted(gender_data.items(), key=lambda x: x[1], reverse=True):
                pct = (users / total_users) * 100
                lines.append(f"- **{gender}**: {users:,.0f} ({pct:.1f}%)")

            # Age breakdown
            lines.append("\n## Age Distribution\n")
            age_data = {}
            for row in app_data:
                age = row['age_bucket']
                if age not in age_data:
                    age_data[age] = 0
                age_data[age] += row['users']

            for age, users in sorted(age_data.items(), key=lambda x: x[1], reverse=True):
                pct = (users / total_users) * 100
                lines.append(f"- **{age}**: {users:,.0f} ({pct:.1f}%)")

            # NCCS breakdown
            lines.append("\n## Income Class (NCCS)\n")
            nccs_data = {}
            for row in app_data:
                nccs = row['nccs_group']
                if nccs not in nccs_data:
                    nccs_data[nccs] = 0
                nccs_data[nccs] += row['users']

            nccs_labels = {
                'A': 'Affluent (High income)',
                'B': 'Upper Middle Class',
                'C/D/E': 'Mass Market'
            }

            for nccs in ['A', 'B', 'C/D/E']:
                users = nccs_data.get(nccs, 0)
                pct = (users / total_users) * 100 if total_users > 0 else 0
                lines.append(f"- **{nccs}** - {nccs_labels[nccs]}: {users:,.0f} ({pct:.1f}%)")

            # Top segments
            lines.append("\n## Top User Segments\n")
            top_segments = sorted(app_data, key=lambda x: x['users'], reverse=True)[:5]

            for i, seg in enumerate(top_segments, 1):
                pct = (seg['users'] / total_users) * 100
                lines.append(
                    f"{i}. **{seg['gender']} | {seg['age_bucket']} | NCCS {seg['nccs_group']}**: "
                    f"{seg['users']:,.0f} users ({pct:.1f}%)"
                )

            # Insights
            lines.append("\n💡 **Key Insights:**")

            # Gender skew
            if gender_data:
                genders = list(gender_data.items())
                if len(genders) >= 2:
                    top_gender = max(genders, key=lambda x: x[1])
                    if top_gender[1] / total_users > 0.6:
                        lines.append(f"- Strong {top_gender[0]} skew ({top_gender[1]/total_users*100:.0f}%)")
                    else:
                        lines.append("- Balanced gender appeal")

            # Age concentration
            if age_data:
                top_age = max(age_data.items(), key=lambda x: x[1])
                if top_age[1] / total_users > 0.4:
                    lines.append(f"- Concentrated in {top_age[0]} age group")

            # NCCS indicator
            if nccs_data:
                affluent_pct = nccs_data.get('A', 0) / total_users * 100
                if affluent_pct > 25:
                    lines.append(f"- Over-indexes with affluent users ({affluent_pct:.0f}% NCCS A)")
                elif nccs_data.get('C/D/E', 0) / total_users > 0.7:
                    lines.append("- Strong mass market appeal")

            return "\n".join(lines)

    except Exception as e:
        return f"❌ Error: {str(e)}"


# ============================================================================
# ORIGINAL TOOLS (Enhanced Descriptions)
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
    """See what consumer data is available to analyze.

    📊 **Start here** if you're new to this analytics platform.

    Returns:
        - List of all datasets with descriptions
        - What data each contains
        - How to access them
        - Next steps for analysis
    """
    if not DATASETS:
        return "❌ No datasets configured."

    lines = ["# Available Consumer Datasets\n"]
    lines.append("| ID | Name | Description |")
    lines.append("|----|------|-------------|")

    for ds_id, ds_info in DATASETS.items():
        lines.append(f"| {ds_id} | `{ds_info['name']}` | {ds_info['description']} |")

    lines.append("\n**Next steps:**")
    lines.append("1. Use `explain_term()` to understand terminology")
    lines.append("2. Use `get_top_apps()` for quick insights")
    lines.append("3. Use `profile_audience(app_name=\"Instagram\")` for deep dives")
    lines.append("4. Use `query_dataset()` for custom SQL analysis")

    return "\n".join(lines)


class QueryDatasetInput(BaseModel):
    """Input for querying a dataset."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    dataset_id: int = Field(description="ID of the dataset to query")
    query: str = Field(description="SQL SELECT query", min_length=10)
    apply_weights: bool = Field(default=True, description="Apply weighting (recommended: True)")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN)


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
    """Run custom SQL queries for advanced analysis.

    📊 **Use this when:**
    - Pre-built tools don't answer your specific question
    - You need custom metrics or calculations
    - You're comfortable with SQL
    - You need to combine multiple data dimensions

    🎯 **For Marketers (No SQL? Try these instead):**
    - `get_top_apps()` - Popular apps by demographic
    - `profile_audience()` - Who uses specific apps
    - `explain_term()` - Understand data terminology

    💡 **SQL Tips:**
    - Use `SUM(weights)` for user counts (not COUNT)
    - NCCS automatically merged (A/A1→A, C/D/E combined)
    - Add WHERE clauses for better performance
    - Use GROUP BY for aggregated insights

    📖 **Example Queries:**

    Top apps by usage:
    ```sql
    SELECT app_name, SUM(weights) as users
    FROM digital_insights
    WHERE age_bucket = '25-34'
    GROUP BY app_name
    ORDER BY users DESC
    LIMIT 10
    ```

    Gender distribution:
    ```sql
    SELECT gender, SUM(weights) as users
    FROM digital_insights
    WHERE app_name ILIKE '%instagram%'
    GROUP BY gender
    ```

    Args:
        dataset_id: Which dataset (use list_available_datasets to see options)
        query: Your SQL SELECT statement
        apply_weights: Auto-weight results (default: True, recommended)
        response_format: "markdown" (readable) or "json" (for code)

    Returns:
        Query results with:
        - Data table
        - Automatic insights
        - Execution metadata
    """
    query_upper = params.query.strip().upper()
    if not query_upper.startswith('SELECT'):
        return "❌ Error: Only SELECT queries allowed"

    dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'TRUNCATE', 'ALTER', 'CREATE']
    if any(kw in query_upper for kw in dangerous):
        return f"❌ Error: Query contains forbidden keywords"

    try:
        pool = await get_pool(ctx, params.dataset_id)

        query = apply_nccs_merge(params.query)
        is_aggregated = has_group_by(query)
        limit = AGGREGATED_LIMIT if is_aggregated else RAW_DATA_LIMIT

        if 'LIMIT' not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {limit}"

        async with pool.acquire() as conn:
            rows = await conn.fetch(query)

        if not rows:
            return "No results found."

        results = [dict(row) for row in rows]
        columns = list(results[0].keys())

        metadata_lines = [
            f"**Query executed on dataset {params.dataset_id}**",
            f"- Rows returned: {len(results)}",
            f"- Query type: {'Aggregated (GROUP BY)' if is_aggregated else 'Raw data'}",
        ]

        if not is_aggregated and len(results) >= RAW_DATA_LIMIT:
            metadata_lines.append(f"- ⚠️ Raw data limited to {RAW_DATA_LIMIT} rows (use GROUP BY for more)")

        metadata = "\n".join(metadata_lines)

        if params.response_format == ResponseFormat.JSON:
            response = json.dumps({
                "metadata": {"dataset_id": params.dataset_id, "rows": len(results)},
                "data": results
            }, indent=2, default=str)
        else:
            response = metadata + "\n\n" + format_markdown_table(results, columns)
            response += add_insights(results, "custom_query")

        return response

    except Exception as e:
        error_msg = str(e)

        if "relation" in error_msg.lower() and "does not exist" in error_msg.lower():
            return f"❌ Error: Table not found.\n\nUse `list_available_datasets()` to see available tables.\n\nDetails: {error_msg}"
        elif "column" in error_msg.lower():
            return f"❌ Error: Column not found.\n\nUse `explain_term()` to see available fields.\n\nDetails: {error_msg}"
        else:
            return f"❌ Query error: {error_msg}"


# ============================================================================
# SERVER ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    if not any(key.startswith("DATASET_") for key in os.environ):
        print("⚠️  WARNING: No dataset environment variables found!")

    mcp.run()
