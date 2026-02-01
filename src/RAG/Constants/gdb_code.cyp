// get_area_ids
MATCH (cy:City)-[:HAS_AREA]->(ar:Area)
WHERE toLower(cy.name) CONTAINS toLower($city_name)
    AND toLower(ar.name) CONTAINS toLower($area_name)
RETURN ar.ids
LIMIT 1

// get_cuisine_name
MATCH (cu:MainCuisine)
WHERE toLower(cu.name) CONTAINS toLower($cuis_name)
RETURN cu.name
LIMIT 1