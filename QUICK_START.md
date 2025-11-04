# Quick Start Guide - Indian Analytics MCP

**Get your first insights in under 5 minutes!**

---

## Step 1: Choose Your Path (30 seconds)

### Path A: I'm a Marketer/Business User
→ **No coding needed!** Skip to Step 3

### Path B: I'm a Data Analyst
→ **SQL access available** - Continue to Step 2

---

## Step 2: Installation (2 minutes)

### Option 1: With Claude Desktop (Easiest)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/adityac7/indian-analytics-mcp.git
   cd indian-analytics-mcp
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Claude Desktop:**

   Find your config file:
   - **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`

   Add this configuration:
   ```json
   {
     "mcpServers": {
       "indian-analytics": {
         "command": "python",
         "args": ["/full/path/to/indian_analytics_mcp.py"],
         "env": {
           "DATASET_1_NAME": "digital_insights",
           "DATASET_1_DESC": "Mobile app usage data including app opens, duration, demographics, and weighted user representation",
           "DATASET_1_CONNECTION": "postgresql://analytics_db_clug_user:sa1jEkjEmuIKRxQu3x6Oa83Ep4AWGSAM@dpg-d3pmmtali9vc73bn81i0-a.singapore-postgres.render.com/analytics_db_clug",
           "DATASET_1_DICTIONARY": "{\"digital_insights\": \"Mobile app usage events with demographics and weights\"}"
         }
       }
     }
   }
   ```

   **Important:** Replace `/full/path/to/` with your actual path!

4. **Restart Claude Desktop**

5. **Verify it's working:**
   - Open a new conversation in Claude Desktop
   - Type: "List available datasets"
   - You should see the Indian Analytics data!

### Option 2: Standalone HTTP Server

```bash
# Set environment variables
export DATASET_1_NAME=digital_insights
export DATASET_1_DESC="Mobile app usage data"
export DATASET_1_CONNECTION="postgresql://analytics_db_clug_user:sa1jEkjEmuIKRxQu3x6Oa83Ep4AWGSAM@dpg-d3pmmtali9vc73bn81i0-a.singapore-postgres.render.com/analytics_db_clug"
export DATASET_1_DICTIONARY='{"digital_insights": "Mobile app usage events"}'

# Run server
python indian_analytics_mcp.py

# Test in browser
open http://localhost:10000
```

---

## Step 3: Your First Query (1 minute)

### For Marketers (No SQL Required)

**Question 1: What are the most popular apps?**

In Claude Desktop, simply ask:
```
What are the top 10 apps overall?
```

Or use the tool directly:
```
get_top_apps(limit=10)
```

**Expected output:**
```
# Top 10 Apps by Reach

1. WhatsApp - 4,890,123 users (92.3%)
2. Instagram - 3,456,789 users (65.2%)
3. YouTube - 3,234,567 users (61.0%)
...

💡 Key Insights:
- Top 3 apps represent 85% of market
- Social media dominates (6 of top 10)
```

---

**Question 2: Who uses Instagram?**

Ask:
```
Who uses Instagram in India?
```

Or use:
```
profile_audience(app_name="Instagram")
```

**Expected output:**
```
# Audience Profile: Instagram
Total Users: 3,456,789 (weighted)

Gender Distribution:
- Female: 2,074,073 (60.0%)
- Male: 1,382,716 (40.0%)

Age Distribution:
- 25-34: 1,520,186 (44.0%)
- 18-24: 1,037,037 (30.0%)
...

