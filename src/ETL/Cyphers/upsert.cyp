// upsert_menu
UNWIND $rows AS row
UNWIND row as food_items
MERGE (food:{label} {{name: food_items.name}})
SET food += food_items.params

// upsert_cuisine
UNWIND $rows AS row
UNWIND row as cuisine
MERGE (cuis:{label} {{name: cuisine.name}})

// upsert_relationship_with_params
UNWIND $rows AS row
UNWIND row as data
MATCH (src:{source_label} {{ids: data.source_ids}})
MATCH (tgt:{target_label} {{name: data.target_ids}})
MERGE (src)-[rlsp:{relationship}]->(tgt)
SET rlsp += data.params