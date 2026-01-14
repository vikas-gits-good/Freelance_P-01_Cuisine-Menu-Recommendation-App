// Check_for_menu_items_with_cuisines_not_served_by_restaurant
MATCH (r:Restaurant)-[:HAS_MENU_ITEM]->(m:MenuItem)-[:BELONGS_TO_CUISINE]->(c:Cuisine)
WHERE NOT (r)-[:SERVES]->(c)
RETURN r.rstn_name as restaurant,
       m.food_name as menu_item,
       c.name as cuisine,
       'WARNING: Menu item cuisine not served by restaurant' as issue

// Check_for_orphaned_nodes
MATCH (m:MenuItem)
WHERE NOT (m)<-[:HAS_MENU_ITEM]-()
RETURN m.food_id, m.food_name, 'Orphaned menu item' as issue

// Check_for_restaurants_without_cuisines
MATCH (r:Restaurant)
WHERE NOT (r)-[:SERVES]->()
RETURN r.rstn_id, r.rstn_name, 'No cuisines assigned' as issue

// Check_for_menu_items_without_cuisine
MATCH (m:MenuItem)
WHERE NOT (m)-[:BELONGS_TO_CUISINE]->()
RETURN m.food_name, 'No cuisine assigned' as issue

// Verify_geographic_hierarchy
MATCH path = (country:Country)<-[:LOCATED_IN*]-(r:Restaurant)
WHERE length(path) <> 5
RETURN r.rstn_name, length(path), 'Invalid hierarchy depth' as issue