💡 Key Insights:
- Skews female (1.5x more female users)
- Concentrated in 18-34 age group (74%)
- Over-indexes with NCCS A (2.3x)
```

---

**Question 3: Where should I advertise to reach young women?**

Ask:
```
What are the top apps for women aged 25-34?
```

Or use:
```
get_top_apps(
    age_group="25-34",
    gender="Female",
    metric="reach",
    limit=20
)
```

**Use the results to:** Plan media buys, allocate budget, select ad platforms

---

### For Analysts (SQL Access)

**Query 1: Basic aggregation**

```python
query_dataset(
    dataset_id=1,
    query="""
    SELECT
        app_name,
        SUM(weights) as total_users,
        SUM(duration_sum) / SUM(weights) as avg_minutes_per_user
    FROM digital_insights
    GROUP BY app_name
    ORDER BY total_users DESC
    LIMIT 10
    """
)
```

**Query 2: Demographic breakdown**

```python
query_dataset(
    dataset_id=1,
    query="""
    SELECT
        age_bucket,
        gender,
        SUM(weights) as users
    FROM digital_insights
    WHERE app_name ILIKE '%instagram%'
    GROUP BY age_bucket, gender
    ORDER BY users DESC
    """
)
```

**Query 3: Category analysis**

```python
query_dataset(
    dataset_id=1,
    query="""
    SELECT
        cat as category,
        COUNT(DISTINCT app_name) as total_apps,
        SUM(weights) as total_users,
        SUM(duration_sum) / SUM(weights) as avg_engagement
    FROM digital_insights
    GROUP BY cat
    ORDER BY total_users DESC
    """
)
```

---

## Step 4: Understand the Data (1 minute)

### Key Concepts You Need to Know

**1. Weighting (MOST IMPORTANT!)**

```
❌ WRONG: SELECT COUNT(*) FROM digital_insights
✅ RIGHT: SELECT SUM(weights) FROM digital_insights
```

**Why?**
- We surveyed 634 users
- Each represents ~8,400 similar users
- `weights` column tells you how many people each user represents
- `weight=4` means this user = 4,000 people

**2. NCCS (Income Classes)**

- **A** = Affluent (top 10%)
- **B** = Upper Middle (next 20%)
- **C/D/E** = Mass Market (remaining 70%)

Use for targeting:
- Premium products → NCCS A
- Mainstream → NCCS B
- Mass market → NCCS C/D/E

**3. Age Buckets**

Available: `18-24`, `25-34`, `35-44`, `45-54`, `55+`

Use for life-stage targeting

**Need more details?**
```
explain_term(term="nccs")
explain_term(term="weights")
explain_term()  # See all terms
```

---

## Step 5: Common Use Cases (30 seconds each)

### Use Case 1: Media Planning

**Goal:** Find where my target audience spends time

```python
# Young affluent women
get_top_apps(
    age_group="25-34",
    gender="Female",
    nccs_class="A",
    metric="reach",
    limit=15
)
```

**Use results for:** Ad platform selection, budget allocation

---

### Use Case 2: Competitive Analysis

**Goal:** Understand competitor's audience

```python
profile_audience(app_name="Competitor App Name")
```

**Use results for:** Positioning, targeting strategy, feature prioritization

---

### Use Case 3: Market Sizing

**Goal:** How big is this opportunity?

```python
query_dataset(
    dataset_id=1,
    query="""
    SELECT
        COUNT(DISTINCT app_name) as total_apps,
        SUM(weights) as total_users,
        SUM(duration_sum) / SUM(weights) as avg_minutes_per_user
    FROM digital_insights
    WHERE cat = 'Your Category'
    """
)
```

**Use results for:** TAM/SAM/SOM calculations, investor pitches

---

### Use Case 4: Audience Segmentation

**Goal:** Find my ideal customer profile

```python
query_dataset(
    dataset_id=1,
    query="""
    SELECT
        age_bucket,
        gender,
        CASE
            WHEN nccs IN ('A', 'A1') THEN 'Affluent'
            WHEN nccs = 'B' THEN 'Middle Class'
            ELSE 'Mass Market'
        END as income_segment,
        SUM(weights) as users
    FROM digital_insights
    WHERE cat = 'Your Category'
    GROUP BY age_bucket, gender, income_segment
    ORDER BY users DESC
    """
)
```

**Use results for:** Persona development, targeting strategy

---

## Step 6: Troubleshooting (If Needed)

### Problem: "No results found"

**Possible causes:**
1. App name misspelled
2. Filters too restrictive
3. Wrong category name

**Solution:**
```python
# Find correct app name
query_dataset(
    dataset_id=1,
    query="SELECT DISTINCT app_name FROM digital_insights WHERE app_name ILIKE '%partial name%' LIMIT 20"
)

