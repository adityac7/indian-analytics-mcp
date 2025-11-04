# Indian Analytics MCP - Usage Examples

This guide shows real-world examples for different user personas.

---

## Quick Start (New Users)

### Step 1: Understand the Data
```python
# See what data is available
list_available_datasets()

# Understand key terminology
explain_term()  # See all terms

# Deep dive on specific concepts
explain_term(term="nccs")  # Income classes
explain_term(term="weights")  # Why we use weights
```

### Step 2: Start with Pre-built Tools
```python
# Quick insights - no SQL needed
get_top_apps(limit=10)

# See who uses Instagram
profile_audience(app_name="Instagram")
```

### Step 3: Custom Analysis (If Needed)
```python
# For advanced users who know SQL
query_dataset(
    dataset_id=1,
    query="SELECT app_name, SUM(weights) FROM digital_insights GROUP BY app_name"
)
```

---

## Marketing Manager Persona

**Name:** Priya
**Role:** Brand Manager at FMCG Company
**Goal:** Understand target audience media consumption

### Example 1: Find Where Young Women Spend Time

**Question:** "Where should we advertise to reach women aged 25-34?"

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
# Top 20 Apps by Reach
Filters: Age: 25-34 | Gender: Female
Metric: Total Users (weighted)

| rank | app_name | category | users_formatted | market_share |
|------|----------|----------|-----------------|--------------|
| 1 | WhatsApp | Social | 1,234,567 | 45.2% |
| 2 | Instagram | Social | 987,654 | 36.1% |
| 3 | YouTube | Video | 876,543 | 32.1% |
...

💡 Key Insights:
- Top 3 apps represent 85% of reach
- Strong concentration in social media
```

**Priya's next action:** Plan ad campaigns on WhatsApp, Instagram, YouTube

---

### Example 2: Premium Product Launch

**Question:** "Who uses luxury shopping apps? What else do they use?"

```python
# First, find affluent shoppers
get_top_apps(
    category="Shopping",
    nccs_class="A",  # Affluent segment
    metric="reach",
    limit=10
)

# Then profile one app to understand crossover
profile_audience(
    app_name="Myntra",  # Popular fashion app
    include_comparisons=True
)
```

**Output:**
```
# Audience Profile: Myntra
Total Users: 456,789 (weighted)

## Income Class (NCCS)
- A - Affluent: 198,765 (43.5%)
- B - Upper Middle: 178,654 (39.1%)
- C/D/E - Mass Market: 79,370 (17.4%)

💡 Key Insights:
- Over-indexes with affluent users (43% NCCS A)
- Strong female skew (67%)
- Concentrated in 25-34 age group
```

**Priya's decision:** Target Myntra for premium product ads, create female-focused creatives

---

### Example 3: Regional Launch Strategy

**Question:** "Should we launch in Tamil Nadu or Karnataka first?"

```python
# Compare app usage by state (custom SQL needed)
query_dataset(
    dataset_id=1,
    query="""
    SELECT
        state_grp,
        SUM(weights) as total_users,
        COUNT(DISTINCT app_name) as app_diversity,
        SUM(duration_sum) / SUM(weights) as avg_minutes_per_user
    FROM digital_insights
    WHERE state_grp IN ('Tamil Nadu', 'Karnataka')
      AND cat = 'Shopping'
    GROUP BY state_grp
    ORDER BY total_users DESC
    """
)
```

**Output:**
```
| state_grp | total_users | app_diversity | avg_minutes_per_user |
|-----------|-------------|---------------|---------------------|
| Karnataka | 1,234,567 | 156 | 45.2 |
| Tamil Nadu | 987,654 | 142 | 38.7 |

💡 Key Insights:
- Karnataka has 25% more shopping app users
- Higher engagement (45 min vs 39 min)
```

**Priya's decision:** Launch in Karnataka first, higher market size and engagement

---

## Media Planner Persona

**Name:** Rahul
**Role:** Digital Media Planner at Agency
**Goal:** Maximize reach within budget across platforms

### Example 1: Build Media Mix for Campaign

**Brief:** Reach men 18-34 interested in sports

```python
# Step 1: Find where target audience is
get_top_apps(
    age_group="18-24",
    gender="Male",
    category="Sports",
    metric="reach",
    limit=15
)

