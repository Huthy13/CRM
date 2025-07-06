import unittest
from shared.structs import Account, AccountType, Address

class TestAccountTypeEnum(unittest.TestCase):
    def test_enum_values(self):
        self.assertEqual(AccountType.CUSTOMER.value, "Customer")
        self.assertEqual(AccountType.VENDOR.value, "Vendor")
        self.assertEqual(AccountType.CONTACT.value, "Contact")

    def test_enum_members(self):
        self.assertIsInstance(AccountType.CUSTOMER, AccountType)
        self.assertIsInstance(AccountType.VENDOR, AccountType)
        self.assertIsInstance(AccountType.CONTACT, AccountType)

class TestAccountClass(unittest.TestCase):
    def test_account_creation_default_type(self):
        account = Account(name="Test Account")
        self.assertEqual(account.name, "Test Account")
        self.assertIsNone(account.account_type)

    def test_account_creation_with_type(self):
        account = Account(name="Vendor Account", account_type=AccountType.VENDOR)
        self.assertEqual(account.name, "Vendor Account")
        self.assertEqual(account.account_type, AccountType.VENDOR)

    def test_account_to_dict_without_type(self):
        account = Account(account_id=1, name="Customer Acc")
        account_dict = account.to_dict()
        self.assertEqual(account_dict["name"], "Customer Acc")
        self.assertIsNone(account_dict["account_type"])

    def test_account_to_dict_with_type(self):
        account = Account(account_id=2, name="Supplier Co", account_type=AccountType.VENDOR)
        account_dict = account.to_dict()
        self.assertEqual(account_dict["name"], "Supplier Co")
        self.assertEqual(account_dict["account_type"], "Vendor")

    def test_account_str_representation_without_type(self):
        account = Account(account_id=3, name="A Contact")
        self.assertIn("Account Type: N/A", str(account))

    def test_account_str_representation_with_type(self):
        account = Account(account_id=4, name="A Customer", account_type=AccountType.CUSTOMER)
        self.assertIn("Account Type: Customer", str(account))

if __name__ == '__main__':
    unittest.main()
