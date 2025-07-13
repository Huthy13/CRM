import sqlite3
from datetime import datetime

DB_NAME = "product_management.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def create_tables(db_conn=None):
    """
    Creates all necessary tables in the database if they don't already exist.
    Accepts an optional database connection. If provided, uses it; otherwise, creates a new one.
    The provided connection is NOT closed by this function. Connections created internally are closed.
    """
    conn_was_provided = db_conn is not None
    conn = db_conn if conn_was_provided else get_db_connection()

    try:
        cursor = conn.cursor()

        # Products Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            category_id INTEGER,
            unit_of_measure_id INTEGER, -- Changed from unit_of_measure TEXT
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES product_categories(id),
            FOREIGN KEY (unit_of_measure_id) REFERENCES product_units_of_measure(id) -- Added FK
        )
        """)

        # Addresses table (must be defined before tables that reference it like accounts, company_information)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS addresses (
            address_id INTEGER PRIMARY KEY AUTOINCREMENT,
            street TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            zip TEXT NOT NULL,
            country TEXT NOT NULL
        )
        """)
        # No specific trigger for addresses in original, can add if needed.

        # Product Units of Measure Table (NEW)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_units_of_measure (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
        """)
        # Trigger for product_units_of_measure (Optional, if needed for auditing)
        # cursor.execute("""
        # CREATE TRIGGER IF NOT EXISTS update_product_units_of_measure_updated_at
        # AFTER UPDATE ON product_units_of_measure
        # FOR EACH ROW
        # BEGIN
        #     UPDATE product_units_of_measure SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        # END;
        # """)


        # Accounts Table (Referenced by SalesDocuments and potentially others)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, -- Removed UNIQUE to match old DB handler schema; can be re-added if logic supports it
            account_type TEXT NOT NULL, -- 'Customer', 'Vendor', 'Contact' (from AccountType enum)
            phone TEXT, -- Made phone not null in old DB handler, but setup allows null. Keeping as is for now.
            email TEXT, -- Removed UNIQUE from email for now, matches old DB handler
            website TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Added
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Added
        )
        """)
        # Account Addresses Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_addresses (
            account_id INTEGER NOT NULL,
            address_id INTEGER NOT NULL,
            address_type TEXT NOT NULL,
            is_primary BOOLEAN DEFAULT 0,
            FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE,
            FOREIGN KEY (address_id) REFERENCES addresses (address_id) ON DELETE CASCADE,
            PRIMARY KEY (account_id, address_id, address_type)
        )
        """)

        # Trigger for accounts updated_at
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_accounts_updated_at
        AFTER UPDATE ON accounts
        FOR EACH ROW
        BEGIN
            UPDATE accounts SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
        """)

        # Contacts Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT, -- Original was NOT NULL, but some tests might pass None if not careful
            email TEXT,
            role TEXT,
            account_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Added
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Added
            FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE SET NULL
        )
        """)
        # Trigger for contacts updated_at
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_contacts_updated_at
        AFTER UPDATE ON contacts
        FOR EACH ROW
        BEGIN
            UPDATE contacts SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
        """)

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
                -- created_at, updated_at could be added if user management becomes more complex
            )
        """)
        # No specific trigger for users in original, can add if needed for updated_at.

        # Interactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER, -- Renamed from account_id in some contexts to company_id
                contact_id INTEGER,
                interaction_type TEXT CHECK(interaction_type IN ('Call', 'Email', 'Meeting', 'Visit', 'Other')) NOT NULL,
                date_time TEXT NOT NULL, -- ISO8601 string
                subject TEXT(150) NOT NULL,
                description TEXT,
                created_by_user_id INTEGER,
                attachment_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Added
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Added
                FOREIGN KEY (company_id) REFERENCES accounts (id) ON DELETE SET NULL,
                FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE SET NULL,
                FOREIGN KEY (created_by_user_id) REFERENCES users (user_id) ON DELETE SET NULL
            )
        """)
        # Trigger for interactions updated_at
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_interactions_updated_at
        AFTER UPDATE ON interactions
        FOR EACH ROW
        BEGIN
            UPDATE interactions SET updated_at = CURRENT_TIMESTAMP WHERE interaction_id = OLD.interaction_id;
        END;
        """)

        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER,
                contact_id INTEGER,
                title VARCHAR(150) NOT NULL,
                description TEXT,
                due_date TEXT NOT NULL, -- ISO8601 string (DATE or DATETIME)
                status TEXT NOT NULL, -- Enum: Open, In Progress, Completed, Overdue
                priority TEXT, -- Enum: Low, Medium, High
                assigned_to_user_id INTEGER,
                created_by_user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL, -- Storing as ISO8601 string
                updated_at TEXT NOT NULL, -- Storing as ISO8601 string
                is_deleted INTEGER DEFAULT 0, -- For soft delete
                FOREIGN KEY (company_id) REFERENCES accounts (id) ON DELETE SET NULL,
                FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE SET NULL,
                FOREIGN KEY (assigned_to_user_id) REFERENCES users (user_id) ON DELETE SET NULL,
                FOREIGN KEY (created_by_user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        """)
        # Trigger for tasks updated_at (already has an updated_at column managed by logic)
        # No separate trigger for updated_at here if logic explicitly sets it.
        # However, a trigger is more robust if direct DB updates might occur.
        # The existing schema from database.py had created_at/updated_at TEXT.
        # Let's add a trigger for consistency with other tables.
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_tasks_updated_at
        AFTER UPDATE ON tasks
        FOR EACH ROW
        WHEN OLD.updated_at = NEW.updated_at -- Only if logic didn't already update it
        BEGIN
            UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE task_id = OLD.task_id;
        END;
        """)


        # Product Categories Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER,
            description TEXT,
            FOREIGN KEY (parent_id) REFERENCES product_categories(id)
        )
        """)

        # Product Prices Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            price_type TEXT NOT NULL DEFAULT 'SALE', -- Added: e.g., 'COST', 'SALE', 'MSRP'
            price DECIMAL(10, 2) NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            valid_from DATE NOT NULL,
            valid_to DATE,
            FOREIGN KEY (product_id) REFERENCES products(id),
            UNIQUE (product_id, price_type, valid_from) -- Ensure unique price per type for a given start date
        )
        """)

        # Product Inventory Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            location_id INTEGER NOT NULL,
            quantity DECIMAL(10, 2) NOT NULL DEFAULT 0,
            min_stock DECIMAL(10, 2) DEFAULT 0,
            max_stock DECIMAL(10, 2) DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
        """)
        cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_product_location ON product_inventory (product_id, location_id);
        """)

        # Product Vendors Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            vendor_id INTEGER NOT NULL,
            vendor_sku TEXT,
            lead_time INTEGER,
            last_price DECIMAL(10, 2),
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (vendor_id) REFERENCES accounts(id), -- Corrected FK
            UNIQUE (product_id, vendor_id)
        )
        """)

        # Triggers to update `updated_at` timestamp on products table
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_products_updated_at
        AFTER UPDATE ON products
        FOR EACH ROW
        BEGIN
            UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
        """)

        # Sales Documents Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_number TEXT UNIQUE NOT NULL,
            customer_id INTEGER NOT NULL, -- Changed from vendor_id
            document_type TEXT NOT NULL, -- e.g., 'QUOTE', 'INVOICE'
            created_date TEXT NOT NULL, -- ISO format string
            expiry_date TEXT, -- For Quotes, ISO format string
            due_date TEXT, -- For Invoices, ISO format string
            status TEXT NOT NULL, -- From SalesDocumentStatus enum
            notes TEXT,
            subtotal REAL DEFAULT 0.0,
            taxes REAL DEFAULT 0.0,
            total_amount REAL DEFAULT 0.0,
            related_quote_id INTEGER, -- Link invoice to quote
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES accounts(id), -- Assuming an 'accounts' table
            FOREIGN KEY (related_quote_id) REFERENCES sales_documents(id)
        )
        """)

        # Sales Document Items Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_document_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sales_document_id INTEGER NOT NULL,
            product_id INTEGER,
            product_description TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL, -- Sale price
            discount_percentage REAL DEFAULT 0.0,
            line_total REAL NOT NULL, -- Calculated: quantity * unit_price * (1 - discount_percentage/100)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sales_document_id) REFERENCES sales_documents(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
        """)

        # Triggers for sales_documents updated_at
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_sales_documents_updated_at
        AFTER UPDATE ON sales_documents
        FOR EACH ROW
        BEGIN
            UPDATE sales_documents SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
        """)

        # Purchase Documents Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_number TEXT UNIQUE NOT NULL,
            vendor_id INTEGER NOT NULL,
            created_date TEXT NOT NULL, -- ISO format string
            status TEXT NOT NULL, -- From PurchaseDocumentStatus enum
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (vendor_id) REFERENCES accounts(id)
        )
        """)

        # Purchase Document Items Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_document_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_document_id INTEGER NOT NULL,
            product_id INTEGER,
            product_description TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL, -- Can be null for RFQ items initially
            total_price REAL, -- Calculated: quantity * unit_price
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (purchase_document_id) REFERENCES purchase_documents(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
        """)

        # Triggers for purchase_documents updated_at
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_purchase_documents_updated_at
        AFTER UPDATE ON purchase_documents
        FOR EACH ROW
        BEGIN
            UPDATE purchase_documents SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
        """)

        # Triggers for purchase_document_items updated_at
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_purchase_document_items_updated_at
        AFTER UPDATE ON purchase_document_items
        FOR EACH ROW
        BEGIN
            UPDATE purchase_document_items SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
        """)

        # Company Information table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_information (
                company_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                billing_address_id INTEGER,
                shipping_address_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Added
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Added
                FOREIGN KEY (billing_address_id) REFERENCES addresses (address_id) ON DELETE SET NULL,
                FOREIGN KEY (shipping_address_id) REFERENCES addresses (address_id) ON DELETE SET NULL
            )
        """)
        # Company Addresses Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_addresses (
            company_id INTEGER NOT NULL,
            address_id INTEGER NOT NULL,
            address_type TEXT NOT NULL,
            is_primary BOOLEAN DEFAULT 0,
            FOREIGN KEY (company_id) REFERENCES company_information (company_id) ON DELETE CASCADE,
            FOREIGN KEY (address_id) REFERENCES addresses (address_id) ON DELETE CASCADE,
            PRIMARY KEY (company_id, address_id, address_type)
        )
        """)

        # Trigger for company_information updated_at
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_company_information_updated_at
        AFTER UPDATE ON company_information
        FOR EACH ROW
        BEGIN
            UPDATE company_information SET updated_at = CURRENT_TIMESTAMP WHERE company_id = OLD.company_id;
        END;
        """)
        # Pre-populate company_information if empty (as done in old DatabaseHandler)
        # This should be done after the table is created.
        # It's better if this is handled by application logic or a separate seeding script,
        # but for consistency with old behavior, can add it here.
        # However, DatabaseHandler.__init__ already calls initialize_database, then DatabaseHandler
        # methods are called by tests. The logic to add default company info is in DatabaseHandler
        # or CompanyInfoTab. So, no need to add default data here in create_tables.

        # Triggers for sales_document_items updated_at
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS update_sales_document_items_updated_at
        AFTER UPDATE ON sales_document_items
        FOR EACH ROW
        BEGIN
            UPDATE sales_document_items SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END;
        """)

        conn.commit() # Commit changes
        print("Database tables created successfully (if they didn't exist).")

    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")
        # If an external connection was provided, do not rollback here; let the caller manage.
        # If an internal connection, a rollback might be considered, but typically
        # CREATE TABLE IF NOT EXISTS failures are due to syntax or DB lock, not data issues needing rollback.
        raise # Re-raise to ensure test setup failure is clear
    finally:
        if not conn_was_provided and conn:
            conn.close()

def initialize_database(db_conn=None):
    """
    Initializes the database by creating the tables and seeding essential data.
    Accepts an optional database connection to pass to create_tables.
    """
    print(f"Initializing database '{DB_NAME if not db_conn else "provided connection"}'...")
    create_tables(db_conn=db_conn)

    # Seed essential data
    conn_was_provided = db_conn is not None
    conn = db_conn if conn_was_provided else get_db_connection()
    try:
        cursor = conn.cursor()
        # Ensure system_user exists
        cursor.execute("INSERT OR IGNORE INTO users (username) VALUES ('system_user')")
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error seeding initial data: {e}")
    finally:
        if not conn_was_provided and conn:
            conn.close()


if __name__ == "__main__":
    initialize_database()
    # Example of how to connect and potentially add some initial data or test
    # conn = get_db_connection()
    # # Example: Add a root category if it doesn't exist
    # try:
    #     conn.execute("INSERT INTO product_categories (name, description) VALUES (?, ?)",
    #                  ('All Products', 'Root category for all products'))
    #     conn.commit()
    #     print("Added 'All Products' root category.")
    # except sqlite3.IntegrityError:
    #     print("'All Products' category likely already exists.")
    # conn.close()
