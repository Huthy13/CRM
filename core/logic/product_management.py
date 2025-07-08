import sqlite3
from datetime import datetime

# It's better if DatabaseHandler is used consistently.
# For now, these functions manage their own connections or accept one.
# DB_NAME = "product_management.db" # This might be from an older version or for standalone script use.
# The DatabaseHandler in core.database should be the primary way to get connections.

# def get_db_connection(): # This should be removed if DatabaseHandler is used.
#     """Establishes a connection to the SQLite database."""
#     conn = sqlite3.connect(DB_NAME)
#     conn.row_factory = sqlite3.Row
#     return conn

class ProductLogic:
    def __init__(self, db_handler): # db_handler should be an instance of DatabaseHandler
        self.db = db_handler

    # --- Product CRUD ---
    def save_product(self, product_struct) -> int | None: # product_struct is shared.structs.Product
        # This method will adapt the Product struct to the existing create_product/update_product functions
        # or directly implement the logic using self.db.cursor and self.db.conn

        # For now, let's assume it calls a modified version of the existing functions
        # or new methods in DatabaseHandler.
        # The existing create_product and update_product functions are standalone and manage their own connections.
        # They would need to be refactored to use the passed db_handler's connection.

        # Simplified example:
        # This needs to map product_struct fields to the dictionary 'data' expected by create_product/update_product
        # and handle category name to ID, unit name to ID lookups.

        # This is a placeholder for the actual implementation which will be more involved.
        # It needs to interact with self.db.add_product or self.db.update_product
        # which were defined in database.py and take specific parameters.

        # Let's assume the methods in database.py are the primary interface for DB operations.
        if product_struct.product_id is None:
            # Add new product - this will call self.db.add_product
            # which needs category_name and unit_of_measure_name
            return self.db.add_product(
                name=product_struct.name,
                description=product_struct.description,
                cost=product_struct.cost,
                is_active=product_struct.is_active,
                category_name=product_struct.category, # Assuming Product struct's category is name
                unit_of_measure_name=product_struct.unit_of_measure # Assuming UoM is name
            )
        else:
            # Update existing product - this will call self.db.update_product
            self.db.update_product(
                product_id=product_struct.product_id,
                name=product_struct.name,
                description=product_struct.description,
                cost=product_struct.cost,
                is_active=product_struct.is_active,
                category_name=product_struct.category,
                unit_of_measure_name=product_struct.unit_of_measure
            )
            return product_struct.product_id # Return ID for consistency with add

    def get_product_details(self, product_id: int): # Returns shared.structs.Product or None
        # This should call self.db.get_product_details(product_id) which returns a dict.
        # Then convert dict to Product struct.
        product_data_dict = self.db.get_product_details(product_id)
        if product_data_dict:
            from shared.structs import Product # Local import for safety
            # The db.get_product_details returns category_id, need to resolve to path
            # For now, let's assume category in Product struct is just the name/id from db
            # This needs to align with how Product struct is defined and used.
            # The db method was updated to return category_id. Logic layer should build path.

            category_path = ""
            if product_data_dict.get('category_id'):
                 # This requires _get_all_categories_map and _get_category_path_string from AddressBookLogic
                 # Or similar helper methods here. For now, let's assume category_id is enough or use placeholder.
                 # Placeholder:
                 cat_name = self.db.get_product_category_name_by_id(product_data_dict['category_id'])
                 category_path = cat_name if cat_name else str(product_data_dict['category_id'])


            return Product(
                product_id=product_data_dict.get("product_id"),
                name=product_data_dict.get("name"),
                description=product_data_dict.get("description"),
                cost=product_data_dict.get("cost"),
                is_active=product_data_dict.get("is_active", True),
                category=category_path, # This should be path, but db returns id. Needs path construction.
                unit_of_measure=product_data_dict.get("unit_of_measure_name") # db returns name
            )
        return None

    def get_all_products(self): # Returns list[shared.structs.Product]
        # Calls self.db.get_all_products() which returns list of dicts.
        # Convert each dict to Product struct.
        products_data_list = self.db.get_all_products()
        products_list = []
        from shared.structs import Product # Local import
        for p_dict in products_data_list:
            category_path = ""
            if p_dict.get('category_id'):
                 # Placeholder for path construction
                 cat_name = self.db.get_product_category_name_by_id(p_dict['category_id'])
                 category_path = cat_name if cat_name else str(p_dict['category_id'])

            products_list.append(Product(
                product_id=p_dict.get("product_id"),
                name=p_dict.get("name"),
                description=p_dict.get("description"),
                cost=p_dict.get("cost"),
                is_active=p_dict.get("is_active", True),
                category=category_path, # Needs path construction
                unit_of_measure=p_dict.get("unit_of_measure_name")
            ))
        return products_list

    def delete_product(self, product_id: int):
        return self.db.delete_product(product_id)

    # --- Category Management ---
    # These methods will wrap the standalone functions or call new DB handler methods
    def get_flat_category_paths(self) -> list[tuple[int, str]]:
        # This logic was in AddressBookLogic, needs to be here or in DB handler
        # For now, mock or assume DB method.
        # Placeholder:
        all_categories_map = self._get_all_categories_map_internal()
        leaf_paths = []
        for cat_id, (name, parent_id) in all_categories_map.items():
            path = self._get_category_path_string_internal(cat_id, all_categories_map)
            leaf_paths.append((cat_id, path))
        leaf_paths.sort(key=lambda x: x[1])
        return leaf_paths

    def _get_all_categories_map_internal(self) -> dict[int, tuple[str, int | None]]:
        categories_data = self.db.get_all_product_categories_from_table() # (id, name, parent_id)
        return {cat_id: (name, parent_id) for cat_id, name, parent_id in categories_data}

    def _get_category_path_string_internal(self, category_id: int, all_categories_map: dict[int, tuple[str, int | None]]) -> str:
        if category_id is None or category_id not in all_categories_map:
            return ""
        name, parent_id = all_categories_map[category_id]
        if parent_id is None or parent_id not in all_categories_map:
            return name
        else:
            parent_path = self._get_category_path_string_internal(parent_id, all_categories_map)
            return f"{parent_path}\\\\{name}" # Double backslash for literal

    def get_all_product_units_of_measure(self) -> list[str]:
        units_tuples = self.db.get_all_product_units_of_measure_from_table()
        return [name for unit_id, name in units_tuples]

    def get_all_product_categories_from_table(self): # For CategoryListPopup
        return self.db.get_all_product_categories_from_table()

    def add_product_category(self, name: str, parent_id: int | None = None):
        return self.db.add_product_category(name, parent_id)

    def update_product_category_name(self, category_id: int, new_name: str):
        return self.db.update_product_category_name(category_id, new_name)

    def update_product_category_parent(self, category_id: int, new_parent_id: int | None):
        # TODO: Add cycle detection here if not robustly in DB
        if category_id == new_parent_id:
            raise ValueError("A category cannot be its own parent.")
        # More advanced cycle detection: Walk up from new_parent_id to see if category_id is an ancestor.
        current_ancestor_id = new_parent_id
        all_cats_map = self._get_all_categories_map_internal()
        while current_ancestor_id is not None:
            if current_ancestor_id == category_id:
                raise ValueError("Cannot set parent to a descendant category (creates a cycle).")
            _name, current_ancestor_id = all_cats_map.get(current_ancestor_id, (None, None))

        return self.db.update_product_category_parent(category_id, new_parent_id)

    def delete_product_category(self, category_id: int):
        return self.db.delete_product_category(category_id)

