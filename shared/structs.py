from enum import Enum
from typing import Optional # Import Optional

class AccountType(Enum):
    CUSTOMER = "Customer"
    VENDOR = "Vendor"
    CONTACT = "Contact"

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
    def __init__(self, account_id=None, name="", phone="", billing_address_id=None, shipping_address_id=None, website="", description="", account_type: AccountType = None):

        self.account_id = account_id
        self.name = name
        self.phone = phone
        self.billing_address_id = billing_address_id
        self.shipping_address_id = shipping_address_id
        self.website = website
        self.description = description
        self.account_type = account_type

    def __str__(self):
        return (f"Data from the string method!!! Account ID: {self.account_id}\n"
                f"Name: {self.name}\n"
                f"Phone: {self.phone}\n"
                f"Billing Address ID: {self.billing_address_id}\n"
                f"Shipping Address ID: {self.shipping_address_id}\n"
                f"Website: {self.website}\n"
                f"Description: {self.description}\n"
                f"Account Type: {self.account_type.value if self.account_type else 'N/A'}")

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
            "description": self.description,
            "account_type": self.account_type.value if self.account_type else None
        }

    def is_billing_same_as_shipping(self):
        """Checks if billing and shipping address IDs are the same."""
        if self.billing_address_id is None and self.shipping_address_id is None:
            return False

        return self.billing_address_id == self.shipping_address_id

    @classmethod
    def from_dict(cls, data: dict) -> 'Account':
        """
        Creates an Account object from a dictionary representation.
        """
        account_type_str = data.get("account_type")
        account_type_enum = None
        if account_type_str:
            try:
                account_type_enum = AccountType(account_type_str)
            except ValueError:
                print(f"Warning: Invalid account type string '{account_type_str}' in data: {data}")

        return cls(
            account_id=data.get("account_id") or data.get("id"),
            name=data.get("name", ""),
            phone=data.get("phone", ""),
            billing_address_id=data.get("billing_address_id"),
            shipping_address_id=data.get("shipping_address_id"),
            website=data.get("website", ""),
            description=data.get("description", ""),
            account_type=account_type_enum
        )


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
    def __init__(self, product_id=None, name="", description="", cost=0.0, sale_price: Optional[float] = None, is_active=True, category="", unit_of_measure=""):
        self.product_id = product_id
        self.name = name
        self.description = description
        self.cost = cost
        self.sale_price = sale_price # Added sale_price field
        self.is_active = is_active
        self.category = category
        self.unit_of_measure = unit_of_measure

    def __str__(self):
        return (f"Product ID: {self.product_id}\n"
                f"Name: {self.name}\n"
                f"Description: {self.description}\n"
                f"Cost: {self.cost}\n"
                f"Sale Price: {self.sale_price if self.sale_price is not None else 'N/A'}\n" # Display sale_price
                f"Active: {self.is_active}\n"
                f"Category: {self.category}\n"
                f"Unit of Measure: {self.unit_of_measure}")

    def to_dict(self):
        """Returns the product as a dictionary."""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "description": self.description,
            "cost": self.cost,
            "sale_price": self.sale_price, # Ensure sale_price is in dict
            "is_active": self.is_active,
            "category": self.category,
            "unit_of_measure": self.unit_of_measure
        }

class PurchaseDocumentStatus(Enum):
    RFQ = "RFQ"
    QUOTED = "Quoted"
    PO_ISSUED = "PO-Issued" # Matches spec
    RECEIVED = "Received"
    CLOSED = "Closed"

# --- Sales Document Structures ---
class SalesDocumentType(Enum):
    QUOTE = "Quote"
    INVOICE = "Invoice"

class SalesDocumentStatus(Enum):
    # Quote statuses
    QUOTE_DRAFT = "Quote Draft"
    QUOTE_SENT = "Quote Sent"
    QUOTE_ACCEPTED = "Quote Accepted"
    QUOTE_REJECTED = "Quote Rejected"
    QUOTE_EXPIRED = "Quote Expired"
    # Invoice statuses
    INVOICE_DRAFT = "Invoice Draft"
    INVOICE_SENT = "Invoice Sent"
    INVOICE_PARTIALLY_PAID = "Invoice Partially Paid"
    INVOICE_PAID = "Invoice Paid"
    INVOICE_VOID = "Invoice Void"
    INVOICE_OVERDUE = "Invoice Overdue"

class SalesDocument:
    def __init__(self, doc_id=None, document_number: str = "", customer_id: int = None,
                 document_type: SalesDocumentType = None,
                 created_date: str = None, expiry_date: Optional[str] = None,  # For Quotes
                 due_date: Optional[str] = None,  # For Invoices
                 status: SalesDocumentStatus = None, notes: str = None,
                 subtotal: Optional[float] = 0.0, taxes: Optional[float] = 0.0, total_amount: Optional[float] = 0.0,
                 related_quote_id: Optional[int] = None): # Link invoice to quote
        self.id = doc_id
        self.document_number = document_number
        self.customer_id = customer_id # Changed from vendor_id
        self.document_type = document_type
        self.created_date = created_date # Should be ISO string
        self.expiry_date = expiry_date
        self.due_date = due_date
        self.status = status
        self.notes = notes
        self.subtotal = subtotal
        self.taxes = taxes
        self.total_amount = total_amount
        self.related_quote_id = related_quote_id


    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "document_number": self.document_number,
            "customer_id": self.customer_id,
            "document_type": self.document_type.value if self.document_type else None,
            "created_date": self.created_date,
            "expiry_date": self.expiry_date,
            "due_date": self.due_date,
            "status": self.status.value if self.status else None,
            "notes": self.notes,
            "subtotal": self.subtotal,
            "taxes": self.taxes,
            "total_amount": self.total_amount,
            "related_quote_id": self.related_quote_id
        }

    def __str__(self) -> str:
        return (f"SalesDocument(ID: {self.id}, Type: {self.document_type.value if self.document_type else 'N/A'}, "
                f"Number: {self.document_number}, CustomerID: {self.customer_id}, "
                f"Status: {self.status.value if self.status else 'N/A'}, Created: {self.created_date})")

