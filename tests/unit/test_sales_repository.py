import unittest
from unittest.mock import MagicMock

from core.repositories import SalesRepository


class TestSalesRepository(unittest.TestCase):
    def test_get_shipments_for_sales_document(self):
        mock_db = MagicMock()
        repo = SalesRepository(mock_db)
        mock_db.get_shipments_for_sales_document.return_value = [
            {"shipment_id": 1}
        ]
        result = repo.get_shipments_for_sales_document(5)
        self.assertEqual(result, [{"shipment_id": 1}])
        mock_db.get_shipments_for_sales_document.assert_called_once_with(5)


if __name__ == "__main__":
    unittest.main()
