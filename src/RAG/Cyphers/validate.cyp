// 1. Check for menu items with cuisines not served by restaurant
MATCH (r:Restaurant)-[:HAS_MENU_ITEM]->(m:MenuItem)-[:BELONGS_TO_CUISINE]->(c:Cuisine)
WHERE NOT (r)-[:SERVES]->(c)
RETURN r.rstn_name as restaurant,
       m.food_name as menu_item,
       c.name as cuisine,
       'WARNING: Menu item cuisine not served by restaurant' as issue

// 2. Check for orphaned nodes
MATCH (m:MenuItem)
WHERE NOT (m)<-[:HAS_MENU_ITEM]-()
RETURN m.food_id, m.food_name, 'Orphaned menu item' as issue

// 3. Check for restaurants without cuisines
MATCH (r:Restaurant)
WHERE NOT (r)-[:SERVES]->()
RETURN r.rstn_id, r.rstn_name, 'No cuisines assigned' as issue

// 4. Check for menu items without cuisine
MATCH (m:MenuItem)
WHERE NOT (m)-[:BELONGS_TO_CUISINE]->()
RETURN m.food_name, 'No cuisine assigned' as issue

// 5. Verify geographic hierarchy
MATCH path = (country:Country)<-[:LOCATED_IN*]-(r:Restaurant)
WHERE length(path) <> 5  // Should be: Restaurant->Locality->Area->City->State->Country
RETURN r.rstn_name, length(path), 'Invalid hierarchy depth' as issue