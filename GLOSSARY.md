# Analytics Glossary - Indian Consumer Data

Quick reference guide for understanding your analytics data.

---

## Demographics

### NCCS (New Consumer Classification System)

**What it is:** India's standard for socioeconomic classification based on education and occupation of chief wage earner.

**Values:**
- **A** - Affluent / High Income
  - Examples: Senior executives, business owners, professionals
  - ~10% of population
  - High purchasing power, early adopters
  - Marketing use: Premium products, luxury brands

- **B** - Upper Middle Class
  - Examples: Mid-level managers, skilled professionals
  - ~20% of population
  - Aspirational consumers, quality-conscious
  - Marketing use: Mainstream premium products

- **C/D/E** - Mass Market
  - Examples: Clerks, skilled workers, laborers
  - ~70% of population
  - Price-sensitive, value seekers
  - Marketing use: Mass market products, value positioning

**Why we merge:**
- A1 → A: Small sample sizes, similar behavior
- C/D/E combined: Statistical reliability, similar consumption patterns

**How to use:**
```sql
-- Premium product targeting
WHERE nccs = 'A'

-- Mass market analysis
WHERE nccs = 'C/D/E'

-- Middle class
WHERE nccs = 'B'
```

---

### Age Buckets

**Available ranges:**
- **18-24** - Gen Z, college students, early career
- **25-34** - Millennials, career building, family formation
- **35-44** - Gen X, established career, family focus
- **45-54** - Peak earning years, mature consumers
- **55+** - Pre-retirement and retirees

**Marketing implications:**
- 18-24: Mobile-first, social media natives, trend-driven
- 25-34: Largest purchasing cohort, brand-conscious
- 35-44: Family purchases, value quality over trends
- 45-54: High disposable income, established preferences
- 55+: Traditional media, trust-based decisions

**How to use:**
```sql
-- Target millennials
WHERE age_bucket = '25-34'

-- Youth market
WHERE age_bucket IN ('18-24', '25-34')

-- Mature audience
WHERE age_bucket IN ('45-54', '55+')
```

---

### Gender

**Values:**
- **Male** / **Female**

**Why it matters:**
- Product positioning (men's vs women's products)
- Media channel selection
- Creative messaging
- Time-of-day patterns

**How to use:**
```sql
-- Women audience
WHERE gender = 'Female'

-- Compare by gender
GROUP BY gender
```

---

### Town Class (Urban Classification)

**Values:**
- **Metro** - Mumbai, Delhi, Bangalore, Chennai, Kolkata, Hyderabad
- **Tier 1** - Large cities (pop >1M)
- **Tier 2** - Medium cities (pop 100K-1M)
- **Tier 3+** - Smaller towns

**Why it matters:**
- Infrastructure differences (4G/5G coverage)
- Purchasing power variation
- Cultural preferences
- Distribution strategy

**Marketing implications:**
- Metro: Sophisticated consumers, global trends, premium pricing
- Tier 1: Aspiring metros, growing affluence
- Tier 2/3: Price-sensitive, local preferences, high growth potential

---

### State/Region (state_grp)

**Major states in dataset:**
- Maharashtra, Karnataka, Tamil Nadu, Delhi, Gujarat, West Bengal, etc.

**Why it matters:**
- Language preferences
- Cultural differences
- Regional festivals and seasons
- Competitive intensity
- Regulatory environment

**How to use:**
```sql
-- South India
WHERE state_grp IN ('Karnataka', 'Tamil Nadu', 'Andhra Pradesh', 'Telangana', 'Kerala')

-- Metro states
WHERE state_grp IN ('Maharashtra', 'Karnataka', 'Delhi')
```

---

## App Data Fields

### app_name

**What it is:** Human-readable app name (e.g., "Instagram", "WhatsApp")

**Use for:**
- User-facing reports
- Competitive analysis
- Audience profiling

**Note:** Some apps may have multiple name variations (e.g., "YouTube" vs "Youtube")

```sql
-- Use ILIKE for fuzzy matching
WHERE app_name ILIKE '%instagram%'
```

---

### package

**What it is:** Android package name (e.g., "com.instagram.android")

**Use for:**
- Precise app identification
- Technical integration
- Avoiding name ambiguity

**Example:**
```sql
WHERE package = 'com.instagram.android'
```

---

### cat (Category)

**What it is:** App category classification

**Common values:**
- Social Media
- Gaming
- Shopping / E-commerce
- Entertainment
- Food & Drink
- Health & Fitness
- Education
- News
- Finance
- Travel

**How to use:**
```sql
-- Single category
WHERE cat = 'Social'

-- Multiple categories
WHERE cat IN ('Social', 'Entertainment', 'Gaming')

-- Fuzzy search
WHERE cat ILIKE '%shop%'
```

---

### duration_sum

**What it is:** Total time spent in the app (minutes or seconds, check data)

**Use for:**
- Engagement analysis
- Session length calculation
- Time-spent trends

**Calculate average per user:**
```sql
SELECT
    app_name,
    SUM(duration_sum) / SUM(weights) as avg_minutes_per_user
FROM digital_insights
GROUP BY app_name
```

---

### event_count

**What it is:** Number of app open/usage events

**Use for:**
- Frequency analysis
- Session count
- Active days

**Calculate average sessions:**
```sql
SELECT
    app_name,
    AVG(event_count) as avg_sessions_per_user
FROM digital_insights
GROUP BY app_name
```

---

## Critical Concepts

