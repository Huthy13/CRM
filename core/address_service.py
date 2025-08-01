from shared.structs import Address
from core.repositories import AddressRepository, AccountRepository


class AddressService:
    """Service layer responsible for address validation and persistence."""

    def __init__(self, address_repo: AddressRepository, account_repo: AccountRepository):
        self.address_repo = address_repo
        self.account_repo = account_repo

    @staticmethod
    def enforce_single_primary(addresses):
        """Ensure only one primary address exists for each type."""
        primary_billing_found = False
        primary_shipping_found = False
        for address in reversed(addresses):
            if getattr(address, "is_primary", False):
                if address.address_type == "Billing":
                    if primary_billing_found:
                        address.is_primary = False
                    else:
                        primary_billing_found = True
                elif address.address_type == "Shipping":
                    if primary_shipping_found:
                        address.is_primary = False
                    else:
                        primary_shipping_found = True

    def add_address(self, street, city, state, zip_code, country):
        """Add a new address and return its ID."""
        return self.address_repo.add_address(street, city, state, zip_code, country)

    def update_address(self, address_id, street, city, state, zip_code, country):
        """Update an existing address."""
        self.address_repo.update_address(address_id, street, city, state, zip_code, country)

    def get_address_obj(self, address_id):
        """Retrieve an Address object by ID."""
        data = self.address_repo.get_address(address_id)
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

    def save_account_addresses(self, account):
        """Persist addresses for an account after enforcing primary constraints."""
        self.account_repo.clear_account_addresses(account.account_id)
        self.enforce_single_primary(account.addresses)
        for address in account.addresses:
            if address.address_id:
                self.address_repo.update_address(
                    address.address_id,
                    address.street,
                    address.city,
                    address.state,
                    address.zip_code,
                    address.country,
                )
                self.account_repo.add_account_address(
                    account.account_id,
                    address.address_id,
                    address.address_type,
                    address.is_primary,
                )
            else:
                address_id = self.address_repo.add_address(
                    address.street,
                    address.city,
                    address.state,
                    address.zip_code,
                    address.country,
                )
                self.account_repo.add_account_address(
                    account.account_id,
                    address_id,
                    address.address_type,
                    address.is_primary,
                )
