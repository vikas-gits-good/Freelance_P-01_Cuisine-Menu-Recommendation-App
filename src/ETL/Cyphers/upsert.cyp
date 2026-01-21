// create_restaurant
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

// create_menu
UNWIND $rows AS row
MERGE (food:{label} {{name: row.name}})
SET food.types = row.types

// create_cuisine
UNWIND $rows AS row
MERGE (cuis:{label} {{name: row.name}})