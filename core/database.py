import sqlite3
import os
import datetime  # Import datetime
import logging
from typing import Optional
from .database_setup import DB_NAME, initialize_database  # Import from database_setup
from shared.structs import InventoryTransactionType

logger = logging.getLogger(__name__)

# --- Custom Adapters and Converters for datetime ---
def adapt_datetime_iso(val):
    """Adapt datetime.datetime to ISO 8601 string."""
    return val.isoformat()

def adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 string."""
    return val.isoformat()

def convert_timestamp_iso(val_bytes):
    """Convert ISO 8601 string to datetime.datetime object. Handles 'Z' and milliseconds."""
    val_str = val_bytes.decode('utf-8')
    try:
        # For 'YYYY-MM-DD HH:MM:SS' format
        return datetime.datetime.strptime(val_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        # Fallback for ISO 8601 format
        if val_str.endswith('Z'):
            val_str = val_str[:-1] + '+00:00'
        # Handle up to nanoseconds, then truncate to microseconds for fromisoformat
        if '.' in val_str and len(val_str.split('.')[1].split('+')[0].split('-')[0]) > 6:
            parts = val_str.split('.')
            time_part_before_frac = parts[0]
            frac_second_and_rest = parts[1]
            frac_second = frac_second_and_rest[:6] # Keep only microseconds
            rest_of_string = frac_second_and_rest[len(frac_second_and_rest.split('+')[0].split('-')[0]):] # Get timezone if present
            val_str = f"{time_part_before_frac}.{frac_second}{rest_of_string}"

        try:
            return datetime.datetime.fromisoformat(val_str)
        except ValueError: # Fallback if not full datetime (e.g. just date)
            try:
                return datetime.datetime.combine(datetime.date.fromisoformat(val_str), datetime.time.min)
            except ValueError:
                return None # Or raise a more specific error / log

def convert_date_iso(val_bytes):
    """Convert ISO 8601 date string to datetime.date object."""
    try:
        return datetime.date.fromisoformat(val_bytes.decode('utf-8'))
    except ValueError:
        return None # Or raise


class DatabaseHandler:
    def __init__(self, db_name=None): # db_name is now optional, primarily for testing
        if db_name is None:
            # Determine the path to the database file relative to this script's location
            # core/database.py
            # core/product_management.db (target)
            base_dir = os.path.dirname(os.path.abspath(__file__)) # core/
            # To place DB_NAME in the same directory as this file (core/),
            # or one level up (project root) depending on desired location.
            # The DB_NAME from database_setup is just the filename.
            # Let's assume DB_NAME is intended to be in the `core` directory.
            # If it's meant for project root, adjust base_dir.
            # For now, assume 'core/product_management.db'
            db_path = os.path.join(base_dir, DB_NAME)
        else:
            db_path = db_name

        # Ensure the directory for the database exists, if db_path includes directories
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir) # Create directory if it doesn't exist

        # Register adapters and converters BEFORE connecting if PARSE_DECLTYPES is used,
        # or after for PARSE_COLNAMES if they are not default.
        # For safety, register them globally here.
        sqlite3.register_adapter(datetime.datetime, adapt_datetime_iso)
        sqlite3.register_adapter(datetime.date, adapt_date_iso)
        sqlite3.register_converter("timestamp", convert_timestamp_iso)
        sqlite3.register_converter("datetime", convert_timestamp_iso)
        sqlite3.register_converter("date", convert_date_iso)

        self.conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.conn.row_factory = sqlite3.Row # Access columns by name, good practice

        # Enable foreign key support. Must be done for each connection if not compiled in.
        try:
            self.conn.execute("PRAGMA foreign_keys = ON;")
        except sqlite3.Error as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error enabling PRAGMA foreign_keys: {e}")
            # Depending on SQLite version/compilation, this might not be strictly necessary
            # or might even error if the connection is already in a transaction from :memory:?cache=shared
            # For now, let's keep it but be aware.

        self.cursor = self.conn.cursor()

        # Initialize tables using the centralized setup script
        # Pass the connection to avoid re-opening or issues with in-memory DBs during tests
        initialize_database(db_conn=self.conn)

    def close(self):
        """Close the database connection."""
        self.conn.close()

    # The create_tables method is now removed from here, as table creation
    # is handled by initialize_database() from database_setup.py

#address related methods
    def add_address(self, street, city, state, zip, country):
        """Add a new address and return its ID."""
        self.cursor.execute("""
            INSERT INTO addresses (street, city, state, zip, country)
            VALUES (?, ?, ?, ?, ?)
        """, (street, city, state, zip, country))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_address(self, address_id):
        """Retrieve an address by ID."""
        self.cursor.execute("""
            SELECT street, city, state, zip, country
            FROM addresses
            WHERE address_id = ?
        """, (address_id,))
        return self.cursor.fetchone()

    def update_address(self, address_id, street, city, state, zip, country):
        """Update an existing address."""
        self.cursor.execute("""
            UPDATE addresses
            SET street = ?, city = ?, state = ?, zip = ?, country = ?
            WHERE address_id = ?
        """, (street, city, state, zip, country, address_id))
        self.conn.commit()

    def get_existing_address_by_id(self, street, city, zip):
        """Check if an address exists in the database and return its address_id if it does."""
        # print(f"data searching for in DB: {street} {city} {zip}") # Commented out print
        query = """
        SELECT address_id FROM Addresses
        WHERE street = ? AND city = ? AND zip = ?
        LIMIT 1;
        """
        self.cursor.execute(query, (street, city, zip))
        result = self.cursor.fetchone()
        return result[0] if result else None

#Contact related methods
    def get_contact_details(self, contact_id):
        """Retrieve a single contact's details by their ID."""
        logger.debug("DB.get_contact_details: received contact_id type %s value %s", type(contact_id), contact_id)
        if not isinstance(contact_id, int):
            logger.error("DB.get_contact_details: contact_id is NOT an int!")
            # raise TypeError("contact_id must be an integer") # Or handle appropriately
        self.cursor.execute("""
            SELECT id, name, phone, email, role, account_id
            FROM contacts
            WHERE id = ?
        """, (contact_id,))
        row = self.cursor.fetchone()
        if row:
            columns = [desc[0] for desc in self.cursor.description]
            return dict(zip(columns, row))
        return None

    def add_contact(self, name, phone, email, role, account_id):
        """Add a new contact including email and role."""
        self.cursor.execute("INSERT INTO contacts (name, phone, email, role, account_id) VALUES (?, ?, ?, ?, ?)",
                            (name, phone, email, role, account_id))
        self.conn.commit()
        return self.cursor.lastrowid

    def update_contact(self, contact_id, name, phone, email, role, account_id):
        """Update contact details in the database including email and role."""
        self.cursor.execute("""
            UPDATE contacts
            SET name = ?, phone = ?, email = ?, role = ?, account_id = ?
            WHERE id = ?
        """, (name, phone, email, role, account_id, contact_id))
        self.conn.commit()

    def get_contacts_by_account(self, account_id):
        """Retrieve contacts for a given account, including email and role."""
        self.cursor.execute("""
            SELECT c.id, c.name, c.phone, c.email, c.role, c.account_id,
                   a.name AS account_name
            FROM contacts AS c
            LEFT JOIN accounts AS a ON c.account_id = a.id
            WHERE c.account_id = ?
        """, (account_id,))
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_all_users(self) -> list[tuple[int, str]]:
        """Retrieve all users (user_id, username)."""
        self.cursor.execute("SELECT user_id, username FROM users ORDER BY username")
        return self.cursor.fetchall()

    def get_all_contacts(self):
        """Retrieve all contacts with full details, including email, role, and account information."""
        self.cursor.execute("""
            SELECT contacts.id, contacts.name, contacts.phone, contacts.email, contacts.role, contacts.account_id,
                   accounts.name AS account_name
            FROM contacts
            LEFT JOIN accounts ON contacts.account_id = accounts.id
        """)
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def delete_contact(self, contact_id):
        """Delete a specific contact."""
        logger.debug("DB.delete_contact: received contact_id type %s value %s", type(contact_id), contact_id)
        if not isinstance(contact_id, int):
            logger.error("DB.delete_contact: contact_id is NOT an int!")
            # raise TypeError("contact_id must be an integer")
        self.cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        self.conn.commit()