# Step 2: Also check general entertainment
get_top_apps(
    age_group="18-24",
    gender="Male",
    metric="engagement",  # Time spent = ad exposure
    limit=15
)

# Step 3: Profile top platform
profile_audience(app_name="Dream11")
```

**Result:**
```
Media Plan:
1. Dream11 (Fantasy Sports) - 2.3M reach - Primary platform
2. Cricbuzz (Sports News) - 1.8M reach - Secondary
3. YouTube Sports channels - 3.1M reach - Video content
4. Instagram Sports pages - 2.7M reach - Visual content

Budget allocation:
- 40% Dream11 (high intent)
- 25% YouTube (broad reach)
- 20% Instagram (engagement)
- 15% Cricbuzz (contextual)
```

---

### Example 2: Competitive Flighting

**Question:** "When do our competitors advertise? Where are the gaps?"

```python
# Analyze app usage patterns by day of week
query_dataset(
    dataset_id=1,
    query="""
    SELECT
        day_of_week,
        SUM(weights) as active_users,
        SUM(duration_sum) / SUM(weights) as avg_minutes
    FROM digital_insights
    WHERE cat = 'Food Delivery'
    GROUP BY day_of_week
    ORDER BY
        CASE day_of_week
            WHEN 'Monday' THEN 1
            WHEN 'Tuesday' THEN 2
            WHEN 'Wednesday' THEN 3
            WHEN 'Thursday' THEN 4
            WHEN 'Friday' THEN 5
            WHEN 'Saturday' THEN 6
            WHEN 'Sunday' THEN 7
        END
    """
)
```

**Output:**
```
| day_of_week | active_users | avg_minutes |
|-------------|--------------|-------------|
| Monday | 1,234,567 | 23.4 |
| Tuesday | 1,189,234 | 22.1 |
| Wednesday | 1,156,789 | 21.8 |
| Thursday | 1,278,901 | 24.6 |
| Friday | 1,456,789 | 28.9 |
| Saturday | 1,523,456 | 31.2 |
| Sunday | 1,489,012 | 29.7 |

💡 Key Insights:
- Peak usage Friday-Sunday
- 25% higher engagement on weekends
```

**Rahul's strategy:** Heavy up on Thursday-Sunday, reduce weekday spend

---

## Product Manager Persona

**Name:** Anjali
**Role:** PM at Startup
**Goal:** Understand market opportunity and user needs

### Example 1: Market Sizing

**Question:** "How big is the fitness app market? Who uses them?"

```python
# Step 1: Get category size
get_top_apps(
    category="Health & Fitness",
    metric="reach",
    limit=20
)

# Step 2: Understand demographics
profile_audience(app_name="HealthifyMe")
profile_audience(app_name="Cure.fit")

# Step 3: Find underserved segments
query_dataset(
    dataset_id=1,
    query="""
    SELECT
        age_bucket,
        gender,
        SUM(weights) as fitness_users,
        (SUM(weights) * 100.0 / (
            SELECT SUM(weights)
            FROM digital_insights
        )) as penetration_pct
    FROM digital_insights
    WHERE cat = 'Health & Fitness'
    GROUP BY age_bucket, gender
    ORDER BY fitness_users DESC
    """
)
```

**Result:**
```
Total Addressable Market:
- 4.2M users of fitness apps (weighted)
- 8% penetration of smartphone users
- Growing 35% YoY

Primary Segments:
1. Women 25-34, NCCS A/B - 1.8M users (43%)
2. Men 25-34, NCCS A/B - 1.2M users (29%)
3. Women 35-44, NCCS A - 0.8M users (19%)

Underserved:
- Men 45+ (only 2% penetration vs 8% average)
- NCCS C/D/E (3% penetration)
- Tier 2/3 cities (5% penetration)