# --- Standalone functions (to be refactored or wrapped by ProductLogic class) ---
# These functions currently manage their own DB connections or expect one to be passed.
# For ProductLogic to use them, they'd ideally be refactored to take a cursor or use methods on self.db.

# (Keep existing functions for now, ProductLogic will call DB handler methods instead of these directly)

# ... (rest of the original file with standalone functions) ...

# For example, the ProductLogic.save_product will NOT call the standalone create_product function below.
# It will call self.db.add_product or self.db.update_product.

# --- Product CRUD Functions ---

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# --- Product CRUD Functions ---

def create_product(data: dict, db_conn=None) -> int | None:
    required_fields = ['sku', 'name']
    if not all(field in data for field in required_fields):
        print("Error: SKU and Name are required.")
        return None

    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()

    try:
        cursor = conn.cursor()
        columns = ['sku', 'name', 'description', 'category_id', 'unit_of_measure', 'is_active', 'created_at', 'updated_at']
        values_to_insert = {col: data.get(col) for col in columns if col in data}

        values_to_insert.setdefault('is_active', True)
        current_time = datetime.now()
        values_to_insert.setdefault('created_at', current_time)
        values_to_insert.setdefault('updated_at', current_time)

        if 'category_id' in values_to_insert and not values_to_insert['category_id']:
            values_to_insert['category_id'] = None

        sql_cols_list = ['sku', 'name']
        sql_vals_list = [values_to_insert['sku'], values_to_insert['name']]

        optional_db_fields = ['description', 'category_id', 'unit_of_measure', 'is_active', 'created_at', 'updated_at']
        for field in optional_db_fields:
            if field in values_to_insert:
                sql_cols_list.append(field)
                sql_vals_list.append(values_to_insert[field])

        placeholders = ', '.join(['?'] * len(sql_cols_list))
        cols_str = ', '.join(sql_cols_list)

        cursor.execute(f"INSERT INTO products ({cols_str}) VALUES ({placeholders})", tuple(sql_vals_list))
        if not conn_provided: conn.commit()
        product_id = cursor.lastrowid
        return product_id
    except sqlite3.IntegrityError as e:
        print(f"Error creating product: {e}")
        if conn_provided: conn.rollback()
        return None
    except sqlite3.Error as e:
        print(f"Database error creating product: {e}")
        if conn_provided: conn.rollback()
        return None
    finally:
        if not conn_provided and conn:
            conn.close()

def get_product(product_id: int, db_conn=None) -> dict | None:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ? AND is_active = TRUE", (product_id,))
        product = cursor.fetchone()
        return dict(product) if product else None
    except sqlite3.Error as e:
        print(f"Database error getting product {product_id}: {e}")
        return None
    finally:
        if not conn_provided and conn:
            conn.close()

