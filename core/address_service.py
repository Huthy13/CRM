from shared.structs import Address
from core.repositories import AddressRepository, AccountRepository


class AddressService:
    """Service layer responsible for address validation and persistence."""

    def __init__(self, address_repo: AddressRepository, account_repo: AccountRepository):
        self.address_repo = address_repo
        self.account_repo = account_repo

    @staticmethod
    def enforce_single_primary(addresses):
        """Ensure only one primary address exists per address type.

        Supports both the legacy single ``address_type``/``is_primary`` attributes
        and the newer ``address_types``/``primary_types`` lists. When multiple
        addresses claim to be primary for the same type, only the last one is kept
        as primary.
        """
        seen_types: set[str] = set()
        for address in reversed(addresses):
            types = getattr(address, "address_types", None) or [
                t for t in [getattr(address, "address_type", "")] if t
            ]
            primary_types = getattr(address, "primary_types", None)
            if not primary_types:
                primary_types = [
                    getattr(address, "address_type", "")
                    if getattr(address, "is_primary", False)
                    else None
                ]
                primary_types = [t for t in primary_types if t]

            cleaned_primary = []
            for addr_type in primary_types:
                if addr_type not in seen_types:
                    seen_types.add(addr_type)
                    cleaned_primary.append(addr_type)
            address.address_types = types
            address.primary_types = cleaned_primary
            address.address_type = types[0] if types else ""
            address.is_primary = address.address_type in address.primary_types

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
                addr_id = address.address_id
            else:
                addr_id = self.address_repo.add_address(
                    address.street,
                    address.city,
                    address.state,
                    address.zip_code,
                    address.country,
                )

            types = getattr(address, "address_types", None) or [
                t for t in [getattr(address, "address_type", "")] if t
            ]
            primary_types = getattr(address, "primary_types", [])
            for addr_type in types:
                self.account_repo.add_account_address(
                    account.account_id,
                    addr_id,
                    addr_type,
                    addr_type in primary_types,
                )
