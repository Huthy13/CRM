import sqlite3
from datetime import datetime
from core.database_setup import DB_NAME as MAIN_APP_DB_NAME

DB_NAME = MAIN_APP_DB_NAME

class ProductLogic:
    def __init__(self, db_handler):
        self.db = db_handler

    def save_product(self, product_struct) -> int | None:
        # Ensure SKU is generated if not present, especially for new products.
        # For existing products, SKU might come from product_struct if it has one, or be regenerated.
        # This simple generation is a placeholder.
        generated_sku = f"SKU_{product_struct.name[:10].replace(' ','_').upper()}" if product_struct.name else "SKU_UNKNOWN"
        sku_to_use = getattr(product_struct, 'sku', None) or generated_sku # Use struct's SKU if available

        if product_struct.product_id is None: # Adding new product
            new_product_id = self.db.add_product(
                sku=sku_to_use,
                name=product_struct.name,
                description=product_struct.description,
                cost=product_struct.cost,
                sale_price=getattr(product_struct, 'sale_price', None),
                is_active=product_struct.is_active,
                category_name=product_struct.category,
                unit_of_measure_name=product_struct.unit_of_measure
                # currency and price_valid_from will use defaults in db.add_product
            )
            if new_product_id:
                product_struct.product_id = new_product_id # Update struct with new ID
            return new_product_id
        else: # Updating existing product
            self.db.update_product(
                product_db_id=product_struct.product_id,
                sku=sku_to_use, # SKU might be updatable
                name=product_struct.name,
                description=product_struct.description,
                cost=product_struct.cost,
                sale_price=getattr(product_struct, 'sale_price', None),
                is_active=product_struct.is_active,
                category_name=product_struct.category,
                unit_of_measure_name=product_struct.unit_of_measure
                # currency and price_valid_from will use defaults in db.update_product
            )
            return product_struct.product_id

    def get_product_details(self, product_id: int):
        product_data_dict = self.db.get_product_details(product_id)
        if product_data_dict:
            from shared.structs import Product
            category_path = ""
            if product_data_dict.get('category_id'):
                 cat_name = self.db.get_product_category_name_by_id(product_data_dict['category_id'])
                 # Full path construction would require _get_all_categories_map and _get_category_path_string
                 # For now, using leaf name or ID if name not found.
                 category_path = cat_name if cat_name else str(product_data_dict['category_id'])

            return Product(
                product_id=product_data_dict.get("product_id"),
                name=product_data_dict.get("name"),
                description=product_data_dict.get("description"),
                cost=product_data_dict.get("cost"), # From product_prices
                sale_price=product_data_dict.get("sale_price"), # From product_prices
                is_active=product_data_dict.get("is_active", True),
                category=category_path,
                unit_of_measure=product_data_dict.get("unit_of_measure_name")
            )
        return None

    def get_all_products(self):
        products_data_list = self.db.get_all_products()
        products_list = []
        from shared.structs import Product
        all_categories_map = self._get_all_categories_map_internal() # Cache for efficiency
        for p_dict in products_data_list:
            category_path = ""
            if p_dict.get('category_id'):
                 category_path = self._get_category_path_string_internal(p_dict['category_id'], all_categories_map)

            products_list.append(Product(
                product_id=p_dict.get("product_id"),
                name=p_dict.get("name"),
                description=p_dict.get("description"),
                cost=p_dict.get("cost"), # From product_prices
                sale_price=p_dict.get("sale_price"), # From product_prices
                is_active=p_dict.get("is_active", True),
                category=category_path,
                unit_of_measure=p_dict.get("unit_of_measure_name")
            ))
        return products_list

    def delete_product(self, product_id: int):
        return self.db.delete_product(product_id)

    def _get_all_categories_map_internal(self) -> dict[int, tuple[str, int | None]]:
        categories_data = self.db.get_all_product_categories_from_table()
        return {cat_id: (name, parent_id) for cat_id, name, parent_id in categories_data}

    def _get_category_path_string_internal(self, category_id: int, all_categories_map: dict[int, tuple[str, int | None]]) -> str:
        if category_id is None or category_id not in all_categories_map:
            return ""
        name, parent_id = all_categories_map[category_id]
        if parent_id is None or parent_id not in all_categories_map:
            return name
        else:
            parent_path = self._get_category_path_string_internal(parent_id, all_categories_map)
            return f"{parent_path}\\\\{name}"

    def get_flat_category_paths(self) -> list[tuple[int, str]]:
        all_categories_map = self._get_all_categories_map_internal()
        leaf_paths = []
        for cat_id, (name, parent_id) in all_categories_map.items():
            path = self._get_category_path_string_internal(cat_id, all_categories_map)
            leaf_paths.append((cat_id, path))
        leaf_paths.sort(key=lambda x: x[1])
        return leaf_paths

    def get_all_product_units_of_measure(self) -> list[str]:
        units_tuples = self.db.get_all_product_units_of_measure_from_table()
        return [name for uom_id, name in units_tuples] # Use uom_id

    def get_all_product_categories_from_table(self):
        return self.db.get_all_product_categories_from_table()

    def add_product_category(self, name: str, parent_id: int | None = None):
        return self.db.add_product_category(name, parent_id)

    def update_product_category_name(self, category_id: int, new_name: str):
        return self.db.update_product_category_name(category_id, new_name)

    def update_product_category_parent(self, category_id: int, new_parent_id: int | None):
        if category_id == new_parent_id:
            raise ValueError("A category cannot be its own parent.")
        current_ancestor_id = new_parent_id
        all_cats_map = self._get_all_categories_map_internal()
        while current_ancestor_id is not None:
            if current_ancestor_id == category_id:
                raise ValueError("Cannot set parent to a descendant category (creates a cycle).")
            _name, current_ancestor_id = all_cats_map.get(current_ancestor_id, (None, None))
        return self.db.update_product_category_parent(category_id, new_parent_id)

    def delete_product_category(self, category_id: int):
        return self.db.delete_product_category(category_id)

    def get_hierarchical_categories(self) -> list[dict]:
        all_categories_raw = self.db.get_all_product_categories_from_table()
        categories_map = {cat_id: {'id': cat_id, 'name': name, 'parent_id': parent_id, 'children': []}
                          for cat_id, name, parent_id in all_categories_raw}
        hierarchical_list = []
        for cat_id, data in categories_map.items():
            if data['parent_id'] is None:
                hierarchical_list.append(data)
            elif data['parent_id'] in categories_map:
                categories_map[data['parent_id']]['children'].append(data)
            else:
                print(f"Warning: Category ID {cat_id} has parent_id {data['parent_id']} which was not found. Treating as root.")
                hierarchical_list.append(data)
        for cat_id_key in categories_map:
            if categories_map[cat_id_key]['children']:
                categories_map[cat_id_key]['children'].sort(key=lambda x: x['name'])
        hierarchical_list.sort(key=lambda x: x['name'])
        return hierarchical_list