# See all categories
query_dataset(
    dataset_id=1,
    query="SELECT DISTINCT cat FROM digital_insights ORDER BY cat"
)
```

---

### Problem: "Tool not found" or "Server not responding"

**Solution:**
1. Check Claude Desktop is running
2. Verify config file path is correct
3. Restart Claude Desktop
4. Check server logs for errors

---

### Problem: "I don't understand the results"

**Solution:**
```python
# Learn about any term
explain_term(term="nccs")
explain_term(term="weights")

# See all terminology
explain_term()

# Read the glossary
# Check GLOSSARY.md file
```

---

## Next Steps

### Level 1: Basic User (You are here!)
✅ Run pre-built tools
✅ Understand results
✅ Make business decisions

**Next:** Try more filters, different demographics

---

### Level 2: Intermediate User
🎯 **Goal:** Combine multiple queries for deeper insights

**Try:**
1. Compare multiple segments
2. Analyze trends over time
3. Create custom dashboards

**Resources:**
- Check USAGE_EXAMPLES.md for 30+ real scenarios
- Browse GLOSSARY.md for all terms

---

### Level 3: Advanced User
🚀 **Goal:** Custom analysis with SQL

**Try:**
1. Complex multi-dimensional analysis
2. Cohort analysis
3. Index calculations
4. Market share modeling

**Resources:**
- See USAGE_EXAMPLES.md → Advanced SQL section
- Review DESIGN_REVIEW.md for architecture

---

## Cheat Sheet

### Quick Commands

```python
# See what's available
list_available_datasets()

# Learn terminology
explain_term()
explain_term(term="nccs")

# Top apps (no filters)
get_top_apps(limit=10)

# Top apps (with filters)
get_top_apps(
    category="Social",
    age_group="25-34",
    gender="Female",
    nccs_class="A",
    metric="reach",
    limit=20
)

# Audience profile
profile_audience(app_name="Instagram")

# Custom SQL
query_dataset(
    dataset_id=1,
    query="SELECT app_name, SUM(weights) FROM digital_insights GROUP BY app_name LIMIT 10"
)
```

---

### Critical Rules

1. **Always use `SUM(weights)`** for user counts, never `COUNT(*)`
2. **Use `ILIKE`** for case-insensitive matching: `WHERE app_name ILIKE '%instagram%'`
3. **Include `WHERE` clauses** to filter data and improve performance
4. **Add `GROUP BY`** when using SUM, AVG, COUNT
5. **Use `LIMIT`** to prevent huge results

---

### Common Patterns

**User count:**
```sql
SUM(weights) as total_users
```

**Percentage:**
```sql
(SUM(weights) * 100.0 / total_population) as percentage
```

**Average per user:**
```sql
SUM(duration_sum) / NULLIF(SUM(weights), 0) as avg_per_user
```

**Filter by demographics:**
```sql
WHERE age_bucket = '25-34'
  AND gender = 'Female'
  AND nccs IN ('A', 'B')
```

---

## Help & Support

### Documentation
- **GLOSSARY.md** - All terms explained
- **USAGE_EXAMPLES.md** - 30+ real-world examples
- **README.md** - Full reference

### In-Tool Help
```python
explain_term()  # Learn terminology
list_available_datasets()  # See data
```

### Community
- GitHub Issues: Report bugs, request features
- Discussions: Ask questions, share use cases

---

## Success!

You're now ready to discover insights about Indian consumers!

**Remember:**
- Start simple with pre-built tools
- Use explain_term() when confused
- Check USAGE_EXAMPLES.md for inspiration
- Graduate to SQL when you need custom analysis

**Happy analyzing! 🎉**