#account related methods
    def add_account_address(self, account_id, address_id, address_type, is_primary):
        """Add an address to an account."""
        self.cursor.execute("""
            INSERT INTO account_addresses (account_id, address_id, address_type, is_primary)
            VALUES (?, ?, ?, ?)
        """, (account_id, address_id, address_type, is_primary))
        self.conn.commit()

    def get_account_addresses(self, account_id):
        """Retrieve all addresses for an account."""
        self.cursor.execute("""
            SELECT a.address_id, a.street, a.city, a.state, a.zip, a.country, aa.address_type, aa.is_primary
            FROM addresses a
            JOIN account_addresses aa ON a.address_id = aa.address_id
            WHERE aa.account_id = ?
        """, (account_id,))
        return self.cursor.fetchall()

    def add_account(self, name, phone, website, description, account_type, pricing_rule_id=None, payment_term_id=None):
        """Add a new account."""
        self.cursor.execute("""
            INSERT INTO accounts (name, phone, website, description, account_type, pricing_rule_id, payment_term_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, phone, website, description, account_type, pricing_rule_id, payment_term_id))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_all_accounts(self):
        """Retrieve all accounts with details."""
        self.cursor.execute("""
            SELECT accounts.id, accounts.name, accounts.phone, accounts.description, accounts.account_type
            FROM accounts
        """)
        results = self.cursor.fetchall()
        return results

    def get_accounts(self):
        """Retrieve all accounts."""
        self.cursor.execute("SELECT id, name FROM accounts") # Potentially for dropdowns
        return self.cursor.fetchall()

    def delete_account(self, account_id):
        """Delete a account and its contacts."""
        # Consider deleting associated contacts or handling them as per application logic
        self.cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        # Add this line to delete associated contacts:
        # self.cursor.execute("DELETE FROM contacts WHERE account_id = ?", (account_id,))
        self.conn.commit()

    def get_account_details(self, account_id):
        """Retrieve full account details, including all associated addresses."""
        self.cursor.execute("""
            SELECT a.id, a.name, a.phone, a.website, a.description, a.account_type, a.pricing_rule_id, a.payment_term_id
            FROM accounts AS a
            WHERE a.id = ?
        """, (account_id,))
        result = self.cursor.fetchone()
        if result:
            account_data = dict(result)
            account_data['addresses'] = self.get_account_addresses(account_id)
            return account_data
        return None

    def update_account(self, account_id, name, phone, website, description, account_type, pricing_rule_id=None, payment_term_id=None):
        """Update an existing account."""
        self.cursor.execute("""
            UPDATE accounts
            SET name = ?, phone = ?, website = ?, description = ?, account_type = ?, pricing_rule_id = ?, payment_term_id = ?
            WHERE id = ?
        """, (name, phone, website, description, account_type, pricing_rule_id, payment_term_id, account_id))
        self.conn.commit()

# Interaction related methods
    def add_interaction(self, company_id, contact_id, interaction_type, date_time, subject, description, created_by_user_id, attachment_path):
        """Add a new interaction and return its ID."""
        if not company_id and not contact_id:
            raise ValueError("Either company_id or contact_id must be provided for an interaction.")

        self.cursor.execute("""
            INSERT INTO interactions (company_id, contact_id, interaction_type, date_time, subject, description, created_by_user_id, attachment_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (company_id, contact_id, interaction_type, date_time, subject, description, created_by_user_id, attachment_path))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_interaction(self, interaction_id):
        """Retrieve an interaction by ID."""
        self.cursor.execute("""
            SELECT interaction_id, company_id, contact_id, interaction_type, date_time, subject, description, created_by_user_id, attachment_path
            FROM interactions
            WHERE interaction_id = ?
        """, (interaction_id,))
        row = self.cursor.fetchone()
        if row:
            columns = [desc[0] for desc in self.cursor.description]
            return dict(zip(columns, row))
        return None

    def get_interactions(self, company_id=None, contact_id=None):
        """Retrieve interactions, filterable by company_id or contact_id."""
        query = """
            SELECT interaction_id, company_id, contact_id, interaction_type, date_time, subject, description, created_by_user_id, attachment_path
            FROM interactions
            WHERE 1=1
        """
        params = []
        if company_id:
            query += " AND company_id = ?"
            params.append(company_id)
        if contact_id:
            query += " AND contact_id = ?"
            params.append(contact_id)

        self.cursor.execute(query, params)
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def update_interaction(self, interaction_id, company_id, contact_id, interaction_type, date_time, subject, description, created_by_user_id, attachment_path):
        """Update an existing interaction."""
        if not company_id and not contact_id:
            raise ValueError("Either company_id or contact_id must be provided for an interaction.")

        self.cursor.execute("""
            UPDATE interactions
            SET company_id = ?, contact_id = ?, interaction_type = ?, date_time = ?, subject = ?, description = ?, created_by_user_id = ?, attachment_path = ?
            WHERE interaction_id = ?
        """, (company_id, contact_id, interaction_type, date_time, subject, description, created_by_user_id, attachment_path, interaction_id))
        self.conn.commit()

    def delete_interaction(self, interaction_id):
        """Delete an interaction by ID."""
        self.cursor.execute("DELETE FROM interactions WHERE interaction_id = ?", (interaction_id,))
        self.conn.commit()

    def get_user_id_by_username(self, username):
        """Retrieve a user's ID by their username."""
        self.cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        result = self.cursor.fetchone()
        return result[0] if result else None

# Task related methods
    def add_task(self, task_data: dict) -> int:
        """Add a new task and return its ID."""
        # Ensure created_by_user_id is present, as it's NOT NULL in DB
        if 'created_by_user_id' not in task_data or task_data['created_by_user_id'] is None:
            # This should ideally be handled by logic layer before DB call
            # or have a more robust default user fetching mechanism here.
            # For now, raising an error if it's missing.
            raise ValueError("created_by_user_id is required to create a task.")

        keys = ', '.join(task_data.keys())
        placeholders = ', '.join(['?'] * len(task_data))
        sql = f"INSERT INTO tasks ({keys}) VALUES ({placeholders})"

        self.cursor.execute(sql, list(task_data.values()))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_task(self, task_id: int) -> dict | None:
        """Retrieve a single task by its ID, excluding soft-deleted tasks."""
        self.cursor.execute("""
            SELECT task_id, company_id, contact_id, title, description, due_date,
                   status, priority, assigned_to_user_id, created_by_user_id,
                   created_at, updated_at
            FROM tasks
            WHERE task_id = ? AND is_deleted = 0
        """, (task_id,))
        row = self.cursor.fetchone()
        if row:
            columns = [desc[0] for desc in self.cursor.description]
            return dict(zip(columns, row))
        return None

    def get_tasks(self, company_id: int = None, contact_id: int = None,
                  status: str = None, due_date_sort_order: str = None,
                  assigned_user_id: int = None, priority: str = None,
                  include_deleted: bool = False) -> list[dict]:
        """Retrieve tasks with optional filters and sorting, excluding soft-deleted by default."""
        query = """
            SELECT task_id, company_id, contact_id, title, description, due_date,
                   status, priority, assigned_to_user_id, created_by_user_id,
                   created_at, updated_at
            FROM tasks
            WHERE 1=1
        """
        params = []

        if not include_deleted:
            query += " AND is_deleted = 0"

        if company_id is not None:
            query += " AND company_id = ?"
            params.append(company_id)
        if contact_id is not None:
            query += " AND contact_id = ?"
            params.append(contact_id)
        if status is not None:
            query += " AND status = ?"
            params.append(status)
        if assigned_user_id is not None:
            query += " AND assigned_to_user_id = ?"
            params.append(assigned_user_id)
        if priority is not None:
            query += " AND priority = ?"
            params.append(priority)

        if due_date_sort_order and due_date_sort_order.upper() in ['ASC', 'DESC']:
            query += f" ORDER BY due_date {due_date_sort_order.upper()}"
        else:
            query += " ORDER BY due_date ASC" # Default sort

        self.cursor.execute(query, params)
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def update_task(self, task_id: int, task_data: dict) -> None:
        """Update an existing task."""
        if not task_data:
            return # Or raise an error: Cannot update with no data

        # Ensure updated_at is always set
        if 'updated_at' not in task_data:
            # This should ideally be set by the logic layer.
            # If called directly, consider adding it here or raising error if critical.
            from datetime import datetime # Local import for safety
            task_data['updated_at'] = datetime.now().isoformat()


        set_clauses = ', '.join([f"{key} = ?" for key in task_data.keys()])
        values = list(task_data.values())
        values.append(task_id)

        sql = f"UPDATE tasks SET {set_clauses} WHERE task_id = ? AND is_deleted = 0"

        self.cursor.execute(sql, values)
        self.conn.commit()

    def delete_task(self, task_id: int, soft_delete: bool = True) -> None:
        """Delete a task. Soft delete by default."""
        if soft_delete:
            from datetime import datetime # Local import for safety
            self.cursor.execute(
                "UPDATE tasks SET is_deleted = 1, updated_at = ? WHERE task_id = ?",
                (datetime.now().isoformat(), task_id)
            )
        else:
            # Hard delete, consider implications (e.g., if task is part of audit trail)
            # For now, as per plan, this option is available.
            self.cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
        self.conn.commit()

    def update_task_status(self, task_id: int, new_status: str, updated_at_iso: str) -> None:
        """Specifically update a task's status and updated_at timestamp."""
        self.cursor.execute(
            "UPDATE tasks SET status = ?, updated_at = ? WHERE task_id = ? AND is_deleted = 0",
            (new_status, updated_at_iso, task_id)
        )
        self.conn.commit()

    def get_overdue_tasks(self, current_date_iso: str) -> list[dict]:
        """
        Retrieve tasks that are overdue (due_date < current_date)
        and not in 'Completed' or 'Overdue' status, excluding soft-deleted tasks.
        """
        query = """
            SELECT task_id, company_id, contact_id, title, description, due_date,
                   status, priority, assigned_to_user_id, created_by_user_id,
                   created_at, updated_at
            FROM tasks
            WHERE due_date < ?
              AND status NOT IN ('Completed', 'Overdue')
              AND is_deleted = 0
        """
        self.cursor.execute(query, (current_date_iso,))
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

# Product related methods

    def _manage_product_price(self, product_id: int, price_type: str, price_value: float, currency: str = 'USD', valid_from: str = None):
        """Adds or updates a specific price type for a product.
        If valid_from is None, it defaults to today."""
        from datetime import date # Local import
        if valid_from is None:
            valid_from = date.today().isoformat()

        # Check if a price of this type for this valid_from date already exists
        self.cursor.execute("""
            SELECT id FROM product_prices
            WHERE product_id = ? AND price_type = ? AND valid_from = ?
        """, (product_id, price_type, valid_from))
        existing_price = self.cursor.fetchone()

        if existing_price:
            # Update existing price record
            self.cursor.execute("""
                UPDATE product_prices
                SET price = ?, currency = ?
                WHERE id = ?
            """, (price_value, currency, existing_price['id']))
        else:
            # Insert new price record
            # Consider if old prices of the same type should be invalidated (valid_to = today)
            # For simplicity, this is not handled here yet.
            self.cursor.execute("""
                INSERT INTO product_prices (product_id, price_type, price, currency, valid_from)
                VALUES (?, ?, ?, ?, ?)
            """, (product_id, price_type, price_value, currency, valid_from))
        self.conn.commit()

    def add_product(self, sku: str, name: str, description: str, cost: float, sale_price: float,
                    is_active: bool, category_name: str = None, unit_of_measure_name: str = None,
                    quantity_on_hand: float = 0, reorder_point: float = 0,
                    reorder_quantity: float = 0, safety_stock: float = 0,
                    currency: str = 'USD', price_valid_from: str = None):
        """Add a new product and its cost and sale price."""
        # Diagnostic print moved after this line in previous step, should be fine.
        # print(f"DEBUG DB.add_product entered. SKU: {sku}, Name: {name}")

        # --- PRAGMA Diagnostic ---
        # print("\n--- DB.add_product: Products table schema BEFORE insert ---")
        # pragma_cursor = self.conn.cursor()
        # try:
        #     pragma_cursor.execute("PRAGMA table_info(products);")
        #     columns = pragma_cursor.fetchall()
        #     if columns:
        #         for col_row in columns:
        #             print(f"Col: {col_row[1]} ({col_row[2]})")
        #     else:
        #         print("PRAGMA table_info(products) returned no data.")
        # except Exception as e_pragma:
        #     print(f"Error executing PRAGMA in add_product: {e_pragma}")
        # print("--- End Products table schema in DB.add_product ---\n")
        # --- End PRAGMA ---

        category_id = self.add_product_category(category_name) if category_name else None
        unit_of_measure_id = self.add_product_unit_of_measure(unit_of_measure_name) if unit_of_measure_name else None

        # SQL for inserting into the 'products' table. This must not include 'cost' or 'sale_price' columns.
        sql_insert_product = """
            INSERT INTO products (
                sku, name, description, category_id, unit_of_measure_id,
                quantity_on_hand, reorder_point, reorder_quantity, safety_stock,
                is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params_insert_product = (
            sku, name, description, category_id, unit_of_measure_id,
            quantity_on_hand, reorder_point, reorder_quantity, safety_stock,
            is_active,
        )

        try:
            self.cursor.execute(sql_insert_product, params_insert_product)
        except sqlite3.OperationalError as e:
            # This is where the "no column named cost" error would be caught IF the SQL was wrong.
            logger.exception("Error during INSERT INTO products. SQL: %s Params: %s", sql_insert_product, params_insert_product)
            logger.debug("\n--- DB.add_product: Products table schema ON ERROR ---")
            error_pragma_cursor = self.conn.cursor()
            try:
                error_pragma_cursor.execute("PRAGMA table_info(products);")
                error_columns = error_pragma_cursor.fetchall()
                if error_columns:
                    for ecol in error_columns:
                        logger.debug("ErrCol: %s (%s)", ecol[1], ecol[2])
                else:
                    logger.debug("PRAGMA on error returned no data.")
            except Exception as ep_pragma:
                logger.exception("Error executing PRAGMA on error: %s", ep_pragma)
            logger.debug("--- End Products table schema ON ERROR ---")
            raise

        inserted_product_id = self.cursor.lastrowid
        self.conn.commit()

        if inserted_product_id:
            if cost is not None: # The 'cost' parameter passed to this method
                self._manage_product_price(inserted_product_id, 'COST', cost, currency, price_valid_from)
            if sale_price is not None:  # The 'sale_price' parameter passed to this method
                self._manage_product_price(inserted_product_id, 'SALE', sale_price, currency, price_valid_from)
        return inserted_product_id

    def get_product_details(self, product_db_id: int) -> dict | None:
        """Retrieve a product's details, including its current cost and sale price, by its DB ID."""
        self.cursor.execute("""
            SELECT p.id as product_id, p.sku, p.name, p.description, p.category_id,
                   p.unit_of_measure_id, uom.name as unit_of_measure_name,
                   p.quantity_on_hand, p.reorder_point, p.reorder_quantity, p.safety_stock,
                   p.is_active, cat.name as category_name
            FROM products p
            LEFT JOIN product_categories cat ON p.category_id = cat.id
            LEFT JOIN product_units_of_measure uom ON p.unit_of_measure_id = uom.id
            WHERE p.id = ?
        """, (product_db_id,))
        row = self.cursor.fetchone()
        if not row:
            return None

        product_dict = dict(row)

        # Fetch current COST price
        self.cursor.execute("""
            SELECT price FROM product_prices
            WHERE product_id = ? AND price_type = 'COST'
            ORDER BY valid_from DESC LIMIT 1
        """, (product_dict['product_id'],)) # Use the id from products table
        cost_row = self.cursor.fetchone()
        product_dict['cost'] = cost_row['price'] if cost_row else None

        # Fetch current SALE price
        self.cursor.execute("""
            SELECT price FROM product_prices
            WHERE product_id = ? AND price_type = 'SALE'
            ORDER BY valid_from DESC LIMIT 1
        """, (product_dict['product_id'],)) # Use the id from products table
        sale_row = self.cursor.fetchone()
        product_dict['sale_price'] = sale_row['price'] if sale_row else None

        return product_dict

    def get_all_products(self) -> list[dict]:
        """Retrieve all products with their current cost and sale price."""
        self.cursor.execute("""
            SELECT p.id as product_id, p.sku, p.name, p.description, p.category_id,
                   p.unit_of_measure_id, uom.name as unit_of_measure_name,
                   p.quantity_on_hand, p.reorder_point, p.reorder_quantity, p.safety_stock,
                   p.is_active, cat.name as category_name
            FROM products p
            LEFT JOIN product_categories cat ON p.category_id = cat.id
            LEFT JOIN product_units_of_measure uom ON p.unit_of_measure_id = uom.id
            ORDER BY p.name
        """)
        products = [dict(row) for row in self.cursor.fetchall()]

        for prod in products:
            # Fetch current COST price
            self.cursor.execute("""
                SELECT price FROM product_prices
                WHERE product_id = ? AND price_type = 'COST'
                ORDER BY valid_from DESC LIMIT 1
            """, (prod['product_id'],)) # Correctly uses the product's actual id
            cost_row = self.cursor.fetchone()
            prod['cost'] = cost_row['price'] if cost_row else None

            # Fetch current SALE price
            self.cursor.execute("""
                SELECT price FROM product_prices
                WHERE product_id = ? AND price_type = 'SALE'
                ORDER BY valid_from DESC LIMIT 1
            """, (prod['product_id'],)) # Correctly uses the product's actual id
            sale_row = self.cursor.fetchone()
            prod['sale_price'] = sale_row['price'] if sale_row else None
        return products

    def update_product(self, product_db_id: int, sku: str, name: str, description: str, cost: float, sale_price: float,
                       is_active: bool, category_name: str = None, unit_of_measure_name: str = None,
                       quantity_on_hand: float = 0, reorder_point: float = 0,
                       reorder_quantity: float = 0, safety_stock: float = 0,
                       currency: str = 'USD', price_valid_from: str = None):
        """Update product details and its cost and sale price, by its DB ID."""
        logger.debug("DB.update_product entered. ID: %s, SKU: %s", product_db_id, sku)
        # --- Add PRAGMA here ---
        logger.debug("\n--- DB.update_product: Products table schema BEFORE update ---")
        pragma_cursor = self.conn.cursor()
        try:
            pragma_cursor.execute("PRAGMA table_info(products);")
            columns = pragma_cursor.fetchall()
            if columns:
                    for col_row in columns:
                        logger.debug("Col: %s (%s)", col_row[1], col_row[2])
            else:
                logger.debug("PRAGMA table_info(products) returned no data.")
        except Exception as e_pragma:
            logger.exception("Error executing PRAGMA in update_product: %s", e_pragma)
        logger.debug("--- End Products table schema in DB.update_product ---")
        # --- End PRAGMA ---

        category_id = self.add_product_category(category_name) if category_name else None
        unit_of_measure_id = self.add_product_unit_of_measure(unit_of_measure_name) if unit_of_measure_name else None

        sql_update_product = """
            UPDATE products
            SET sku = ?, name = ?, description = ?, category_id = ?, unit_of_measure_id = ?,
                quantity_on_hand = ?, reorder_point = ?, reorder_quantity = ?, safety_stock = ?,
                is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        params_update_product = (
            sku, name, description, category_id, unit_of_measure_id,
            quantity_on_hand, reorder_point, reorder_quantity, safety_stock,
            is_active, product_db_id,
        )

        try:
            self.cursor.execute(sql_update_product, params_update_product)
        except sqlite3.OperationalError as e:
            logger.exception("Error during UPDATE products. SQL: %s Params: %s", sql_update_product, params_update_product)
            raise

        self.conn.commit() # Commit product update

        if cost is not None:
            self._manage_product_price(product_db_id, 'COST', cost, currency, price_valid_from) # Use product_db_id
        if sale_price is not None:
            self._manage_product_price(product_db_id, 'SALE', sale_price, currency, price_valid_from) # Use product_db_id


    def delete_product(self, product_db_id: int): # Renamed parameter
        """Delete a specific product by its DB ID."""
        # Also need to delete associated prices from product_prices, or use ON DELETE CASCADE
        # Assuming ON DELETE CASCADE is NOT set on product_prices.product_id FK
        self.cursor.execute("DELETE FROM product_prices WHERE product_id = ?", (product_db_id,))
        self.cursor.execute("DELETE FROM products WHERE id = ?", (product_db_id,)) # Use product_db_id
        self.conn.commit()

# --- Sales Document CRUD Methods ---
    def add_sales_document(self, doc_number: str, customer_id: int, document_type: str,
                           created_date: str, status: str, reference_number: str = None,
                           expiry_date: str = None, due_date: str = None,
                           notes: str = None, subtotal: float = 0.0, taxes: float = 0.0, total_amount: float = 0.0,
                           related_quote_id: int = None) -> int:
        """Adds a new sales document and returns its ID."""
        self.cursor.execute("""
            INSERT INTO sales_documents (document_number, customer_id, document_type, created_date, status,
                                         reference_number, expiry_date, due_date, notes, subtotal, taxes, total_amount, related_quote_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (doc_number, customer_id, document_type, created_date, status, reference_number, expiry_date, due_date,
              notes, subtotal, taxes, total_amount, related_quote_id))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_sales_document_by_id(self, doc_id: int) -> dict | None:
        """Retrieves a sales document by its ID."""
        self.cursor.execute("SELECT * FROM sales_documents WHERE id = ?", (doc_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_all_sales_documents(
        self,
        customer_id: int = None,
        document_type: str = None,
        status: str = None,
        is_active: Optional[bool] = True,
    ) -> list[dict]:
        """Retrieves sales documents with optional filters."""
        query = "SELECT * FROM sales_documents WHERE 1=1"
        params = []
        if customer_id is not None:
            query += " AND customer_id = ?"
            params.append(customer_id)
        if document_type is not None:
            query += " AND document_type = ?"
            params.append(document_type)
        if status is not None:
            query += " AND status = ?"
            params.append(status)
        if is_active is not None:
            query += " AND is_active = ?"
            params.append(1 if is_active else 0)
        query += " ORDER BY created_date DESC, id DESC"

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def update_sales_document(self, doc_id: int, updates: dict):
        """Updates a sales document. 'updates' is a dict of column:value."""
        if not updates:
            return
        # updated_at is handled by a database trigger, no need to set it here.

        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(doc_id)

        self.cursor.execute(f"UPDATE sales_documents SET {set_clause} WHERE id = ?", values)
        self.conn.commit()

    def delete_sales_document(self, doc_id: int):
        """Soft deletes a sales document by marking it inactive."""
        self.cursor.execute(
            "UPDATE sales_documents SET is_active = 0 WHERE id = ?",
            (doc_id,),
        )
        self.conn.commit()

# --- Sales Document Item CRUD Methods ---
    def add_sales_document_item(self, sales_doc_id: int, product_id: int, product_description: str,
                                quantity: float, unit_price: float, discount_percentage: float = 0.0,
                                line_total: float = None, note: str | None = None) -> int:
        """Adds a new item to a sales document."""
        # Calculate line_total if not provided
        if line_total is None:
            discount_factor = 1.0 - (discount_percentage / 100.0 if discount_percentage is not None else 0.0)
            line_total = quantity * unit_price * discount_factor

        self.cursor.execute("""
            INSERT INTO sales_document_items (sales_document_id, product_id, product_description,
                                              quantity, unit_price, discount_percentage, line_total, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (sales_doc_id, product_id, product_description, quantity, unit_price, discount_percentage, line_total, note))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_items_for_sales_document(self, sales_doc_id: int) -> list[dict]:
        """Retrieves all items for a given sales document ID."""
        self.cursor.execute("SELECT * FROM sales_document_items WHERE sales_document_id = ?", (sales_doc_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_sales_document_item_by_id(self, item_id: int) -> dict | None:
        """Retrieves a specific sales document item by its ID."""
        self.cursor.execute("SELECT * FROM sales_document_items WHERE id = ?", (item_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def update_sales_document_item(self, item_id: int, updates: dict):
        """Updates a sales document item."""
        if not updates:
            return
        # updated_at is handled by a database trigger, no need to set it here.

        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(item_id)

        self.cursor.execute(f"UPDATE sales_document_items SET {set_clause} WHERE id = ?", values)
        self.conn.commit()

    def delete_sales_document_item(self, item_id: int):
        """Deletes a specific sales document item."""
        self.cursor.execute("DELETE FROM sales_document_items WHERE id = ?", (item_id,))
        self.conn.commit()

# Category specific methods
    def add_product_category(self, name: str, parent_id: int | None = None) -> int:
        """Adds a new category to product_categories if it doesn't exist, returns the category ID."""
        if not name:
            return None # Or raise ValueError
        try:
            self.cursor.execute(
                "INSERT INTO product_categories (name, parent_id) VALUES (?, ?)",
                (name, parent_id)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError: # Handles UNIQUE constraint on name
            self.conn.rollback()
            return self.get_product_category_id_by_name(name) # Return existing ID

    def update_product_category_name(self, category_db_id: int, new_name: str): # Renamed category_id to category_db_id
        """Updates a category's name."""
        if not new_name:
            raise ValueError("New category name cannot be empty.")
        try:
            self.cursor.execute("UPDATE product_categories SET name = ? WHERE id = ?", (new_name, category_db_id)) # Use id
            self.conn.commit()
        except sqlite3.IntegrityError:
            self.conn.rollback()
            raise ValueError(f"Category name '{new_name}' already exists.")

    def update_product_category_parent(self, category_db_id: int, new_parent_id: int | None): # Renamed
        """Updates a category's parent_id."""
        if category_db_id == new_parent_id:
            raise ValueError("A category cannot be its own parent.")
        # Cycle detection should be in logic layer if more complex than self-parenting
        self.cursor.execute("UPDATE product_categories SET parent_id = ? WHERE id = ?", (new_parent_id, category_db_id)) # Use id
        self.conn.commit()

    def delete_product_category(self, category_db_id: int): # Renamed
        """Deletes a category. Products using it will have category_id set to NULL.
           Child categories will have parent_id set to NULL."""
        # FK constraints (ON DELETE SET NULL) handle relationships.
        self.cursor.execute("DELETE FROM product_categories WHERE id = ?", (category_db_id,)) # Use id
        self.conn.commit()

    def get_product_category_id_by_name(self, name: str) -> int | None:
        """Retrieves the ID of a category by its name."""
        if not name:
            return None
        self.cursor.execute("SELECT id FROM product_categories WHERE name = ?", (name,)) # Use id
        row = self.cursor.fetchone()
        return row[0] if row else None

    def get_product_category_name_by_id(self, category_db_id: int) -> str | None: # Renamed
        """Retrieves the name of a category by its ID."""
        if category_db_id is None:
            return None
        self.cursor.execute("SELECT name FROM product_categories WHERE id = ?", (category_db_id,)) # Use id
        row = self.cursor.fetchone()
        return row[0] if row else None

    def get_all_product_categories_from_table(self) -> list[tuple[int, str, int | None]]:
        """Retrieves all categories (ID, name, parent_id) from the product_categories table."""
        # Returns (id, name, parent_id). Alias 'id' to 'category_id' for consumers if needed,
        # but internal consistency uses 'id'.
        self.cursor.execute("SELECT id, name, parent_id FROM product_categories ORDER BY name")
        return self.cursor.fetchall()

# Unit of Measure specific methods
    def add_product_unit_of_measure(self, name: str) -> int | None: # Return None if name is empty
        """Adds a new unit of measure to product_units_of_measure if it doesn't exist, returns the unit ID."""
        if not name:
            return None
        try:
            self.cursor.execute("INSERT INTO product_units_of_measure (name) VALUES (?)", (name,))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError: # Unit name already exists
            self.conn.rollback()
            return self.get_product_unit_of_measure_id_by_name(name)

    def get_product_unit_of_measure_id_by_name(self, name: str) -> int | None:
        """Retrieves the ID of a unit of measure by its name."""
        if not name:
            return None
        self.cursor.execute("SELECT id FROM product_units_of_measure WHERE name = ?", (name,)) # Use id
        row = self.cursor.fetchone()
        return row[0] if row else None

    def get_product_unit_of_measure_name_by_id(self, uom_db_id: int) -> str | None: # Renamed unit_id to uom_db_id
        """Retrieves the name of a unit of measure by its ID."""
        if uom_db_id is None:
            return None
        self.cursor.execute("SELECT name FROM product_units_of_measure WHERE id = ?", (uom_db_id,)) # Use id
        row = self.cursor.fetchone()
        return row[0] if row else None

    def get_all_product_units_of_measure_from_table(self) -> list[tuple[int, str]]:
        """Retrieves all units of measure (ID, name) from the product_units_of_measure table."""
        self.cursor.execute("SELECT id, name FROM product_units_of_measure ORDER BY name") # Use id
        # The following line was a bug, fetching categories instead of UoMs and overwriting the result.
        # self.cursor.execute("SELECT category_id, name FROM product_categories ORDER BY name")
        return self.cursor.fetchall()

# --- Pricing Rule CRUD Methods ---
    def add_pricing_rule(self, rule_name: str, markup_percentage: float | None, fixed_markup: float | None) -> int:
        """Adds a new pricing rule and returns its ID."""
        self.cursor.execute("""
            INSERT INTO pricing_rules (rule_name, markup_percentage, fixed_markup)
            VALUES (?, ?, ?)
        """, (rule_name, markup_percentage, fixed_markup))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_pricing_rule(self, rule_id: int) -> dict | None:
        """Retrieves a pricing rule by its ID."""
        self.cursor.execute("SELECT * FROM pricing_rules WHERE rule_id = ?", (rule_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_all_pricing_rules(self) -> list[dict]:
        """Retrieves all pricing rules."""
        self.cursor.execute("SELECT * FROM pricing_rules ORDER BY rule_name")
        return [dict(row) for row in self.cursor.fetchall()]

    def update_pricing_rule(self, rule_id: int, rule_name: str, markup_percentage: float | None, fixed_markup: float | None):
        """Updates a pricing rule."""
        self.cursor.execute("""
            UPDATE pricing_rules
            SET rule_name = ?, markup_percentage = ?, fixed_markup = ?
            WHERE rule_id = ?
        """, (rule_name, markup_percentage, fixed_markup, rule_id))
        self.conn.commit()

    def delete_pricing_rule(self, rule_id: int):
        """Deletes a pricing rule."""
        self.cursor.execute("DELETE FROM pricing_rules WHERE rule_id = ?", (rule_id,))
        self.conn.commit()

    def assign_pricing_rule_to_customer(self, customer_id: int, rule_id: int):
        """Assigns a pricing rule to a customer."""
        self.cursor.execute("UPDATE accounts SET pricing_rule_id = ? WHERE id = ?", (rule_id, customer_id))
        self.conn.commit()

    def remove_pricing_rule_from_customer(self, customer_id: int):
        """Removes a pricing rule from a customer."""
        self.cursor.execute("UPDATE accounts SET pricing_rule_id = NULL WHERE id = ?", (customer_id,))
        self.conn.commit()

    # --- Payment Term CRUD Methods ---
    def add_payment_term(self, term_name: str, days: int | None) -> int:
        """Adds a new payment term and returns its ID."""
        self.cursor.execute(
            """
            INSERT INTO payment_terms (term_name, days)
            VALUES (?, ?)
            """,
            (term_name, days),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_payment_term(self, term_id: int) -> dict | None:
        """Retrieves a payment term by its ID."""
        self.cursor.execute("SELECT * FROM payment_terms WHERE term_id = ?", (term_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_all_payment_terms(self) -> list[dict]:
        """Retrieves all payment terms."""
        self.cursor.execute("SELECT * FROM payment_terms ORDER BY term_name")
        return [dict(row) for row in self.cursor.fetchall()]

    def update_payment_term(self, term_id: int, term_name: str, days: int | None):
        """Updates a payment term."""
        self.cursor.execute(
            """
            UPDATE payment_terms
            SET term_name = ?, days = ?
            WHERE term_id = ?
            """,
            (term_name, days, term_id),
        )
        self.conn.commit()

    def delete_payment_term(self, term_id: int):
        """Deletes a payment term."""
        self.cursor.execute("DELETE FROM payment_terms WHERE term_id = ?", (term_id,))
        self.conn.commit()

    def assign_payment_term_to_account(self, account_id: int, term_id: int):
        """Assigns a payment term to an account."""
        self.cursor.execute("UPDATE accounts SET payment_term_id = ? WHERE id = ?", (term_id, account_id))
        self.conn.commit()

    def remove_payment_term_from_account(self, account_id: int):
        """Removes a payment term from an account."""
        self.cursor.execute("UPDATE accounts SET payment_term_id = NULL WHERE id = ?", (account_id,))
        self.conn.commit()

    # Account document methods
    def add_account_document(
        self,
        account_id: int,
        document_type: str,
        file_path: str,
        uploaded_at: str | None = None,
        expires_at: str | None = None,
    ) -> int:
        """Adds a document associated with an account and returns its ID."""
        self.cursor.execute(
            """
            INSERT INTO account_documents (account_id, document_type, file_path, uploaded_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (account_id, document_type, file_path, uploaded_at, expires_at),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_account_documents(self, account_id: int) -> list[dict]:
        """Retrieves all documents linked to a given account."""
        self.cursor.execute(
            """
            SELECT document_id, account_id, document_type, file_path, uploaded_at, expires_at
            FROM account_documents
            WHERE account_id = ?
            ORDER BY uploaded_at DESC
            """,
            (account_id,),
        )
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def delete_account_document(self, document_id: int) -> None:
        """Deletes a document by its ID."""
        self.cursor.execute("DELETE FROM account_documents WHERE document_id = ?", (document_id,))
        self.conn.commit()

    def count_account_documents_by_path(self, file_path: str) -> int:
        """Return how many records reference the given file path."""
        self.cursor.execute(
            "SELECT COUNT(*) FROM account_documents WHERE file_path = ?",
            (file_path,),
        )
        row = self.cursor.fetchone()
        return row[0] if row else 0

# Purchase Document related methods
    def add_purchase_document(self, doc_number: str, vendor_id: int, created_date: str, status: str, notes: str = None) -> int:
        """Adds a new purchase document and returns its ID."""
        self.cursor.execute("""
            INSERT INTO purchase_documents (document_number, vendor_id, created_date, status, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (doc_number, vendor_id, created_date, status, notes))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_purchase_document_by_id(self, doc_id: int) -> dict | None:
        """Retrieves a purchase document by its ID."""
        self.cursor.execute("SELECT * FROM purchase_documents WHERE id = ?", (doc_id,))
        row = self.cursor.fetchone()
        if row:
            columns = [desc[0] for desc in self.cursor.description]
            return dict(zip(columns, row))
        return None

    def get_purchase_document_by_number(self, doc_number: str) -> dict | None:
        """Retrieves a purchase document by its document_number."""
        self.cursor.execute("SELECT * FROM purchase_documents WHERE document_number = ?", (doc_number,))
        row = self.cursor.fetchone()
        if row:
            columns = [desc[0] for desc in self.cursor.description]
            return dict(zip(columns, row))
        return None

    def get_all_purchase_documents(
        self,
        vendor_id: int = None,
        status: str = None,
        is_active: Optional[bool] = True,
    ) -> list[dict]:
        """Retrieves purchase documents with optional filters."""
        query = "SELECT * FROM purchase_documents WHERE 1=1"
        params = []
        if vendor_id is not None:
            query += " AND vendor_id = ?"
            params.append(vendor_id)
        if status is not None:
            query += " AND status = ?"
            params.append(status)
        if is_active is not None:
            query += " AND is_active = ?"
            params.append(1 if is_active else 0)
        query += " ORDER BY created_date DESC"  # Default sort order

        self.cursor.execute(query, params)
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def update_purchase_document_status(self, doc_id: int, new_status: str):
        """Updates the status of a purchase document."""
        self.cursor.execute("UPDATE purchase_documents SET status = ? WHERE id = ?", (new_status, doc_id))
        self.conn.commit()

    def update_purchase_document(self, doc_id: int, updates: dict):
        """Updates a purchase document. 'updates' is a dict of column:value."""
        if not updates:
            return
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(doc_id)

        self.cursor.execute(f"UPDATE purchase_documents SET {set_clause} WHERE id = ?", values)
        self.conn.commit()

    def update_purchase_document_notes(self, doc_id: int, notes: str):
        """Updates the notes of a purchase document."""
        self.cursor.execute("UPDATE purchase_documents SET notes = ? WHERE id = ?", (notes, doc_id))
        self.conn.commit()

    def delete_purchase_document(self, doc_id: int):
        """Soft deletes a purchase document by marking it inactive."""
        self.cursor.execute(
            "UPDATE purchase_documents SET is_active = 0 WHERE id = ?",
            (doc_id,),
        )
        self.conn.commit()

# Purchase Document Item related methods
    def add_purchase_document_item(self, doc_id: int, product_description: str, quantity: float, product_id: int = None, unit_price: float = None, total_price: float = None, note: str | None = None) -> int:
        """Adds a new item to a purchase document and returns its ID."""
        self.cursor.execute("""
            INSERT INTO purchase_document_items (purchase_document_id, product_description, quantity, product_id, unit_price, total_price, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (doc_id, product_description, quantity, product_id, unit_price, total_price, note))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_items_for_document(self, doc_id: int) -> list[dict]:
        """Retrieves all items for a given purchase document ID."""
        self.cursor.execute("SELECT * FROM purchase_document_items WHERE purchase_document_id = ?", (doc_id,))
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def update_purchase_document_item(self, item_id: int, product_description: str, quantity: float, product_id: int = None, unit_price: float = None, total_price: float = None, note: str | None = None):
        """Updates an existing purchase document item."""
        self.cursor.execute("""
            UPDATE purchase_document_items
            SET product_description = ?, quantity = ?, product_id = ?, unit_price = ?, total_price = ?, note = ?
            WHERE id = ?
        """, (product_description, quantity, product_id, unit_price, total_price, note, item_id))
        self.conn.commit()

    def delete_purchase_document_item(self, item_id: int):
        """Deletes a specific purchase document item."""
        self.cursor.execute("DELETE FROM purchase_document_items WHERE id = ?", (item_id,))
        self.conn.commit()

    def get_purchase_document_item_by_id(self, item_id: int) -> dict | None:
        """Retrieves a specific purchase document item by its ID."""
        self.cursor.execute("SELECT * FROM purchase_document_items WHERE id = ?", (item_id,))
        row = self.cursor.fetchone()
        if row:
            columns = [desc[0] for desc in self.cursor.description]
            return dict(zip(columns, row))
        return None

    def add_purchase_receipt(self, item_id: int, quantity: float, received_date: str | None = None) -> int:
        """Add a receipt entry for a purchase document item."""
        if received_date is None:
            received_date = datetime.datetime.now().isoformat()
        self.cursor.execute(
            """
            INSERT INTO purchase_receipts (purchase_document_item_id, quantity, received_date)
            VALUES (?, ?, ?)
            """,
            (item_id, quantity, received_date),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_total_received_for_item(self, item_id: int) -> float:
        """Return total quantity received for a given purchase document item."""
        self.cursor.execute(
            "SELECT COALESCE(SUM(quantity), 0) FROM purchase_receipts WHERE purchase_document_item_id = ?",
            (item_id,),
        )
        result = self.cursor.fetchone()
        return result[0] if result else 0.0

    def mark_purchase_item_received(self, item_id: int):
        """Mark a purchase document item as fully received."""
        self.cursor.execute(
            "UPDATE purchase_document_items SET is_received = 1 WHERE id = ?",
            (item_id,),
        )
        self.conn.commit()

    def are_all_items_received(self, doc_id: int) -> bool:
        """Check if all items for a purchase document are fully received."""
        self.cursor.execute(
            "SELECT COUNT(*) FROM purchase_document_items WHERE purchase_document_id = ? AND is_received = 0",
            (doc_id,),
        )
        return self.cursor.fetchone()[0] == 0

    def are_all_items_shipped(self, doc_id: int) -> bool:
        """Check if all items for a sales document are fully shipped."""
        self.cursor.execute(
            "SELECT COUNT(*) FROM sales_document_items WHERE sales_document_id = ? AND is_shipped = 0",
            (doc_id,),
        )
        return self.cursor.fetchone()[0] == 0

    def get_shipments_for_sales_document(self, sales_doc_id: int) -> list[dict]:
        """Retrieve shipment entries and their items for a sales document."""
        self.cursor.execute(
            "SELECT document_number FROM sales_documents WHERE id = ?",
            (sales_doc_id,),
        )
        row = self.cursor.fetchone()
        if not row:
            return []
        doc_number = row["document_number"]
        pattern = f"{doc_number}.%"
        self.cursor.execute(
            """
            SELECT it.reference AS shipment_number,
                   it.created_at,
                   sdi.id AS item_id,
                   sdi.product_description,
                   -it.quantity_change AS quantity
            FROM inventory_transactions it
            JOIN sales_document_items sdi
              ON sdi.product_id = it.product_id AND sdi.sales_document_id = ?
            WHERE it.transaction_type = ? AND it.reference LIKE ?
            ORDER BY it.reference, it.id
            """,
            (sales_doc_id, InventoryTransactionType.SALE.value, pattern),
        )
        return [dict(r) for r in self.cursor.fetchall()]

    def get_shipment_references_for_sales_document(self, sales_doc_id: int) -> list[str]:
        """Return existing shipment reference numbers for a sales document."""
        self.cursor.execute(
            "SELECT document_number FROM sales_documents WHERE id = ?",
            (sales_doc_id,),
        )
        row = self.cursor.fetchone()
        if not row:
            return []
        doc_number = row["document_number"]
        pattern = f"{doc_number}.%"
        self.cursor.execute(
            "SELECT DISTINCT reference FROM inventory_transactions WHERE reference LIKE ?",
            (pattern,),
        )
        return [r["reference"] for r in self.cursor.fetchall()]

    # delete_items_for_document is not strictly needed if ON DELETE CASCADE is reliable,
    # but can be implemented for explicit control if desired.
    # def delete_items_for_document(self, doc_id: int):
    #     """Deletes all items for a given purchase document ID."""
    #     self.cursor.execute("DELETE FROM purchase_document_items WHERE purchase_document_id = ?", (doc_id,))
    #     self.conn.commit()

# --- Inventory management methods ---
    def log_inventory_transaction(self, product_id: int, quantity_change: float,
                                  transaction_type: str, reference: str = None) -> int:
        """Log an inventory transaction and update product stock."""
        self.cursor.execute(
            """
            INSERT INTO inventory_transactions (product_id, quantity_change, transaction_type, reference)
            VALUES (?, ?, ?, ?)
            """,
            (product_id, quantity_change, transaction_type, reference),
        )
        if transaction_type != InventoryTransactionType.PURCHASE_ORDER.value:
            self.cursor.execute(
                "UPDATE products SET quantity_on_hand = quantity_on_hand + ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (quantity_change, product_id),
            )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_inventory_transactions(self, product_id: int = None) -> list[dict]:
        """Retrieve inventory transactions, optionally filtered by product."""
        query = "SELECT * FROM inventory_transactions"
        params: list = []
        if product_id is not None:
            query += " WHERE product_id = ?"
            params.append(product_id)
        query += " ORDER BY created_at DESC"
        self.cursor.execute(query, params)
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_stock_level(self, product_id: int) -> float:
        """Return current on-hand quantity for a product."""
        self.cursor.execute("SELECT quantity_on_hand FROM products WHERE id = ?", (product_id,))
        row = self.cursor.fetchone()
        return row["quantity_on_hand"] if row else 0.0

    def get_on_order_quantity(self, product_id: int) -> float:
        """Return quantity currently on order for a product."""
        self.cursor.execute(
            "SELECT COALESCE(SUM(quantity_change), 0) AS qty FROM inventory_transactions WHERE product_id = ? AND transaction_type = ?",
            (product_id, InventoryTransactionType.PURCHASE_ORDER.value),
        )
        row = self.cursor.fetchone()
        return row[0] if row else 0.0

    def get_all_on_order_quantities(self) -> list[dict]:
        """Return on-order quantities grouped by product."""
        self.cursor.execute(
            """
            SELECT product_id, SUM(quantity_change) AS qty
            FROM inventory_transactions
            WHERE transaction_type = ?
            GROUP BY product_id
            HAVING qty > 0
            """,
            (InventoryTransactionType.PURCHASE_ORDER.value,),
        )
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def add_replenishment_item(self, product_id: int, quantity_needed: float) -> int:
        """Queue a product for replenishment."""
        self.cursor.execute(
            "INSERT INTO replenishment_queue (product_id, quantity_needed) VALUES (?, ?)",
            (product_id, quantity_needed),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_replenishment_queue(self) -> list[dict]:
        """Fetch all pending replenishment items."""
        self.cursor.execute("SELECT * FROM replenishment_queue ORDER BY created_at")
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def remove_replenishment_item(self, item_id: int) -> None:
        """Delete a replenishment queue entry."""
        self.cursor.execute("DELETE FROM replenishment_queue WHERE id = ?", (item_id,))
        self.conn.commit()

    def get_default_vendor_for_product(self, product_id: int) -> int | None:
        """Return the default vendor ID for a product, if one exists."""
        self.cursor.execute(
            "SELECT vendor_id FROM product_vendors WHERE product_id = ? ORDER BY id LIMIT 1",
            (product_id,),
        )
        row = self.cursor.fetchone()
        return row["vendor_id"] if row else None

# Purchase order related methods
    def add_purchase_order(self, vendor_id: int, order_date: str, status: str,
                           expected_date: str = None) -> int:
        """Create a purchase order and return its ID."""
        self.cursor.execute(
            """
            INSERT INTO purchase_orders (vendor_id, order_date, status, expected_date)
            VALUES (?, ?, ?, ?)
            """,
            (vendor_id, order_date, status, expected_date),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_purchase_order_by_id(self, order_id: int) -> dict | None:
        """Retrieve a purchase order by ID."""
        self.cursor.execute("SELECT * FROM purchase_orders WHERE id = ?", (order_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_all_purchase_orders(self, status: str = None) -> list[dict]:
        """Retrieve purchase orders, optionally filtered by status."""
        query = "SELECT * FROM purchase_orders"
        params: list = []
        if status is not None:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY order_date DESC"
        self.cursor.execute(query, params)
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def update_purchase_order_status(self, order_id: int, new_status: str) -> None:
        """Update status for a purchase order."""
        self.cursor.execute(
            "UPDATE purchase_orders SET status = ? WHERE id = ?",
            (new_status, order_id),
        )
        self.conn.commit()

    def delete_purchase_order(self, order_id: int) -> None:
        """Delete a purchase order and associated line items."""
        self.cursor.execute("DELETE FROM purchase_orders WHERE id = ?", (order_id,))
        self.conn.commit()

    def add_purchase_order_line_item(self, purchase_order_id: int, product_id: int,
                                     quantity: float, unit_cost: float = None) -> int:
        """Add a line item to a purchase order."""
        self.cursor.execute(
            """
            INSERT INTO purchase_order_line_items (purchase_order_id, product_id, quantity, unit_cost)
            VALUES (?, ?, ?, ?)
            """,
            (purchase_order_id, product_id, quantity, unit_cost),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_purchase_order_line_items(self, purchase_order_id: int) -> list[dict]:
        """Retrieve line items for a purchase order."""
        self.cursor.execute(
            "SELECT * FROM purchase_order_line_items WHERE purchase_order_id = ?",
            (purchase_order_id,),
        )
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def delete_purchase_order_line_item(self, item_id: int) -> None:
        """Delete a purchase order line item."""
        self.cursor.execute(
            "DELETE FROM purchase_order_line_items WHERE id = ?",
            (item_id,),
        )
        self.conn.commit()

# Company Information related methods
    def add_company_address(self, company_id, address_id, address_type, is_primary):
        """Add an address to a company."""
        self.cursor.execute("""
            INSERT INTO company_addresses (company_id, address_id, address_type, is_primary)
            VALUES (?, ?, ?, ?)
        """, (company_id, address_id, address_type, is_primary))
        self.conn.commit()

    def get_company_addresses(self, company_id):
        """Retrieve all addresses for a company."""
        self.cursor.execute("""
            SELECT a.address_id, a.street, a.city, a.state, a.zip, a.country, ca.address_type, ca.is_primary
            FROM addresses a
            JOIN company_addresses ca ON a.address_id = ca.address_id
            WHERE ca.company_id = ?
        """, (company_id,))
        return self.cursor.fetchall()

    def get_company_information(self) -> dict | None:
        """Retrieve the company information. Assumes a single entry."""
        self.cursor.execute("""
            SELECT ci.company_id, ci.name, ci.phone
            FROM company_information AS ci
            LIMIT 1
        """) # Ensure only one row is fetched, typically the first one if multiple exist.
        row = self.cursor.fetchone()
        if row:
            company_data = dict(row)
            company_data['addresses'] = self.get_company_addresses(company_data['company_id'])
            return company_data
        return None

    def update_company_information(self, company_id: int, name: str, phone: str):
        """Update the company information."""
        self.cursor.execute("""
            UPDATE company_information
            SET name = ?, phone = ?
            WHERE company_id = ?
        """, (name, phone, company_id))
        self.conn.commit()

    def add_company_information(self, name: str, phone: str) -> int:
        """Add company information. Primarily for initial setup if needed, or if table could be empty."""
        self.cursor.execute("""
            INSERT INTO company_information (name, phone)
            VALUES (?, ?)
        """, (name, phone))
        self.conn.commit()
        return self.cursor.lastrowid
