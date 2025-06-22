from shared.structs import Address, Account, Contact # Import Contact
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from shared.structs import Interaction # For type hinting

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

    # Interaction Methods
    def save_interaction(self, interaction: 'Interaction') -> Optional[int]:
        """
        Saves an interaction (creates or updates) after validation.
        Returns the interaction ID.
        """
        from shared.structs import InteractionType, Interaction # Local import
        import datetime

        # Validation
        if not interaction.company_id and not interaction.contact_id:
            raise ValueError("Interaction must be associated with a company or a contact.")

        if not isinstance(interaction.interaction_type, InteractionType):
            # Attempt to convert from string if necessary, e.g. from API payload
            if isinstance(interaction.interaction_type, str):
                try:
                    interaction.interaction_type = InteractionType(interaction.interaction_type)
                except ValueError:
                    raise ValueError(f"Invalid interaction type string: '{interaction.interaction_type}'. Must be one of {', '.join([it.value for it in InteractionType])}.")
            else:
                raise ValueError(f"Invalid interaction type. Must be an InteractionType enum. Got {type(interaction.interaction_type)}")

        # Ensure date_time is a datetime object before comparison
        if isinstance(interaction.date_time, str):
            try:
                interaction.date_time = datetime.datetime.fromisoformat(interaction.date_time)
            except ValueError:
                raise ValueError("Invalid date_time format. Expected ISO format string.")

        if interaction.date_time and interaction.date_time.replace(tzinfo=None) > datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None):
            raise ValueError("Interaction date and time cannot be in the future.")

        if not interaction.subject:
            raise ValueError("Interaction subject cannot be empty.")
        if len(interaction.subject) > 150:
            raise ValueError("Interaction subject cannot exceed 150 characters.")

        # Ensure created_by_user_id is set (e.g., from a logged-in user or default)
        # For now, using a default system user if not provided.
        if interaction.created_by_user_id is None:
            system_user_id = self.db.get_user_id_by_username('system_user')
            if not system_user_id: # Should not happen if DB setup is correct
                raise Exception("Default system user not found. Please initialize the database correctly.")
            interaction.created_by_user_id = system_user_id

        # Convert datetime to ISO string for DB storage
        date_time_str = interaction.date_time.isoformat() if interaction.date_time else None

        if interaction.interaction_id is None:
            # Add new interaction
            new_id = self.db.add_interaction(
                company_id=interaction.company_id,
                contact_id=interaction.contact_id,
                interaction_type=interaction.interaction_type.value, # Store enum value
                date_time=date_time_str,
                subject=interaction.subject,
                description=interaction.description,
                created_by_user_id=interaction.created_by_user_id,
                attachment_path=interaction.attachment_path
            )
            interaction.interaction_id = new_id
            return new_id
        else:
            # Update existing interaction
            self.db.update_interaction(
                interaction_id=interaction.interaction_id,
                company_id=interaction.company_id,
                contact_id=interaction.contact_id,
                interaction_type=interaction.interaction_type.value, # Store enum value
                date_time=date_time_str,
                subject=interaction.subject,
                description=interaction.description,
                created_by_user_id=interaction.created_by_user_id,
                attachment_path=interaction.attachment_path
            )
            return interaction.interaction_id

    def get_interaction_details(self, interaction_id: int) -> Optional['Interaction']:
        """Retrieve full interaction details and return an Interaction object."""
        from shared.structs import Interaction, InteractionType # Local import
        import datetime

        data = self.db.get_interaction(interaction_id) # db returns a dict
        if data:
            # Convert interaction_type string from DB back to Enum member
            interaction_type_enum = None
            if data.get("interaction_type"):
                try:
                    interaction_type_enum = InteractionType(data["interaction_type"])
                except ValueError:
                    # Handle cases where the value from DB might not be a valid enum member
                    # This could be due to data corruption or if values were inserted bypassing enum checks
                    print(f"Warning: Invalid interaction type '{data['interaction_type']}' found in database for interaction ID {interaction_id}.")
                    interaction_type_enum = InteractionType.OTHER # Fallback or handle as error

            # Convert ISO string date_time back to datetime object
            date_time_obj = None
            if data.get("date_time"):
                try:
                    date_time_obj = datetime.datetime.fromisoformat(data["date_time"])
                except ValueError:
                    print(f"Warning: Invalid date format '{data['date_time']}' found in database for interaction ID {interaction_id}.")


            return Interaction(
                interaction_id=data.get("interaction_id"),
                company_id=data.get("company_id"),
                contact_id=data.get("contact_id"),
                interaction_type=interaction_type_enum,
                date_time=date_time_obj,
                subject=data.get("subject"),
                description=data.get("description"),
                created_by_user_id=data.get("created_by_user_id"),
                attachment_path=data.get("attachment_path")
            )
        return None

    def get_all_interactions(self, company_id: int = None, contact_id: int = None) -> List['Interaction']:
        """Retrieve all interactions, optionally filtered by company or contact, as Interaction objects."""
        from shared.structs import Interaction, InteractionType # Local import
        import datetime

        interactions_data = self.db.get_interactions(company_id=company_id, contact_id=contact_id) # db returns list of dicts
        interaction_list = []
        for row_data in interactions_data:
            interaction_type_enum = None
            if row_data.get("interaction_type"):
                try:
                    interaction_type_enum = InteractionType(row_data["interaction_type"])
                except ValueError:
                    print(f"Warning: Invalid interaction type '{row_data['interaction_type']}' found for interaction ID {row_data.get('interaction_id')}.")
                    interaction_type_enum = InteractionType.OTHER

            date_time_obj = None
            if row_data.get("date_time"):
                try:
                    date_time_obj = datetime.datetime.fromisoformat(row_data["date_time"])
                except ValueError:
                     print(f"Warning: Invalid date format '{row_data['date_time']}' found for interaction ID {row_data.get('interaction_id')}.")

            interaction_list.append(Interaction(
                interaction_id=row_data.get("interaction_id"),
                company_id=row_data.get("company_id"),
                contact_id=row_data.get("contact_id"),
                interaction_type=interaction_type_enum,
                date_time=date_time_obj,
                subject=row_data.get("subject"),
                description=row_data.get("description"),
                created_by_user_id=row_data.get("created_by_user_id"),
                attachment_path=row_data.get("attachment_path")
            ))
        return interaction_list

    def delete_interaction(self, interaction_id: int):
        """Delete a specific interaction."""
        self.db.delete_interaction(interaction_id)