# Standalone functions below are problematic for testing and consistency.
# Tests should ideally target ProductLogic class methods.

# --- Custom Adapters and Converters for datetime (copied from core/database.py for standalone use) ---
def adapt_datetime_iso_pm(val):
    return val.isoformat()

def adapt_date_iso_pm(val):
    return val.isoformat()

def convert_timestamp_iso_pm(val_bytes):
    val_str = val_bytes.decode('utf-8')
    if val_str.endswith('Z'):
        val_str = val_str[:-1] + '+00:00'
    if '.' in val_str and len(val_str.split('.')[1].split('+')[0].split('-')[0]) > 6:
        parts = val_str.split('.')
        time_part_before_frac = parts[0]
        frac_second_and_rest = parts[1]
        frac_second = frac_second_and_rest[:6]
        rest_of_string = frac_second_and_rest[len(frac_second_and_rest.split('+')[0].split('-')[0]):]
        val_str = f"{time_part_before_frac}.{frac_second}{rest_of_string}"
    try:
        return datetime.datetime.fromisoformat(val_str)
    except ValueError:
        try:
            return datetime.datetime.combine(datetime.date.fromisoformat(val_str), datetime.time.min)
        except ValueError:
            return None

def convert_date_iso_pm(val_bytes):
    try:
        return datetime.date.fromisoformat(val_bytes.decode('utf-8'))
    except ValueError:
        return None

