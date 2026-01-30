// cypher_get_competitors_data
MATCH (:Area {name: $area})-[:HAS_LOCALITY]->(:Locality)-[:HAS_RESTAURANT]->(r:Restaurant)
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

