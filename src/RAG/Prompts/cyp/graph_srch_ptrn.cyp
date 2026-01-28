// PATTERN 1.1: Search for Restaurants by City
MATCH (:City {ids: $ids})-[]-()-[]-()-[:HAS_RESTAURANT]->(r:Restaurant)
RETURN r LIMIT 5000 ASC r.ids

// PATTERN 1.2: Search for Restaurants by Area
MATCH (:Area {ids: $ids})-[]-()-[:HAS_RESTAURANT]->(r:Restaurant)
RETURN r LIMIT 5000 ASC r.ids

// PATTERN 1.3: Search for Restaurants by Locality
MATCH (:Locality {ids: $ids})-[:HAS_RESTAURANT]->(r:Restaurant)
RETURN r LIMIT 5000 ASC r.ids


// PATTERN 2.1: Search for Menus by City
MATCH (:City {ids: $ids})-[]-()-[]-()-[:HAS_RESTAURANT]->()-[:HAS_MENU]-(m:Menu)
RETURN m LIMIT 5000 ASC m.name

// PATTERN 2.2: Search for Menus by Area
MATCH (:Area {ids: $ids})-[]-()-[:HAS_RESTAURANT]->()-[:HAS_MENU]-(m:Menu)
RETURN m LIMIT 5000 ASC m.name

// PATTERN 2.3: Search for Menus by Locality
MATCH (:Locality {ids: $ids})-[:HAS_RESTAURANT]->()-[:HAS_MENU]-(m:Menu)
RETURN m LIMIT 5000 ASC m.name