Opportunity: Senior fitness (45+) or mass market fitness
```

**Anjali's decision:** Build affordable fitness app for 45+ segment

---

### Example 2: Competitive Analysis

**Question:** "How do we differentiate from existing players?"

```python
# Compare multiple competitors
query_dataset(
    dataset_id=1,
    query="""
    SELECT
        app_name,
        SUM(weights) as users,
        AVG(duration_sum) as avg_session_duration,
        COUNT(DISTINCT vtionid) as unique_users_sample,
        SUM(event_count) / COUNT(DISTINCT vtionid) as events_per_user
    FROM digital_insights
    WHERE app_name IN ('HealthifyMe', 'Cure.fit', 'Fitbit', 'Nike Run Club')
    GROUP BY app_name
    ORDER BY users DESC
    """
)

# Deep dive on leader
profile_audience(app_name="HealthifyMe")
```

**Output:**
```
Competitive Landscape:

HealthifyMe (Market Leader):
- 1.8M users, high engagement (45 min/session)
- Strong with women 25-34, NCCS A/B
- Positioning: Premium diet coaching

Cure.fit:
- 1.2M users, moderate engagement (32 min)
- Balanced gender, younger (18-34)
- Positioning: Holistic wellness

White space:
- Senior fitness (45+)
- Budget fitness (NCCS C/D/E)
- Men-focused fitness
- Tier 2/3 cities
```

**Anjali's strategy:** Position as "affordable fitness for everyone" targeting NCCS C/D/E

---

## Data Analyst Persona

**Name:** Vikram
**Role:** Analytics Lead
**Goal:** Advanced insights and custom analysis

### Example 1: Cohort Analysis

**Question:** "How does app usage vary by demographic cohorts?"

```python
# Complex multi-dimensional analysis
query_dataset(
    dataset_id=1,
    query="""
    WITH cohorts AS (
        SELECT
            CASE
                WHEN age_bucket IN ('18-24', '25-34') THEN 'Young'
                WHEN age_bucket IN ('35-44', '45-54') THEN 'Middle'
                ELSE 'Senior'
            END as age_cohort,
            CASE
                WHEN nccs IN ('A', 'A1') THEN 'Affluent'
                WHEN nccs = 'B' THEN 'Middle Class'
                ELSE 'Mass Market'
            END as income_cohort,
            SUM(weights) as users,
            SUM(duration_sum) / NULLIF(SUM(weights), 0) as avg_minutes,
            COUNT(DISTINCT app_name) as app_variety
        FROM digital_insights
        WHERE cat = 'Entertainment'
        GROUP BY age_cohort, income_cohort
    )
    SELECT
        age_cohort,
        income_cohort,
        users,
        avg_minutes,
        app_variety,
        (users * avg_minutes) as total_engagement_hours
    FROM cohorts
    ORDER BY total_engagement_hours DESC
    """
)
```

---

### Example 2: Category Migration

**Question:** "Are users moving from one category to another?"

```python
# Compare time periods (requires date filtering)
query_dataset(
    dataset_id=1,
    query="""
    SELECT
        cat as category,
        DATE_TRUNC('month', date) as month,
        SUM(weights) as active_users,
        SUM(duration_sum) / NULLIF(SUM(weights), 0) as avg_engagement
    FROM digital_insights
    WHERE date >= CURRENT_DATE - INTERVAL '6 months'
      AND cat IN ('OTT', 'Social', 'Gaming', 'Shopping')
    GROUP BY cat, DATE_TRUNC('month', date)
    ORDER BY month, active_users DESC
    """
)
```

**Analysis:**
```
Trends:
- OTT: +15% user growth, +23% engagement growth (strong)
- Social: +5% users, -8% engagement (saturation)
- Gaming: +12% users, +18% engagement (growing)
- Shopping: +8% users, +3% engagement (steady)

Insight: Users spending more time on OTT, less on social
Recommendation: OTT partnerships for advertising
```

---

## Executive/Leadership Persona

**Name:** Meera
**Role:** CMO
**Goal:** Strategic insights for board presentation

### Example 1: Market Overview

**Question:** "What's the state of digital media in India? Key trends?"

```python
# High-level category view
get_top_apps(
    metric="reach",
    limit=25
)

