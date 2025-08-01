from typing import Optional
from shared.structs import Address, Account
from shared.utils import ensure_single_primary


class AddressService:
    """Service for address validation and persistence."""

    def __init__(self, db_handler):
        self.db = db_handler

    # Basic CRUD wrappers
    def add_address(self, street, city, state, zip_code, country):
        """Add a new address and return its ID."""
        return self.db.add_address(street, city, state, zip_code, country)

    def update_address(self, address_id, street, city, state, zip_code, country):
        """Update an existing address."""
        self.db.update_address(address_id, street, city, state, zip_code, country)

    def get_address_obj(self, address_id) -> Optional[Address]:
        """Retrieve an Address object for the given ID."""
        data = self.db.get_address(address_id)
        if data:
            return Address(
                address_id=address_id,
                street=data[0],
                city=data[1],
                state=data[2],
                zip_code=data[3],
                country=data[4],
            )
        return None

    # Higher level coordination
    def save_account_addresses(self, account: Account):
        """Persist all addresses for an account after enforcing validation rules."""
        self.db.cursor.execute(
            "DELETE FROM account_addresses WHERE account_id = ?", (account.account_id,)
        )

        ensure_single_primary(account.addresses)

        for address in account.addresses:
            if address.address_id:
                self.update_address(
                    address.address_id,
                    address.street,
                    address.city,
                    address.state,
                    address.zip_code,
                    address.country,
                )
                self.db.add_account_address(
                    account.account_id, address.address_id, address.address_type, address.is_primary
                )
            else:
                address_id = self.add_address(
                    address.street,
                    address.city,
                    address.state,
                    address.zip_code,
                    address.country,
                )
                self.db.add_account_address(
                    account.account_id, address_id, address.address_type, address.is_primary
                )
