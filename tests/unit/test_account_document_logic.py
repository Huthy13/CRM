import unittest
import tempfile
import os
import datetime
from core.database import DatabaseHandler
from core.address_book_logic import AddressBookLogic
from shared import Account, AccountType, AccountDocument

class TestAccountDocumentLogic(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseHandler(db_name=':memory:')
        self.logic = AddressBookLogic(self.db)
        account = Account(name="Vendor", account_type=AccountType.VENDOR)
        saved = self.logic.save_account(account)
        self.account_id = saved.account_id

    def tearDown(self):
        self.db.close()

    def test_save_get_delete_document(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "doc.txt")
            with open(file_path, "w", encoding="utf-8") as fh:
                fh.write("content")

            doc1 = AccountDocument(
                account_id=self.account_id,
                document_type="License",
                file_path=file_path,
                uploaded_at=datetime.datetime.now(),
            )
            saved1 = self.logic.save_account_document(doc1)
            self.assertIsNotNone(saved1.document_id)

            doc2 = AccountDocument(
                account_id=self.account_id,
                document_type="Contract",
                file_path=file_path,
                uploaded_at=datetime.datetime.now(),
            )
            saved2 = self.logic.save_account_document(doc2)

            docs = self.logic.get_account_documents(self.account_id)
            self.assertEqual(len(docs), 2)

            self.logic.delete_account_document(saved1)
            self.assertTrue(os.path.exists(file_path))

            self.logic.delete_account_document(saved2)
            self.assertFalse(os.path.exists(file_path))

if __name__ == '__main__':
    unittest.main()
