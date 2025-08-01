from enum import Enum
from typing import Optional
import datetime

# Re-export account, interaction, and task structures
from .account_structs import AccountType, Address, Account, Contact
from .interaction_structs import InteractionType, Interaction
from .task_structs import TaskStatus, TaskPriority, Task

class PricingRule:
    def __init__(self, rule_id: int | None = None, rule_name: str = "", markup_percentage: float | None = None, fixed_price: float | None = None):
        self.rule_id = rule_id
        self.rule_name = rule_name
        self.markup_percentage = markup_percentage
        self.fixed_price = fixed_price

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "markup_percentage": self.markup_percentage,
            "fixed_price": self.fixed_price,
        }

class Product:
    def __init__(self, product_id=None, name="", description="", cost=0.0, sale_price: Optional[float] = None, is_active=True, category="", unit_of_measure=""):
        self.product_id = product_id
        self.name = name
        self.description = description
        self.cost = cost
        self.sale_price = sale_price  # Added sale_price field
        self.is_active = is_active
        self.category = category
        self.unit_of_measure = unit_of_measure

    def __str__(self):
        return (f"Product ID: {self.product_id}\n"
                f"Name: {self.name}\n"
                f"Description: {self.description}\n"
                f"Cost: {self.cost}\n"
                f"Sale Price: {self.sale_price if self.sale_price is not None else 'N/A'}\n"  # Display sale_price
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
            "sale_price": self.sale_price,  # Ensure sale_price is in dict
            "is_active": self.is_active,
            "category": self.category,
            "unit_of_measure": self.unit_of_measure,
        }

class PurchaseDocumentStatus(Enum):
    RFQ = "RFQ"
    QUOTED = "Quoted"
    PO_ISSUED = "PO-Issued"  # Matches spec
    RECEIVED = "Received"
    CLOSED = "Closed"

# --- Sales Document Structures ---
class SalesDocumentType(Enum):
    QUOTE = "Quote"
    SALES_ORDER = "Sales Order"
    INVOICE = "Invoice"

class SalesDocumentStatus(Enum):
    # Quote statuses
    QUOTE_DRAFT = "Quote Draft"
    QUOTE_SENT = "Quote Sent"
    QUOTE_ACCEPTED = "Quote Accepted"
    QUOTE_REJECTED = "Quote Rejected"
    QUOTE_EXPIRED = "Quote Expired"

    # Sales Order statuses
    SO_OPEN = "SO Open"
    SO_FULFILLED = "SO Fulfilled"
    SO_CLOSED = "SO Closed"

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
                 related_quote_id: Optional[int] = None):  # Link invoice to quote
        self.id = doc_id
        self.document_number = document_number
        self.customer_id = customer_id  # Changed from vendor_id
        self.document_type = document_type
        self.created_date = created_date  # Should be ISO string
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
            "related_quote_id": self.related_quote_id,
        }

class SalesDocumentItem:
    def __init__(self, item_id=None, sales_document_id: int = None, product_id: Optional[int] = None,
                 product_description: str = "", quantity: float = 0.0,
                 unit_price: float = None,  # This would be sale_price from Product
                 discount_percentage: Optional[float] = 0.0,
                 line_total: float = None):  # quantity * unit_price * (1 - discount_percentage/100)
        self.id = item_id
        self.sales_document_id = sales_document_id
        self.product_id = product_id
        self.product_description = product_description
        self.quantity = quantity
        self.unit_price = unit_price  # Sale price
        self.discount_percentage = discount_percentage if discount_percentage is not None else 0.0
        self.line_total = line_total  # Calculated

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
            "line_total": self.line_total,
        }

    def __str__(self) -> str:
        return (f"SalesDocumentItem(ID: {self.id}, DocID: {self.sales_document_id}, "
                f"Product: {self.product_description}, Qty: {self.quantity}, UnitPrice: {self.unit_price}, "
                f"Discount: {self.discount_percentage}%)")
# --- End Sales Document Structures ---

class PurchaseDocument:
    def __init__(self, doc_id=None, document_number: str = "", vendor_id: int = None,
                 created_date: str = None, status: PurchaseDocumentStatus = None, notes: str = None):
        self.id = doc_id  # Using 'id' to match table column consistently
        self.document_number = document_number
        self.vendor_id = vendor_id
        self.created_date = created_date  # Should be ISO string
        self.status = status
        self.notes = notes

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "document_number": self.document_number,
            "vendor_id": self.vendor_id,
            "created_date": self.created_date,
            "status": self.status.value if self.status else None,
            "notes": self.notes,
        }

    def __str__(self) -> str:
        return (f"PurchaseDocument(ID: {self.id}, Number: {self.document_number}, VendorID: {self.vendor_id}, "
                f"Status: {self.status.value if self.status else 'N/A'}, Created: {self.created_date})")

class CompanyInformation:
    def __init__(self, company_id=None, name="", phone="", addresses=None):
        self.company_id = company_id
        self.name = name
        self.phone = phone
        self.addresses = addresses if addresses is not None else []

    def to_dict(self):
        return {
            "company_id": self.company_id,
            "name": self.name,
            "phone": self.phone,
            "addresses": [addr.to_dict() for addr in self.addresses],
        }

    def __str__(self):
        addresses_str = "\n".join([str(addr) for addr in self.addresses])
        return (f"Company ID: {self.company_id}\n"
                f"Name: {self.name}\n"
                f"Phone: {self.phone}\n"
                f"Addresses:\n{addresses_str}")

class PurchaseDocumentItem:
    def __init__(self, item_id=None, purchase_document_id: int = None, product_id: Optional[int] = None,
                 product_description: str = "", quantity: float = 0.0,
                 unit_price: float = None, total_price: float = None):
        self.id = item_id  # Using 'id'
        self.purchase_document_id = purchase_document_id
        self.product_id = product_id
        self.product_description = product_description  # Could be from product or overridden
        self.quantity = quantity
        self.unit_price = unit_price
        self.total_price = total_price  # Should be calculated quantity * unit_price if unit_price is known

    def calculate_total_price(self):
        """Calculates total price if quantity and unit_price are set."""
        if self.quantity is not None and self.unit_price is not None:
            self.total_price = self.quantity * self.unit_price
        else:
            self.total_price = None  # Or 0.0, depending on desired behavior for null unit_price
        return self.total_price

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "purchase_document_id": self.purchase_document_id,
            "product_id": self.product_id,
            "product_description": self.product_description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_price": self.total_price,
        }

    def __str__(self) -> str:
        return (f"PurchaseDocumentItem(ID: {self.id}, DocID: {self.purchase_document_id}, "
                f"Product: {self.product_description}, Qty: {self.quantity}, UnitPrice: {self.unit_price})")
