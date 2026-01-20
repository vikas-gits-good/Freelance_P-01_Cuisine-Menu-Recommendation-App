// create_restaurant
MERGE (rstn:{label} {{ids: $ids}})
SET rstn.name = $name,
    rstn.city = $city,
    rstn.area = $area,
    rstn.locality = $locality,
    rstn.cuisines = $cuisines,
    rstn.rating = $rating,
    rstn.address = $address,
    rstn.coords = $coords,
    rstn.chain = $chain

// create_menu
MERGE (food:{label} {{name: $name}})
SET food.category = $category,
    food.description = $description,
    food.price = $price,
    food.rating = $rating,
    food.types = $types,
    food.cuisine = $cuisine

// create_cuisine
MERGE (cuis:{label} {{name: $name}})