class SalesDocumentItem:
    def __init__(self, item_id=None, sales_document_id: int = None, product_id: Optional[int] = None,
                 product_description: str = "", quantity: float = 0.0,
                 unit_price: float = None, # This would be sale_price from Product
                 discount_percentage: Optional[float] = 0.0,
                 line_total: float = None): # quantity * unit_price * (1 - discount_percentage/100)
        self.id = item_id
        self.sales_document_id = sales_document_id
        self.product_id = product_id
        self.product_description = product_description
        self.quantity = quantity
        self.unit_price = unit_price # Sale price
        self.discount_percentage = discount_percentage if discount_percentage is not None else 0.0
        self.line_total = line_total # Calculated

    def calculate_line_total(self):
        """Calculates line total based on quantity, unit_price, and discount."""
        if self.quantity is not None and self.unit_price is not None:
            discount_factor = 1.0 - (self.discount_percentage / 100.0 if self.discount_percentage is not None else 0.0)
            self.line_total = self.quantity * self.unit_price * discount_factor
        else:
            self.line_total = None
        return self.line_total

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sales_document_id": self.sales_document_id,
            "product_id": self.product_id,
            "product_description": self.product_description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "discount_percentage": self.discount_percentage,
            "line_total": self.line_total
        }

    def __str__(self) -> str:
        return (f"SalesDocumentItem(ID: {self.id}, DocID: {self.sales_document_id}, "
                f"Product: {self.product_description}, Qty: {self.quantity}, UnitPrice: {self.unit_price}, "
                f"Discount: {self.discount_percentage}%)")
# --- End Sales Document Structures ---

class PurchaseDocument:
    def __init__(self, doc_id=None, document_number: str = "", vendor_id: int = None,
                 created_date: str = None, status: PurchaseDocumentStatus = None, notes: str = None):
        self.id = doc_id # Using 'id' to match table column consistently
        self.document_number = document_number
        self.vendor_id = vendor_id
        self.created_date = created_date # Should be ISO string
        self.status = status
        self.notes = notes

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "document_number": self.document_number,
            "vendor_id": self.vendor_id,
            "created_date": self.created_date,
            "status": self.status.value if self.status else None,
            "notes": self.notes
        }

    def __str__(self) -> str:
        return (f"PurchaseDocument(ID: {self.id}, Number: {self.document_number}, VendorID: {self.vendor_id}, "
                f"Status: {self.status.value if self.status else 'N/A'}, Created: {self.created_date})")


class CompanyInformation:
    def __init__(self, company_id=None, name="", phone="", billing_address_id=None, shipping_address_id=None):
        self.company_id = company_id
        self.name = name
        self.phone = phone
        self.billing_address_id = billing_address_id
        self.shipping_address_id = shipping_address_id

    def to_dict(self):
        return {
            "company_id": self.company_id,
            "name": self.name,
            "phone": self.phone,
            "billing_address_id": self.billing_address_id,
            "shipping_address_id": self.shipping_address_id,
        }

    def __str__(self):
        return (f"Company ID: {self.company_id}\n"
                f"Name: {self.name}\n"
                f"Phone: {self.phone}\n"
                f"Billing Address ID: {self.billing_address_id}\n"
                f"Shipping Address ID: {self.shipping_address_id}")


class PurchaseDocumentItem:
    def __init__(self, item_id=None, purchase_document_id: int = None, product_id: Optional[int] = None,
                 product_description: str = "", quantity: float = 0.0,
                 unit_price: float = None, total_price: float = None):
        self.id = item_id # Using 'id'
        self.purchase_document_id = purchase_document_id
        self.product_id = product_id
        self.product_description = product_description # Could be from product or overridden
        self.quantity = quantity
        self.unit_price = unit_price
        self.total_price = total_price # Should be calculated quantity * unit_price if unit_price is known

    def calculate_total_price(self):
        """Calculates total price if quantity and unit_price are set."""
        if self.quantity is not None and self.unit_price is not None:
            self.total_price = self.quantity * self.unit_price
        else:
            self.total_price = None # Or 0.0, depending on desired behavior for null unit_price
        return self.total_price

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "purchase_document_id": self.purchase_document_id,
            "product_id": self.product_id,
            "product_description": self.product_description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_price": self.total_price
        }

    def __str__(self) -> str:
        return (f"PurchaseDocumentItem(ID: {self.id}, DocID: {self.purchase_document_id}, "
                f"Product: {self.product_description}, Qty: {self.quantity}, UnitPrice: {self.unit_price})")