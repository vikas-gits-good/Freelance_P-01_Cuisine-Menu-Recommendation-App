// PATTERN 1.1: Search for Restaurants by City
MATCH (:City {ids: $ids})-[]-()-[]-()-[:HAS_RESTAURANT]->(r:Restaurant)
RETURN r LIMIT 5000 ASC r.ids

MATCH (:City {ids: $ids})-[*3]->(r:Restaurant)
RETURN r LIMIT 5000 ASC r.ids


// PATTERN 1.2: Search for Restaurants by Area
MATCH (:Area {ids: $ids})-[]-()-[:HAS_RESTAURANT]->(r:Restaurant)
RETURN r LIMIT 5000 ASC r.ids

// PATTERN 1.3: Search for Restaurants by Locality
MATCH (:Locality {ids: $ids})-[:HAS_RESTAURANT]->(r:Restaurant)
RETURN r LIMIT 5000 ASC r.ids


// PATTERN 2.1: Search for Menus by City
MATCH (:City {ids: $ids})-[]-()-[]-()-[:HAS_RESTAURANT]->()-[:HAS_MENU]-(mn:Menu)
RETURN mn LIMIT 5000 ASC mn.name

// PATTERN 2.2: Search for Menus by Area
MATCH (:Area {ids: $ids})-[]-()-[:HAS_RESTAURANT]->()-[:HAS_MENU]-(mn:Menu)
RETURN mn LIMIT 5000 ASC mn.name

// PATTERN 2.3: Search for Menus by Locality
MATCH (:Locality {ids: $ids})-[:HAS_RESTAURANT]->()-[:HAS_MENU]-(mn:Menu)
RETURN mn LIMIT 5000 ASC mn.name


// PATTERN 3.1: Search for Cuisines by City
MATCH (:City {ids: $ids})-[]-()-[]-()-[:HAS_RESTAURANT]->()-[:HAS_MAIN_CUISINE]-(mc:MainCuisine)
RETURN mc LIMIT 5000 ASC mc.name

// PATTERN 3.2: Search for Cuisines by Area
MATCH (:Area {ids: $ids})-[]-()-[:HAS_RESTAURANT]->()-[:HAS_MAIN_CUISINE]-(mc:MainCuisine)
RETURN mc LIMIT 5000 ASC mc.name

// PATTERN 3.3: Search for Cuisines by Locality
MATCH (:Locality {ids: $ids})-[:HAS_RESTAURANT]->()-[:HAS_MAIN_CUISINE]-(mc:MainCuisine)
RETURN mc LIMIT 5000 ASC mc.name



// PATTERN 1.1: Search for Restaurants by City
MATCH (:{loc_lbl} {{ids: $ids}})-[]-()-[]-()-[:HAS_RESTAURANT]->(r:Restaurant)
RETURN r LIMIT 5000 ASC r.ids

// PATTERN 1.2: Search for Restaurants by Area
MATCH (:Area {ids: $ids})-[]-()-[:HAS_RESTAURANT]->(r:Restaurant)
RETURN r LIMIT 5000 ASC r.ids

// PATTERN 1.3: Search for Restaurants by Locality
MATCH (:Locality {ids: $ids})-[:HAS_RESTAURANT]->(r:Restaurant)
RETURN r LIMIT 5000 ASC r.ids



// Restaurant by City, Area, Locality
MATCH (:{loc_lbl} {{ids: $ids}})-{rlsp_ptrn}-[:HAS_RESTAURANT]->(r:Restaurant)
RETURN r LIMIT 5000 ASC r.ids

// Menu by City, Area, Locality
MATCH (:{loc_lbl} {{ids: $ids}})-{rlsp_ptrn}-[:HAS_RESTAURANT]->()-[:HAS_MENU]-(mn:Menu)
RETURN mn LIMIT 5000 ASC mn.name, Uniqnue name??

// Cuisine by City, Area, Locality
MATCH (:{loc_lbl} {{ids: $ids}})-{rlsp_ptrn}-[:HAS_RESTAURANT]->()-[:HAS_MAIN_CUISINE]-(mc:MainCuisine)
RETURN mc LIMIT 5000 ASC mc.name Uniqnue name??



// loc_lbl = City, Area, Locality
// rlsp_ptrn: int = 3,2,1
// obj_label = final object name
// obj_limit = 5000

MATCH (a)-[*2]-(b)
MATCH (a)-[]->()-[]->(b)



// 
MATCH (:{loc_lbl} {{ids: $ids}})-[*{rlsp_len}]->(obj:{obj_label})
RETURN obj LIMIT {obj_limit} ORDER BY ASC obj.{obj_param}

// Example
// top 20 restaurants in Bengaluru
MATCH (:City {ids: 'relation:7902476'})-[*3]->(obj:Restaurant)
WHERE obj.rating > 4.5
RETURN obj.name
ORDER BY obj.name ASC
LIMIT 200