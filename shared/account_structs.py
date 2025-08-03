from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

class AccountType(Enum):
    CUSTOMER = "Customer"
    VENDOR = "Vendor"
    CONTACT = "Contact"

@dataclass
class Address:
    address_id: Optional[int] = None
    street: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = ""
    # An address can serve multiple purposes (Billing, Shipping, etc.)
    types: list[str] = field(default_factory=list)
    # Tracks which types this address is the primary for
    primary_types: list[str] = field(default_factory=list)

    @property
    def address_type(self) -> str:
        """Backwards compatible single address type.

        Many parts of the codebase still reference a single ``address_type``
        attribute.  For compatibility we expose the first entry in ``types``
        as ``address_type``.  Setting ``address_type`` will update the first
        element in ``types`` accordingly.
        """
        return self.types[0] if self.types else ""

    @address_type.setter
    def address_type(self, value: str) -> None:
        if self.types:
            if value:
                self.types[0] = value
            else:
                self.types.pop(0)
        elif value:
            self.types.append(value)

    @property
    def is_primary(self) -> bool:
        """Backwards compatible primary flag for the first type."""
        return bool(self.types) and self.types[0] in self.primary_types

    @is_primary.setter
    def is_primary(self, value: bool) -> None:
        if not self.types:
            return
        atype = self.types[0]
        if value:
            if atype not in self.primary_types:
                self.primary_types.append(atype)
        else:
            if atype in self.primary_types:
                self.primary_types.remove(atype)

    def __str__(self) -> str:
        type_str = ", ".join(self.types)
        primary_str = ", ".join(self.primary_types)
        return (
            f"Address ID: {self.address_id}\n"
            f"Street: {self.street}\n"
            f"City: {self.city}\n"
            f"State: {self.state}\n"
            f"ZIP Code: {self.zip_code}\n"
            f"Country: {self.country}\n"
            f"Types: {type_str}\n"
            f"Primary For: {primary_str}"
        )

    def to_dict(self) -> dict:
        """Returns the address as a dictionary."""
        return {
            "address_id": self.address_id,
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country,
            "types": list(self.types),
            "primary_types": list(self.primary_types),
            # Include legacy keys for compatibility
            "address_type": self.address_type,
            "is_primary": self.is_primary,
        }

@dataclass
class Account:
    account_id: Optional[int] = None
    name: str = ""
    phone: str = ""
    addresses: List[Address] = field(default_factory=list)
    website: str = ""
    description: str = ""
    account_type: Optional[AccountType] = None
    pricing_rule_id: Optional[int] = None
    payment_term_id: Optional[int] = None

    def __str__(self) -> str:
        addresses_str = "\n".join([str(addr) for addr in self.addresses])
        return (
            f"Data from the string method!!! Account ID: {self.account_id}\n"
            f"Name: {self.name}\n"
            f"Phone: {self.phone}\n"
            f"Addresses:\n{addresses_str}\n"
            f"Website: {self.website}\n"
            f"Description: {self.description}\n"
            f"Account Type: {self.account_type.value if self.account_type else 'N/A'}\n"
            f"Pricing Rule ID: {self.pricing_rule_id}\n"
            f"Payment Term ID: {self.payment_term_id}"
        )

    def to_dict(self) -> dict:
        """Returns the account as a dictionary."""
        return {
            "account_id": self.account_id,
            "name": self.name,
            "phone": self.phone,
            "addresses": [addr.to_dict() for addr in self.addresses],
            "website": self.website,
            "description": self.description,
            "account_type": self.account_type.value if self.account_type else None,
            "pricing_rule_id": self.pricing_rule_id,
            "payment_term_id": self.payment_term_id,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "Account":
        """Creates an Account object from a database row."""
        if len(row) == 7:
            account_id, name, phone, description, account_type_str, pricing_rule_id, payment_term_id = row
        elif len(row) == 6:
            account_id, name, phone, description, account_type_str, pricing_rule_id = row
            payment_term_id = None
        else:
            account_id, name, phone, description, account_type_str = row
            pricing_rule_id = None
            payment_term_id = None

        account_type_enum = None
        if account_type_str:
            try:
                account_type_enum = AccountType(account_type_str)
            except ValueError:
                print(f"Warning: Invalid account type string '{account_type_str}' in data: {row}")

        return cls(
            account_id=account_id,
            name=name,
            phone=phone,
            description=description,
            account_type=account_type_enum,
            pricing_rule_id=pricing_rule_id,
            payment_term_id=payment_term_id,
        )

@dataclass
class Contact:
    contact_id: Optional[int] = None
    name: str = ""
    phone: str = ""
    email: str = ""
    account_id: Optional[int] = None
    role: str = ""

    def __str__(self) -> str:
        return (
            f"Contact ID: {self.contact_id}\n"
            f"Name: {self.name}\n"
            f"Phone: {self.phone}\n"
            f"Email: {self.email}\n"
            f"Account ID: {self.account_id}\n"
            f"Role: {self.role}"
        )

    def to_dict(self) -> dict:
        """Returns the contact as a dictionary."""
        return {
            "contact_id": self.contact_id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "account_id": self.account_id,
            "role": self.role,
        }
