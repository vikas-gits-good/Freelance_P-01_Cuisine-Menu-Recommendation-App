// create_location_with_iso_code
MERGE (loc:{loc_label} {{ids: $ids}})
SET loc.name = $name,
    loc.iso_code = $iso_code,
    loc.coords = $coords,
    loc.boundingbox = $boundingbox

// create_location_without_iso_code
MERGE (loc:{loc_label} {{ids: $ids}})
SET loc.name = $name,
    loc.coords = $coords,
    loc.boundingbox = $boundingbox

// create_location_relationship
MATCH (loc1:{label1} {{name: $source_name}})
MATCH (loc2:{label2} {{name: $target_name}})
MERGE (loc1)-[:{relationship}]->(loc2)

// create_index
CREATE INDEX FOR (loc:{loc_label}) ON (loc.ids)
CREATE INDEX FOR (loc:{loc_label}) ON (loc.name)