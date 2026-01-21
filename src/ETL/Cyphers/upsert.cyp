// upsert_restaurant
UNWIND $rows AS row
MERGE (rstn:{label} {{ids: row.ids}})
SET rstn.name = row.name,
    rstn.city = row.city,
    rstn.area = row.area,
    rstn.locality = row.locality,
    rstn.cuisines = row.cuisines,
    rstn.rating = row.rating,
    rstn.address = row.address,
    rstn.coords = row.coords,
    rstn.chain = row.chain

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
UNWIND row AS data
MATCH (src:{source_label} {{name: data.source_ids}})
MATCH (tgt:{target_label} {{name: data.target_ids}})
MERGE (src)-[rlsp:{relationship}]->(tgt)
SET rlsp += data.params

// UNWIND $rows AS row
// UNWIND row AS data
// MATCH (src:source_label {name: data.source_ids})
// MATCH (tgt:target_label {name: data.target_ids})
// MERGE (src)-[rlsp:{relationship}]->(tgt)
// SET rlsp += data.params