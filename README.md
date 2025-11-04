# Indian Consumer Analytics MCP Server

> **AI-powered insights into Indian smartphone users** - Analyze app usage, demographics, and behavior patterns across 5.3M weighted users through natural conversation.

[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What Can You Discover?

### 📱 App Usage Intelligence
- Which apps dominate in your target demographic?
- How does engagement vary by age, gender, and income class?
- Where should you advertise to reach your audience?

### 👥 Audience Insights
- Who are Instagram's users in India?
- What's the demographic profile of gaming app users?
- Which income groups use food delivery apps?

### 🎯 Market Analysis
- What's the market share of top social apps?
- How do competitors compare in reach and engagement?
- Where are the white space opportunities?

### 📊 Trend Discovery
- Which categories are growing fastest?
- What are emerging apps in each segment?
- How do usage patterns differ by region?

---

## Quick Start (5 Minutes)

### For Marketers & Business Users

**No coding required!** Just ask questions in plain English:

```
"What are the top 10 social apps for women aged 25-34?"
"Show me the demographic profile of Instagram users"
"Which gaming apps are popular with affluent users?"
```

**Available Tools:**
- `get_top_apps()` - Discover popular apps by segment
- `profile_audience()` - Understand who uses specific apps
- `explain_term()` - Learn the data (NCCS, weights, etc.)

### For Analysts & Data Scientists

**Full SQL access** with automatic optimizations:

```sql
-- Top apps by reach (auto-weighted)
SELECT app_name, SUM(weights) as users
FROM digital_insights
WHERE age_bucket = '25-34' AND gender = 'Female'
GROUP BY app_name
ORDER BY users DESC
LIMIT 10
```

**Advanced features:**
- Automatic population weighting
- NCCS class merging
- Query optimization suggestions
- Intelligent insights generation

---

## Installation

### Option 1: Use with Claude Desktop (Recommended)

1. **Install the MCP server:**
   ```bash
   git clone https://github.com/adityac7/indian-analytics-mcp.git
   cd indian-analytics-mcp
   pip install -r requirements.txt
   ```

2. **Configure Claude Desktop:**

   Edit `claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "indian-analytics": {
         "command": "python",
         "args": ["/full/path/to/indian_analytics_mcp.py"],
         "env": {
           "DATASET_1_NAME": "digital_insights",
           "DATASET_1_DESC": "Mobile app usage data",
           "DATASET_1_CONNECTION": "postgresql://...",
           "DATASET_1_DICTIONARY": "{\"digital_insights\": \"Mobile app usage events\"}"
         }
       }
     }
   }
   ```

3. **Start asking questions!**

### Option 2: Run as HTTP Server

```bash
# Set environment variables
export DATASET_1_NAME=digital_insights
export DATASET_1_DESC="Mobile app usage data"
export DATASET_1_CONNECTION="postgresql://..."
export DATASET_1_DICTIONARY='{"digital_insights": "Main table"}'

# Run server
python server.py
```

Access at: `http://localhost:10000`

---

## Data Overview

### What's Included

- **100K active users** (mobile app data)
- **5.3M weighted users** (representative of Indian smartphone population)
- **2,138 unique apps** tracked
- **839K+ events** recorded
- **Monthly updates** with latest data

### Demographics Available

- **Age:** 18-24, 25-34, 35-44, 45-54, 55+
- **Gender:** Male, Female
- **Income Class (NCCS):** A (Affluent), B (Upper Middle), C/D/E (Mass Market)
- **Location:** Metro, Tier 1, Tier 2/3 cities
- **States:** All major Indian states

### App Categories

Social Media • Gaming • Shopping • Entertainment • Food & Drink • Health & Fitness • News • Finance • Travel • Education • and more

---

## Usage Examples

### Example 1: Media Planning

**Question:** "Where should we advertise to reach young women?"

```python
get_top_apps(
    age_group="25-34",
    gender="Female",
    metric="reach",
    limit=20
)
```

**Output:**
```
Top 20 Apps by Reach
Filters: Age: 25-34 | Gender: Female

1. WhatsApp - 1,234,567 users (45.2%)
2. Instagram - 987,654 users (36.1%)
3. YouTube - 876,543 users (32.1%)
...

💡 Key Insights:
- Top 3 apps represent 85% of reach
- Social media dominates (6 of top 10)
```

**Decision:** Allocate budget to WhatsApp, Instagram, YouTube

---

### Example 2: Audience Profiling

**Question:** "Who uses Netflix in India?"

```python
profile_audience(app_name="Netflix")
```

**Output:**
```
Audience Profile: Netflix
Total Users: 456,789 (weighted)

Gender Distribution:
- Female: 245,678 (53.8%)
- Male: 211,111 (46.2%)

Age Distribution:
- 25-34: 198,765 (43.5%)
- 35-44: 145,321 (31.8%)
- 18-24: 89,012 (19.5%)

Income Class (NCCS):
- A (Affluent): 198,765 (43.5%)
- B (Upper Middle): 178,654 (39.1%)
- C/D/E (Mass Market): 79,370 (17.4%)

💡 Key Insights:
- Over-indexes with affluent users (43% NCCS A vs 10% population)
- Strong millennial appeal (25-34 dominates)
- Balanced gender distribution
```

**Insight:** Netflix is a premium product appealing to affluent millennials

---

### Example 3: Competitive Analysis

**Question:** "Compare social media apps"

```sql
query_dataset(
    dataset_id=1,
    query="""
    SELECT
        app_name,
        SUM(weights) as total_users,
        SUM(duration_sum) / SUM(weights) as avg_minutes_per_user
    FROM digital_insights
    WHERE cat = 'Social'
    GROUP BY app_name
    ORDER BY total_users DESC
    LIMIT 10
    """
)
```

**Output:** Market share and engagement for top social apps

---

## Available Tools

### 🎯 For Everyone

#### `list_available_datasets()`
See what data is available to analyze.

#### `explain_term(term="nccs")`
Understand analytics terminology:
- NCCS (income classes)
- Weights (population extrapolation)
- Age buckets, town classes, etc.

---

### 📊 For Marketers

#### `get_top_apps(category, age_group, gender, nccs_class, metric, limit)`
Discover the most popular apps by reach or engagement.

**Parameters:**
- `category`: "Social", "Gaming", "Shopping", etc.
- `age_group`: "18-24", "25-34", etc.
- `gender`: "Male" or "Female"
- `nccs_class`: "A", "B", or "C/D/E"
- `metric`: "reach" (user count) or "engagement" (time spent)
- `limit`: Number of apps (default: 10)

**Returns:** Ranked list with market share, insights, and recommendations

---

#### `profile_audience(app_name, include_comparisons)`
Get complete demographic breakdown of app users.

**Parameters:**
- `app_name`: Name of the app (e.g., "Instagram")
- `include_comparisons`: Compare to population benchmarks

**Returns:** Age, gender, income, location breakdowns with strategic insights

---

### 🔧 For Analysts

#### `query_dataset(dataset_id, query, apply_weights, response_format)`
Execute custom SQL queries with automatic optimizations.

**Features:**
- Automatic weighting applied
- NCCS merging handled
- Query optimization suggestions
- Automatic insights generation

**Example:**
```sql
SELECT
    app_name,
    SUM(weights) as users,
    AVG(duration_sum) as avg_engagement
FROM digital_insights
WHERE age_bucket = '25-34'
GROUP BY app_name
ORDER BY users DESC
LIMIT 10
```

---

## Documentation

- **[GLOSSARY.md](GLOSSARY.md)** - Understand all data fields and terminology
- **[USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)** - 30+ real-world scenarios for different personas
- **[DESIGN_REVIEW.md](DESIGN_REVIEW.md)** - Deep architectural analysis and design decisions
- **[IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)** - Future enhancements and timelines
- **[QUICK_START.md](QUICK_START.md)** - Step-by-step guide for first-time users

---

## Key Features

### ✅ Automatic Weighting
Every query automatically applies population weights. Users in our sample represent thousands of similar users, giving you true market insights.

**You get:** 5.3M user estimates
**From:** 634 surveyed users
**How:** Demographic cell weighting to match census data

### ✅ Smart NCCS Merging
Income classes automatically merged for statistical reliability:
- A, A1 → A (Affluent)
- B → B (Upper Middle)
- C, D, E → C/D/E (Mass Market)

### ✅ Automatic Insights
Every query includes business insights:
- Market concentration ("Top 3 = 80% share")
- Demographic skews ("2.3x over-indexed with affluent")
- Opportunities ("Underserved: Men 45+")

### ✅ Marketing-Friendly
- Tools named by value, not mechanics
- Examples for every use case
- Business context in all descriptions
- Plain English error messages

### ✅ Power User Ready
- Full SQL access
- Query optimization
- Result caching
- Parallel execution

---

## API Reference

### MCP Tools

| Tool | Purpose | Best For |
|------|---------|----------|
| `list_available_datasets()` | See available data | First-time users |
| `explain_term(term)` | Learn terminology | Understanding data |
| `get_top_apps(...)` | Popular apps by segment | Media planning, market research |
| `profile_audience(app)` | Demographic breakdown | Audience analysis, targeting |
| `query_dataset(...)` | Custom SQL analysis | Advanced analytics, custom metrics |

### HTTP Endpoints (Optional)

```bash
# Health check
GET http://localhost:10000/health

# List datasets
GET http://localhost:10000/datasets

# Execute query
POST http://localhost:10000/query
Content-Type: application/json
{
  "dataset_id": 1,
  "query": "SELECT app_name, SUM(weights) as users FROM digital_insights GROUP BY app_name LIMIT 10"
}
```

---

## Data Schema

### Main Table: `digital_insights`

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `vtionid` | text | User identifier (anonymized) | "user_12345" |
| `app_name` | text | App name | "Instagram" |
| `package` | text | Android package | "com.instagram.android" |
| `cat` | text | App category | "Social" |
| `age_bucket` | text | Age group | "25-34" |
| `gender` | text | Gender | "Female" |
| `nccs` | text | Income class | "A" |
| `state_grp` | text | State/region | "Maharashtra" |
| `weights` | numeric | Population weight | 4.0 (= 4,000 users) |
| `duration_sum` | numeric | Total time spent | 1234 (minutes) |
| `event_count` | integer | Number of events | 15 |
| `date` | date | Event date | "2024-01-15" |
| `day_of_week` | text | Day of week | "Monday" |

**Critical:** Always use `SUM(weights)` for user counts, never `COUNT(*)`

---

## Best Practices

### ✅ Do's

- **Use SUM(weights)** for all user counts
- **Filter data** with WHERE clauses for performance
- **Group by demographics** for actionable insights
- **Check GLOSSARY.md** when confused about terms
- **Start with pre-built tools** before writing SQL

### ❌ Don'ts

- **Don't use COUNT(*)** - it counts survey respondents, not population
- **Don't forget GROUP BY** when using aggregations
- **Don't extrapolate events** - only extrapolate users
- **Don't skip WHERE clauses** - they improve performance
- **Don't guess** - use explain_term() to learn

---

## Common Questions

### "I don't know SQL. Can I still use this?"

**Yes!** Use pre-built tools:
- `get_top_apps()` - No SQL needed
- `profile_audience()` - Just provide app name
- `explain_term()` - Learn as you go

### "How accurate is this data?"

- **Sample size:** 634 active users, statistically weighted
- **Represents:** 5.3M smartphone users across India
- **Weighting:** Demographic cells matched to census data
- **Update frequency:** Monthly refreshes

### "What if I need data not available here?"

Contact the data team or check IMPLEMENTATION_ROADMAP.md for planned enhancements (e-commerce, OTT, social media ads coming soon).

### "Can I export results?"

Yes! Use `response_format="json"` for programmatic access:

```python
query_dataset(
    dataset_id=1,
    query="...",
    response_format="json"
)
```

### "Is this data real-time?"

No. Data updated monthly. For real-time analytics, this MCP server would need integration with streaming data sources.

---

## Troubleshooting

### Issue: "No results found"

**Causes:**
- Filters too restrictive
- App name misspelled
- Date range too narrow

**Solution:**
```python
# Find correct app name
query_dataset(dataset_id=1, query="SELECT DISTINCT app_name FROM digital_insights WHERE app_name ILIKE '%insta%'")

# Check available filters
explain_term(term="age_bucket")
```

---

### Issue: "Table not found"

**Solution:**
```python
list_available_datasets()  # See what's available
```

---

### Issue: "Query is slow"

**Optimization tips:**
- Add WHERE clause to filter data
- Use specific columns instead of SELECT *
- Add LIMIT to reduce result size
- Check USAGE_EXAMPLES.md for optimized patterns

---

## Deployment

### Render (Recommended for Production)

1. Push to GitHub
2. Connect Render to repository
3. Use included `render.yaml` configuration
4. Environment variables auto-configured

**Live at:** https://indian-analytics-mcp.onrender.com

### Docker (Coming Soon)

```bash
docker build -t indian-analytics-mcp .
docker run -p 10000:10000 indian-analytics-mcp
```

### Local Development

```bash
# Clone repository
git clone https://github.com/adityac7/indian-analytics-mcp.git
cd indian-analytics-mcp

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your database credentials

# Run server
python indian_analytics_mcp.py
```

---

## Security

- ✅ **Read-only** queries (SELECT only)
- ✅ **SQL injection protection** (dangerous keywords blocked)
- ✅ **Connection pooling** (prevents resource exhaustion)
- ✅ **Anonymized data** (no PII)
- ⚠️ **No authentication** (add for production use)
- ⚠️ **No rate limiting** (add for public APIs)

**For production:**
- Add API key authentication
- Implement rate limiting
- Set up monitoring and alerts
- Use SSL/TLS for connections

---

## Contributing

We welcome contributions! Areas of interest:

- **New tools** for common use cases
- **Natural language query** improvements
- **Visualization** capabilities
- **Additional datasets** (e-commerce, OTT, etc.)
- **Documentation** improvements

See [IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md) for planned enhancements.

---

## Roadmap

### ✅ Phase 1 (Completed)
- Core MCP server
- SQL query execution
- Automatic weighting
- Business-friendly tools

### 🚧 Phase 2 (In Progress)
- Enhanced error messages
- Automatic insights generation
- Query optimization

### 📅 Phase 3 (Q2 2025)
- Natural language queries
- Trend analysis tools
- Competitive intelligence features

### 📅 Phase 4 (Q3 2025)
- E-commerce funnel data
- OTT consumption data
- Social media ad exposure
- CTV usage patterns

---

## Support

- **Documentation:** Check GLOSSARY.md, USAGE_EXAMPLES.md
- **Issues:** [GitHub Issues](https://github.com/adityac7/indian-analytics-mcp/issues)
- **Examples:** See USAGE_EXAMPLES.md for 30+ real scenarios

---

## License

MIT License - see [LICENSE](LICENSE) file for details

---

## Acknowledgments

Built using:
- [Model Context Protocol](https://modelcontextprotocol.io) by Anthropic
- [FastMCP](https://github.com/jlowin/fastmcp) framework
- PostgreSQL for data storage
- AsyncPG for async database operations

---

## Version

**2.0** - Enhanced with business-friendly tools and marketing focus

**What's New in 2.0:**
- 🎯 Pre-built tools for marketers (no SQL needed)
- 📚 Comprehensive glossary and examples
- 💡 Automatic insights generation
- 🚀 Better error messages and guidance
- 📊 Marketing-first tool descriptions

---

**Ready to discover insights?** Install now and start asking questions!

```bash
git clone https://github.com/adityac7/indian-analytics-mcp.git
cd indian-analytics-mcp
pip install -r requirements.txt
python indian_analytics_mcp.py
```
