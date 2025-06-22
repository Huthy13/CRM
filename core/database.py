import sqlite3
import os # Make sure os is imported

class DatabaseHandler:
    def __init__(self, db_name=None): # db_name is now optional
        if db_name is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, "address_book.db")
        else:
            # This else branch allows using a different DB path if explicitly provided,
            # which can be useful for testing or other configurations.
            # However, for the main app, src/main.py will call DatabaseHandler()
            # without args, using the new default path.
            db_path = db_name

        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;") # Enable foreign key support
        self.cursor = self.conn.cursor()
        self.create_tables()

    def close(self):
        """Close the database connection."""
        self.conn.close()

    def create_tables(self):
        """Create the necessary tables if they don't exist."""

        # Addresses table for storing individual addresses
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS addresses (
                address_id INTEGER PRIMARY KEY AUTOINCREMENT,
                street TEXT NOT NULL,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                zip TEXT NOT NULL,
                country TEXT NOT NULL
            )
        """)

        # Accounts table with references to billing and shipping addresses
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                billing_address_id INTEGER,
                shipping_address_id INTEGER,
                same_as_billing BOOLEAN DEFAULT 0,
                website TEXT,
                description TEXT,
                FOREIGN KEY (billing_address_id) REFERENCES addresses (address_id),
                FOREIGN KEY (shipping_address_id) REFERENCES addresses (address_id)
            )
        """)

        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                role TEXT,
                account_id INTEGER,
                FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE SET NULL
            )"""
        )

        # Users table (simplified for now)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL
            )
        """)
        # Pre-populate a default user if the table is empty (for created_by_user_id)
        self.cursor.execute("SELECT COUNT(*) FROM users")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("INSERT INTO users (username) VALUES (?)", ('system_user',))


        # Interactions table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER,
                contact_id INTEGER,
                interaction_type TEXT CHECK(interaction_type IN ('Call', 'Email', 'Meeting', 'Visit', 'Other')) NOT NULL,
                date_time TEXT NOT NULL, -- Storing as ISO8601 string
                subject TEXT(150) NOT NULL,
                description TEXT,
                created_by_user_id INTEGER,
                attachment_path TEXT,
                FOREIGN KEY (company_id) REFERENCES accounts (id) ON DELETE SET NULL,
                FOREIGN KEY (contact_id) REFERENCES contacts (id) ON DELETE SET NULL,
                FOREIGN KEY (created_by_user_id) REFERENCES users (user_id) ON DELETE SET NULL
            )
        """)

        # Tasks table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER,
                contact_id INTEGER,
                title VARCHAR(150) NOT NULL,
                description TEXT,
                due_date TEXT NOT NULL, -- Storing as ISO8601 string (DATE or DATETIME)
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
                FOREIGN KEY (created_by_user_id) REFERENCES users (user_id) ON DELETE CASCADE -- Or SET NULL if preferred
            )
        """)
        self.conn.commit()

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
        self.cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        self.conn.commit()

#account related methods
    def add_account(self, name, phone, billing_address_id, shipping_address_id, same_as_billing, website, description):
        """Add a new account with billing and shipping address IDs."""
        self.cursor.execute("""
            INSERT INTO accounts (name, phone, billing_address_id, shipping_address_id, same_as_billing, website, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, phone, billing_address_id, shipping_address_id, same_as_billing, website, description))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_all_accounts(self):
        """Retrieve all accounts with details."""
        self.cursor.execute("""
            SELECT accounts.id, accounts.name, accounts.phone, accounts.description
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
        """Retrieve full account details, including both billing and shipping addresses."""
        self.cursor.execute("""
            SELECT a.id, a.name, a.phone, a.website, a.description,
                   a.billing_address_id, a.shipping_address_id, a.same_as_billing,
                   b.street AS billing_street, b.city AS billing_city, b.state AS billing_state,
                   b.zip AS billing_zip, b.country AS billing_country,
                   s.street AS shipping_street, s.city AS shipping_city, s.state AS shipping_state,
                   s.zip AS shipping_zip, s.country AS shipping_country
            FROM accounts AS a
            LEFT JOIN addresses AS b ON a.billing_address_id = b.address_id
            LEFT JOIN addresses AS s ON a.shipping_address_id = s.address_id
            WHERE a.id = ?
        """, (account_id,))
        result = self.cursor.fetchone()
        if result:
            columns = [desc[0] for desc in self.cursor.description]
            return dict(zip(columns, result))
        return None

    def update_account(self, account_id, name, phone, billing_address_id, shipping_address_id, same_as_billing, website, description):
        """Update an existing account."""
        self.cursor.execute("""
            UPDATE accounts
            SET name = ?, phone = ?, billing_address_id = ?, shipping_address_id = ?, same_as_billing = ?, website = ?, description = ?
            WHERE id = ?
        """, (name, phone, billing_address_id, shipping_address_id, same_as_billing, website, description, account_id))
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