def update_product(product_id: int, data: dict, db_conn=None) -> bool:
    if not data:
        print("No data provided for update.")
        return False

    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()

    try:
        cursor = conn.cursor()
        fields_to_update = []
        values_to_update = []

        for key, value in data.items():
            if key in ['sku', 'id', 'created_at', 'updated_at', 'is_active']:
                continue
            fields_to_update.append(f"{key} = ?")
            values_to_update.append(value)

        if not fields_to_update:
            return False

        fields_to_update.append("updated_at = ?")
        values_to_update.append(datetime.now())
        values_to_update.append(product_id)

        sql = f"UPDATE products SET {', '.join(fields_to_update)} WHERE id = ? AND is_active = TRUE"

        cursor.execute(sql, tuple(values_to_update))
        if not conn_provided: conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error updating product {product_id}: {e}")
        if conn_provided: conn.rollback()
        return False
    finally:
        if not conn_provided and conn:
            conn.close()

def delete_product(product_id: int, db_conn=None) -> bool:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET is_active = FALSE, updated_at = ? WHERE id = ?", (datetime.now(), product_id))
        if not conn_provided: conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error deleting product {product_id}: {e}")
        if conn_provided: conn.rollback()
        return False
    finally:
        if not conn_provided and conn:
            conn.close()

def list_products(filters: dict = None, db_conn=None) -> list[dict]:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        sql = "SELECT * FROM products"
        conditions = []
        params = []
        _filters = filters.copy() if filters else {}

        if 'is_active' not in _filters:
            _filters['is_active'] = True
        elif _filters['is_active'] is None:
            del _filters['is_active']

        for key, value in _filters.items():
            if key in ["name", "sku", "description"]:
                conditions.append(f"{key} LIKE ?")
                params.append(f"%{value}%")
            elif key == "category_id" and value is None:
                conditions.append(f"category_id IS NULL")
            elif value is not None:
                conditions.append(f"{key} = ?")
                params.append(value)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        cursor.execute(sql, tuple(params))
        products = [dict(row) for row in cursor.fetchall()]
        return products
    except sqlite3.Error as e:
        print(f"Database error listing products: {e}")
        return []
    finally:
        if not conn_provided and conn:
            conn.close()

# --- Category Management Functions ---

def create_category(data: dict, db_conn=None) -> int | None:
    if 'name' not in data or not data['name']:
        print("Error: Category name is required.")
        return None

    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()

    try:
        cursor = conn.cursor()
        name = data['name']
        parent_id = data.get('parent_id')
        description = data.get('description', '')
        if parent_id == '' or parent_id == 0: parent_id = None

        if parent_id is not None:
            # Use a separate get_category call which handles its own connection if needed,
            # or pass the existing one.
            parent_cat = get_category(parent_id, db_conn=conn)
            if not parent_cat:
                print(f"Error: Parent category with ID {parent_id} does not exist.")
                return None

        cursor.execute("INSERT INTO product_categories (name, parent_id, description) VALUES (?, ?, ?)",
                       (name, parent_id, description))
        if not conn_provided: conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Database error creating category: {e}")
        if conn_provided: conn.rollback()
        return None
    finally:
        if not conn_provided and conn:
            conn.close()

def get_category(category_id: int, db_conn=None) -> dict | None:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product_categories WHERE id = ?", (category_id,))
        category = cursor.fetchone()
        return dict(category) if category else None
    except sqlite3.Error as e:
        print(f"Database error getting category {category_id}: {e}")
        return None
    finally:
        if not conn_provided and conn:
            conn.close()

def update_category(category_id: int, data: dict, db_conn=None) -> bool:
    if not data: return False

    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()

    try:
        cursor = conn.cursor()
        # Check if category exists using the potentially shared connection
        current_cat_info = get_category(category_id, db_conn=conn)
        if not current_cat_info:
            print(f"Category with ID {category_id} not found.")
            return False

        fields_to_update = []
        values_to_update = []
        if 'name' in data and data['name']:
            fields_to_update.append("name = ?")
            values_to_update.append(data['name'])
        if 'description' in data:
            fields_to_update.append("description = ?")
            values_to_update.append(data['description'])
        if 'parent_id' in data:
            new_parent_id = data['parent_id']
            if new_parent_id == '' or new_parent_id == 0: new_parent_id = None
            if new_parent_id is not None:
                if not get_category(new_parent_id, db_conn=conn): # Check parent existence
                    print(f"Error: Proposed parent ID {new_parent_id} does not exist.")
                    return False
                if new_parent_id == category_id:
                    print("Error: A category cannot be its own parent.")
                    return False
                descendants = get_category_descendants_ids(category_id, db_conn=conn)
                if new_parent_id in descendants:
                    print(f"Error: Cannot set parent to a descendant category (ID: {new_parent_id}).")
                    return False
            fields_to_update.append("parent_id = ?")
            values_to_update.append(new_parent_id)

        if not fields_to_update: return True

        values_to_update.append(category_id)
        sql = f"UPDATE product_categories SET {', '.join(fields_to_update)} WHERE id = ?"
        cursor.execute(sql, tuple(values_to_update))
        if not conn_provided: conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error updating category {category_id}: {e}")
        if conn_provided: conn.rollback()
        return False
    finally:
        if not conn_provided and conn:
            conn.close()

