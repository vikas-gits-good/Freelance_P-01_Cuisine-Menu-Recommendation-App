// upsert_menu_cuisine
UNWIND $rows AS row
UNWIND row as item
MERGE (food:{label} {{name: item.name}})
SET food += item.params

// upsert_relationship_with_params
UNWIND $rows AS row
UNWIND row as data
MERGE (src:{source_label} {{ids: data.source_ids}})
MERGE (tgt:{target_label} {{name: data.target_ids}})
MERGE (src)-[rlsp:{relationship}]->(tgt)
SET rlsp += data.params