def get_db_connection():
    # Register for connections made by these standalone functions
    sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso_pm)
    sqlite3.register_adapter(datetime.date, adapt_date_iso_pm)
    sqlite3.register_converter("timestamp", convert_timestamp_iso_pm)
    sqlite3.register_converter("datetime", convert_timestamp_iso_pm)
    sqlite3.register_converter("date", convert_date_iso_pm)

    conn = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn

def create_product(data: dict, db_conn=None) -> int | None:
    required_fields = ['sku', 'name']
    if not all(field in data for field in required_fields):
        print("Error: SKU and Name are required.")
        return None

    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()

    try:
        cursor = conn.cursor()

        direct_product_cols = ['sku', 'name', 'description', 'category_id', 'unit_of_measure_id', 'is_active']
        values_to_insert = {col: data.get(col) for col in direct_product_cols if col in data}
        values_to_insert.setdefault('is_active', True)

        if 'category_name' in data and 'category_id' not in data:
            print("Warning (standalone create_product): category_name provided but ID resolution not implemented here. Set category_id to None.")
            values_to_insert['category_id'] = None
        elif 'category_id' in data and not data['category_id']:
             values_to_insert['category_id'] = None

        if 'unit_of_measure' in data and 'unit_of_measure_id' not in data:
            print(f"Warning (standalone create_product): unit_of_measure name '{data['unit_of_measure']}' provided but ID resolution not implemented here. Setting unit_of_measure_id to None.")
            values_to_insert['unit_of_measure_id'] = None
        elif 'unit_of_measure_id' in data and not data['unit_of_measure_id']:
            values_to_insert['unit_of_measure_id'] = None

        current_time_iso = datetime.now().isoformat()
        values_to_insert.setdefault('created_at', current_time_iso)
        values_to_insert.setdefault('updated_at', current_time_iso)

        sql_cols_list = []
        sql_vals_list = []
        for col_name in ['sku', 'name', 'description', 'category_id', 'unit_of_measure_id', 'is_active', 'created_at', 'updated_at']:
            if col_name in values_to_insert:
                sql_cols_list.append(col_name)
                sql_vals_list.append(values_to_insert[col_name])
            elif col_name == 'unit_of_measure_id' and 'unit_of_measure_id' not in values_to_insert:
                sql_cols_list.append('unit_of_measure_id')
                sql_vals_list.append(None)

        placeholders = ', '.join(['?'] * len(sql_cols_list))
        cols_str = ', '.join(sql_cols_list)

        cursor.execute(f"INSERT INTO products ({cols_str}) VALUES ({placeholders})", tuple(sql_vals_list))
        product_id = cursor.lastrowid

        if not conn_provided: conn.commit()
        return product_id
    except sqlite3.Error as e:
        print(f"Error creating product (standalone): {e}")
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
        product_row = cursor.fetchone()
        if not product_row:
            return None

        product_dict = dict(product_row)

        if product_dict.get('unit_of_measure_id'):
            cursor.execute("SELECT name FROM product_units_of_measure WHERE id = ?", (product_dict['unit_of_measure_id'],))
            uom_row = cursor.fetchone()
            product_dict['unit_of_measure_name'] = uom_row['name'] if uom_row else None
        else:
            product_dict['unit_of_measure_name'] = None

        if product_dict.get('category_id'):
            cursor.execute("SELECT name FROM product_categories WHERE id = ?", (product_dict['category_id'],))
            cat_row = cursor.fetchone()
            product_dict['category_name'] = cat_row['name'] if cat_row else None
        else:
            product_dict['category_name'] = None

        cursor.execute("""
            SELECT price FROM product_prices
            WHERE product_id = ? AND price_type = 'COST' AND date(valid_from) <= date('now')
            AND (valid_to IS NULL OR date(valid_to) >= date('now'))
            ORDER BY valid_from DESC LIMIT 1
        """, (product_id,))
        cost_row = cursor.fetchone()
        product_dict['cost'] = cost_row['price'] if cost_row else None

        cursor.execute("""
            SELECT price FROM product_prices
            WHERE product_id = ? AND price_type = 'SALE' AND date(valid_from) <= date('now')
            AND (valid_to IS NULL OR date(valid_to) >= date('now'))
            ORDER BY valid_from DESC LIMIT 1
        """, (product_id,))
        sale_row = cursor.fetchone()
        product_dict['sale_price'] = sale_row['price'] if sale_row else None

        return product_dict
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

        allowed_fields_map = {
            'name': 'name', 'description': 'description', 'category_id': 'category_id',
            'unit_of_measure_id': 'unit_of_measure_id', 'is_active': 'is_active'
        }

        for key_in_data, db_column_name in allowed_fields_map.items():
            if key_in_data in data:
                fields_to_update.append(f"{db_column_name} = ?")
                values_to_update.append(data[key_in_data])

        if 'unit_of_measure' in data and 'unit_of_measure_id' not in data:
            print(f"Warning (standalone update_product): unit_of_measure name '{data['unit_of_measure']}' provided. This function expects 'unit_of_measure_id'. Field not updated by name.")
        if 'category' in data and 'category_id' not in data:
            print(f"Warning (standalone update_product): category name '{data['category']}' provided. This function expects 'category_id'. Field not updated by name.")

        if not fields_to_update:
            print("No valid fields provided for product table update.")

        if fields_to_update:
            fields_to_update.append("updated_at = ?")
            values_to_update.append(datetime.now().isoformat())
            values_to_update.append(product_id)
            sql = f"UPDATE products SET {', '.join(fields_to_update)} WHERE id = ?"
            cursor.execute(sql, tuple(values_to_update))

        if not conn_provided: conn.commit()
        return cursor.rowcount > 0 if fields_to_update else True
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
        cursor.execute("UPDATE products SET is_active = FALSE, updated_at = ? WHERE id = ?", (datetime.now().isoformat(), product_id))
        if not conn_provided: conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error soft-deleting product {product_id}: {e}")
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
            conditions.append("is_active = TRUE")
        elif _filters['is_active'] is not None:
            conditions.append("is_active = ?")
            params.append(1 if _filters['is_active'] else 0)
        _filters.pop('is_active', None)

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

        sql += " ORDER BY name"

        cursor.execute(sql, tuple(params))
        products_raw = [dict(row) for row in cursor.fetchall()]
        return products_raw
    except sqlite3.Error as e:
        print(f"Database error listing products: {e}")
        return []
    finally:
        if not conn_provided and conn:
            conn.close()

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
                if not get_category(new_parent_id, db_conn=conn):
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

