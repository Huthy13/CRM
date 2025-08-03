from shared.structs import CompanyInformation, Address
from core.address_service import AddressService
from .company_repository import ICompanyRepository


class CompanyService:
    """Service layer for managing company information and addresses."""

    def __init__(self, repo: ICompanyRepository, address_service: AddressService):
        self.repo = repo
        self.address_service = address_service

    def load_company_information(self) -> CompanyInformation:
        """Retrieve company information, creating a default if none exists."""
        data = self.repo.get_company_information()
        if not data:
            company_id = self.repo.add_company_information("My Company", "")
            return CompanyInformation(company_id=company_id, name="My Company", phone="", addresses=[])

        company = CompanyInformation(
            company_id=data.get("company_id"),
            name=data.get("name", ""),
            phone=data.get("phone", ""),
            addresses=[],
        )
        addresses_data = self.repo.get_company_addresses(company.company_id)
        address_map: dict[int, Address] = {}
        for addr_data in addresses_data:
            addr_id = addr_data["address_id"]
            address = address_map.get(addr_id)
            if not address:
                address = Address(
                    address_id=addr_id,
                    street=addr_data["street"],
                    city=addr_data["city"],
                    state=addr_data["state"],
                    zip_code=addr_data["zip"],
                    country=addr_data["country"],
                )
                address.address_types = []
                address.primary_types = []
                address_map[addr_id] = address
            address.address_types.append(addr_data["address_type"])
            if addr_data["is_primary"]:
                address.primary_types.append(addr_data["address_type"])

        company.addresses = list(address_map.values())
        for addr in company.addresses:
            addr.address_type = addr.address_types[0] if addr.address_types else ""
            addr.is_primary = addr.address_type in addr.primary_types
        return company

    def save_company_information(self, company: CompanyInformation) -> None:
        """Persist updated company information and its addresses."""
        self.address_service.enforce_single_primary(company.addresses)
        self.repo.clear_company_addresses(company.company_id)
        for address in company.addresses:
            if address.address_id:
                self.address_service.update_address(
                    address.address_id,
                    address.street,
                    address.city,
                    address.state,
                    address.zip_code,
                    address.country,
                )
                addr_id = address.address_id
            else:
                addr_id = self.address_service.add_address(
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
                self.repo.add_company_address(
                    company.company_id,
                    addr_id,
                    addr_type,
                    addr_type in primary_types,
                )
        self.repo.update_company_information(company.company_id, company.name, company.phone)
