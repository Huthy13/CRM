from shared.structs import Address, Account, Contact, Product # Import Product
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
        """Add a new product or update an existing one. Returns Product ID."""
        if product.product_id is None:
            # Call db.add_product with all required arguments
            new_product_id = self.db.add_product(
                name=product.name,
                description=product.description,
                price=product.price,
                is_active=product.is_active,
                category=product.category,
                unit_of_measure=product.unit_of_measure
            )
            if new_product_id:
                product.product_id = new_product_id # Update object with new ID
            return new_product_id
        else:
            # Call db.update_product with all required arguments
            self.db.update_product(
                product_id=product.product_id,
                name=product.name,
                description=product.description,
                price=product.price,
                is_active=product.is_active,
                category=product.category,
                unit_of_measure=product.unit_of_measure
            )
            return product.product_id

    def get_product_details(self, product_id: int) -> Optional['Product']:
        """Retrieve full product details and return a Product object."""
        product_data = self.db.get_product_details(product_id) # db returns a dict
        if product_data:
            return Product(
                product_id=product_data["product_id"],
                name=product_data["name"],
                description=product_data["description"],
                price=product_data["price"],
                is_active=product_data.get("is_active", True), # Default to True if missing
                category=product_data.get("category", ""),
                unit_of_measure=product_data.get("unit_of_measure", "")
            )
        return None

    def get_all_products(self) -> list['Product']:
        """Retrieve all products as Product objects."""
        products_data = self.db.get_all_products() # db returns list of dicts
        product_list = []
        for row_data in products_data:
            product_list.append(Product(
                product_id=row_data["product_id"],
                name=row_data["name"],
                description=row_data["description"],
                price=row_data["price"],
                is_active=row_data.get("is_active", True),
                category=row_data.get("category", ""),
                unit_of_measure=row_data.get("unit_of_measure", "")
            ))
        return product_list

    def delete_product(self, product_id: int):
        """Delete a specific product."""
        self.db.delete_product(product_id)

    def get_all_product_categories(self) -> list[str]:
        """Retrieve a unique list of all product categories."""
        return self.db.get_all_product_categories()

from typing import TYPE_CHECKING, Optional, List
from enum import Enum # Placed here for broader scope within the module if needed
if TYPE_CHECKING:
    from shared.structs import Interaction, Task, TaskStatus, TaskPriority, Product # For type hinting
    # from enum import Enum # No longer needed here if imported above
