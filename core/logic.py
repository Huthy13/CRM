from shared.structs import Address, Account, Contact # Import Contact

class AddressBookLogic:
    def __init__(self, db_handler):
        self.db = db_handler

#Address Methods
    def add_address(self, street, city, state, zip, country):
        """Add a new address and return its ID."""
        return self.db.add_address(street, city, state, zip, country)

    def update_address(self, address_id, street, city, state, zip, country):
        """Update an existing address."""
        self.db.update_address(address_id, street, city, state, zip, country)

    def get_existing_address_by_id(self, id): # TODO: Fix this method's signature/implementation if used
        """Update an existing address."""
        # self.db.get_existing_address_by_id(street, city, zip) # Original had undefined vars
        pass # Placeholder

    def get_address_obj(self, address_id):
        data = self.db.get_address(address_id)
        if data: # Ensure data is not None
            return Address(
                address_id=address_id,
                street=data[0],
                city=data[1],
                state=data[2],
                zip_code=data[3],
                country=data[4]
            )
        return None # Or raise an error

#Account Methods
    def save_account(self, account: Account):
        """Add a new account, or update existing account if valid account ID is provided"""
        if account.account_id is None:
            # Call the specific add_account that takes an Account object
            self.db.add_account(account.name, account.phone, account.billing_address_id,
                                account.shipping_address_id, account.is_billing_same_as_shipping(),
                                account.website, account.description)
        else:
            # Call the specific update_account that takes an Account object
            self.db.update_account(account.account_id, account.name, account.phone, account.billing_address_id,
                                   account.shipping_address_id, account.is_billing_same_as_shipping(),
                                   account.website, account.description)


    def get_all_accounts(self): # This likely returns tuples, not Account objects
        """Retrieve all accounts. Consider returning list of Account objects if needed elsewhere."""
        return self.db.get_all_accounts()

    # These methods below seem redundant if save_account is used.
    # Consider refactoring or removing if save_account is the preferred interface.
    def add_account(self, account: Account): # This was specific to logic layer
        """Add a new account with all additional fields."""
        return self.db.add_account(account.name, account.phone, account.billing_address_id,
            account.shipping_address_id, account.is_billing_same_as_shipping(), account.website, account.description)

    def update_account(self, account: Account): # This was specific to logic layer
        return self.db.update_account(account.account_id, account.name, account.phone, account.billing_address_id,
            account.shipping_address_id, account.is_billing_same_as_shipping(), account.website, account.description)

    def get_account_details(self, account_id) -> Account | None:
        """Retrieve full account details, including new fields."""
        data = self.db.get_account_details(account_id) # db returns a dict
        if data:
            return Account(
                    account_id=data.get("id"), # Ensure key matches db output
                    name=data.get("name"),
                    phone=data.get("phone"),
                    billing_address_id=data.get("billing_address_id"),
                    shipping_address_id=data.get("shipping_address_id"),
                    # same_as_billing is handled by is_billing_same_as_shipping()
                    website=data.get("website"),
                    description=data.get("description")
                )
        return None

    def get_accounts(self): # This likely returns tuples (id, name)
        """Retrieve all accounts (typically for dropdowns)."""
        return self.db.get_accounts()

    def delete_account(self, account_id):
        """Delete an account and its associated contacts."""
        self.db.delete_account(account_id) # The DB handler should also handle deleting related contacts.

