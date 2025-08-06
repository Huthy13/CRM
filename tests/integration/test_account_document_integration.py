import unittest
import os
import tempfile
import shutil
import datetime
from core.database import DatabaseHandler
from core.address_book_logic import AddressBookLogic
from shared import Account, AccountType, AccountDocument

class TestAccountDocumentIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_name = "test_account_documents_integration.db"
        if os.path.exists(cls.db_name):
            os.remove(cls.db_name)
        cls.db = DatabaseHandler(db_name=cls.db_name)
        cls.logic = AddressBookLogic(cls.db)
        account = Account(name="Vendor Int", account_type=AccountType.VENDOR)
        saved = cls.logic.save_account(account)
        cls.account_id = saved.account_id

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        if os.path.exists(cls.db_name):
            os.remove(cls.db_name)

    def test_upload_retrieve_delete_document(self):
        tmpdir = tempfile.mkdtemp()
        try:
            src = os.path.join(tmpdir, "src.txt")
            with open(src, "w", encoding="utf-8") as fh:
                fh.write("data")

            storage_dir = os.path.join(tmpdir, "storage")
            os.makedirs(storage_dir, exist_ok=True)
            stored = os.path.join(storage_dir, "stored.txt")
            shutil.copy(src, stored)

            doc = AccountDocument(
                account_id=self.account_id,
                document_type="License",
                file_path=stored,
                uploaded_at=datetime.datetime.now(),
            )
            saved = self.logic.save_account_document(doc)
            self.assertIsNotNone(saved.document_id)

            docs = self.logic.get_account_documents(self.account_id)
            self.assertEqual(len(docs), 1)
            self.assertEqual(docs[0].file_path, stored)

            self.logic.delete_account_document(saved)
            self.assertFalse(os.path.exists(stored))
            self.assertEqual(self.logic.get_account_documents(self.account_id), [])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == '__main__':
    unittest.main()
