# Indian Analytics MCP Server - Deployment

## Overview

This is a Model Context Protocol (MCP) server that provides access to Indian consumer analytics data stored in PostgreSQL.

## Features

- **Progressive Context Loading**: Get schema and metadata on demand
- **SQL Query Execution**: Run SELECT queries with automatic weighting
- **NCCS Merging**: Automatic socioeconomic class merging (A/A1→A, B→B, C/D/E→C/D/E)
- **Weighted Analysis**: All user counts automatically weighted to represent population
- **HTTP API**: RESTful endpoints for testing and integration

## Deployment

### Render (Recommended)

1. Push this repository to GitHub
2. Connect to Render
3. Deploy using the included `render.yaml` configuration
4. Environment variables are pre-configured in `render.yaml`

### Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATASET_1_NAME=digital_insights
export DATASET_1_DESC="Mobile app usage data"
export DATASET_1_CONNECTION="postgresql://..."
export DATASET_1_DICTIONARY='{"digital_insights": "Main table"}'

# Run server
python server.py
```

## API Endpoints

### Health Check
```
GET /
GET /health
```

### List Datasets
```
GET /datasets
```

### Execute Query (Testing)
```
POST /query
Content-Type: application/json

{
  "dataset_id": 1,
  "query": "SELECT app_name, SUM(weights) as users FROM digital_insights GROUP BY app_name LIMIT 10"
}
```

## Database Schema

### digital_insights Table

Main table containing mobile app usage data:

- `vtionid`: User identifier
- `package`: App package name
- `app_name`: Human-readable app name
- `duration_sum`: Total usage duration
- `event_count`: Number of events
- `date`: Event date
- `type`: Event type (e.g., "app_usage")
- `cat`: App category
- `genre`: App genre
- `age_bucket`: User age group
- `gender`: User gender
- `nccs_class`: Socioeconomic class (A, B, C, D, E)
- `state_grp`: State/region
- `weights`: Representativeness weight (user represents N others)
- `population`: Population segment
- `day_of_week`: Day of the week

## Data Statistics

- **Total rows**: 839,077
- **Unique users**: 634
- **Unique apps**: 2,138
- **Total weighted users**: 5.3 million
- **Date range**: 1970-01-01 to 2025-12-08

## MCP Tools

The server provides these MCP tools:

1. **get_context**: Progressive context loading (levels 0-3)
2. **list_available_datasets**: List all configured datasets
3. **get_dataset_schema**: Get schema for specific dataset
4. **run_query**: Execute SQL queries with automatic weighting

## Usage with MCP Clients

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "indian-analytics": {
      "command": "python",
      "args": ["/path/to/indian_analytics_mcp.py"],
      "env": {
        "DATASET_1_NAME": "digital_insights",
        "DATASET_1_DESC": "Mobile app usage data",
        "DATASET_1_CONNECTION": "postgresql://...",
        "DATASET_1_DICTIONARY": "{\"digital_insights\": \"Main table\"}"
      }
    }
  }
}
```

## Security

- Read-only queries (SELECT only)
- Dangerous SQL keywords blocked
- Connection pooling prevents resource exhaustion
- No authentication (add for production use)

## Support

For issues or questions, check the logs:

```bash
# On Render
View logs in Render dashboard

# Local
Check console output
```

## Version

1.0 - Initial deployment
