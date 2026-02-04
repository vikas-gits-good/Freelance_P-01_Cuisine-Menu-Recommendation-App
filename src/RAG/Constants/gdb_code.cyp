// get_area_ids
MATCH (city:City)-[:HAS_AREA]->(area:Area)
WHERE 
    toLower(city.name) CONTAINS toLower($city_name) AND 
    toLower(area.name) CONTAINS toLower($area_name)
RETURN area.ids
LIMIT 1

// get_cuis_name
MATCH (cuis:MainCuisine)
WHERE toLower(cuis.name) CONTAINS toLower($cuis_name)
RETURN cuis.name
LIMIT 1

// get_rstn_ids
MATCH (city:City)-[:HAS_AREA]->(area:Area)-[:HAS_LOCALITY]-(:Locality)-[:HAS_RESTAURANT]-(rstn:Restaurant)
WHERE 
    toLower(city.name) CONTAINS toLower($city_name) AND 
    toLower(area.name) CONTAINS toLower($area_name) AND 
    toLower(rstn.name) CONTAINS toLower($rstn_name)
RETURN rstn.ids
ORDER BY rstn.ids ASC
LIMIT 1