def delete_category(category_id: int, db_conn=None) -> bool:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        children = list_categories(parent_id=category_id, db_conn=conn)
        if children:
            print(f"Error: Category {category_id} has child categories.")
            return False
        products_in_cat = list_products(filters={'category_id': category_id, 'is_active': None}, db_conn=conn)
        if products_in_cat:
            print(f"Category {category_id} has products. Unassigning them.")
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
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    all_categories_for_tree = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, parent_id FROM product_categories")
        all_categories_for_tree = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error fetching all categories for descendants check: {e}")
        return set()
    finally:
        if not conn_provided and conn and conn != db_conn:
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

def add_or_update_product_price(data: dict, db_conn=None) -> int | None:
    required_fields = ['product_id', 'price', 'currency', 'valid_from']
    if not all(field in data for field in required_fields):
        print("Error: product_id, price, currency, valid_from are required.")
        return None
    price_type = data.get('price_type', 'SALE').upper()
    if price_type not in ['SALE', 'COST', 'MSRP']:
        print(f"Warning: Invalid price_type '{price_type}'. Defaulting to SALE.")
        price_type = 'SALE'
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
        valid_from = datetime.strptime(raw_valid_from, '%Y-%m-%d').date() if isinstance(raw_valid_from, str) else getattr(raw_valid_from, 'date', lambda: raw_valid_from)()
        valid_to = (datetime.strptime(raw_valid_to, '%Y-%m-%d').date() if isinstance(raw_valid_to, str) else getattr(raw_valid_to, 'date', lambda: raw_valid_to)()) if raw_valid_to is not None else None
        if valid_to and valid_from and valid_to < valid_from:
            print("Error: valid_to date cannot be before valid_from date."); return None
        prod_exists = get_product(product_id, db_conn=conn)
        if not prod_exists:
            print(f"Error: Product with ID {product_id} does not exist."); return None
        query_find = "SELECT id FROM product_prices WHERE product_id = ? AND price_type = ? AND valid_from = ? AND currency = ?"
        params_find = [product_id, price_type, valid_from, currency]
        cursor.execute(query_find, tuple(params_find))
        existing_record = cursor.fetchone()
        if existing_record:
            price_record_id = existing_record['id']
            cursor.execute("UPDATE product_prices SET price = ?, valid_to = ? WHERE id = ?",
                           (price_value, valid_to, price_record_id))
        else:
            cursor.execute("INSERT INTO product_prices (product_id, price_type, price, currency, valid_from, valid_to) VALUES (?, ?, ?, ?, ?, ?)",
                           (product_id, price_type, price_value, currency, valid_from, valid_to))
            price_record_id = cursor.lastrowid
        if price_record_id is not None and not conn_provided: conn.commit()
        elif price_record_id is None and conn_provided: conn.rollback()
        return price_record_id
    except ValueError as ve: print(f"Date parsing error: {ve}"); return None
    except sqlite3.Error as e: print(f"Database error adding/updating price: {e}"); return None
    finally:
        if not conn_provided and conn: conn.close()

