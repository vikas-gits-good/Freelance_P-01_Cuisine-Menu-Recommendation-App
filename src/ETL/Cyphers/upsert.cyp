// upsert_restaurant
UNWIND $rows AS row
MERGE (rstn:{label} {{ids: row.ids}})
SET rstn += row.params

// upsert_menu
UNWIND $rows AS row
UNWIND row as food_items
MERGE (food:{label} {{name: food_items.name}})
SET food.types = food_items.types

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