import unittest
from core.database import DatabaseHandler
from core.repositories import AccountRepository
from shared import AccountType

class TestAccountDocumentRepository(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseHandler(db_name=':memory:')
        self.repo = AccountRepository(self.db)
        self.account_id = self.repo.add_account(
            name="Vendor A",
            phone="123",
            website="",
            description="",
            account_type=AccountType.VENDOR.value,
        )

    def tearDown(self):
        self.db.close()

    def test_add_get_delete_and_count_documents(self):
        path = "testfile.txt"
        doc1_id = self.repo.add_account_document(self.account_id, "License", path)
        doc2_id = self.repo.add_account_document(self.account_id, "Contract", path)

        docs = self.repo.get_account_documents(self.account_id)
        self.assertEqual(len(docs), 2)
        self.assertEqual(self.repo.count_account_documents_by_path(path), 2)

        self.repo.delete_account_document(doc1_id)
        self.assertEqual(self.repo.count_account_documents_by_path(path), 1)
        docs_after = self.repo.get_account_documents(self.account_id)
        self.assertEqual(len(docs_after), 1)

        self.repo.delete_account_document(doc2_id)
        self.assertEqual(self.repo.count_account_documents_by_path(path), 0)
        docs_final = self.repo.get_account_documents(self.account_id)
        self.assertEqual(docs_final, [])

if __name__ == '__main__':
    unittest.main()
