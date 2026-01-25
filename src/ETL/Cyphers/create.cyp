// create_location_nodes
UNWIND $rows AS row
MERGE (loc:{label} {{ids: row.ids}})
SET loc += row.params

// create_location_links
UNWIND $rows AS row
MERGE (src:{source_label} {{ids: row.source_ids}})
MERGE (tgt:{target_label} {{ids: row.target_ids}})
MERGE (src)-[rlsp:{relationship}]->(tgt)
SET rlsp += row.params

// create_location_indexes
CREATE INDEX FOR (c:{index_label}) ON (c.{index_id})