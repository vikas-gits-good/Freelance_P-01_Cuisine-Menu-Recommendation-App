// create_country_state_city_area_locality
UNWIND $rows AS row
MERGE (loc:{label} {{ids: row.ids}})
SET loc.name = row.name,
    loc.iso_code = row.iso_code,
    loc.coords = row.coords,
    loc.boundingbox = row.boundingbox

// create_location_relationship
UNWIND $rows AS row
MATCH (src:{source_label} {{name: row.source_ids}})
MATCH (tgt:{target_label} {{name: row.target_ids}})
MERGE (src)-[:{relationship}]->(tgt)

// create_index
CREATE INDEX {index_name} FOR (c:{index_label}) ON (c.{index_id})