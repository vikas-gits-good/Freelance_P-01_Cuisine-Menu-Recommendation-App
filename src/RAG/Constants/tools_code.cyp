// get_competitors_data
MATCH (:Area {ids: $area_ids})-[:HAS_LOCALITY]->(:Locality)-[:HAS_RESTAURANT]->(r:Restaurant)
MATCH (r)-[:SERVES_MAIN_CUISINE]->(:MainCuisine {name: $cuisine})
MATCH (r)-[link:HAS_MENU]->(menu:Menu)
WHERE r.rating IS NOT NULL AND r.rating >= $min_cmpt_rating
RETURN  
    r.name AS rstn_name,
    r.area AS rstn_area,
    r.cuisines AS rstn_cuisine,
    r.rating AS rstn_rating,
    r.chain AS rstn_chain,
    min(link.rating) AS min_menu_rating,
    avg(link.rating) AS avg_menu_rating,
    max(link.rating) AS max_menu_rating,
    min(link.price) AS min_menu_price,
    avg(link.price) AS avg_menu_price,
    max(link.price) AS max_menu_price,
    stDev(link.price) AS sd_menu_price
ORDER BY rstn_rating DESC, rstn_name ASC
LIMIT $limit

// get_competitors_menu
MATCH (:Area {ids: $area_ids})-[:HAS_LOCALITY]->(:Locality)-[:HAS_RESTAURANT]->(rstn:Restaurant)
MATCH (rstn)-[:SERVES_MAIN_CUISINE]->(:MainCuisine {name: $cuisine})
MATCH (rstn)-[link:HAS_MENU]->(menu:Menu)
WHERE link.rating IS NOT NULL AND link.rating >= $min_menu_rating
WITH rstn, menu, link
ORDER BY rstn.name ASC, link.rating DESC, menu.name ASC
WITH rstn, collect({
    rstn_name: rstn.name,
    rstn_area: rstn.area,
    rstn_cuisines: rstn.cuisines,
    rstn_rating: rstn.rating,
    rstn_chain: rstn.chain,
    menu_name: menu.name,
    menu_types: menu.types,
    menu_price: link.price,
    menu_rating: link.rating
})[0..$num_per_rstn] AS top_menus
UNWIND top_menus AS item
RETURN 
    item.rstn_name AS rstn_name,
    item.rstn_area AS rstn_area,
    item.rstn_cuisines AS rstn_cuisines,
    item.rstn_rating AS rstn_rating,
    item.rstn_chain AS rstn_chain,
    item.menu_name AS menu_name,
    item.menu_types AS menu_types,
    item.menu_price AS menu_price,
    item.menu_rating AS menu_rating
LIMIT $limit

// get_menu_benchmark
MATCH (:Area {ids: $area_ids})-[:HAS_LOCALITY]->(:Locality)-[:HAS_RESTAURANT]->(r:Restaurant)
MATCH (r)-[:SERVES_MAIN_CUISINE]->(:MainCuisine {name: $cuisine})
MATCH (r)-[link:HAS_MENU]->(m:Menu)
WHERE toLower(m.name) CONTAINS toLower($menu_name)
    AND link.price IS NOT NULL
RETURN
    m.name AS menu_name,
    link.price AS menu_price,
    link.rating AS menu_rating,
    r.name AS rstn_name,
    r.rating AS rstn_rating
ORDER BY rstn_name ASC, menu_price DESC
LIMIT $limit

// get_menu_opportunities
MATCH (:Area {ids: $area_ids})-[:HAS_LOCALITY]->(:Locality)-[:HAS_RESTAURANT]->(r:Restaurant)
MATCH (r)-[:SERVES_MAIN_CUISINE]->(:MainCuisine {name: $cuisine})
MATCH (r)-[link:HAS_MENU]->(m:Menu)
WHERE link.rating IS NOT NULL AND link.rating >= $min_menu_rating
RETURN
    m.name AS menu_name,
    m.types AS menu_types,
    count(DISTINCT r.ids) AS competitor_count,
    min(link.rating) AS min_menu_rating,
    avg(link.rating) AS avg_menu_rating,
    max(link.rating) AS max_menu_rating,
    min(link.price) AS min_menu_price,
    avg(link.price) AS avg_menu_price,
    max(link.price) AS max_menu_price,
    stDev(link.price) AS sd_menu_price
ORDER BY competitor_count ASC, avg_menu_rating DESC
LIMIT $limit