### Weighting (THE MOST IMPORTANT CONCEPT)

**What it is:** Each user in our sample represents multiple people in the population.

**Example:**
- User ID 12345 has `weight = 4`
- This means: User 12345 represents 4,000 similar users

**Why we weight:**
- Sample size: 634 users surveyed
- Population: 5.3 million smartphone users
- Demographic cells: ~850 combinations (age × gender × NCCS × town × state)
- Each cell weighted to match census data

**The Golden Rule:**
```sql
-- ❌ WRONG - Counts survey respondents
SELECT COUNT(*) FROM digital_insights

-- ✅ RIGHT - Extrapolates to population
SELECT SUM(weights) FROM digital_insights
```

**Always use weights for:**
- User counts
- Market sizing
- Penetration calculations
- Reach estimates

**Never extrapolate for:**
- Events (one user's 10 sessions ≠ 40,000 sessions)
- Duration (one user's 30 minutes ≠ 120,000 minutes total)
- Just scale the user count

**Correct patterns:**
```sql
-- Total users
SUM(weights) as total_users

-- Average per user (divide totals, then weight)
SUM(duration_sum) / NULLIF(SUM(weights), 0) as avg_minutes_per_user

-- Percentage of users
(SUM(weights) * 100.0 / total_population) as penetration_pct
```

---

### Date and Time Fields

**date**
- Event date
- Use for trend analysis
- Filter recent data for relevance

```sql
-- Last 30 days
WHERE date >= CURRENT_DATE - INTERVAL '30 days'

-- Specific month
WHERE DATE_TRUNC('month', date) = '2024-01-01'
```

**day_of_week**
- Monday, Tuesday, etc.
- Use for day-part analysis
- Weekend vs weekday patterns

```sql
-- Weekends
WHERE day_of_week IN ('Saturday', 'Sunday')
```

---

### User Identifier

**vtionid**
- Anonymized user ID
- Use for unique user counts
- Cross-app analysis

```sql
-- Unique users for app
SELECT COUNT(DISTINCT vtionid)
FROM digital_insights
WHERE app_name = 'Instagram'
```

---

## Common Calculations

### Market Share

```sql
WITH category_total AS (
    SELECT SUM(weights) as total
    FROM digital_insights
    WHERE cat = 'Social'
)
SELECT
    app_name,
    SUM(weights) as users,
    (SUM(weights) * 100.0 / (SELECT total FROM category_total)) as market_share_pct
FROM digital_insights
WHERE cat = 'Social'
GROUP BY app_name
ORDER BY market_share_pct DESC
```

---

### Penetration Rate

```sql
WITH segment_total AS (
    SELECT SUM(weights) as total
    FROM digital_insights
    WHERE age_bucket = '25-34'
)
SELECT
    app_name,
    SUM(weights) as users,
    (SUM(weights) * 100.0 / (SELECT total FROM segment_total)) as penetration_pct
FROM digital_insights
WHERE age_bucket = '25-34'
GROUP BY app_name
ORDER BY penetration_pct DESC
```

---

### Index vs Population

```sql
-- Index: 100 = average, >100 = over-indexed, <100 = under-indexed
WITH app_segment AS (
    SELECT SUM(weights) as segment_users
    FROM digital_insights
    WHERE app_name = 'Instagram' AND gender = 'Female'
),
app_total AS (
    SELECT SUM(weights) as total_users
    FROM digital_insights
    WHERE app_name = 'Instagram'
),
population_segment AS (
    SELECT SUM(weights) as segment_users
    FROM digital_insights
    WHERE gender = 'Female'
),
population_total AS (
    SELECT SUM(weights) as total_users
    FROM digital_insights
)
SELECT
    ((aps.segment_users::float / apt.total_users) /
     (ps.segment_users::float / pt.total_users) * 100) as index
FROM app_segment aps, app_total apt, population_segment ps, population_total pt
```

---

### Engagement Score

```sql
SELECT
    app_name,
    -- Frequency
    AVG(event_count) as avg_sessions,
    -- Duration
    SUM(duration_sum) / NULLIF(SUM(weights), 0) as avg_minutes,
    -- Combined engagement score
    (AVG(event_count) * (SUM(duration_sum) / NULLIF(SUM(weights), 0))) as engagement_score
FROM digital_insights
GROUP BY app_name
ORDER BY engagement_score DESC
```

---

## Quick Reference

### Do's
✅ Always use `SUM(weights)` for user counts
✅ Use `ILIKE` for case-insensitive string matching
✅ Include `WHERE` clauses to filter data
✅ Use `GROUP BY` for aggregated analysis
✅ Add `LIMIT` to prevent huge results
✅ Use `NULLIF(SUM(weights), 0)` to avoid division by zero

### Don'ts
❌ Don't use `COUNT(*)` for user counts
❌ Don't forget to weight your results
❌ Don't extrapolate events (only users)
❌ Don't use `SELECT *` without LIMIT
❌ Don't compare absolute numbers across different time periods without normalization

---

## Need Help?

**For beginners:**
- Use `explain_term(term="nccs")` to learn specific concepts
- Try pre-built tools: `get_top_apps()`, `profile_audience()`
- Check USAGE_EXAMPLES.md for real scenarios

**For analysts:**
- See USAGE_EXAMPLES.md for advanced SQL patterns
- Use query_dataset() for custom analysis
- Refer to this glossary for correct calculations

**For executives:**
- Focus on insights from pre-built tools
- Let analysts handle the SQL
- Use this glossary to understand reports