def get_product_prices(product_id: int, currency: str | None = None, price_type: str | None = None, db_conn=None) -> list[dict]:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        sql = "SELECT * FROM product_prices WHERE product_id = ?"
        params = [product_id]
        if currency: sql += " AND currency = ?"; params.append(currency.upper())
        if price_type: sql += " AND price_type = ?"; params.append(price_type.upper())
        sql += " ORDER BY price_type, valid_from DESC, valid_to DESC, currency"
        cursor.execute(sql, tuple(params))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e: print(f"Database error getting product prices: {e}"); return []
    finally:
        if not conn_provided and conn: conn.close()

def get_effective_price(product_id: int, target_date_str: str | None = None, currency: str = "USD", price_type: str = "SALE", db_conn=None) -> dict | None:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        target_date_obj = (datetime.strptime(target_date_str, '%Y-%m-%d').date() if isinstance(target_date_str, str) else getattr(target_date_str, 'date', lambda: target_date_str)()) if target_date_str else datetime.now().date()
        sql = """SELECT * FROM product_prices WHERE product_id = ? AND currency = ? AND price_type = ?
                 AND date(valid_from) <= date(?) AND (valid_to IS NULL OR date(valid_to) >= date(?))
                 ORDER BY date(valid_from) DESC, CASE WHEN valid_to IS NULL THEN 0 ELSE 1 END ASC, date(valid_to) DESC, id DESC LIMIT 1"""
        target_date_iso = target_date_obj.isoformat()
        cursor.execute(sql, (product_id, currency.upper(), price_type.upper(), target_date_iso, target_date_iso))
        price_record = cursor.fetchone()
        return dict(price_record) if price_record else None
    except ValueError as ve: print(f"Date parsing error in get_effective_price: {ve}"); return None
    except sqlite3.Error as e: print(f"Database error in get_effective_price: {e}"); return None
    finally:
        if not conn_provided and conn: conn.close()

def delete_product_price(price_id: int, db_conn=None) -> bool:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM product_prices WHERE id = ?", (price_id,))
        if not conn_provided: conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e: print(f"Error deleting price record {price_id}: {e}"); return False
    finally:
        if not conn_provided and conn: conn.close()

def adjust_inventory(product_id: int, location_id: int, delta_quantity: float, min_stock: float | None = None, max_stock: float | None = None, db_conn=None) -> dict | None:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        prod = get_product(product_id, db_conn=conn)
        if not prod : print(f"Error: Active product with ID {product_id} not found for inventory adjustment."); return None
        inv_rec = get_inventory_at_location(product_id, location_id, db_conn=conn)
        cur_qty, rec_id, db_min, db_max = (inv_rec['quantity'], inv_rec['id'], inv_rec['min_stock'], inv_rec['max_stock']) if inv_rec else (0, None, 0, 0)
        new_qty = cur_qty + delta_quantity
        if new_qty < 0: print(f"Error: Adjustment for product {product_id} at loc {location_id} would result in negative quantity."); return None
        final_min = min_stock if min_stock is not None else db_min
        final_max = max_stock if max_stock is not None else db_max
        if rec_id:
            cursor.execute("UPDATE product_inventory SET quantity = ?, min_stock = ?, max_stock = ? WHERE id = ?", (new_qty, final_min, final_max, rec_id))
        else:
            cursor.execute("INSERT INTO product_inventory (product_id, location_id, quantity, min_stock, max_stock) VALUES (?, ?, ?, ?, ?)", (product_id, location_id, new_qty, final_min if final_min is not None else 0, final_max if final_max is not None else 0))
            rec_id = cursor.lastrowid
        if not conn_provided: conn.commit()
        return {'id': rec_id, 'product_id': product_id, 'location_id': location_id, 'quantity': new_qty, 'min_stock': final_min, 'max_stock': final_max}
    except sqlite3.Error as e: print(f"Database error during inventory adjustment: {e}"); return None
    finally:
        if not conn_provided and conn: conn.close()

