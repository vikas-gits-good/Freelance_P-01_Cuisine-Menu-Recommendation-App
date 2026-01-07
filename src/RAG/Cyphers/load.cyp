// Load_Country
MERGE (country:Country {name: $country_name})
ON CREATE SET 
    country.country_code = $country_code
RETURN country

// Load_State
MATCH (country:Country {name: $country_name})
MERGE (state:State {name: $state_name})
ON CREATE SET 
    state.state_code = $state_code
MERGE (state)-[:LOCATED_IN]->(country)
RETURN state

// Load_City
MATCH (state:State {name: $state_name, country_name: $country_name})
MERGE (city:City {name: $city_name, state_name: $state_name})
ON CREATE SET
    city.latitude = $latitude,
    city.longitude = $longitude,
    city.boundingbox = $boundingbox
MERGE (city)-[:LOCATED_IN]->(state)
RETURN city

//Load_Area
MATCH (city:City {name: $city_name, state_name: $state_name})
MERGE (area:Area {name: $area_name, city_name: $city_name})
MERGE (area)-[:LOCATED_IN]->(city)
RETURN area

// Load_Locality
MATCH (area:Area {name: $area_name, city_name: $city_name})
MERGE (locality:Locality {name: $locality_name, area_name: $area_name, city_name: $city_name})
MERGE (locality)-[:LOCATED_IN]->(area)
RETURN locality

// Load_Cuisine
MERGE (cuisine:Cuisine {name: $cuisine_name})
RETURN cuisine

// Load_Restaurant
MATCH (locality:Locality {name: $locality_name, area_name: $area_name, city_name: $city_name})
MERGE (restaurant:Restaurant {rstn_id: $rstn_id})
ON CREATE SET
    restaurant.rstn_name = $rstn_name,
    restaurant.rstn_city = $rstn_city,
    restaurant.rstn_rating = $rstn_rating,
    restaurant.rstn_address = $rstn_address
ON MATCH SET
    restaurant.rstn_rating = $rstn_rating
MERGE (restaurant)-[:LOCATED_IN]->(locality)
RETURN restaurant

// Link_Restaurant_Cuisine
MATCH (restaurant:Restaurant {rstn_id: $rstn_id})
MATCH (cuisine:Cuisine {name: $cuisine_name})
MERGE (restaurant)-[:SERVES]->(cuisine)

// Load_Food
MATCH (restaurant:Restaurant {rstn_id: $rstn_id})
MERGE (item:MenuItem {food_id: $food_id})
ON CREATE SET
    item.food_name = $food_name,
    item.food_category = $food_category,
    item.food_description = $food_description,
    item.food_price = $food_price,
    item.food_rating = $food_rating,
    item.food_type = $food_type,
    item.food_cuisine = $food_cuisine
ON MATCH SET
    item.food_rating = $food_rating,
    item.food_price = $food_price
MERGE (restaurant)-[:HAS_MENU_ITEM]->(item)
RETURN item

// Link_Restaurant_Food
MERGE (restaurant)-[:HAS_MENU_ITEM]->(item)

// Link_Cuisine_Food
MERGE (cuisine:Cuisine {name: $food_cuisine})
MERGE (item)-[:BELONGS_TO_CUISINE]->(cuisine)
