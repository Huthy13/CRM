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
                account_id INTEGER,
                FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE SET NULL
            )"""
        )
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
            SELECT id, name, phone, email, account_id
            FROM contacts
            WHERE id = ?
        """, (contact_id,))
        row = self.cursor.fetchone()
        if row:
            columns = [desc[0] for desc in self.cursor.description]
            return dict(zip(columns, row))
        return None

    def add_contact(self, name, phone, email, account_id):
        """Add a new contact including email."""
        self.cursor.execute("INSERT INTO contacts (name, phone, email, account_id) VALUES (?, ?, ?, ?)",
                            (name, phone, email, account_id))
        self.conn.commit()
        return self.cursor.lastrowid

    def update_contact(self, contact_id, name, phone, email, account_id):
        """Update contact details in the database including email."""
        self.cursor.execute("""
            UPDATE contacts
            SET name = ?, phone = ?, email = ?, account_id = ?
            WHERE id = ?
        """, (name, phone, email, account_id, contact_id))
        self.conn.commit()

    def get_contacts_by_account(self, account_id):
        """Retrieve contacts for a given account, including email."""
        self.cursor.execute("""
            SELECT c.id, c.name, c.phone, c.email, c.account_id,
                   a.name AS account_name
            FROM contacts AS c
            LEFT JOIN accounts AS a ON c.account_id = a.id
            WHERE c.account_id = ?
        """, (account_id,))
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

    def get_all_contacts(self):
        """Retrieve all contacts with full details, including email and account information."""
        self.cursor.execute("""
            SELECT contacts.id, contacts.name, contacts.phone, contacts.email, contacts.account_id,
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
