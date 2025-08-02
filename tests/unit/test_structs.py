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

# --- Purchase Document Structs Tests ---
from shared.structs import PurchaseDocumentStatus, PurchaseDocument, PurchaseDocumentItem

class TestPurchaseDocumentStatusEnum(unittest.TestCase):
    def test_enum_values(self):
        self.assertEqual(PurchaseDocumentStatus.RFQ.value, "RFQ")
        self.assertEqual(PurchaseDocumentStatus.QUOTED.value, "Quoted")
        self.assertEqual(PurchaseDocumentStatus.PO_ISSUED.value, "PO-Issued")
        self.assertEqual(PurchaseDocumentStatus.RECEIVED.value, "Received")
        self.assertEqual(PurchaseDocumentStatus.CLOSED.value, "Closed")

class TestPurchaseDocumentClass(unittest.TestCase):
    def test_purchase_document_creation_defaults(self):
        doc = PurchaseDocument()
        self.assertIsNone(doc.id)
        self.assertEqual(doc.document_number, "")
        self.assertIsNone(doc.vendor_id)
        self.assertIsNone(doc.created_date)
        self.assertIsNone(doc.status)
        self.assertIsNone(doc.notes)

    def test_purchase_document_creation_with_values(self):
        now_iso = "2023-10-27T10:00:00"
        doc = PurchaseDocument(doc_id=1, document_number="P00001", vendor_id=10,
                               created_date=now_iso, status=PurchaseDocumentStatus.RFQ, notes="Test RFQ")
        self.assertEqual(doc.id, 1)
        self.assertEqual(doc.document_number, "P00001")
        self.assertEqual(doc.vendor_id, 10)
        self.assertEqual(doc.created_date, now_iso)
        self.assertEqual(doc.status, PurchaseDocumentStatus.RFQ)
        self.assertEqual(doc.notes, "Test RFQ")

    def test_purchase_document_to_dict(self):
        now_iso = "2023-10-27T10:00:00"
        doc = PurchaseDocument(doc_id=1, document_number="P00001", vendor_id=5,
                               created_date=now_iso, status=PurchaseDocumentStatus.QUOTED, notes="Quoted notes")
        doc_dict = doc.to_dict()
        expected_dict = {
            "id": 1, "document_number": "P00001", "vendor_id": 5,
            "created_date": now_iso, "status": "Quoted", "notes": "Quoted notes", "is_active": True
        }
        self.assertEqual(doc_dict, expected_dict)

    def test_purchase_document_str(self):
        doc = PurchaseDocument(doc_id=1, document_number="P00002", status=PurchaseDocumentStatus.PO_ISSUED)
        self.assertIn("P00002", str(doc))
        self.assertIn("PO-Issued", str(doc))

class TestPurchaseDocumentItemClass(unittest.TestCase):
    def test_item_creation_defaults(self):
        item = PurchaseDocumentItem()
        self.assertIsNone(item.id)
        self.assertIsNone(item.purchase_document_id)
        self.assertEqual(item.product_description, "")
        self.assertEqual(item.quantity, 0.0)
        self.assertIsNone(item.unit_price)
        self.assertIsNone(item.total_price)
        self.assertIsNone(item.note)

    def test_item_creation_with_values(self):
        item = PurchaseDocumentItem(item_id=100, purchase_document_id=1, product_description="Test Product",
                                    quantity=10.5, unit_price=2.0, total_price=21.0, note="Sample")
        self.assertEqual(item.id, 100)
        self.assertEqual(item.purchase_document_id, 1)
        self.assertEqual(item.product_description, "Test Product")
        self.assertEqual(item.quantity, 10.5)
        self.assertEqual(item.unit_price, 2.0)
        self.assertEqual(item.total_price, 21.0)
        self.assertEqual(item.note, "Sample")

    def test_item_calculate_total_price(self):
        item = PurchaseDocumentItem(quantity=5, unit_price=10.0)
        self.assertEqual(item.calculate_total_price(), 50.0)
        self.assertEqual(item.total_price, 50.0)

        item.unit_price = None
        self.assertIsNone(item.calculate_total_price())
        self.assertIsNone(item.total_price)

        item.unit_price = 20.0
        item.quantity = None
        self.assertIsNone(item.calculate_total_price())
        self.assertIsNone(item.total_price)


    def test_item_to_dict(self):
        item = PurchaseDocumentItem(item_id=1, purchase_document_id=2, product_description="Another Product",
                                    quantity=3, unit_price=5.0)
        item.calculate_total_price()
        item_dict = item.to_dict()
        expected_dict = {
            "id": 1, "purchase_document_id": 2, "product_id": None, # Added product_id
            "product_description": "Another Product",
            "quantity": 3, "unit_price": 5.0, "total_price": 15.0, "note": None
        }
        self.assertEqual(item_dict, expected_dict)

    def test_item_str(self):
        item = PurchaseDocumentItem(item_id=1, product_description="Widget", quantity=5)
        self.assertIn("Widget", str(item))
        self.assertIn("Qty: 5", str(item))

if __name__ == '__main__':
    unittest.main()
