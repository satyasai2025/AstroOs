-- Check all schemas
\dn

-- List all tables
\dt *.*

-- Check research_cases structure
\d research_cases

-- Search for Kundalee-related rows
SELECT source_batch, COUNT(*)
FROM research_cases
GROUP BY source_batch;

-- Look for any kundalee mentions
SELECT source_batch, COUNT(*)
FROM research_cases
WHERE LOWER(CAST(source_batch AS TEXT)) LIKE '%kunda%'
   OR LOWER(CAST(source_batch AS TEXT)) LIKE '%celebr%'
   OR LOWER(CAST(source_batch AS TEXT)) LIKE '%astrodat%'
GROUP BY source_batch;

-- Total counts per table
SELECT 'research_cases' AS tbl, COUNT(*) FROM research_cases
UNION ALL SELECT 'life_events', COUNT(*) FROM life_events
UNION ALL SELECT 'people', COUNT(*) FROM people;

-- Recent imports
SELECT source_batch, MIN(created_at) AS first, MAX(created_at) AS last, COUNT(*)
FROM research_cases
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY source_batch;

-- Distinct source_batch values
SELECT DISTINCT source_batch FROM research_cases ORDER BY source_batch;
