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
        for addr_data in addresses_data:
            address = Address(
                address_id=addr_data["address_id"],
                street=addr_data["street"],
                city=addr_data["city"],
                state=addr_data["state"],
                zip_code=addr_data["zip"],
                country=addr_data["country"],
            )
            address.address_type = addr_data["address_type"]
            address.is_primary = addr_data["is_primary"]
            company.addresses.append(address)
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
            self.repo.add_company_address(
                company.company_id, addr_id, address.address_type, getattr(address, "is_primary", False)
            )
        self.repo.update_company_information(company.company_id, company.name, company.phone)