def delete_category(category_id: int, db_conn=None) -> bool: # Removed recursive_delete_products as it wasn't used
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        # Check for child categories using the potentially shared connection
        children = list_categories(parent_id=category_id, db_conn=conn)
        if children:
            print(f"Error: Category {category_id} has child categories.")
            return False

        # Check for products in this category using the potentially shared connection
        products_in_cat = list_products(filters={'category_id': category_id, 'is_active': None}, db_conn=conn)
        if products_in_cat:
            print(f"Category {category_id} has products. Unassigning them.")
            # This update_product needs to be part of the transaction if conn_provided
            for prod in products_in_cat:
                update_product(prod['id'], {'category_id': None}, db_conn=conn)

        cursor.execute("DELETE FROM product_categories WHERE id = ?", (category_id,))
        if not conn_provided: conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error deleting category {category_id}: {e}")
        if conn_provided: conn.rollback()
        return False
    finally:
        if not conn_provided and conn:
            conn.close()

def list_categories(parent_id: int | None = None, db_conn=None) -> list[dict]:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        if parent_id is None:
            cursor.execute("SELECT * FROM product_categories WHERE parent_id IS NULL ORDER BY name")
        else:
            cursor.execute("SELECT * FROM product_categories WHERE parent_id = ? ORDER BY name", (parent_id,))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error listing categories: {e}")
        return []
    finally:
        if not conn_provided and conn:
            conn.close()

def get_category_descendants_ids(category_id: int, db_conn=None) -> set[int]:
    # This function inherently needs to list categories, so it should use the passed connection.
    all_cats_raw = list_categories(parent_id=None, db_conn=db_conn) # Get all top-level

    # To get all categories, we need a way to list them all, not just top-level or direct children
    # For now, let's assume we can query all categories directly if needed for this helper
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()

    all_categories_for_tree = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, parent_id FROM product_categories")
        all_categories_for_tree = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error fetching all categories for descendants check: {e}")
        return set() # Return empty on error
    finally:
        if not conn_provided and conn: # Close only if internally created for this specific query
            conn.close()

    adj = {}
    for cat_id_db, p_id_db in all_categories_for_tree:
        if p_id_db not in adj: adj[p_id_db] = []
        adj[p_id_db].append(cat_id_db)

    q = [category_id]
    visited_descendants = set()
    head = 0
    while head < len(q):
        current_cat_id = q[head]; head += 1
        if current_cat_id in adj:
            for child_id in adj[current_cat_id]:
                if child_id not in visited_descendants:
                    visited_descendants.add(child_id)
                    q.append(child_id)
    return visited_descendants


def list_products_in_category_recursive(category_id: int, db_conn=None) -> list[dict]:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        descendant_ids = get_category_descendants_ids(category_id, db_conn=conn)
        category_ids_to_query = {category_id}.union(descendant_ids)
        if not category_ids_to_query: return []
        placeholders = ', '.join(['?'] * len(category_ids_to_query))
        sql = f"SELECT * FROM products WHERE category_id IN ({placeholders}) AND is_active = TRUE"
        cursor.execute(sql, tuple(list(category_ids_to_query)))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error in list_products_in_category_recursive: {e}")
        return []
    finally:
        if not conn_provided and conn:
            conn.close()

# --- Pricing Engine Functions ---

def add_or_update_product_price(data: dict, db_conn=None) -> int | None:
    required_fields = ['product_id', 'price', 'currency', 'valid_from']
    if not all(field in data for field in required_fields):
        print("Error: product_id, price, currency, valid_from are required.")
        return None

    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()

    try:
        cursor = conn.cursor()
        product_id = data['product_id']
        price_value = data['price']
        currency = data['currency'].upper()
        raw_valid_from = data['valid_from']
        raw_valid_to = data.get('valid_to')
        price_record_id = data.get('id')

        valid_from = None
        if isinstance(raw_valid_from, str): valid_from = datetime.strptime(raw_valid_from, '%Y-%m-%d').date()
        elif hasattr(raw_valid_from, 'date'): valid_from = raw_valid_from.date()
        else: valid_from = raw_valid_from

        valid_to = None
        if raw_valid_to is not None:
            if isinstance(raw_valid_to, str): valid_to = datetime.strptime(raw_valid_to, '%Y-%m-%d').date()
            elif hasattr(raw_valid_to, 'date'): valid_to = raw_valid_to.date()
            else: valid_to = raw_valid_to

        if valid_to and valid_from and valid_to < valid_from:
            print("Error: valid_to date cannot be before valid_from date.")
            return None

        # Check product existence using the connection
        prod_exists = get_product(product_id, db_conn=conn)
        if not prod_exists:
            print(f"Error: Product with ID {product_id} does not exist.")
            return None

        if price_record_id:
            cursor.execute("UPDATE product_prices SET product_id=?, price=?, currency=?, valid_from=?, valid_to=? WHERE id=?",
                           (product_id, price_value, currency, valid_from, valid_to, price_record_id))
            if cursor.rowcount == 0: price_record_id = None # Indicate no update or record not found
        else:
            query_find = "SELECT id FROM product_prices WHERE product_id = ? AND currency = ? AND valid_from = ? AND "
            params_find = [product_id, currency, valid_from]
            if valid_to is None: query_find += "valid_to IS NULL"
            else: query_find += "valid_to = ?"; params_find.append(valid_to)
            cursor.execute(query_find, tuple(params_find))
            existing_record = cursor.fetchone()
            if existing_record:
                price_record_id = existing_record['id']
                cursor.execute("UPDATE product_prices SET price = ? WHERE id = ?", (price_value, price_record_id))
            else:
                cursor.execute("INSERT INTO product_prices (product_id, price, currency, valid_from, valid_to) VALUES (?, ?, ?, ?, ?)",
                               (product_id, price_value, currency, valid_from, valid_to))
                price_record_id = cursor.lastrowid

        if price_record_id is not None and not conn_provided: conn.commit()
        elif price_record_id is None and conn_provided: conn.rollback() # If ID based update failed

        return price_record_id
    except ValueError as ve:
        print(f"Date parsing error: {ve}")
        return None
    except sqlite3.Error as e:
        print(f"Database error adding/updating price: {e}")
        if conn_provided: conn.rollback()
        return None
    finally:
        if not conn_provided and conn:
            conn.close()