# Then break down by categories
query_dataset(
    dataset_id=1,
    query="""
    SELECT
        cat as category,
        COUNT(DISTINCT app_name) as total_apps,
        SUM(weights) as total_users,
        SUM(duration_sum) / SUM(weights) as avg_minutes_per_user,
        (SUM(weights) * 100.0 / (
            SELECT SUM(weights) FROM digital_insights
        )) as market_share_pct
    FROM digital_insights
    GROUP BY cat
    ORDER BY total_users DESC
    LIMIT 10
    """
)
```

**Board Presentation:**
```
Digital India - Key Stats:
- 5.3M smartphone users (weighted sample)
- Average 3.2 hours/day on apps
- 2,138 unique apps tracked

Top Categories:
1. Social Media - 4.8M users (91% reach)
2. Messaging - 4.9M users (93% reach)
3. Video/OTT - 3.2M users (60% reach)
4. Shopping - 2.1M users (40% reach)

Strategic Opportunities:
- OTT fastest growing (+35% YoY)
- Shopping highly engaged (avg 48 min/user)
- Gaming undermonetized (high time, low revenue)
```

---

### Example 2: Competitive Position

**Question:** "How do we stack up against competitors?"

```python
# If your app is in the dataset
profile_audience(app_name="YourApp")

# Compare to competitors
get_top_apps(
    category="YourCategory",
    metric="reach",
    limit=15
)

# Market share analysis
query_dataset(
    dataset_id=1,
    query="""
    WITH category_total AS (
        SELECT SUM(weights) as total
        FROM digital_insights
        WHERE cat = 'YourCategory'
    )
    SELECT
        app_name,
        SUM(weights) as users,
        (SUM(weights) * 100.0 / (SELECT total FROM category_total)) as market_share,
        SUM(duration_sum) / SUM(weights) as avg_engagement
    FROM digital_insights
    WHERE cat = 'YourCategory'
    GROUP BY app_name
    ORDER BY users DESC
    LIMIT 10
    """
)
```

**Strategic Implications:**
```
Your Position: #3 in category with 15% market share

Strengths:
- Higher engagement than competitors (52 min vs 38 min avg)
- Strong with NCCS A/B (premium positioning)
- Loyal user base (high frequency)

