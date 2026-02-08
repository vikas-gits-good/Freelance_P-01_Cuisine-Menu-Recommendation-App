// create_user_node
MERGE (u:User {user_id: $user_id})
SET u += $params

// create_preference_node
MATCH (u:User {user_id: $user_id})
MERGE (u)-[:HAS_PREFERENCE]->(p:Preference {category: $category, value: $value})
SET p += $params

// create_session_node
MATCH (u:User {user_id: $user_id})
MERGE (u)-[:HAS_SESSION]->(s:Session {session_id: $session_id})
SET s += $params

// create_interaction_node
MATCH (s:Session {session_id: $session_id})
CREATE (s)-[:HAS_INTERACTION {turn_number: $turn_number}]->(i:Interaction)
SET i += $params

// create_summary_node
MATCH (u:User {user_id: $user_id})
CREATE (u)-[:HAS_SUMMARY]->(s:Summary)
SET s += $params

// create_index
CREATE INDEX FOR (u:User) ON (u.user_id)
CREATE INDEX FOR (s:Session) ON (s.session_id)
CREATE INDEX FOR (p:Preference) ON (p.category)