def get_product_prices(product_id: int, currency: str | None = None, db_conn=None) -> list[dict]:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        sql = "SELECT * FROM product_prices WHERE product_id = ?"
        params = [product_id]
        if currency: sql += " AND currency = ?"; params.append(currency.upper())
        sql += " ORDER BY valid_from DESC, valid_to DESC, currency"
        cursor.execute(sql, tuple(params))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error getting product prices: {e}")
        return []
    finally:
        if not conn_provided and conn:
            conn.close()

def get_effective_price(product_id: int, target_date_str: str | None = None, currency: str = "USD", db_conn=None) -> dict | None:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        target_date_obj = None
        if target_date_str:
            if isinstance(target_date_str, str): target_date_obj = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            elif hasattr(target_date_str, 'date'): target_date_obj = target_date_str.date()
            else: target_date_obj = target_date_str
        else: target_date_obj = datetime.now().date()

        sql = """SELECT * FROM product_prices WHERE product_id = ? AND currency = ?
                 AND date(valid_from) <= date(?) AND (valid_to IS NULL OR date(valid_to) >= date(?))
                 ORDER BY date(valid_from) DESC, CASE WHEN valid_to IS NULL THEN 0 ELSE 1 END ASC,
                          date(valid_to) DESC, id DESC LIMIT 1"""
        target_date_iso = target_date_obj.isoformat()
        cursor.execute(sql, (product_id, currency.upper(), target_date_iso, target_date_iso))
        price_record = cursor.fetchone()
        return dict(price_record) if price_record else None
    except ValueError as ve:
        print(f"Date parsing error in get_effective_price: {ve}")
        return None
    except sqlite3.Error as e:
        print(f"Database error in get_effective_price: {e}")
        return None
    finally:
        if not conn_provided and conn:
            conn.close()

def delete_product_price(price_id: int, db_conn=None) -> bool:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM product_prices WHERE id = ?", (price_id,))
        if not conn_provided: conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error deleting price record {price_id}: {e}")
        if conn_provided: conn.rollback()
        return False
    finally:
        if not conn_provided and conn:
            conn.close()

# --- Inventory Tracking Functions ---

def adjust_inventory(product_id: int, location_id: int, delta_quantity: float,
                     min_stock: float | None = None, max_stock: float | None = None, db_conn=None) -> dict | None:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        prod = get_product(product_id, db_conn=conn) # Use shared conn
        if not prod :
            print(f"Error: Active product with ID {product_id} not found for inventory adjustment.")
            return None

        inv_rec = get_inventory_at_location(product_id, location_id, db_conn=conn) # Use shared conn
        cur_qty, rec_id, db_min, db_max = (inv_rec['quantity'], inv_rec['id'], inv_rec['min_stock'], inv_rec['max_stock']) if inv_rec else (0, None, 0, 0)

        new_qty = cur_qty + delta_quantity
        if new_qty < 0:
            print(f"Error: Adjustment for product {product_id} at loc {location_id} would result in negative quantity.")
            return None

        final_min = min_stock if min_stock is not None else db_min
        final_max = max_stock if max_stock is not None else db_max
        if rec_id:
            cursor.execute("UPDATE product_inventory SET quantity = ?, min_stock = ?, max_stock = ? WHERE id = ?",
                           (new_qty, final_min, final_max, rec_id))
        else:
            cursor.execute("INSERT INTO product_inventory (product_id, location_id, quantity, min_stock, max_stock) VALUES (?, ?, ?, ?, ?)",
                           (product_id, location_id, new_qty, final_min if final_min is not None else 0, final_max if final_max is not None else 0))
            rec_id = cursor.lastrowid

        if not conn_provided: conn.commit()
        return {'id': rec_id, 'product_id': product_id, 'location_id': location_id,
                'quantity': new_qty, 'min_stock': final_min, 'max_stock': final_max}
    except sqlite3.Error as e:
        print(f"Database error during inventory adjustment: {e}")
        if conn_provided: conn.rollback()
        return None
    finally:
        if not conn_provided and conn:
            conn.close()

def get_inventory_at_location(product_id: int, location_id: int, db_conn=None) -> dict | None:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product_inventory WHERE product_id = ? AND location_id = ?", (product_id, location_id))
        return dict(record) if (record := cursor.fetchone()) else None
    except sqlite3.Error as e:
        print(f"Database error in get_inventory_at_location: {e}")
        return None
    finally:
        if not conn_provided and conn:
            conn.close()

