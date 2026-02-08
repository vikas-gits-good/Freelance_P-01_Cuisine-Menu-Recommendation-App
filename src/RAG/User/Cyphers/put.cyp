// update_user_last_active
MATCH (u:User {user_id: $user_id})
SET u.last_active = $timestamp

// delete_old_interactions
MATCH (u:User {user_id: $user_id})-[:HAS_SESSION]->(s:Session)-[link:HAS_INTERACTION]->(i:Interaction)
WITH i ORDER BY i.timestamp DESC
SKIP $keep_count
DETACH DELETE i

// delete_old_summaries
MATCH (u:User {user_id: $user_id})-[:HAS_SUMMARY]->(s:Summary)
WITH s ORDER BY s.version DESC
SKIP $keep_count
DETACH DELETE s
