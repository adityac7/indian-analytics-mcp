# Indian Analytics MCP Server - Deployment Summary

## 🎉 Deployment Successful!

Your MCP server has been successfully deployed and is now live.

---

## 📍 Hosted URL

**Primary Endpoint**: https://indian-analytics-mcp.onrender.com

---

## 🔗 Quick Links

- **GitHub Repository**: https://github.com/adityac7/indian-analytics-mcp
- **Render Dashboard**: https://dashboard.render.com/web/srv-d444ba3e5dus73ahm5d0
- **Blueprint**: https://dashboard.render.com/blueprint/exs-d444b3pr0fns73fn8e4g

---

## ✅ API Endpoints

### Health Check
```bash
curl https://indian-analytics-mcp.onrender.com/
```

**Response**:
```json
{
    "status": "ok",
    "service": "Indian Analytics MCP Server",
    "datasets": 1,
    "version": "1.0"
}
```

### List Datasets
```bash
curl https://indian-analytics-mcp.onrender.com/datasets
```

**Response**:
```json
{
    "datasets": [
        {
            "id": 1,
            "name": "digital_insights",
            "description": "Mobile app usage data including app opens, duration, demographics, and weighted user representation",
            "tables": [
                "digital_insights",
                "datasets",
                "metadata",
                "query_logs"
            ]
        }
    ]
}
```

### Execute Query
```bash
curl -X POST https://indian-analytics-mcp.onrender.com/query \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": 1,
    "query": "SELECT app_name, COUNT(*) as count FROM digital_insights GROUP BY app_name ORDER BY count DESC LIMIT 5"
  }'
```

**Response**:
```json
{
    "success": true,
    "rows": [
        {
            "app_name": "WhatsApp",
            "count": 72918
        },
        {
            "app_name": "Instagram",
            "count": 52099
        },
        {
            "app_name": "Youtube",
            "count": 45411
        },
        {
            "app_name": "YouTube",
            "count": 42089
        },
        {
            "app_name": "Google Chrome",
            "count": 41034
        }
    ],
    "count": 5
}
```

---

## 📊 Database Configuration

**Connection**: PostgreSQL (Render Singapore)
- **Database**: analytics_db_clug
- **Host**: dpg-d3pmmtali9vc73bn81i0-a.singapore-postgres.render.com
- **Tables**: 
  - `digital_insights` (839,077 rows)
  - `datasets`
  - `metadata`
  - `query_logs`

**Data Statistics**:
- Total rows: 839,077
- Unique users: 634
- Unique apps: 2,138
- Total weighted users: 5.3 million
- Date range: 1970-01-01 to 2025-12-08

---

## 🛠️ Deployment Details

**Platform**: Render
- **Service Type**: Web Service
- **Runtime**: Python 3
- **Plan**: Free Tier
- **Region**: Singapore
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python server.py`
- **Auto-Deploy**: Enabled (on push to master branch)

**Environment Variables** (configured in render.yaml):
- `PORT`: 10000
- `DATASET_1_NAME`: digital_insights
- `DATASET_1_DESC`: Mobile app usage data...
- `DATASET_1_CONNECTION`: postgresql://...
- `DATASET_1_DICTIONARY`: JSON with table descriptions

---

## 🚀 MCP Server Features

### Available MCP Tools

1. **get_context**: Progressive context loading (levels 0-3)
   - Level 0: Global rules (weighting, NCCS merging)
   - Level 1: Dataset list
   - Level 2: Schema for specific dataset
   - Level 3: Full details with samples

2. **list_available_datasets**: List all configured datasets

3. **get_dataset_schema**: Get schema for specific dataset

4. **run_query**: Execute SQL queries with automatic weighting

### Automatic Features

- **Weighting**: All user counts automatically weighted to represent population
- **NCCS Merging**: Socioeconomic class merging (A/A1→A, B→B, C/D/E→C/D/E)
- **Query Limits**: 
  - Raw queries (no GROUP BY): Max 5 rows
  - Aggregated queries (with GROUP BY): Max 1,000 rows

---

## 🔒 Security

- ✅ Read-only queries (SELECT only)
- ✅ Dangerous SQL keywords blocked
- ✅ Connection pooling prevents resource exhaustion
- ⚠️ No authentication (add for production use)
- ⚠️ No rate limiting (add for production use)

---

## 📝 Usage with MCP Clients

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
        "DATASET_1_CONNECTION": "postgresql://analytics_db_clug_user:sa1jEkjEmuIKRxQu3x6Oa83Ep4AWGSAM@dpg-d3pmmtali9vc73bn81i0-a.singapore-postgres.render.com/analytics_db_clug",
        "DATASET_1_DICTIONARY": "{\"digital_insights\": \"Mobile app usage events with demographics and weights\", \"datasets\": \"Dataset metadata\", \"metadata\": \"Column descriptions\", \"query_logs\": \"Query execution logs\"}"
      }
    }
  }
}
```

---

## ⚠️ Important Notes

### Free Tier Limitations

- **Cold Starts**: Service spins down after 15 minutes of inactivity
- **Wake-up Time**: ~50 seconds to wake up on first request
- **Uptime**: Not suitable for production 24/7 services
- **Upgrade**: Consider upgrading to paid plan for production use

### Database Schema

The `digital_insights` table contains:
- `vtionid`: User identifier
- `package`: App package name
- `app_name`: Human-readable app name
- `duration_sum`: Total usage duration
- `event_count`: Number of events
- `date`: Event date
- `type`: Event type
- `cat`: App category
- `genre`: App genre
- `age_bucket`: User age group
- `gender`: User gender
- `nccs_class`: Socioeconomic class
- `state_grp`: State/region
- `weights`: Representativeness weight
- `population`: Population segment
- `day_of_week`: Day of the week

---

## 🔄 Updating the Server

To update the server:

1. Make changes to the code locally
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Your update message"
   git push origin master
   ```
3. Render will automatically detect changes and redeploy

---

## 📞 Support

For issues or questions:
- Check logs in Render Dashboard
- Review README.md in the repository
- Test endpoints with curl or Postman

---

## 🎯 Next Steps

1. **Test the MCP server** with your MCP client (Claude Desktop, etc.)
2. **Monitor performance** in Render Dashboard
3. **Consider upgrading** to paid plan for production use
4. **Add authentication** if exposing to external users
5. **Set up monitoring** and alerts

---

**Deployment Date**: November 3, 2025  
**Version**: 1.0  
**Status**: ✅ Live and Running