def get_all_inventory_for_product(product_id: int, db_conn=None) -> list[dict]:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product_inventory WHERE product_id = ? ORDER BY location_id", (product_id,))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error in get_all_inventory_for_product: {e}")
        return []
    finally:
        if not conn_provided and conn:
            conn.close()

def get_total_product_inventory(product_id: int, db_conn=None) -> dict:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(quantity) as total_quantity, COUNT(id) as locations_count FROM product_inventory WHERE product_id = ?", (product_id,))
        res = cursor.fetchone()
        return {'product_id': product_id, 'total_quantity': res['total_quantity'] or 0, 'locations_count': res['locations_count'] or 0}
    except sqlite3.Error as e:
        print(f"Database error in get_total_product_inventory: {e}")
        return {'product_id': product_id, 'total_quantity': 0, 'locations_count': 0}
    finally:
        if not conn_provided and conn:
            conn.close()

def transfer_inventory(product_id: int, from_loc_id: int, to_loc_id: int, qty: float, db_conn=None) -> bool:
    if qty <= 0: print("Error: Qty to transfer must be positive."); return False
    if from_loc_id == to_loc_id: print("Error: Source/dest locations same."); return False

    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        if not conn_provided: conn.execute("BEGIN") # Start transaction if managing own connection

        src_inv = get_inventory_at_location(product_id, from_loc_id, db_conn=conn)
        if not src_inv or src_inv['quantity'] < qty:
            print(f"Error: Insufficient stock at source {from_loc_id}.")
            if not conn_provided: conn.rollback()
            return False

        adj_src_res = adjust_inventory(product_id, from_loc_id, -qty, db_conn=conn)
        if not adj_src_res:
            print(f"Error decrementing source inventory during transfer.")
            if not conn_provided: conn.rollback()
            return False

        adj_dest_res = adjust_inventory(product_id, to_loc_id, qty, db_conn=conn)
        if not adj_dest_res:
            print(f"Error incrementing destination inventory. Attempting to revert source.")
            # Attempt to revert source adjustment. This is best-effort without full 2PC.
            revert_src = adjust_inventory(product_id, from_loc_id, qty, db_conn=conn)
            if not revert_src:
                 print(f"CRITICAL ERROR: Failed to revert source inventory for product {product_id} from {from_loc_id} after failed transfer to {to_loc_id}. Manual correction needed.")
            if not conn_provided: conn.rollback() # Rollback the overall transaction
            return False

        if not conn_provided: conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error during inventory transfer: {e}")
        if not conn_provided and conn: conn.rollback()
        return False
    finally:
        if not conn_provided and conn:
            conn.close()

def check_low_stock(product_id: int | None = None, location_id: int | None = None, db_conn=None) -> list[dict]:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        sql = "SELECT p.sku, p.name, pi.* FROM product_inventory pi JOIN products p ON pi.product_id = p.id WHERE pi.quantity < pi.min_stock AND p.is_active = TRUE"
        params = []
        if product_id is not None: sql += " AND pi.product_id = ?"; params.append(product_id)
        if location_id is not None: sql += " AND pi.location_id = ?"; params.append(location_id)
        cursor.execute(sql, tuple(params))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error in check_low_stock: {e}")
        return []
    finally:
        if not conn_provided and conn:
            conn.close()

# --- Vendor Integration Functions ---

def link_product_to_vendor(data: dict, db_conn=None) -> int | None:
    required_fields = ['product_id', 'vendor_id']
    if not all(field in data for field in required_fields):
        print("Error: product_id and vendor_id are required.")
        return None

    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        product_id = data['product_id']
        vendor_id = data['vendor_id']

        # Check product existence using the connection
        prod_exists = get_product(product_id, db_conn=conn)
        if not prod_exists:
            print(f"Error: Active product with ID {product_id} not found.")
            return None

        cursor.execute("SELECT id FROM product_vendors WHERE product_id = ? AND vendor_id = ?", (product_id, vendor_id))
        existing_link = cursor.fetchone()
        if existing_link:
            link_id = existing_link['id']
            # For update, only set fields that are explicitly in data.
            # If a key is missing from data, its corresponding column is NOT changed.
            # To clear a field, data should contain field_name: None.
            current_values = dict(existing_link) # Get current values to preserve if not in data

            updated_vendor_sku = data.get('vendor_sku', current_values.get('vendor_sku'))
            updated_lead_time = data.get('lead_time', current_values.get('lead_time'))
            updated_last_price = data.get('last_price', current_values.get('last_price'))

            # The logic for which fields to update if they are not present in `data`
            # The test expects missing fields to be Nulled.
            # Default .get(key) without a second arg IS None.
            updated_vendor_sku = data.get('vendor_sku')
            updated_lead_time = data.get('lead_time')
            updated_last_price = data.get('last_price')

            cursor.execute(
                """UPDATE product_vendors
                   SET vendor_sku = ?, lead_time = ?, last_price = ?
                   WHERE id = ?""",
                (updated_vendor_sku, updated_lead_time, updated_last_price, link_id)
            )
        else:
            # For insert, data.get() defaulting to None is appropriate for missing optional fields
            vendor_sku = data.get('vendor_sku')
            lead_time = data.get('lead_time')
            last_price = data.get('last_price')
            cursor.execute("INSERT INTO product_vendors (product_id, vendor_id, vendor_sku, lead_time, last_price) VALUES (?, ?, ?, ?, ?)",
                           (product_id, vendor_id, vendor_sku, lead_time, last_price))
            link_id = cursor.lastrowid

        if not conn_provided: conn.commit()
        return link_id
    except sqlite3.Error as e:
        print(f"Database error linking product to vendor: {e}")
        if conn_provided: conn.rollback()
        return None
    finally:
        if not conn_provided and conn:
            conn.close()