def get_inventory_at_location(product_id: int, location_id: int, db_conn=None) -> dict | None:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product_inventory WHERE product_id = ? AND location_id = ?", (product_id, location_id))
        return dict(record) if (record := cursor.fetchone()) else None
    except sqlite3.Error as e: print(f"Database error in get_inventory_at_location: {e}"); return None
    finally:
        if not conn_provided and conn: conn.close()

def get_all_inventory_for_product(product_id: int, db_conn=None) -> list[dict]:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM product_inventory WHERE product_id = ? ORDER BY location_id", (product_id,))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e: print(f"Database error in get_all_inventory_for_product: {e}"); return []
    finally:
        if not conn_provided and conn: conn.close()

def get_total_product_inventory(product_id: int, db_conn=None) -> dict:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(quantity) as total_quantity, COUNT(id) as locations_count FROM product_inventory WHERE product_id = ?", (product_id,))
        res = cursor.fetchone()
        return {'product_id': product_id, 'total_quantity': res['total_quantity'] or 0, 'locations_count': res['locations_count'] or 0}
    except sqlite3.Error as e: print(f"Database error in get_total_product_inventory: {e}"); return {'product_id': product_id, 'total_quantity': 0, 'locations_count': 0}
    finally:
        if not conn_provided and conn: conn.close()

def transfer_inventory(product_id: int, from_loc_id: int, to_loc_id: int, qty: float, db_conn=None) -> bool:
    if qty <= 0: print("Error: Qty to transfer must be positive."); return False
    if from_loc_id == to_loc_id: print("Error: Source/dest locations same."); return False
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        if not conn_provided: conn.execute("BEGIN")
        src_inv = get_inventory_at_location(product_id, from_loc_id, db_conn=conn)
        if not src_inv or src_inv['quantity'] < qty: print(f"Error: Insufficient stock at source {from_loc_id}."); return False
        adj_src_res = adjust_inventory(product_id, from_loc_id, -qty, db_conn=conn)
        if not adj_src_res: print(f"Error decrementing source inventory during transfer."); return False
        adj_dest_res = adjust_inventory(product_id, to_loc_id, qty, db_conn=conn)
        if not adj_dest_res:
            print(f"Error incrementing destination inventory. Attempting to revert source.")
            revert_src = adjust_inventory(product_id, from_loc_id, qty, db_conn=conn)
            if not revert_src: print(f"CRITICAL ERROR: Failed to revert source inventory for product {product_id} from {from_loc_id} after failed transfer to {to_loc_id}. Manual correction needed.")
            if not conn_provided: conn.rollback()
            return False
        if not conn_provided: conn.commit()
        return True
    except sqlite3.Error as e: print(f"Database error during inventory transfer: {e}"); return False
    finally:
        if not conn_provided and conn: conn.close()

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
    except sqlite3.Error as e: print(f"Database error in check_low_stock: {e}"); return []
    finally:
        if not conn_provided and conn: conn.close()

