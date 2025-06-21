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
                role=contact_data.get("role", ""), # Add role, with default
                account_id=contact_data["account_id"]
            )
        return None

    def save_contact(self, contact: Contact) -> int | None :
        """Add a new contact or update an existing one. Returns Contact ID."""
        if contact.contact_id is None:
            # Call db.add_contact with all required arguments, including role
            new_contact_id = self.db.add_contact(
                name=contact.name,
                phone=contact.phone,
                email=contact.email,
                role=contact.role,  # Pass the role attribute
                account_id=contact.account_id
            )
            if new_contact_id:
                contact.contact_id = new_contact_id # Update object with new ID
            return new_contact_id
        else:
            # Call db.update_contact with all required arguments, including role
            self.db.update_contact(
                contact_id=contact.contact_id,
                name=contact.name,
                phone=contact.phone,
                email=contact.email,
                role=contact.role,  # Pass the role attribute
                account_id=contact.account_id
            )
            return contact.contact_id

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
                role=row_data.get("role", ""), # Add role
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
                role=row_data.get("role", ""), # Add role
                account_id=row_data["account_id"]
            ))
        return contact_list

    def delete_contact(self, contact_id: int):
        """Delete a specific contact."""
        self.db.delete_contact(contact_id)