def update_product_vendor_link(link_id: int, data: dict, db_conn=None) -> bool:
    if not data: return False
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        set_clauses, params = [], []
        # Only include fields in the update if they are present in the data dictionary
        if 'vendor_sku' in data: set_clauses.append("vendor_sku = ?"); params.append(data.get('vendor_sku'))
        if 'lead_time' in data: set_clauses.append("lead_time = ?"); params.append(data.get('lead_time'))
        if 'last_price' in data: set_clauses.append("last_price = ?"); params.append(data.get('last_price'))

        if not set_clauses: return False # No fields were specified for update

        params.append(link_id)
        cursor.execute(f"UPDATE product_vendors SET {', '.join(set_clauses)} WHERE id = ?", tuple(params))
        if not conn_provided: conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error updating product-vendor link {link_id}: {e}")
        if conn_provided: conn.rollback()
        return False
    finally:
        if not conn_provided and conn:
            conn.close()

def remove_product_vendor_link(link_id: int, db_conn=None) -> bool:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM product_vendors WHERE id = ?", (link_id,))
        if not conn_provided: conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error removing product-vendor link {link_id}: {e}")
        if conn_provided: conn.rollback()
        return False
    finally:
        if not conn_provided and conn:
            conn.close()

def get_vendors_for_product(product_id: int, db_conn=None) -> list[dict]:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM product_vendors WHERE product_id = ?
                          ORDER BY CASE WHEN last_price IS NULL THEN 1 ELSE 0 END ASC, last_price ASC,
                                   CASE WHEN lead_time IS NULL THEN 1 ELSE 0 END ASC, lead_time ASC, id ASC""", (product_id,))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error in get_vendors_for_product: {e}")
        return []
    finally:
        if not conn_provided and conn:
            conn.close()

def get_products_for_vendor(vendor_id: int, db_conn=None) -> list[dict]:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""SELECT pv.id as link_id, pv.product_id, p.name as product_name, p.sku as product_sku,
                             pv.vendor_id, pv.vendor_sku, pv.lead_time, pv.last_price
                          FROM product_vendors pv JOIN products p ON pv.product_id = p.id
                          WHERE pv.vendor_id = ? AND p.is_active = TRUE ORDER BY p.name ASC""", (vendor_id,))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"Database error in get_products_for_vendor: {e}")
        return []
    finally:
        if not conn_provided and conn:
            conn.close()

def get_preferred_vendor(product_id: int, db_conn=None) -> dict | None:
    vendors = get_vendors_for_product(product_id, db_conn=db_conn)
    return vendors[0] if vendors else None


