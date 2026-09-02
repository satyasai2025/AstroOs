SELECT COUNT(*) AS total_research_cases FROM research_cases;

SELECT source_batch, COUNT(*) AS cases_count
FROM research_cases
GROUP BY source_batch
ORDER BY cases_count DESC;

SELECT COUNT(*) AS total_life_events FROM life_events;

SELECT event_type, COUNT(*) AS event_type_count
FROM life_events
GROUP BY event_type
ORDER BY event_type_count DESC;

SELECT birth_time_confidence, COUNT(*) AS count
FROM research_cases
WHERE source_batch = 'kundaleestore_v2'
GROUP BY birth_time_confidence
ORDER BY count DESC;
