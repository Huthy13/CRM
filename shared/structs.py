class Address:
    def __init__(self, address_id=None, street="", city="", state="", zip_code="", country=""):
        self.address_id = address_id
        self.street = street
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.country = country

    def __str__(self):
        return (f"Address ID: {self.address_id}\n"
                f"Street: {self.street}\n"
                f"City: {self.city}\n"
                f"State: {self.state}\n"
                f"ZIP Code: {self.zip_code}\n"
                f"Country: {self.country}")

    def to_dict(self):
        """Returns the address as a dictionary."""
        return {
            "address_id": self.address_id,
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country
        }

class Account:
    def __init__(self, account_id=None, name="", phone="", billing_address_id=None, shipping_address_id=None, website="", description=""):
        
        self.account_id = account_id
        self.name = name
        self.phone = phone
        self.billing_address_id = billing_address_id
        self.shipping_address_id = shipping_address_id
        self.website = website
        self.description = description

    def __str__(self):
        return (f"Data from the string method!!! Account ID: {self.account_id}\n"
                f"Name: {self.name}\n"
                f"Phone: {self.phone}\n"
                f"Billing Address ID: {self.billing_address_id}\n"
                f"Shipping Address ID: {self.shipping_address_id}\n"
                f"Website: {self.website}\n"
                f"Description: {self.description}")

    def to_dict(self):
        """Returns the account as a dictionary."""
        return {
            "account_id": self.account_id,
            "name": self.name,
            "phone": self.phone,
            "billing_address_id": self.billing_address_id,
            "shipping_address_id": self.shipping_address_id,
            "same_as_billing": self.is_billing_same_as_shipping(),
            "website": self.website,
            "description": self.description
        }
    
    def is_billing_same_as_shipping(self):
        """Checks if billing and shipping address IDs are the same."""
        if self.billing_address_id is None and self.shipping_address_id is None:
            return False

        return self.billing_address_id == self.shipping_address_id


class Contact:
    def __init__(self, contact_id=None, name="", phone="", email="", account_id=None, role=""):
        self.contact_id = contact_id
        self.name = name
        self.phone = phone
        self.email = email
        self.account_id = account_id
        self.role = role

    def __str__(self):
        return (f"Contact ID: {self.contact_id}\n"
                f"Name: {self.name}\n"
                f"Phone: {self.phone}\n"
                f"Email: {self.email}\n"
                f"Account ID: {self.account_id}\n"
                f"Role: {self.role}")

    def to_dict(self):
        """Returns the contact as a dictionary."""
        return {
            "contact_id": self.contact_id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "account_id": self.account_id,
            "role": self.role
        }

from enum import Enum
import datetime

class InteractionType(Enum):
    CALL = "Call"
    EMAIL = "Email"
    MEETING = "Meeting"
    VISIT = "Visit"
    OTHER = "Other"

class Interaction:
    def __init__(self, interaction_id=None, company_id=None, contact_id=None,
                 interaction_type: InteractionType = None, date_time: datetime.datetime = None,
                 subject="", description="", created_by_user_id=None, attachment_path=""):
        self.interaction_id = interaction_id
        self.company_id = company_id
        self.contact_id = contact_id
        self.interaction_type = interaction_type
        self.date_time = date_time
        self.subject = subject
        self.description = description
        self.created_by_user_id = created_by_user_id
        self.attachment_path = attachment_path

    def __str__(self):
        return (f"Interaction ID: {self.interaction_id}\n"
                f"Company ID: {self.company_id}\n"
                f"Contact ID: {self.contact_id}\n"
                f"Type: {self.interaction_type.value if self.interaction_type else 'N/A'}\n"
                f"Date/Time: {self.date_time.isoformat() if self.date_time else 'N/A'}\n"
                f"Subject: {self.subject}\n"
                f"Description: {self.description}\n"
                f"Created By User ID: {self.created_by_user_id}\n"
                f"Attachment Path: {self.attachment_path}")

    def to_dict(self):
        """Returns the interaction as a dictionary."""
        return {
            "interaction_id": self.interaction_id,
            "company_id": self.company_id,
            "contact_id": self.contact_id,
            "interaction_type": self.interaction_type.value if self.interaction_type else None,
            "date_time": self.date_time.isoformat() if self.date_time else None,
            "subject": self.subject,
            "description": self.description,
            "created_by_user_id": self.created_by_user_id,
            "attachment_path": self.attachment_path
        }

import datetime # Ensure datetime is imported for Task due_date typing
from enum import Enum

class TaskStatus(Enum):
    """Enumeration for the status of a Task."""
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    OVERDUE = "Overdue"

