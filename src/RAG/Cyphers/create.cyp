// Unique_constraints
CREATE CONSTRAINT country_name IF NOT EXISTS FOR (c:Country) REQUIRE (c.name, c.iso_code )IS UNIQUE;
CREATE CONSTRAINT state_name IF NOT EXISTS FOR (s:State) REQUIRE (s.name, s.country_name, s.iso_code) IS UNIQUE;
CREATE CONSTRAINT city_name IF NOT EXISTS FOR (c:City) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT restaurant_id IF NOT EXISTS FOR (r:Restaurant) REQUIRE r.rstn_id IS UNIQUE;
CREATE CONSTRAINT menu_item_id IF NOT EXISTS FOR (m:MenuItem) REQUIRE m.food_id IS UNIQUE;
CREATE CONSTRAINT cuisine_name IF NOT EXISTS FOR (c:Cuisine) REQUIRE c.name IS UNIQUE;

// Performance_indexes
CREATE INDEX restaurant_rating IF NOT EXISTS FOR (r:Restaurant) ON (r.rstn_rating);
CREATE INDEX menu_price IF NOT EXISTS FOR (m:MenuItem) ON (m.food_price);
CREATE INDEX city_coords IF NOT EXISTS FOR (c:City) ON (c.latitude, c.longitude);