def link_product_to_vendor(data: dict, db_conn=None) -> int | None:
    required_fields = ['product_id', 'vendor_id']
    if not all(field in data for field in required_fields): print("Error: product_id and vendor_id are required."); return None
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        product_id = data['product_id']
        vendor_id = data['vendor_id']
        prod_exists = get_product(product_id, db_conn=conn)
        if not prod_exists: print(f"Error: Active product with ID {product_id} not found."); return None
        cursor.execute("SELECT id FROM product_vendors WHERE product_id = ? AND vendor_id = ?", (product_id, vendor_id))
        existing_link = cursor.fetchone()
        if existing_link:
            link_id = existing_link['id']
            current_values = dict(existing_link)
            updated_vendor_sku = data.get('vendor_sku', current_values.get('vendor_sku'))
            updated_lead_time = data.get('lead_time', current_values.get('lead_time'))
            updated_last_price = data.get('last_price', current_values.get('last_price'))
            updated_vendor_sku = data.get('vendor_sku')
            updated_lead_time = data.get('lead_time')
            updated_last_price = data.get('last_price')
            cursor.execute("""UPDATE product_vendors SET vendor_sku = ?, lead_time = ?, last_price = ? WHERE id = ?""", (updated_vendor_sku, updated_lead_time, updated_last_price, link_id))
        else:
            vendor_sku = data.get('vendor_sku')
            lead_time = data.get('lead_time')
            last_price = data.get('last_price')
            cursor.execute("INSERT INTO product_vendors (product_id, vendor_id, vendor_sku, lead_time, last_price) VALUES (?, ?, ?, ?, ?)", (product_id, vendor_id, vendor_sku, lead_time, last_price))
            link_id = cursor.lastrowid
        if not conn_provided: conn.commit()
        return link_id
    except sqlite3.Error as e: print(f"Database error linking product to vendor: {e}"); return None
    finally:
        if not conn_provided and conn: conn.close()

def update_product_vendor_link(link_id: int, data: dict, db_conn=None) -> bool:
    if not data: return False
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        set_clauses, params = [], []
        if 'vendor_sku' in data: set_clauses.append("vendor_sku = ?"); params.append(data.get('vendor_sku'))
        if 'lead_time' in data: set_clauses.append("lead_time = ?"); params.append(data.get('lead_time'))
        if 'last_price' in data: set_clauses.append("last_price = ?"); params.append(data.get('last_price'))
        if not set_clauses: return False
        params.append(link_id)
        cursor.execute(f"UPDATE product_vendors SET {', '.join(set_clauses)} WHERE id = ?", tuple(params))
        if not conn_provided: conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e: print(f"Error updating product-vendor link {link_id}: {e}"); return False
    finally:
        if not conn_provided and conn: conn.close()

def remove_product_vendor_link(link_id: int, db_conn=None) -> bool:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM product_vendors WHERE id = ?", (link_id,))
        if not conn_provided: conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e: print(f"Error removing product-vendor link {link_id}: {e}"); return False
    finally:
        if not conn_provided and conn: conn.close()

def get_vendors_for_product(product_id: int, db_conn=None) -> list[dict]:
    conn_provided = db_conn is not None
    conn = db_conn if conn_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""SELECT * FROM product_vendors WHERE product_id = ?
                          ORDER BY CASE WHEN last_price IS NULL THEN 1 ELSE 0 END ASC, last_price ASC,
                                   CASE WHEN lead_time IS NULL THEN 1 ELSE 0 END ASC, lead_time ASC, id ASC""", (product_id,))
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e: print(f"Database error in get_vendors_for_product: {e}"); return []
    finally:
        if not conn_provided and conn: conn.close()

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
    except sqlite3.Error as e: print(f"Database error in get_products_for_vendor: {e}"); return []
    finally:
        if not conn_provided and conn: conn.close()

def get_preferred_vendor(product_id: int, db_conn=None) -> dict | None:
    vendors = get_vendors_for_product(product_id, db_conn=db_conn)
    return vendors[0] if vendors else None

if __name__ == '__main__' and DB_NAME != ":memory:":
    import database_setup
    db_main_conn = get_db_connection()
    if db_main_conn.dsn == database_setup.DB_NAME: # type: ignore
        print(f"Initializing main DB: {database_setup.DB_NAME}")
        database_setup.initialize_database(db_conn=db_main_conn)
    else:
        print(f"Skipping __main__ block DB initialization for DB: {db_main_conn.dsn}") # type: ignore
    print("\n--- Testing Product CRUD ---")
    # ... (rest of __main__ block) ...
    if db_main_conn:
        db_main_conn.close()