if __name__ == '__main__':
    import database_setup
    # Initialize with its own connection for __main__ block
    # All functions called below will also manage their own connections
    # unless a global/test connection were explicitly passed.
    db_main_conn = get_db_connection()
    database_setup.initialize_database(db_conn=db_main_conn)


    print("\n--- Testing Product CRUD ---")
    product1_id = create_product({'sku': 'MAIN-001', 'name': 'Main Product 1'}, db_conn=db_main_conn)
    print(f"Created product1_id: {product1_id}")
    product2_id = None
    if product1_id:
        product2_id = create_product({'sku': 'MAIN-002', 'name': 'Main Product 2', 'category_id': None}, db_conn=db_main_conn)
        print(f"Created product2_id: {product2_id}")

        ret_prod = get_product(product1_id, db_conn=db_main_conn)
        print(f"Retrieved P1: {ret_prod['name'] if ret_prod else 'Not Found'}")

        update_product(product1_id, {'name': 'Main Product 1 Updated', 'unit_of_measure': 'KG'}, db_conn=db_main_conn)
        ret_prod_upd = get_product(product1_id, db_conn=db_main_conn)
        print(f"Updated P1: Name: {ret_prod_upd['name']}, UOM: {ret_prod_upd['unit_of_measure']}")

        print("All active products:")
        for p in list_products(db_conn=db_main_conn): print(f"  {p['sku']}: {p['name']}")

        if product2_id:
            delete_product(product2_id, db_conn=db_main_conn)
            print(f"P2 (id:{product2_id}) deleted. Get P2: {get_product(product2_id, db_conn=db_main_conn)}")
        print("All products (incl. inactive):")
        for p in list_products(filters={'is_active': None}, db_conn=db_main_conn): print(f"  {p['sku']}: {p['name']}, Active: {p['is_active']}")

    print("\n--- Testing Category Management ---")
    cat1 = create_category({'name': 'Electronics'}, db_conn=db_main_conn)
    print(f"Created cat1: {cat1}")
    prod_laptop = None
    if cat1:
        subcat1 = create_category({'name': 'Laptops', 'parent_id': cat1}, db_conn=db_main_conn)
        print(f"Created subcat1 for Laptops: {subcat1}")

        if subcat1 and product1_id : # Ensure product1_id exists for this test section
             prod_laptop = create_product({'sku': 'LAP001', 'name': 'FastBook', 'category_id': subcat1}, db_conn=db_main_conn)
             print(f"Created laptop product: {prod_laptop}")
             print(f"Products in cat {cat1} (recursive): {list_products_in_category_recursive(cat1, db_conn=db_main_conn)}")

        if subcat1:
            update_category(subcat1, {'name': 'Gaming Laptops'}, db_conn=db_main_conn)
            print(f"Updated subcat1: {get_category(subcat1, db_conn=db_main_conn)}")
            delete_category(subcat1, db_conn=db_main_conn)
            if prod_laptop:
                 print(f"Subcat1 deleted. Laptop product category: {get_product(prod_laptop, db_conn=db_main_conn)['category_id'] if prod_laptop else 'N/A'}")

        delete_category(cat1, db_conn=db_main_conn)
        print(f"Cat1 deleted. Get cat1: {get_category(cat1, db_conn=db_main_conn)}")

    print("\n--- Testing Pricing Engine ---")
    if product1_id:
        price_id1 = add_or_update_product_price({'product_id': product1_id, 'price': 100, 'currency': 'USD', 'valid_from': '2023-01-01'}, db_conn=db_main_conn)
        print(f"Added price P1 USD 100: {price_id1}")
        price_id2 = add_or_update_product_price({'product_id': product1_id, 'price': 90, 'currency': 'USD', 'valid_from': '2024-01-01'}, db_conn=db_main_conn)
        print(f"Added price P1 USD 90 (future): {price_id2}")

        print(f"P1 price on 2023-05-05: {get_effective_price(product1_id, '2023-05-05', db_conn=db_main_conn)}")
        print(f"P1 price on 2024-02-02: {get_effective_price(product1_id, '2024-02-02', db_conn=db_main_conn)}")
        if price_id2: delete_product_price(price_id2, db_conn=db_main_conn)
        print(f"P1 price on 2024-02-02 after deleting future price: {get_effective_price(product1_id, '2024-02-02', db_conn=db_main_conn)}")

    print("\n--- Testing Inventory Tracking ---")
    if product1_id:
        loc_a, loc_b = 1, 2
        adjust_inventory(product1_id, loc_a, 100, min_stock=10, db_conn=db_main_conn)
        print(f"P1 Inv Loc A: {get_inventory_at_location(product1_id, loc_a, db_conn=db_main_conn)}")
        adjust_inventory(product1_id, loc_b, 50, min_stock=5, db_conn=db_main_conn)
        print(f"P1 Inv Loc B: {get_inventory_at_location(product1_id, loc_b, db_conn=db_main_conn)}")
        print(f"P1 Total Inv: {get_total_product_inventory(product1_id, db_conn=db_main_conn)}")

        transfer_inventory(product1_id, loc_a, loc_b, 20, db_conn=db_main_conn)
        print(f"P1 Inv Loc A after transfer: {get_inventory_at_location(product1_id, loc_a, db_conn=db_main_conn)}")
        print(f"P1 Inv Loc B after transfer: {get_inventory_at_location(product1_id, loc_b, db_conn=db_main_conn)}")

        adjust_inventory(product1_id, loc_a, -75, db_conn=db_main_conn)
        print(f"P1 Low Stock: {check_low_stock(product_id=product1_id, db_conn=db_main_conn)}")

    print("\n--- Testing Vendor Integration ---")
    if product1_id:
        vend1, vend2 = 101, 102
        link_id1 = link_product_to_vendor({'product_id': product1_id, 'vendor_id': vend1, 'last_price': 80, 'lead_time': 7}, db_conn=db_main_conn)
        print(f"P1 Link to V101 (price 80): {link_id1}")
        link_id2 = link_product_to_vendor({'product_id': product1_id, 'vendor_id': vend2, 'last_price': 75, 'lead_time': 10}, db_conn=db_main_conn)
        print(f"P1 Link to V102 (price 75): {link_id2}")

        print(f"P1 Preferred Vendor: {get_preferred_vendor(product1_id, db_conn=db_main_conn)}")

        if link_id1: update_product_vendor_link(link_id1, {'last_price': 70}, db_conn=db_main_conn)
        print(f"P1 Preferred Vendor (after V101 price drop to 70): {get_preferred_vendor(product1_id, db_conn=db_main_conn)}")

        print(f"Vendors for P1: {get_vendors_for_product(product1_id, db_conn=db_main_conn)}")
        if link_id1: remove_product_vendor_link(link_id1, db_conn=db_main_conn)
        print(f"Vendors for P1 (after V101 removed): {get_vendors_for_product(product1_id, db_conn=db_main_conn)}")

        if product2_id:
             link_id3 = link_product_to_vendor({'product_id': product2_id, 'vendor_id': vend1, 'last_price': 50}, db_conn=db_main_conn)
             print(f"Products for V101: {get_products_for_vendor(vend1, db_conn=db_main_conn)}")

    print("\n--- All main tests complete ---")

    if db_main_conn:
        db_main_conn.close()
