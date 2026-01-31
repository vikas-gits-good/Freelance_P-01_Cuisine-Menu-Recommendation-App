// get_area_ids
MATCH (cy:City)
WHERE toLower(cy.name) CONTAINS toLower($city_name)
MATCH (ar:Area)
WHERE toLower(ar.name) CONTAINS toLower($area_name)
RETURN ar.ids
LIMIT 1

// get_cuisine_name
MATCH (cu:MainCuisine)
WHERE toLower(cu.name) CONTAINS toLower($cuis_name)
RETURN cu.name
LIMIT 1