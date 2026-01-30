// cypher_get_competitors_data
MATCH (:Area {ids: $area_ids})-[:HAS_LOCALITY]->(:Locality)-[:HAS_RESTAURANT]->(r:Restaurant)
MATCH (r)-[:SERVES_MAIN_CUISINE]->(:MainCuisine {name: $cuisine})
MATCH (r)-[link:HAS_MENU]->(menu:Menu)
WHERE r.rating IS NOT NULL AND r.rating >= $min_rating
RETURN  
    r.name, r.area, r.cuisines, r.rating, r.chain,
    min(link.rating) AS min_menu_rating,
    avg(link.rating) AS avg_menu_rating,
    max(link.rating) AS max_menu_rating,
    min(link.price) AS min_menu_price,
    avg(link.price) AS avg_menu_price,
    max(link.price) AS max_menu_price,
    stDev(link.price) AS sd_menu_price
ORDER BY r.rating DESC, r.name ASC
LIMIT $limit

// cypher_get_competitors_menu
MATCH (:Area {ids: $area_ids})-[:HAS_LOCALITY]->(:Locality)-[:HAS_RESTAURANT]->(rstn:Restaurant)
MATCH (rstn)-[:SERVES_MAIN_CUISINE]->(:MainCuisine {name: $cuisine})
MATCH (rstn)-[link:HAS_MENU]->(menu:Menu)
WHERE link.rating IS NOT NULL AND link.rating >= $min_menu_rating
WITH rstn, menu, link
ORDER BY rstn.name ASC, link.rating DESC, menu.name ASC
WITH rstn, collect({
    rstn: properties(rstn),
    menu: properties(menu),
    food: properties(link)
})[0..20] AS top_menus
UNWIND top_menus AS merged
RETURN merged
LIMIT $limit

// cypher_get_menu_benchmark
MATCH (:Area {ids: $area_ids})-[:HAS_LOCALITY]->(:Locality)-[:HAS_RESTAURANT]->(r:Restaurant)
MATCH (r)-[:SERVES_MAIN_CUISINE]->(:MainCuisine {name: $cuisine})
MATCH (r)-[link:HAS_MENU]->(m:Menu)
WHERE toLower(m.name) CONTAINS toLower($menu_name)
    AND link.price IS NOT NULL
RETURN
    m.name,
    link.price,
    link.rating,
    r.name,
    r.rating
ORDER BY r.name ASC, link.price DESC
LIMIT $limit

// cypher_get_menu_opportunities
MATCH (:Area {ids: $area_ids})-[:HAS_LOCALITY]->(:Locality)-[:HAS_RESTAURANT]->(r:Restaurant)
MATCH (r)-[:SERVES_MAIN_CUISINE]->(:MainCuisine {name: $cuisine})
MATCH (r)-[link:HAS_MENU]->(m:Menu)
WHERE link.rating IS NOT NULL AND link.rating >= $min_menu_rating
WITH
    m.name AS menu_name,
    m.types AS types,
    count(DISTINCT r.ids) AS competitor_count,
    avg(link.rating) AS avg_menu_rating,
    min(link.price) AS min_menu_price,
    avg(link.price) AS avg_menu_price,
    max(link.price) AS max_menu_price,
    stDev(link.price) AS sd_menu_price
RETURN
    menu_name, types,
    competitor_count,
    avg_menu_rating,
    min_menu_price,
    avg_menu_price,
    max_menu_price,
    sd_menu_price
ORDER BY competitor_count ASC, avg_menu_rating DESC
LIMIT $limit

// cypher_get_overpriced_menu
MATCH (:Area {ids: $area_ids})-[:HAS_LOCALITY]->(:Locality)-[:HAS_RESTAURANT]->(r:Restaurant)
MATCH (r)-[:SERVES_MAIN_CUISINE]->(:MainCuisine {name:$cuisine})
MATCH (r)-[link:HAS_MENU]->(m:Menu)
WHERE link.price IS NOT NULL AND link.rating IS NOT NULL
WITH
    m.name AS food_name,
    min(link.price) AS min_food_price,
    avg(link.price) AS avg_food_price,
    max(link.price) AS max_food_price,
    stDev(link.price) AS sd_food_price,
    min(link.rating) AS min_food_rating,
    avg(link.rating) AS avg_food_rating,
    max(link.rating) AS max_food_rating,
    count(*) AS listings
WHERE listings >= $min_listings AND avg_food_rating <= $max_avg_rating
RETURN food_name, min_food_price, avg_food_price, max_food_price, sd_food_price, 
min_food_rating, avg_food_rating, max_food_rating, listings
ORDER BY food_name ASC, avg_food_rating DESC
LIMIT $limit

// cypher_get_premium_menu
MATCH (:Area {ids: $area_ids})-[:HAS_LOCALITY]->(:Locality)-[:HAS_RESTAURANT]->(r:Restaurant)
MATCH (r)-[:SERVES_MAIN_CUISINE]->(:MainCuisine {name:$cuisine})
MATCH (r)-[link:HAS_MENU]->(m:Menu)
WHERE link.price IS NOT NULL AND link.rating IS NOT NULL
WITH
    m.name AS food_name,
    min(link.price) AS min_food_price,
    avg(link.price) AS avg_food_price,
    max(link.price) AS max_food_price,
    stDev(link.price) AS sd_food_price,
    min(link.rating) AS min_food_rating,
    avg(link.rating) AS avg_food_rating,
    max(link.rating) AS max_food_rating,
    count(*) AS listings
WHERE listings >= $min_listings AND avg_food_rating >= $min_avg_rating
RETURN food_name, min_food_price, avg_food_price, max_food_price, sd_food_price, 
min_food_rating, avg_food_rating, max_food_rating, listings
ORDER BY food_name ASC, avg_food_rating DESC, avg_food_price DESC
LIMIT $limit

