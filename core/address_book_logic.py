from shared.structs import Address, Account, Contact, Product, AccountType # Import Product and AccountType
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
    def save_account(self, account: Account) -> Account | None:
        """Add a new account, or update existing account if valid account ID is provided. Returns the Account object."""
        account_type_value = None
        if account.account_type:
            account_type_value = account.account_type.value
        elif account.account_id is None:  # It's a new account and no type provided
            account.account_type = AccountType.CONTACT  # Default to CONTACT for new accounts if none specified
            account_type_value = account.account_type.value

        if not account_type_value:  # This implies an update is trying to set type to None, or initial was None and no default applied
            # The DB has NOT NULL constraint on account_type.
            # Allowing None here would lead to IntegrityError at DB level.
            # Business logic should decide if this is an error or if a default should apply on update too.
            # For now, let's enforce that a type must be present for DB operation.
            raise ValueError("Account type cannot be None due to NOT NULL database constraint.")

        if account.account_id is None:
            # Add the account to get an ID
            new_id = self.db.add_account(account.name, account.phone, account.website, account.description, account_type_value)
            if new_id:
                account.account_id = new_id
                # Now, add the addresses
                for address in account.addresses:
                    address_id = self.db.add_address(address.street, address.city, address.state, address.zip_code, address.country)
                    self.db.add_account_address(new_id, address_id, address.address_type, address.is_primary)
                return account
            return None  # Failed to add
        else:
            # Update the account details
            self.db.update_account(account.account_id, account.name, account.phone, account.website, account.description, account_type_value)
            # Clear existing addresses and add the new ones
            # A more sophisticated approach would be to diff the addresses
            self.db.cursor.execute("DELETE FROM account_addresses WHERE account_id = ?", (account.account_id,))
            for address in account.addresses:
                if address.address_id:
                    self.db.update_address(address.address_id, address.street, address.city, address.state, address.zip_code, address.country)
                    self.db.add_account_address(account.account_id, address.address_id, address.address_type, address.is_primary)
                else:
                    address_id = self.db.add_address(address.street, address.city, address.state, address.zip_code, address.country)
                    self.db.add_account_address(account.account_id, address_id, address.address_type, address.is_primary)
            return account  # Return the updated account object


    def get_all_accounts(self) -> List[Account]:
        """
        Retrieve all accounts from the database and return them as a list of Account objects.
        This method is intended for use cases where the full Account object is needed, for example,
        in UI dropdowns that need to filter by account type.
        """
        accounts_data = self.db.get_all_accounts()
        accounts_list = []
        for acc_data in accounts_data:
            try:
                account = Account.from_row(acc_data)
                accounts_list.append(account)
            except (ValueError, KeyError) as e:
                # Log an error if a record is malformed or has an invalid account_type
                print(f"Warning: Could not process account record: {acc_data}. Error: {e}")
        return accounts_list

    def get_account_details(self, account_id) -> Account | None:
        """Retrieve full account details, including new fields."""
        data = self.db.get_account_details(account_id)  # db returns a dict
        if data:
            account_type_enum = None
            account_type_str = data.get("account_type")
            if account_type_str:
                try:
                    account_type_enum = AccountType(account_type_str)
                except ValueError:
                    print(f"Warning: Invalid account type string '{account_type_str}' in DB for account ID {data.get('id')}.")

            addresses = []
            for addr_data in data.get('addresses', []):
                address = Address(
                    address_id=addr_data['address_id'],
                    street=addr_data['street'],
                    city=addr_data['city'],
                    state=addr_data['state'],
                    zip_code=addr_data['zip'],
                    country=addr_data['country']
                )
                address.address_type = addr_data['address_type']
                address.is_primary = addr_data['is_primary']
                addresses.append(address)

            return Account(
                account_id=data.get("id"),  # Ensure key matches db output
                name=data.get("name"),
                phone=data.get("phone"),
                addresses=addresses,
                website=data.get("website"),
                description=data.get("description"),
                account_type=account_type_enum
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

    def save_contact(self, contact: Contact) -> Contact | None :
        """Add a new contact or update an existing one. Returns the Contact object."""
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
                return contact
            return None # Failed to add
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
            return contact

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

    # Task Methods
    def create_task(self, task: 'Task') -> 'Task':
        """
        Creates a new task after validation.
        Sets default status, timestamps, and created_by_user_id if not set.
        Returns the created Task object with all fields populated.
        """
        from shared.structs import Task, TaskStatus # Local import for Task
        import datetime

        if not isinstance(task, Task):
            raise TypeError("Input must be a Task object.")

        # Validation (title and due_date are validated by Task constructor)
        # Additional validation can be added here if needed.

        # Set defaults
        task.status = TaskStatus.OPEN
        now = datetime.datetime.now(datetime.timezone.utc)
        task.created_at = now
        task.updated_at = now

        # Ensure created_by_user_id is set (e.g., from a logged-in user or default)
        if task.created_by_user_id is None:
            system_user_id = self.db.get_user_id_by_username('system_user')
            if not system_user_id: # Should not happen if DB setup is correct
                raise Exception("Default system user not found. Please initialize the database correctly.")
            task.created_by_user_id = system_user_id

        task_data_dict = task.to_dict()

        # Remove task_id for insertion, as it's auto-generated
        task_data_dict.pop('task_id', None)

        # Convert enums to values for DB storage if not already handled by to_dict
        if isinstance(task_data_dict.get('status'), TaskStatus):
            task_data_dict['status'] = task_data_dict['status'].value
        if task_data_dict.get('priority') and isinstance(task_data_dict.get('priority'), Enum): # TaskPriority
             task_data_dict['priority'] = task_data_dict['priority'].value


        new_task_id = self.db.add_task(task_data_dict)
        task.task_id = new_task_id

        # Fetch from DB to confirm all fields, especially auto-generated ones like created_at from DB trigger (if any)
        # However, our current DB schema relies on application to set created_at/updated_at
        return task

    def get_task_details(self, task_id: int) -> Optional['Task']:
        """Retrieve a task by ID and return a Task object."""
        from shared.structs import Task # Local import
        task_data = self.db.get_task(task_id)
        if task_data:
            return Task.from_dict(task_data)
        return None

    def get_all_tasks(self, company_id: int = None, contact_id: int = None,
                      status: Optional['TaskStatus'] = None,
                      due_date_sort_order: str = None,
                      assigned_user_id: int = None,
                      priority: Optional['TaskPriority'] = None) -> List['Task']:
        """
        Retrieve all tasks, optionally filtered, as Task objects.
        Converts enum filters to their string values for DB query.
        """
        from shared.structs import Task # Local import

        status_str = status.value if status else None
        priority_str = priority.value if priority else None

        tasks_data = self.db.get_tasks(
            company_id=company_id,
            contact_id=contact_id,
            status=status_str,
            due_date_sort_order=due_date_sort_order,
            assigned_user_id=assigned_user_id,
            priority=priority_str
        )

        task_list = [Task.from_dict(data) for data in tasks_data]
        return task_list

    def update_task_details(self, task: 'Task') -> 'Task':
        """
        Updates an existing task after validation.
        Sets the updated_at timestamp.
        Returns the updated Task object.
        """
        from shared.structs import Task # Local import
        import datetime

        if not isinstance(task, Task):
            raise TypeError("Input must be a Task object.")
        if task.task_id is None:
            raise ValueError("Task ID must be provided to update a task.")

        # Validation (title and due_date are validated by Task constructor on modification)
        # Add more validation if necessary

        task.updated_at = datetime.datetime.now(datetime.timezone.utc)

        task_data_dict = task.to_dict()

        # Remove task_id from data to be updated, it's used in WHERE clause
        task_id = task_data_dict.pop('task_id')

        # Convert enums to values for DB storage if not already handled by to_dict
        if isinstance(task_data_dict.get('status'), Enum): # TaskStatus
            task_data_dict['status'] = task_data_dict['status'].value
        if task_data_dict.get('priority') and isinstance(task_data_dict.get('priority'), Enum): # TaskPriority
             task_data_dict['priority'] = task_data_dict['priority'].value


        self.db.update_task(task_id, task_data_dict)

        # Fetch from DB to ensure the returned object is consistent with DB state
        # return self.get_task_details(task_id)
        # Or, if confident, just return the modified task object:
        return task


    def delete_task_by_id(self, task_id: int, soft_delete: bool = True) -> None:
        """Deletes a task by its ID. Uses soft delete by default."""
        self.db.delete_task(task_id, soft_delete=soft_delete)

    def mark_task_completed(self, task_id: int) -> Optional['Task']:
        """Updates task status to COMPLETED and sets updated_at."""
        from shared.structs import TaskStatus # Local import
        import datetime

        task = self.get_task_details(task_id)
        if not task:
            return None # Or raise error

        task.status = TaskStatus.COMPLETED
        task.updated_at = datetime.datetime.now(datetime.timezone.utc)

        self.db.update_task_status(task.task_id, task.status.value, task.updated_at.isoformat())
        return task

    def check_and_update_overdue_tasks(self) -> int:
        """
        Checks for tasks that are past their due date and not yet 'Completed' or 'Overdue'.
        Updates their status to 'Overdue'.
        Returns the number of tasks updated.
        """
        from shared.structs import TaskStatus, Task # Local import
        import datetime

        now = datetime.datetime.now(datetime.timezone.utc)
        # For due_date comparison, if due_date is just a date, compare against date part of now.
        # If due_date includes time, compare against now (datetime).
        # The DB stores due_date as ISO string.
        # To correctly identify tasks due *before* today as overdue,
        # we should compare against the beginning of the current day.
        # If a task's due_date is 'YYYY-MM-DD', it implies by end of that day.
        # So, it's overdue if current_date is already YYYY-MM-(DD+1).

        current_day_iso_date_str = now.date().isoformat()
        overdue_tasks_data = self.db.get_overdue_tasks(current_day_iso_date_str)

        updated_count = 0
        for task_data in overdue_tasks_data:
            task = Task.from_dict(task_data) # Convert to Task object to easily manage status
            if task.status != TaskStatus.COMPLETED and task.status != TaskStatus.OVERDUE:
                updated_at_ts = datetime.datetime.now(datetime.timezone.utc)
                self.db.update_task_status(task.task_id, TaskStatus.OVERDUE.value, updated_at_ts.isoformat())
                updated_count += 1
        return updated_count

    # User methods
    def get_all_users(self) -> list[tuple[int, str]]:
        """
        Retrieve all users from the database.
        Returns a list of tuples, where each tuple is (user_id, username).
        """
        return self.db.get_all_users()

    # Product Methods
    def save_product(self, product: 'Product') -> Optional[int]:
        """Add a new product or update an existing one. Returns Product ID.
           Calls the newer DatabaseHandler methods that handle product_prices table."""

        # Basic SKU generation if not provided (can be made more robust or required on Product struct)
        # For now, assuming Product struct might not have SKU, so we generate one for add.
        # If Product struct is expected to have SKU, this logic might change.
        sku = f"SKU_{product.name[:10].replace(' ','_').upper()}" if product.name else "SKU_UNKNOWN"

        if product.product_id is None: # Adding a new product
            new_product_id = self.db.add_product(
                sku=sku, # Pass SKU
                name=product.name,
                description=product.description,
                cost=product.cost,
                sale_price=product.sale_price, # Pass sale_price
                is_active=product.is_active,
                category_name=product.category,
                unit_of_measure_name=product.unit_of_measure
                # currency and price_valid_from will use defaults in db.add_product
            )
            if new_product_id:
                product.product_id = new_product_id # Update struct with new ID
            return new_product_id
        else: # Updating an existing product
            # For update, SKU might be part of the update or fixed.
            # Assuming SKU can be updated or is derived similarly.
            # The db.update_product expects product_db_id.
            self.db.update_product(
                product_db_id=product.product_id, # Correct parameter name for DB method
                sku=sku, # Pass SKU
                name=product.name,
                description=product.description,
                cost=product.cost,
                sale_price=product.sale_price, # Pass sale_price
                is_active=product.is_active,
                category_name=product.category,
                unit_of_measure_name=product.unit_of_measure
                # currency and price_valid_from will use defaults in db.update_product
            )
            return product.product_id

    def get_product_details(self, product_id: int) -> Optional['Product']:
        """Retrieve full product details and return a Product object."""
        product_data_from_db = self.db.get_product_details(product_id)
        if product_data_from_db:
            return Product(
                product_id=product_data_from_db.get("product_id"),
                name=product_data_from_db.get("name"),
                description=product_data_from_db.get("description"),
                cost=product_data_from_db.get("cost"),
                sale_price=product_data_from_db.get("sale_price"),
                is_active=product_data_from_db.get("is_active", True),
                category=product_data_from_db.get("category_name") or "",
                unit_of_measure=product_data_from_db.get("unit_of_measure_name") or ""
            )
        return None

    def get_all_products(self) -> list['Product']:
        """Retrieve all products as Product objects."""
        products_data_from_db = self.db.get_all_products()
        product_list = []

        for row_data in products_data_from_db:
            product_list.append(Product(
                product_id=row_data.get("product_id"),
                name=row_data.get("name"),
                description=row_data.get("description"),
                cost=row_data.get("cost"),
                sale_price=row_data.get("sale_price"),
                is_active=row_data.get("is_active", True),
                category=row_data.get("category_name") or "",
                unit_of_measure=row_data.get("unit_of_measure_name") or ""
            ))
        return product_list

    def delete_product(self, product_id: int):
        """Delete a specific product."""
        self.db.delete_product(product_id)

    def get_all_product_categories(self) -> list[str]: # Renamed this back or re-added for tests/old UI
        """Retrieve a flat, unique, sorted list of all product category names."""
        # Fetches (id, name, parent_id)
        categories_data = self.db.get_all_product_categories_from_table()
        if not categories_data:
            return []
        # Get unique names and sort them
        unique_names = sorted(list(set(cat[1] for cat in categories_data if cat[1]))) # Ensure name is not empty
        return unique_names

    def get_hierarchical_categories(self) -> list[dict]: # For Treeview
        """
        Retrieves all categories and processes them into a hierarchical structure
        suitable for a Treeview (e.g., list of dicts with 'id', 'name', 'parent_id', 'children').
        """
        all_categories_raw = self.db.get_all_product_categories_from_table() # (id, name, parent_id)

        categories_map = {cat_id: {'id': cat_id, 'name': name, 'parent_id': parent_id, 'children': []}
                          for cat_id, name, parent_id in all_categories_raw}

        hierarchical_list = []
        for cat_id, data in categories_map.items():
            if data['parent_id'] is None:
                hierarchical_list.append(data)
            elif data['parent_id'] in categories_map: # Check if parent exists in map
                categories_map[data['parent_id']]['children'].append(data)
            else: # Orphaned category (parent_id exists but parent record doesn't - should ideally not happen with FKs)
                hierarchical_list.append(data) # Add as a root to make it visible

        # Sort children for consistent display if needed (e.g., by name)
        for cat_id in categories_map:
            categories_map[cat_id]['children'].sort(key=lambda x: x['name'])
        hierarchical_list.sort(key=lambda x: x['name'])

        return hierarchical_list

    def get_flat_category_paths(self) -> list[tuple[int, str]]:
        """
        Returns a flat list of (leaf_category_id, full_path_string) for all leaf categories.
        Example: [(10, "Electronics\\Audio\\Headphones"), (12, "Books\\Fiction")]
        """
        all_categories_map = self._get_all_categories_map()
        leaf_paths = []

        # Identify all leaf nodes (nodes that are not parents to any other node)
        # More simply, any node can be a leaf if it's selected.
        # The goal is to list all categories with their full path.

        for cat_id, (name, parent_id) in all_categories_map.items():
            path = self._get_category_path_string(cat_id, all_categories_map)
            leaf_paths.append((cat_id, path))

        leaf_paths.sort(key=lambda x: x[1]) # Sort by path string
        return leaf_paths


    def add_category(self, name: str, parent_id: int | None = None) -> int:
        """Adds a new category."""
        if not name.strip():
            raise ValueError("Category name cannot be empty.")
        # Consider adding validation for cyclical dependencies if parent_id is provided,
        # though basic check (cat_id != parent_id) is in DB layer.
        return self.db.add_product_category(name.strip(), parent_id)

    def update_category_name(self, category_id: int, new_name: str):
        """Updates an existing category's name."""
        if not new_name.strip():
            raise ValueError("New category name cannot be empty.")
        self.db.update_product_category_name(category_id, new_name.strip())

    def update_category_parent(self, category_id: int, new_parent_id: int | None):
        """Updates an existing category's parent."""
        # Add more sophisticated cycle detection here if needed.
        # E.g., ensure new_parent_id is not a descendant of category_id.
        if category_id == new_parent_id: # Basic check already in DB, but good to have in logic too
            raise ValueError("A category cannot be its own parent.")

        # More advanced cycle detection: Walk up from new_parent_id to see if category_id is an ancestor.
        current_ancestor_id = new_parent_id
        all_cats_map = self._get_all_categories_map()
        while current_ancestor_id is not None:
            if current_ancestor_id == category_id:
                raise ValueError("Cannot set parent to a descendant category (creates a cycle).")
            _name, current_ancestor_id = all_cats_map.get(current_ancestor_id, (None, None))

        self.db.update_product_category_parent(category_id, new_parent_id)

    def delete_category(self, category_id: int):
        """Deletes a category."""
        # Add any pre-deletion business logic here if needed.
        # E.g., check if category is in use by non-product entities if that becomes a feature.
        # The DB handles setting product.category_id to NULL and child categories' parent_id to NULL.
        self.db.delete_product_category(category_id)


    def get_all_product_units_of_measure(self) -> list[str]:
        """Retrieve a list of all product unit of measure names from the dedicated table."""
        units_tuples = self.db.get_all_product_units_of_measure_from_table() # Returns list of (id, name)
        return [name for id, name in units_tuples] # Extract just the names

    def _get_category_path_string(self, category_id: int, all_categories_map: dict[int, tuple[str, int | None]]) -> str:
        """
        Helper function to recursively build the full category path string.
        all_categories_map is a dictionary: {id: (name, parent_id)}
        """
        if category_id is None or category_id not in all_categories_map:
            return ""

        name, parent_id = all_categories_map[category_id]
        if parent_id is None or parent_id not in all_categories_map:
            return name
        else:
            parent_path = self._get_category_path_string(parent_id, all_categories_map)
            return f"{parent_path}\\{name}"

    def _get_all_categories_map(self) -> dict[int, tuple[str, int | None]]:
        """Helper to fetch all categories and put them into a map for easy lookup."""
        categories_data = self.db.get_all_product_categories_from_table() # (id, name, parent_id)
        return {cat_id: (name, parent_id) for cat_id, name, parent_id in categories_data}

from typing import TYPE_CHECKING, Optional, List
from enum import Enum # Placed here for broader scope within the module if needed
if TYPE_CHECKING:
    from shared.structs import Interaction, Task, TaskStatus, TaskPriority, Product # For type hinting
    # from enum import Enum # No longer needed here if imported above