#Contacts Methods
    def get_contact_details(self, contact_id: int) -> Contact | None:
        """Retrieve full contact details and return a Contact object."""
        contact_data = self.db.get_contact_details(contact_id) # db returns a dict
        if contact_data:
            return Contact(
                contact_id=contact_data["id"], # Ensure key matches db output
                name=contact_data["name"],
                phone=contact_data["phone"],
                email=contact_data["email"],
                account_id=contact_data["account_id"]
            )
        return None

    def save_contact(self, contact: Contact) -> int | None :
        """Add a new contact or update an existing one. Returns Contact ID."""
        if contact.contact_id is None:
            new_contact_id = self.db.add_contact( # db.add_contact now returns id
                name=contact.name,
                phone=contact.phone,
                email=contact.email,
                account_id=contact.account_id
            )
            if new_contact_id:
                contact.contact_id = new_contact_id # Update object with new ID
            return new_contact_id
        else:
            self.db.update_contact(
                contact_id=contact.contact_id,
                name=contact.name,
                phone=contact.phone,
                email=contact.email,
                account_id=contact.account_id
            )
            return contact.contact_id

    # Note: The following add_contact and update_contact methods are now less ideal.
    # They are retained for now but save_contact should be preferred.
    # Their signatures are updated to include email to match the DB layer.
    def add_contact(self, name: str, phone: str, email: str | None, account_id: int):
        """(Deprecated: Use save_contact) Add a new contact."""
        return self.db.add_contact(name, phone, email, account_id)

    def update_contact(self, contact_id: int, name: str, phone: str, email: str | None, account_id: int):
        """(Deprecated: Use save_contact) Update an existing contact."""
        self.db.update_contact(contact_id, name, phone, email, account_id)

    def get_contacts_by_account(self, account_id: int) -> list[Contact]:
        """Retrieve contacts associated with a specific account as Contact objects."""
        contacts_data = self.db.get_contacts_by_account(account_id) # db returns list of dicts
        contact_list = []
        for row_data in contacts_data:
            contact_list.append(Contact(
                contact_id=row_data["id"], # Ensure key matches db output
                name=row_data["name"],
                phone=row_data["phone"],
                email=row_data["email"],
                account_id=row_data["account_id"]
            ))
        return contact_list

    def get_all_contacts(self) -> list[Contact]:
        """Retrieve all contacts as Contact objects."""
        contacts_data = self.db.get_all_contacts() # db returns list of dicts
        contact_list = []
        for row_data in contacts_data:
            contact_list.append(Contact(
                contact_id=row_data["id"], # Ensure key matches db output
                name=row_data["name"],
                phone=row_data["phone"],
                email=row_data["email"],
                account_id=row_data["account_id"]
            ))
        return contact_list

    def delete_contact(self, contact_id: int):
        """Delete a specific contact."""
        self.db.delete_contact(contact_id)

    def import_accounts_from_csv(self, filepath: str):
        """Import accounts from a CSV file."""
        import csv
        import logging # Import logging module
        from shared.structs import Account # Address is not directly instantiated here

        # Configure basic logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        accounts_processed = 0
        accounts_imported = 0
        accounts_skipped = 0

        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                # Verify headers
                expected_headers = ['Name', 'Phone', 'Billing Street', 'Billing City', 'Billing State', 'Billing Zip', 'Billing Country',
                                    'Shipping Street', 'Shipping City', 'Shipping State', 'Shipping Zip', 'Shipping Country', 'Website', 'Description']
                if not all(header in reader.fieldnames for header in ['Name']): # At least 'Name' must be present
                    logging.error(f"CSV file is missing essential headers (e.g., 'Name'). Found headers: {reader.fieldnames}")
                    raise ValueError("CSV file is missing essential headers (e.g., 'Name').")

                for row in reader:
                    accounts_processed += 1
                    account_name = row.get('Name')

                    if not account_name:
                        logging.warning(f"[Row {accounts_processed}] Skipping due to missing 'Name'. Data: {row}")
                        accounts_skipped += 1
                        continue

                    logging.info(f"[Row {accounts_processed}] Processing data: {row}")

                    # Extract data for billing address
                    billing_street = row.get('Billing Street')
                    billing_city = row.get('Billing City')
                    billing_state = row.get('Billing State')
                    billing_zip = row.get('Billing Zip')
                billing_country = row.get('Billing Country')

                # Create and save billing address
                billing_address_id = None
                if all([billing_street, billing_city, billing_state, billing_zip, billing_country]):
                    billing_address_id = self.add_address(
                        billing_street, billing_city, billing_state, billing_zip, billing_country
                    )

                # Extract data for shipping address
                shipping_street = row.get('Shipping Street')
                shipping_city = row.get('Shipping City')
                shipping_state = row.get('Shipping State')
                shipping_zip = row.get('Shipping Zip')
                shipping_country = row.get('Shipping Country')

                # Create and save shipping address
                shipping_address_id = None
                # Determine if shipping is same as billing
                is_billing_same = (billing_street == shipping_street and
                                   billing_city == shipping_city and
                                   billing_state == shipping_state and
                                   billing_zip == shipping_zip and
                                   billing_country == shipping_country)

                if is_billing_same:
                    shipping_address_id = billing_address_id
                elif all([shipping_street, shipping_city, shipping_state, shipping_zip, shipping_country]):
                    shipping_address_id = self.add_address(
                        shipping_street, shipping_city, shipping_state, shipping_zip, shipping_country
                    )

                # Create Account object
                account = Account(
                    name=row.get('Name'),
                    phone=row.get('Phone'),
                    billing_address_id=billing_address_id,
                    shipping_address_id=shipping_address_id,
                    # is_billing_same_as_shipping is a method, not a field to be set directly
                    website=row.get('Website'),
                    description=row.get('Description')
                )
                # Manually set same_as_billing based on comparison
                if billing_address_id and shipping_address_id and billing_address_id == shipping_address_id:
                    account.same_as_billing = True
                else:
                    account.same_as_billing = False

                logging.debug(f"[Row {accounts_processed}] Account object created: Name='{account.name}', Phone='{account.phone}', BillingsID='{account.billing_address_id}', ShippingID='{account.shipping_address_id}', Website='{account.website}'")

                try:
                    logging.debug(f"[Row {accounts_processed}] Attempting to save account: {account.name}")
                    # Save the account
                    self.save_account(account)
                    accounts_imported += 1
                    logging.info(f"[Row {accounts_processed}] Successfully imported account: {account.name}")
                except Exception as e: # Catch potential DB errors during save
                    logging.error(f"[Row {accounts_processed}] Error saving account {account.name} to database: {e}. Row data: {row}")
                    accounts_skipped += 1
            # This summary log should be outside the loop, after all rows are processed.
            logging.info(f"CSV Import Summary: Processed={accounts_processed}, Imported={accounts_imported}, Skipped={accounts_skipped}")

        except FileNotFoundError:
            logging.error(f"Error: The file '{filepath}' was not found.")
            raise # Re-raise to be caught by UI
        except csv.Error as e:
            logging.error(f"Error parsing CSV file '{filepath}': {e}")
            raise # Re-raise to be caught by UI
        except ValueError as e: # For header validation
            # Logging already done
            raise # Re-raise to be caught by UI
        except Exception as e: # Catch any other unexpected errors
            logging.error(f"An unexpected error occurred during CSV import: {e}")
            raise # Re-raise to be caught by UI

    def import_contacts_from_csv(self, filepath: str) -> tuple[int, int]:
        """Import contacts from a CSV file."""
        import csv
        import logging
        from shared.structs import Contact

        # Ensure logging is configured (it might have been by account import)
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        contacts_processed = 0
        contacts_imported = 0
        contacts_skipped = 0

        expected_headers = ['name', 'phone', 'email', 'account_id']

        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                # Verify essential headers ('name', 'phone')
                if not all(header in reader.fieldnames for header in ['name', 'phone']):
                    logging.error(
                        f"CSV file '{filepath}' is missing essential headers ('name', 'phone'). Found headers: {reader.fieldnames}"
                    )
                    raise ValueError("CSV file is missing essential headers ('name', 'phone').")

                logging.info(f"Starting CSV import for contacts from file: {filepath}")

                for row in reader:
                    contacts_processed += 1
                    contact_name = row.get('name')
                    contact_phone = row.get('phone')
                    contact_email = row.get('email') # Optional
                    account_id_str = row.get('account_id') # Optional

                    if not contact_name or not contact_phone:
                        logging.warning(
                            f"Skipping row {contacts_processed + 1} in '{filepath}' due to missing 'name' or 'phone'. Data: {row}"
                        )
                        contacts_skipped += 1
                        continue

                    contact_account_id = None
                    if account_id_str:
                        try:
                            contact_account_id = int(account_id_str)
                        except ValueError:
                            logging.warning(
                                f"Invalid account_id '{account_id_str}' for contact '{contact_name}' in row {contacts_processed + 1}. Treating as None. File: '{filepath}'"
                            )
                            # contact_account_id remains None

                    contact = Contact(
                        name=contact_name,
                        phone=contact_phone,
                        email=contact_email,
                        account_id=contact_account_id
                    )

                    try:
                        self.save_contact(contact)
                        contacts_imported += 1
                        logging.info(f"Successfully imported contact: {contact.name}")
                    except Exception as e:
                        logging.error(
                            f"Error saving contact {contact.name} to database: {e}. Row data: {row}. File: '{filepath}'"
                        )
                        contacts_skipped += 1

            logging.info(
                f"CSV Contact Import Summary for '{filepath}': Processed={contacts_processed}, Imported={contacts_imported}, Skipped={contacts_skipped}"
            )
            return contacts_imported, contacts_skipped

        except FileNotFoundError:
            logging.error(f"Error: The contact CSV file '{filepath}' was not found.")
            raise
        except csv.Error as e:
            logging.error(f"Error parsing CSV file '{filepath}': {e}")
            raise
        except ValueError as e: # For header validation
            # Logging already done by the check itself or above
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred during contact CSV import from '{filepath}': {e}")
            raise
