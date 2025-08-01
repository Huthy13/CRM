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

    def __str__(self) -> str:
        return (
            f"Address ID: {self.address_id}\n"
            f"Street: {self.street}\n"
            f"City: {self.city}\n"
            f"State: {self.state}\n"
            f"ZIP Code: {self.zip_code}\n"
            f"Country: {self.country}"
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
            f"Pricing Rule ID: {self.pricing_rule_id}"
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
        }

    @classmethod
    def from_row(cls, row: tuple) -> "Account":
        """Creates an Account object from a database row."""
        if len(row) == 6:
            account_id, name, phone, description, account_type_str, pricing_rule_id = row
        else:
            account_id, name, phone, description, account_type_str = row
            pricing_rule_id = None

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
