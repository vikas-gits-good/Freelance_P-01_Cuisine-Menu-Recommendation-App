// create_country_state_city_area_locality
MERGE (loc:{loc_label} {{ids: $ids}})
SET loc.name = $name,
    loc.iso_code = $iso_code,
    loc.coords = $coords,
    loc.boundingbox = $boundingbox

// create_location_relationship
MATCH (src:{source_label} {{name: $source_name}})
MATCH (tgt:{target_label} {{name: $target_name}})
MERGE (src)-[:{relationship}]->(tgt)

// create_index
CREATE INDEX FOR (loc:{loc_label}) ON (loc.ids)
CREATE INDEX FOR (loc:{loc_label}) ON (loc.name)