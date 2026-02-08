// get_user_node
MATCH (u:User {user_id: $user_id})
RETURN u.user_id AS user_id, u.name AS name, u.last_active AS last_active

// get_user_preferences
MATCH (u:User {user_id: $user_id})-[:HAS_PREFERENCE]->(p:Preference)
WHERE p.confidence >= $min_confidence
RETURN p.category AS category, p.value AS value, p.confidence AS confidence
ORDER BY p.confidence DESC

// get_latest_summary
MATCH (u:User {user_id: $user_id})-[:HAS_SUMMARY]->(s:Summary)
RETURN s.text AS text, s.version AS version
ORDER BY s.version DESC
LIMIT 1

// get_recent_interactions
MATCH (u:User {user_id: $user_id})-[:HAS_SESSION]->(s:Session)-[link:HAS_INTERACTION]->(i:Interaction)
RETURN i.query AS query, i.intent AS intent, i.tool_used AS tool_used, i.timestamp AS timestamp
ORDER BY i.timestamp DESC
LIMIT $limit
