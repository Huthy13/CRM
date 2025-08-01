from abc import ABC, abstractmethod
from core.database import DatabaseHandler


class ICompanyRepository(ABC):
    """Interface for company-related database operations."""

    @abstractmethod
    def get_company_information(self) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def update_company_information(self, company_id: int, name: str, phone: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def add_company_information(self, name: str, phone: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_company_addresses(self, company_id: int) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def add_company_address(self, company_id: int, address_id: int, address_type: str, is_primary: bool) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear_company_addresses(self, company_id: int) -> None:
        raise NotImplementedError


class CompanyRepository(ICompanyRepository):
    """Concrete repository that uses DatabaseHandler for persistence."""

    def __init__(self, db: DatabaseHandler):
        self.db = db

    def get_company_information(self) -> dict | None:
        return self.db.get_company_information()

    def update_company_information(self, company_id: int, name: str, phone: str) -> None:
        self.db.update_company_information(company_id, name, phone)

    def add_company_information(self, name: str, phone: str) -> int:
        return self.db.add_company_information(name, phone)

    def get_company_addresses(self, company_id: int) -> list[dict]:
        return self.db.get_company_addresses(company_id)

    def add_company_address(self, company_id: int, address_id: int, address_type: str, is_primary: bool) -> None:
        self.db.add_company_address(company_id, address_id, address_type, is_primary)

    def clear_company_addresses(self, company_id: int) -> None:
        self.db.cursor.execute("DELETE FROM company_addresses WHERE company_id = ?", (company_id,))
        self.db.conn.commit()