Weaknesses:
- Lower reach than leaders (#1 has 3x users)
- Skewed to metros (opportunity in Tier 2/3)
- Minimal presence in NCCS C/D/E

Strategy:
1. Maintain premium positioning (don't compete on price)
2. Expand to Tier 2 cities (growth market)
3. Partner with category leader for distribution
```

---

## Advanced SQL Examples

For power users who want full control:

### Example 1: User Overlap Analysis

```python
query_dataset(
    dataset_id=1,
    query="""
    WITH instagram_users AS (
        SELECT DISTINCT vtionid
        FROM digital_insights
        WHERE app_name ILIKE '%instagram%'
    ),
    snapchat_users AS (
        SELECT DISTINCT vtionid
        FROM digital_insights
        WHERE app_name ILIKE '%snapchat%'
    )
    SELECT
        COUNT(DISTINCT i.vtionid) as instagram_only,
        COUNT(DISTINCT s.vtionid) as snapchat_only,
        COUNT(DISTINCT CASE WHEN s.vtionid IS NOT NULL THEN i.vtionid END) as both_apps
    FROM instagram_users i
    FULL OUTER JOIN snapchat_users s ON i.vtionid = s.vtionid
    """
)
```

### Example 2: Engagement Scoring

```python
query_dataset(
    dataset_id=1,
    query="""
    SELECT
        app_name,
        COUNT(DISTINCT vtionid) as user_count,
        AVG(event_count) as avg_sessions,
        AVG(duration_sum) as avg_minutes,
        -- Engagement score: frequency × duration
        (AVG(event_count) * AVG(duration_sum)) as engagement_score
    FROM digital_insights
    WHERE cat = 'Social'
    GROUP BY app_name
    HAVING COUNT(DISTINCT vtionid) >= 50  -- Minimum sample size
    ORDER BY engagement_score DESC
    LIMIT 20
    """
)
```

### Example 3: Demographic Index

```python
query_dataset(
    dataset_id=1,
    query="""
    WITH app_demographic AS (
        SELECT
            gender,
            SUM(weights) as app_users
        FROM digital_insights
        WHERE app_name ILIKE '%netflix%'
        GROUP BY gender
    ),
    total_demographic AS (
        SELECT
            gender,
            SUM(weights) as total_users
        FROM digital_insights
        GROUP BY gender
    )
    SELECT
        a.gender,
        a.app_users,
        t.total_users,
        (a.app_users::float / t.total_users * 100) as penetration_pct,
        -- Index: 100 = average, >100 = over-indexed
        ((a.app_users::float / t.total_users) /
         ((SELECT SUM(app_users) FROM app_demographic)::float /
          (SELECT SUM(total_users) FROM total_demographic)) * 100) as index
    FROM app_demographic a
    JOIN total_demographic t ON a.gender = t.gender
    ORDER BY index DESC
    """
)
```

---

## Common Patterns & Best Practices

### Pattern 1: Always Use Weighting

❌ **Wrong:**
```sql
SELECT app_name, COUNT(*) as users
FROM digital_insights
GROUP BY app_name
```

✅ **Right:**
```sql
SELECT app_name, SUM(weights) as users
FROM digital_insights
GROUP BY app_name
```

**Why:** COUNT(*) gives you survey respondents, SUM(weights) extrapolates to population

---

### Pattern 2: Filter for Performance

❌ **Slow:**
```sql
SELECT * FROM digital_insights
```

✅ **Fast:**
```sql
SELECT app_name, SUM(weights)
FROM digital_insights
WHERE date >= '2024-01-01'
  AND state_grp = 'Maharashtra'
GROUP BY app_name
```

**Why:** Filtering reduces data scanned, GROUP BY required for large datasets

---

### Pattern 3: Handle NCCS Properly

❌ **Wrong:**
```sql
SELECT nccs, SUM(weights)
FROM digital_insights
WHERE nccs = 'A'  -- Misses A1!
```

✅ **Right (Automatic):**
```sql
-- NCCS automatically merged by system
SELECT nccs, SUM(weights)
FROM digital_insights
-- Returns: A (includes A1), B, C/D/E (combined)
```

Or manual:
```sql
SELECT
    CASE
        WHEN nccs IN ('A', 'A1') THEN 'Affluent'
        WHEN nccs = 'B' THEN 'Upper Middle'
        ELSE 'Mass Market'
    END as income_segment,
    SUM(weights) as users
FROM digital_insights
GROUP BY income_segment
```

---

### Pattern 4: Readable Column Names

❌ **Hard to read:**
```sql
SELECT ab, SUM(w) as u
FROM digital_insights
GROUP BY ab
```

✅ **Clear:**
```sql
SELECT
    age_bucket as age_group,
    SUM(weights) as total_users,
    SUM(duration_sum) / SUM(weights) as avg_minutes_per_user
FROM digital_insights
GROUP BY age_bucket
ORDER BY total_users DESC
```

---

## Troubleshooting

### Issue: "No results found"

**Possible causes:**
1. Filters too restrictive
2. App name misspelled
3. Category name incorrect

**Solution:**
```python
# Find correct app name
query_dataset(
    dataset_id=1,
    query="SELECT DISTINCT app_name FROM digital_insights WHERE app_name ILIKE '%insta%'"
)

# Find available categories
query_dataset(
    dataset_id=1,
    query="SELECT DISTINCT cat, COUNT(*) FROM digital_insights GROUP BY cat"
)
```

---

### Issue: "Table not found"

**Solution:**
```python
list_available_datasets()  # See what's available
```

---

### Issue: "Column not found"

**Solution:**
```python
explain_term()  # See available fields

# Or query schema
query_dataset(
    dataset_id=1,
    query="SELECT * FROM digital_insights LIMIT 1"
)
```

---

## Next Steps

1. **Start simple**: Use `get_top_apps()` and `profile_audience()`
2. **Learn the data**: Use `explain_term()` to understand fields
3. **Graduate to SQL**: Once comfortable, try `query_dataset()`
4. **Share insights**: Export results for presentations

**Need help?** Check the glossary with `explain_term()` or ask for examples!
