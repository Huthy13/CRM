import unittest
from core.database import DatabaseHandler
from core.company_repository import CompanyRepository
from core.company_service import CompanyService
from core.address_service import AddressService
from core.repositories import AddressRepository, AccountRepository
from shared.structs import Address


class TestCompanyService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = DatabaseHandler(db_name=':memory:')
        address_repo = AddressRepository(cls.db)
        account_repo = AccountRepository(cls.db)
        cls.address_service = AddressService(address_repo, account_repo)
        company_repo = CompanyRepository(cls.db)
        cls.service = CompanyService(company_repo, cls.address_service)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_load_default_company(self):
        company = self.service.load_company_information()
        self.assertEqual(company.name, "My Company")
        self.assertIsNotNone(company.company_id)

    def test_save_company_information(self):
        company = self.service.load_company_information()
        company.addresses.clear()
        company.name = "Service Test Co"
        company.phone = "555-1234"
        addr = Address(street="1 Test St", city="Testville", state="TS", zip_code="12345", country="Testland")
        addr.address_type = "Billing"
        addr.is_primary = True
        company.addresses.append(addr)
        self.service.save_company_information(company)
        data = self.db.get_company_information()
        self.assertEqual(data['name'], "Service Test Co")
        self.assertEqual(data['phone'], "555-1234")
        self.assertEqual(len(data['addresses']), 1)

    def test_address_with_multiple_types(self):
        company = self.service.load_company_information()
        company.addresses.clear()
        addr = Address(street="2 Multi Ave", city="Town", state="TS", zip_code="22222", country="TC")
        addr.types = ["Billing", "Shipping"]
        addr.primary_types = ["Billing", "Shipping"]
        company.addresses.append(addr)
        self.service.save_company_information(company)
        rows = self.db.get_company_addresses(company.company_id)
        billing = [r for r in rows if r['address_type'] == 'Billing']
        shipping = [r for r in rows if r['address_type'] == 'Shipping']
        self.assertEqual(len(billing), 1)
        self.assertTrue(billing[0]['is_primary'])
        self.assertEqual(len(shipping), 1)
        self.assertTrue(shipping[0]['is_primary'])