class TaskPriority(Enum):
    """Enumeration for the priority level of a Task."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class Task:
    """
    Represents a task in the CRM system.

    Attributes:
        task_id (int | None): The unique identifier for the task.
        company_id (int | None): The ID of the company associated with this task.
        contact_id (int | None): The ID of the contact associated with this task.
        title (str): The title of the task. Cannot be empty.
        description (str | None): A detailed description of the task.
        due_date (datetime.date | datetime.datetime | None): The date/datetime when the task is due. Must be provided.
        status (TaskStatus): The current status of the task (e.g., Open, Completed).
        priority (TaskPriority | None): The priority level of the task (e.g., Low, High).
        assigned_to_user_id (int | None): The ID of the user to whom this task is assigned.
        created_by_user_id (int | None): The ID of the user who created this task.
        created_at (datetime.datetime | None): Timestamp of when the task was created.
        updated_at (datetime.datetime | None): Timestamp of when the task was last updated.
    """
    def __init__(self,
                 task_id: int | None = None,
                 company_id: int | None = None,
                 contact_id: int | None = None,
                 title: str = "",
                 description: str | None = None,
                 due_date: datetime.date | datetime.datetime | None = None,
                 status: TaskStatus = TaskStatus.OPEN,
                 priority: TaskPriority | None = None,
                 assigned_to_user_id: int | None = None,
                 created_by_user_id: int | None = None, # Should be set, but allow None initially
                 created_at: datetime.datetime | None = None,
                 updated_at: datetime.datetime | None = None):
        if not title:
            raise ValueError("Task title cannot be empty.")
        if due_date is None:
            raise ValueError("Task due_date must be provided.")

        self.task_id = task_id
        self.company_id = company_id
        self.contact_id = contact_id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.status = status
        self.priority = priority
        self.assigned_to_user_id = assigned_to_user_id
        self.created_by_user_id = created_by_user_id
        self.created_at = created_at
        self.updated_at = updated_at

    def __str__(self) -> str:
        """Returns a string representation of the Task object, primarily for debugging."""
        return (f"Task ID: {self.task_id}\n"
                f"Title: {self.title}\n"
                f"Status: {self.status.value}\n"
                f"Priority: {self.priority.value if self.priority else 'N/A'}\n"
                f"Due Date: {self.due_date.isoformat() if self.due_date else 'N/A'}\n"
                f"Assigned To User ID: {self.assigned_to_user_id}\n"
                f"Created By User ID: {self.created_by_user_id}\n"
                f"Company ID: {self.company_id}\n"
                f"Contact ID: {self.contact_id}")

    def to_dict(self) -> dict:
        """Returns the task as a dictionary."""
        return {
            "task_id": self.task_id,
            "company_id": self.company_id,
            "contact_id": self.contact_id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status.value,
            "priority": self.priority.value if self.priority else None,
            "assigned_to_user_id": self.assigned_to_user_id,
            "created_by_user_id": self.created_by_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """
        Creates a Task object from a dictionary representation.

        Args:
            data (dict): A dictionary containing task data, typically from a database record
                         or an API payload. Keys should match Task attributes.

        Returns:
            Task: An instance of the Task class.

        Raises:
            ValueError: If essential fields like 'title' or 'due_date' are missing or
                        if 'status' or 'priority' have values not in their respective enums.
        """
        due_date = data.get("due_date")
        if isinstance(due_date, str):
            # Attempt to parse as datetime first, then date
            try:
                due_date = datetime.datetime.fromisoformat(due_date)
            except ValueError:
                due_date = datetime.date.fromisoformat(due_date)

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.datetime.fromisoformat(created_at)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.datetime.fromisoformat(updated_at)

        return cls(
            task_id=data.get("task_id"),
            company_id=data.get("company_id"),
            contact_id=data.get("contact_id"),
            title=data.get("title", ""), # Ensure title is present
            description=data.get("description"),
            due_date=due_date,
            status=TaskStatus(data.get("status", "Open")) if data.get("status") else TaskStatus.OPEN,
            priority=TaskPriority(data.get("priority")) if data.get("priority") else None,
            assigned_to_user_id=data.get("assigned_to_user_id"),
            created_by_user_id=data.get("created_by_user_id"),
            created_at=created_at,
            updated_at=updated_at
        )

class Product:
    def __init__(self, product_id=None, name="", description="", price=0.0):
        self.product_id = product_id
        self.name = name
        self.description = description
        self.price = price

    def __str__(self):
        return (f"Product ID: {self.product_id}\n"
                f"Name: {self.name}\n"
                f"Description: {self.description}\n"
                f"Price: {self.price}")

    def to_dict(self):
        """Returns the product as a dictionary."""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "price": self.price
        }