// get_overpriced_menu
MATCH (:Area {ids: $area_ids})-[:HAS_LOCALITY]->(:Locality)-[:HAS_RESTAURANT]->(r:Restaurant)
MATCH (r)-[:SERVES_MAIN_CUISINE]->(:MainCuisine {name:$cuisine})
MATCH (r)-[link:HAS_MENU]->(m:Menu)
WHERE link.price IS NOT NULL AND link.rating IS NOT NULL
WITH
    m.name AS menu_name,
    min(link.price) AS min_menu_price,
    avg(link.price) AS avg_menu_price,
    max(link.price) AS max_menu_price,
    stDev(link.price) AS sd_menu_price,
    min(link.rating) AS min_menu_rating,
    avg(link.rating) AS avg_menu_rating,
    max(link.rating) AS max_menu_rating,
    count(*) AS listings
WHERE listings >= $min_listings AND avg_menu_rating <= $max_avg_rating
RETURN menu_name, min_menu_price, avg_menu_price, max_menu_price, sd_menu_price, 
min_menu_rating, avg_menu_rating, max_menu_rating, listings
ORDER BY menu_name ASC, avg_menu_rating DESC
LIMIT $limit

// get_premium_menu
MATCH (:Area {ids: $area_ids})-[:HAS_LOCALITY]->(:Locality)-[:HAS_RESTAURANT]->(r:Restaurant)
MATCH (r)-[:SERVES_MAIN_CUISINE]->(:MainCuisine {name:$cuisine})
MATCH (r)-[link:HAS_MENU]->(m:Menu)
WHERE link.price IS NOT NULL AND link.rating IS NOT NULL
WITH
    m.name AS menu_name,
    min(link.price) AS min_menu_price,
    avg(link.price) AS avg_menu_price,
    max(link.price) AS max_menu_price,
    stDev(link.price) AS sd_menu_price,
    min(link.rating) AS min_menu_rating,
    avg(link.rating) AS avg_menu_rating,
    max(link.rating) AS max_menu_rating,
    count(*) AS listings
WHERE listings >= $min_listings AND avg_menu_rating >= $min_avg_rating
RETURN menu_name, min_menu_price, avg_menu_price, max_menu_price, sd_menu_price, 
min_menu_rating, avg_menu_rating, max_menu_rating, listings
ORDER BY menu_name ASC, avg_menu_rating DESC, avg_menu_price DESC
LIMIT $limit

// get_specific_competitor_menu
MATCH (rstn:Restaurant {ids: $rstn_id})-[link:HAS_MENU]->(m:Menu)
RETURN
    rstn.name AS rstn_name,
    rstn.area AS rstn_area,
    m.name AS menu_name,
    m.types AS menu_types,
    link.price AS menu_price,
    link.rating AS menu_rating
ORDER BY menu_rating DESC, menu_name ASC
LIMIT $limit

// recommend_menu
MATCH (:Area {ids: $area_ids})-[:HAS_LOCALITY]->(:Locality)-[:HAS_RESTAURANT]->(r:Restaurant)
MATCH (r)-[:SERVES_MAIN_CUISINE]->(:MainCuisine {name:$cuisine})
MATCH (r)-[link:HAS_MENU]->(m:Menu)
WHERE link.rating IS NOT NULL AND link.rating >= $min_menu_rating
RETURN
    m.name AS menu_name,
    m.types AS menu_types,
    avg(link.price) AS avg_menu_price,
    avg(link.rating) AS avg_menu_rating
ORDER BY avg_menu_rating DESC
LIMIT $limit

// get_area_ids
MATCH (city:City)-[:HAS_AREA]->(area:Area)
WHERE 
    (toLower(city.name) CONTAINS toLower($city_name) OR
    toLower(city.old_name) CONTAINS toLower($city_name)) AND 
    toLower(area.name) CONTAINS toLower($area_name)
RETURN area.ids AS area_ids
LIMIT 1

// get_cuis_name
MATCH (cuis:MainCuisine)
WHERE toLower(cuis.name) CONTAINS toLower($cuis_name)
RETURN cuis.name AS cuisine
LIMIT 1

// get_rstn_ids
MATCH (city:City)-[:HAS_AREA]->(area:Area)-[:HAS_LOCALITY]-(:Locality)-[:HAS_RESTAURANT]-(rstn:Restaurant)
WHERE 
    (toLower(city.name) CONTAINS toLower($city_name) OR
    toLower(city.old_name) CONTAINS toLower($city_name)) AND
    toLower(area.name) CONTAINS toLower($area_name) AND
    toLower(rstn.name) CONTAINS toLower($rstn_name)
RETURN rstn.ids AS rstn_id
ORDER BY rstn.ids ASC 
LIMIT 1