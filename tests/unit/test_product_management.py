import unittest
import sqlite3
from datetime import datetime, date, timedelta
import os

import core.logic.product_management as pm
from core import database_setup

TEST_DB_NAME = ":memory:"

class BaseTestCase(unittest.TestCase):

    def setUp(self):
        """Set up a fresh in-memory database and connection for each test."""
        self.conn = sqlite3.connect(TEST_DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        self.conn.row_factory = sqlite3.Row

        pm.DB_NAME = TEST_DB_NAME
        database_setup.DB_NAME = TEST_DB_NAME
        database_setup.initialize_database(db_conn=self.conn)

    def tearDown(self):
        if self.conn:
            self.conn.close()

class TestProductCRUD(BaseTestCase):

    def test_create_product_success(self):
        data = {'sku': 'PROD001', 'name': 'Test Product 1', 'description': 'Desc 1', 'unit_of_measure': 'EA'}
        product_id = pm.create_product(data, db_conn=self.conn)
        self.assertIsNotNone(product_id)

        retrieved = pm.get_product(product_id, db_conn=self.conn)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['sku'], 'PROD001')
        self.assertEqual(retrieved['name'], 'Test Product 1')
        self.assertTrue(retrieved['is_active'])
        self.assertIsNotNone(retrieved['created_at'])
        self.assertIsNotNone(retrieved['updated_at'])

    def test_create_product_missing_required_fields(self):
        product_id = pm.create_product({'name': 'Incomplete Prod'}, db_conn=self.conn)
        self.assertIsNone(product_id)
        product_id_2 = pm.create_product({'sku': 'INC002'}, db_conn=self.conn)
        self.assertIsNone(product_id_2)

    def test_create_product_duplicate_sku(self):
        pm.create_product({'sku': 'DUP001', 'name': 'Product A'}, db_conn=self.conn)
        product_id_dup = pm.create_product({'sku': 'DUP001', 'name': 'Product B'}, db_conn=self.conn)
        self.assertIsNone(product_id_dup, "Should not create product with duplicate SKU")

    def test_get_product(self):
        p_id = pm.create_product({'sku': 'GET001', 'name': 'Gettable'}, db_conn=self.conn)
        self.assertIsNotNone(p_id)
        retrieved = pm.get_product(p_id, db_conn=self.conn)
        self.assertEqual(retrieved['id'], p_id)

        non_existent = pm.get_product(99999, db_conn=self.conn)
        self.assertIsNone(non_existent)

    def test_update_product(self):
        p_id = pm.create_product({'sku': 'UPD001', 'name': 'Original Name'}, db_conn=self.conn)
        self.assertIsNotNone(p_id)

        update_data = {'name': 'Updated Name', 'description': 'New Desc'}
        success = pm.update_product(p_id, update_data, db_conn=self.conn)
        self.assertTrue(success)

        updated_product = pm.get_product(p_id, db_conn=self.conn)
        self.assertEqual(updated_product['name'], 'Updated Name')
        self.assertEqual(updated_product['description'], 'New Desc')

    def test_update_product_sku_unchanged(self):
        p_id = pm.create_product({'sku': 'SKU-TEST', 'name': 'Original Name'}, db_conn=self.conn)
        pm.update_product(p_id, {'sku': 'NEW-SKU', 'name': 'New Name'}, db_conn=self.conn)
        product = pm.get_product(p_id, db_conn=self.conn)
        self.assertEqual(product['sku'], 'SKU-TEST')
        self.assertEqual(product['name'], 'New Name')

    def test_delete_product_soft_delete(self):
        p_id = pm.create_product({'sku': 'DEL001', 'name': 'Deletable'}, db_conn=self.conn)
        self.assertIsNotNone(p_id)

        success = pm.delete_product(p_id, db_conn=self.conn)
        self.assertTrue(success)

        retrieved = pm.get_product(p_id, db_conn=self.conn)
        self.assertIsNone(retrieved)

        all_products = pm.list_products({'sku': 'DEL001', 'is_active': None}, db_conn=self.conn)
        self.assertEqual(len(all_products), 1)
        self.assertFalse(all_products[0]['is_active'])

    def test_list_products(self):
        pm.create_product({'sku': 'LIST001', 'name': 'List Prod 1'}, db_conn=self.conn)
        pm.create_product({'sku': 'LIST002', 'name': 'List Prod 2'}, db_conn=self.conn)
        p3_id = pm.create_product({'sku': 'LIST003', 'name': 'List Prod 3 Inactive'}, db_conn=self.conn)
        pm.delete_product(p3_id, db_conn=self.conn)

        active_products = pm.list_products(db_conn=self.conn)
        self.assertEqual(len(active_products), 2)
        self.assertTrue(all(p['is_active'] for p in active_products))

        all_prods_filter = pm.list_products({'is_active': None}, db_conn=self.conn)
        self.assertEqual(len(all_prods_filter), 3)

        named_filter = pm.list_products({'name': 'List Prod 1'}, db_conn=self.conn)
        self.assertEqual(len(named_filter), 1)
        self.assertEqual(named_filter[0]['sku'], 'LIST001')

    def test_list_products_no_match(self):
        products = pm.list_products({'name': 'NonExistentProductName'}, db_conn=self.conn)
        self.assertEqual(len(products), 0)

    def test_update_non_existent_product(self):
        success = pm.update_product(9999, {'name': 'Ghost Product'}, db_conn=self.conn)
        self.assertFalse(success)

    def test_create_product_with_null_optional_fields(self):
        data = {'sku': 'PROD_NULL', 'name': 'Product With Nulls', 'description': None, 'category_id': None, 'unit_of_measure': None}
        product_id = pm.create_product(data, db_conn=self.conn)
        self.assertIsNotNone(product_id)
        retrieved = pm.get_product(product_id, db_conn=self.conn)
        self.assertIsNone(retrieved['description'])
        self.assertIsNone(retrieved['category_id'])
        self.assertIsNone(retrieved['unit_type_name'])


class TestCategoryManagement(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.cat1_id = pm.create_category({'name': 'Electronics'}, db_conn=self.conn)
        self.cat2_id = pm.create_category({'name': 'Books'}, db_conn=self.conn)
        self.sub_cat1_id = pm.create_category({'name': 'Laptops', 'parent_id': self.cat1_id}, db_conn=self.conn)

    def test_create_category(self):
        self.assertIsNotNone(self.cat1_id)
        self.assertIsNotNone(self.sub_cat1_id)
        cat = pm.get_category(self.sub_cat1_id, db_conn=self.conn)
        self.assertEqual(cat['parent_id'], self.cat1_id)

    def test_create_category_invalid_parent(self):
        cat_id = pm.create_category({'name': 'Orphan', 'parent_id': 9999}, db_conn=self.conn)
        self.assertIsNone(cat_id)

    def test_update_category_name_description(self):
        pm.update_category(self.cat1_id, {'name': 'Digital Goods', 'description': 'Updated Desc'}, db_conn=self.conn)
        cat = pm.get_category(self.cat1_id, db_conn=self.conn)
        self.assertEqual(cat['name'], 'Digital Goods')
        self.assertEqual(cat['description'], 'Updated Desc')

    def test_update_category_parent(self):
        pm.update_category(self.sub_cat1_id, {'parent_id': self.cat2_id}, db_conn=self.conn)
        cat = pm.get_category(self.sub_cat1_id, db_conn=self.conn)
        self.assertEqual(cat['parent_id'], self.cat2_id)

    def test_update_category_prevent_self_parent(self):
        success = pm.update_category(self.cat1_id, {'parent_id': self.cat1_id}, db_conn=self.conn)
        self.assertFalse(success, "Should not allow self-parenting")

    def test_update_category_prevent_circular_dependency(self):
        success = pm.update_category(self.cat1_id, {'parent_id': self.sub_cat1_id}, db_conn=self.conn)
        self.assertFalse(success, "Should prevent circular dependency")

    def test_delete_category_empty(self):
        temp_cat_id = pm.create_category({'name': 'Temporary'}, db_conn=self.conn)
        self.assertTrue(pm.delete_category(temp_cat_id, db_conn=self.conn))
        self.assertIsNone(pm.get_category(temp_cat_id, db_conn=self.conn))

    def test_delete_category_with_children_fail(self):
        self.assertFalse(pm.delete_category(self.cat1_id, db_conn=self.conn))

    def test_delete_category_with_products_unassigns(self):
        prod_id = pm.create_product({'sku': 'CATPROD01', 'name': 'Laptop X', 'category_id': self.sub_cat1_id}, db_conn=self.conn)
        self.assertTrue(pm.delete_category(self.sub_cat1_id, db_conn=self.conn))
        product = pm.get_product(prod_id, db_conn=self.conn)
        self.assertIsNotNone(product)
        self.assertIsNone(product['category_id'])

    def test_list_categories_top_level(self):
        top_level = pm.list_categories(db_conn=self.conn)
        self.assertEqual(len(top_level), 2)
        self.assertTrue(any(c['id'] == self.cat1_id for c in top_level))
        self.assertTrue(any(c['id'] == self.cat2_id for c in top_level))

    def test_list_categories_children(self):
        children_of_cat1 = pm.list_categories(parent_id=self.cat1_id, db_conn=self.conn)
        self.assertEqual(len(children_of_cat1), 1)
        self.assertEqual(children_of_cat1[0]['id'], self.sub_cat1_id)

    def test_list_products_in_category_recursive(self):
        cat_grandparent_id = pm.create_category({'name': 'GP'}, db_conn=self.conn)
        cat_parent_id = pm.create_category({'name': 'P', 'parent_id': cat_grandparent_id}, db_conn=self.conn)
        cat_child_id = pm.create_category({'name': 'C', 'parent_id': cat_parent_id}, db_conn=self.conn)

        pm.create_product({'sku': 'P1', 'name': 'Prod In GP', 'category_id': cat_grandparent_id}, db_conn=self.conn)
        pm.create_product({'sku': 'P2', 'name': 'Prod In P', 'category_id': cat_parent_id}, db_conn=self.conn)
        pm.create_product({'sku': 'P3', 'name': 'Prod In C', 'category_id': cat_child_id}, db_conn=self.conn)
        pm.create_product({'sku': 'P4', 'name': 'Prod Unrelated', 'category_id': self.cat2_id}, db_conn=self.conn)

        products = pm.list_products_in_category_recursive(cat_grandparent_id, db_conn=self.conn)
        self.assertEqual(len(products), 3)
        skus = {p['sku'] for p in products}
        self.assertEqual(skus, {'P1', 'P2', 'P3'})

    def test_delete_category_product_reassignment_check(self):
        # Create a product in a category
        prod_id = pm.create_product({'sku': 'CATDELCHECK', 'name': 'Prod in SubCat', 'category_id': self.sub_cat1_id}, db_conn=self.conn)
        self.assertIsNotNone(prod_id)

        # Delete the sub-category
        delete_success = pm.delete_category(self.sub_cat1_id, db_conn=self.conn)
        self.assertTrue(delete_success, "Sub-category deletion should succeed")

        # Verify product is unassigned
        product_after_del = pm.get_product(prod_id, db_conn=self.conn)
        self.assertIsNotNone(product_after_del)
        self.assertIsNone(product_after_del['category_id'], "Product should be unassigned from deleted category")

        # Attempting to assign a product to the deleted category ID should ideally not be possible
        # or result in an error if the ID was somehow reused (not with autoincrement) or if FK constraints are deferred.
        # However, our system doesn't prevent creating a product with a non-existent category_id during create_product.
        # The FK constraint in SQLite is typically enforced on INSERT/UPDATE.
        # So, creating a new product with an old, now-deleted category_id might pass pm.create_product's internal checks
        # (if it doesn't re-verify category_id existence) but would fail at DB level if FKs are on.
        # Let's check if create_product handles non-existent category_id robustly.
        # pm.create_product already has an implicit check via the FK constraint.
        # No, create_product doesn't explicitly check category_id validity before insert.
        # The database foreign key constraint will handle this.
        # For this test, we've confirmed product unassignment.

class TestPricingEngine(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.product_id = pm.create_product({'sku': 'PRICEPROD', 'name': 'Pricing Product'}, db_conn=self.conn)
        self.assertIsNotNone(self.product_id)

        self.price1_id = pm.add_or_update_product_price({ # SALE price by default
            'product_id': self.product_id, 'price': 10.00, 'currency': 'USD',
            'valid_from': '2023-01-01', 'price_type': 'SALE'
        }, db_conn=self.conn)
        self.price2_id = pm.add_or_update_product_price({ # SALE price
            'product_id': self.product_id, 'price': 12.00, 'currency': 'USD',
            'valid_from': '2023-06-01', 'valid_to': '2023-08-31', 'price_type': 'SALE'
        }, db_conn=self.conn)
        self.price3_id = pm.add_or_update_product_price({ # EUR SALE price
            'product_id': self.product_id, 'price': 9.50, 'currency': 'EUR',
            'valid_from': '2023-01-01', 'price_type': 'SALE'
        }, db_conn=self.conn)
        self.price4_id = pm.add_or_update_product_price({ # Shorter valid SALE price
            'product_id': self.product_id, 'price': 11.00, 'currency': 'USD',
            'valid_from': '2023-07-01', 'valid_to': '2023-07-31', 'price_type': 'SALE'
        }, db_conn=self.conn)
        self.cost_price_id = pm.add_or_update_product_price({ # COST price
            'product_id': self.product_id, 'price': 7.00, 'currency': 'USD',
            'valid_from': '2023-01-01', 'price_type': 'COST'
        }, db_conn=self.conn)

    def test_add_product_price(self):
        self.assertIsNotNone(self.price1_id)
        # Test fetching specific price type
        prices = pm.get_product_prices(self.product_id, 'USD', price_type='SALE', db_conn=self.conn)
        self.assertTrue(any(p['id'] == self.price1_id and p['price_type'] == 'SALE' for p in prices))

        cost_prices = pm.get_product_prices(self.product_id, 'USD', price_type='COST', db_conn=self.conn)
        self.assertTrue(any(p['id'] == self.cost_price_id and p['price_type'] == 'COST' for p in cost_prices))


    def test_update_price_by_id(self):
        pm.add_or_update_product_price({
            'id': self.price1_id, 'product_id': self.product_id,
            'price': 9.99, 'currency': 'USD', 'valid_from': '2023-01-01', 'price_type': 'SALE' # Ensure price_type
        }, db_conn=self.conn)
        prices = pm.get_product_prices(self.product_id, 'USD', price_type='SALE', db_conn=self.conn)
        updated_price = next(p for p in prices if p['id'] == self.price1_id)
        self.assertEqual(updated_price['price'], 9.99)

    def test_update_price_by_fields_match(self):
        # This test updates based on product_id, currency, valid_from, and now price_type
        pm.add_or_update_product_price({
             'product_id': self.product_id, 'price': 9.75, 'currency': 'USD',
             'valid_from': '2023-01-01', 'price_type': 'SALE' # Specify price_type for update
        }, db_conn=self.conn)
        prices = pm.get_product_prices(self.product_id, 'USD', price_type='SALE', db_conn=self.conn)
        # Find the specific price record (price1_id was for SALE type)
        updated_price = next(p for p in prices if p['id'] == self.price1_id)
        self.assertEqual(updated_price['price'], 9.75)

    def test_get_effective_price(self):
        # Test for SALE prices (default price_type for get_effective_price)
        self.assertIsNone(pm.get_effective_price(self.product_id, '2022-12-31', 'USD', price_type='SALE', db_conn=self.conn))
        eff_price = pm.get_effective_price(self.product_id, '2023-03-01', 'USD', price_type='SALE', db_conn=self.conn)
        self.assertEqual(eff_price['id'], self.price1_id)
        eff_price = pm.get_effective_price(self.product_id, '2023-06-15', 'USD', price_type='SALE', db_conn=self.conn)
        self.assertEqual(eff_price['id'], self.price2_id)
        eff_price = pm.get_effective_price(self.product_id, '2023-07-15', 'USD', price_type='SALE', db_conn=self.conn)
        self.assertEqual(eff_price['id'], self.price4_id)
        eff_price = pm.get_effective_price(self.product_id, '2023-08-15', 'USD', price_type='SALE', db_conn=self.conn)
        self.assertEqual(eff_price['id'], self.price2_id)
        eff_price = pm.get_effective_price(self.product_id, '2023-09-01', 'USD', price_type='SALE', db_conn=self.conn)
        self.assertEqual(eff_price['id'], self.price1_id)
        eff_price_eur = pm.get_effective_price(self.product_id, '2023-03-01', 'EUR', price_type='SALE', db_conn=self.conn)
        self.assertEqual(eff_price_eur['id'], self.price3_id)

        # Test for COST price
        eff_cost_price = pm.get_effective_price(self.product_id, '2023-03-01', 'USD', price_type='COST', db_conn=self.conn)
        self.assertIsNotNone(eff_cost_price)
        self.assertEqual(eff_cost_price['id'], self.cost_price_id)
        self.assertEqual(eff_cost_price['price'], 7.00)


    def test_delete_product_price(self):
        temp_price_id = pm.add_or_update_product_price({
            'product_id': self.product_id, 'price': 5.00, 'currency': 'CAD',
            'valid_from': '2023-01-01', 'price_type': 'SALE'
        }, db_conn=self.conn)
        self.assertTrue(pm.delete_product_price(temp_price_id, db_conn=self.conn))
        self.assertIsNone(pm.get_effective_price(self.product_id, '2023-01-01', 'CAD', price_type='SALE', db_conn=self.conn))

    def test_get_effective_price_no_prices_for_product(self):
        new_prod_id = pm.create_product({'sku': 'NOPRICE', 'name': 'No Price Product'}, db_conn=self.conn)
        self.assertIsNotNone(new_prod_id)
        price = pm.get_effective_price(new_prod_id, '2023-01-01', 'USD', price_type='SALE', db_conn=self.conn)
        self.assertIsNone(price)

    def test_get_effective_price_no_price_for_currency(self):
        price = pm.get_effective_price(self.product_id, '2023-03-01', 'CAD', price_type='SALE', db_conn=self.conn)
        self.assertIsNone(price)

    def test_get_effective_price_no_price_for_type(self):
        # Prices exist for SALE and COST in USD. Request MSRP.
        price = pm.get_effective_price(self.product_id, '2023-03-01', 'USD', price_type='MSRP', db_conn=self.conn)
        self.assertIsNone(price)


    def test_add_or_update_product_price_exact_duplicate_period(self):
        new_price_val = 10.50
        # This will update self.price1_id because product_id, price_type ('SALE'), and valid_from match
        updated_id = pm.add_or_update_product_price({
            'product_id': self.product_id, 'price': new_price_val, 'currency': 'USD',
            'valid_from': '2023-01-01', 'price_type': 'SALE'
        }, db_conn=self.conn)
        self.assertEqual(updated_id, self.price1_id, "Should update existing record for exact period and type match")

        eff_price = pm.get_effective_price(self.product_id, '2023-03-01', 'USD', price_type='SALE', db_conn=self.conn)
        self.assertEqual(eff_price['price'], new_price_val)
        self.assertEqual(eff_price['id'], self.price1_id)

    def test_price_validity_same_day_from_to(self):
        price_id = pm.add_or_update_product_price({
            'product_id': self.product_id, 'price': 25.00, 'currency': 'USD',
            'valid_from': '2023-10-10', 'valid_to': '2023-10-10', 'price_type': 'SALE'
        }, db_conn=self.conn)
        self.assertIsNotNone(price_id)

        eff_price = pm.get_effective_price(self.product_id, '2023-10-10', 'USD', price_type='SALE', db_conn=self.conn)
        self.assertIsNotNone(eff_price)
        self.assertEqual(eff_price['id'], price_id)

        eff_price_after = pm.get_effective_price(self.product_id, '2023-10-11', 'USD', price_type='SALE', db_conn=self.conn)
        # After 'valid_to', this specific price should not be effective.
        # The effective price might fall back to price1_id.
        self.assertNotEqual(eff_price_after['id'] if eff_price_after else None, price_id)


class TestInventoryTracking(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.product_id = pm.create_product({'sku': 'INVPROD', 'name': 'Inventory Product'}, db_conn=self.conn)
        self.loc1 = 100
        self.loc2 = 200

    def test_adjust_inventory_create_and_update(self):
        rec = pm.adjust_inventory(self.product_id, self.loc1, 50, min_stock=10, max_stock=100, db_conn=self.conn)
        self.assertIsNotNone(rec)
        self.assertEqual(rec['quantity'], 50)
        rec = pm.adjust_inventory(self.product_id, self.loc1, -20, min_stock=5, db_conn=self.conn)
        self.assertEqual(rec['quantity'], 30)
        self.assertEqual(rec['min_stock'], 5)
        self.assertEqual(rec['max_stock'], 100)

    def test_adjust_inventory_prevent_negative(self):
        pm.adjust_inventory(self.product_id, self.loc1, 10, db_conn=self.conn)
        rec = pm.adjust_inventory(self.product_id, self.loc1, -20, db_conn=self.conn)
        self.assertIsNone(rec, "Should not allow negative inventory")
        current_inv = pm.get_inventory_at_location(self.product_id, self.loc1, db_conn=self.conn)
        self.assertEqual(current_inv['quantity'], 10)

    def test_get_inventory_location_and_total(self):
        pm.adjust_inventory(self.product_id, self.loc1, 30, db_conn=self.conn)
        pm.adjust_inventory(self.product_id, self.loc2, 70, db_conn=self.conn)
        loc1_inv = pm.get_inventory_at_location(self.product_id, self.loc1, db_conn=self.conn)
        self.assertEqual(loc1_inv['quantity'], 30)
        all_inv = pm.get_all_inventory_for_product(self.product_id, db_conn=self.conn)
        self.assertEqual(len(all_inv), 2)
        total_inv = pm.get_total_product_inventory(self.product_id, db_conn=self.conn)
        self.assertEqual(total_inv['total_quantity'], 100)

    def test_transfer_inventory_success(self):
        pm.adjust_inventory(self.product_id, self.loc1, 50, db_conn=self.conn)
        pm.adjust_inventory(self.product_id, self.loc2, 10, db_conn=self.conn)
        success = pm.transfer_inventory(self.product_id, self.loc1, self.loc2, 20, db_conn=self.conn)
        self.assertTrue(success)
        self.assertEqual(pm.get_inventory_at_location(self.product_id, self.loc1, db_conn=self.conn)['quantity'], 30)
        self.assertEqual(pm.get_inventory_at_location(self.product_id, self.loc2, db_conn=self.conn)['quantity'], 30)

    def test_transfer_inventory_insufficient_stock(self):
        pm.adjust_inventory(self.product_id, self.loc1, 10, db_conn=self.conn)
        success = pm.transfer_inventory(self.product_id, self.loc1, self.loc2, 20, db_conn=self.conn)
        self.assertFalse(success)
        self.assertEqual(pm.get_inventory_at_location(self.product_id, self.loc1, db_conn=self.conn)['quantity'], 10)

    def test_check_low_stock(self):
        pm.adjust_inventory(self.product_id, self.loc1, 5, min_stock=10, db_conn=self.conn)
        pm.adjust_inventory(self.product_id, self.loc2, 20, min_stock=10, db_conn=self.conn)
        low_items = pm.check_low_stock(product_id=self.product_id, db_conn=self.conn)
        self.assertEqual(len(low_items), 1)
        self.assertEqual(low_items[0]['location_id'], self.loc1)
        low_loc1 = pm.check_low_stock(location_id=self.loc1, db_conn=self.conn)
        self.assertTrue(any(item['product_id'] == self.product_id and item['location_id'] == self.loc1 for item in low_loc1))
        not_low_loc2 = pm.check_low_stock(location_id=self.loc2, db_conn=self.conn)
        self.assertFalse(any(item['product_id'] == self.product_id and item['location_id'] == self.loc2 for item in not_low_loc2))

    def test_adjust_inventory_delta_zero(self):
        pm.adjust_inventory(self.product_id, self.loc1, 50, min_stock=10, db_conn=self.conn)
        rec = pm.adjust_inventory(self.product_id, self.loc1, 0, min_stock=12, db_conn=self.conn) # Delta 0, but update min_stock
        self.assertIsNotNone(rec)
        self.assertEqual(rec['quantity'], 50) # Quantity unchanged
        self.assertEqual(rec['min_stock'], 12) # Min_stock updated

    def test_transfer_inventory_to_new_location(self):
        pm.adjust_inventory(self.product_id, self.loc1, 50, db_conn=self.conn)
        loc_new = 300

        success = pm.transfer_inventory(self.product_id, self.loc1, loc_new, 20, db_conn=self.conn)
        self.assertTrue(success)
        self.assertEqual(pm.get_inventory_at_location(self.product_id, self.loc1, db_conn=self.conn)['quantity'], 30)
        new_loc_inv = pm.get_inventory_at_location(self.product_id, loc_new, db_conn=self.conn)
        self.assertIsNotNone(new_loc_inv)
        self.assertEqual(new_loc_inv['quantity'], 20)
        self.assertEqual(new_loc_inv['min_stock'], 0) # Default min_stock for new record in transfer

    def test_check_low_stock_min_stock_zero(self):
        pm.adjust_inventory(self.product_id, self.loc1, 5, min_stock=0, db_conn=self.conn)
        low_items = pm.check_low_stock(product_id=self.product_id, location_id=self.loc1, db_conn=self.conn)
        self.assertEqual(len(low_items), 0, "Should not be low stock if min_stock is 0 and quantity is >= 0")

        pm.adjust_inventory(self.product_id, self.loc2, 0, min_stock=0, db_conn=self.conn)
        low_items_zero_qty = pm.check_low_stock(product_id=self.product_id, location_id=self.loc2, db_conn=self.conn)
        self.assertEqual(len(low_items_zero_qty), 0)


class TestVendorIntegration(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.product_id = pm.create_product({'sku': 'VENDPROD', 'name': 'Vendor Product'}, db_conn=self.conn)
        self.vendor1 = 9001
        self.vendor2 = 9002

    def test_link_product_to_vendor_create_and_update(self):
        link1_id = pm.link_product_to_vendor({
            'product_id': self.product_id, 'vendor_id': self.vendor1,
            'vendor_sku': 'V1SKU', 'lead_time': 10, 'last_price': 5.00
        }, db_conn=self.conn)
        self.assertIsNotNone(link1_id)
        vendors = pm.get_vendors_for_product(self.product_id, db_conn=self.conn)
        self.assertEqual(vendors[0]['vendor_sku'], 'V1SKU')

        link1_updated_id = pm.link_product_to_vendor({
            'product_id': self.product_id, 'vendor_id': self.vendor1,
            'vendor_sku': 'V1SKU-UPD', 'last_price': 4.50
        }, db_conn=self.conn)
        self.assertEqual(link1_updated_id, link1_id)
        vendors = pm.get_vendors_for_product(self.product_id, db_conn=self.conn)
        self.assertEqual(vendors[0]['vendor_sku'], 'V1SKU-UPD')
        self.assertEqual(vendors[0]['last_price'], 4.50)
        self.assertIsNone(vendors[0]['lead_time'])

    def test_update_product_vendor_link_by_id(self):
        link_id = pm.link_product_to_vendor({
            'product_id': self.product_id, 'vendor_id': self.vendor1, 'lead_time': 10
        }, db_conn=self.conn)
        success = pm.update_product_vendor_link(link_id, {'lead_time': 7, 'last_price': 3.99}, db_conn=self.conn)
        self.assertTrue(success)
        vendor_link = pm.get_vendors_for_product(self.product_id, db_conn=self.conn)[0]
        self.assertEqual(vendor_link['lead_time'], 7)
        self.assertEqual(vendor_link['last_price'], 3.99)

    def test_remove_product_vendor_link(self):
        link_id = pm.link_product_to_vendor({'product_id': self.product_id, 'vendor_id': self.vendor1}, db_conn=self.conn)
        self.assertTrue(pm.remove_product_vendor_link(link_id, db_conn=self.conn))
        self.assertEqual(len(pm.get_vendors_for_product(self.product_id, db_conn=self.conn)), 0)

    def test_get_preferred_vendor(self):
        pm.link_product_to_vendor({
            'product_id': self.product_id, 'vendor_id': self.vendor1,
            'last_price': 5.00, 'lead_time': 10
        }, db_conn=self.conn)
        pm.link_product_to_vendor({
            'product_id': self.product_id, 'vendor_id': self.vendor2,
            'last_price': 5.50, 'lead_time': 5
        }, db_conn=self.conn)
        preferred = pm.get_preferred_vendor(self.product_id, db_conn=self.conn)
        self.assertEqual(preferred['vendor_id'], self.vendor1)

        link_v2_id = [v['id'] for v in pm.get_vendors_for_product(self.product_id, db_conn=self.conn) if v['vendor_id'] == self.vendor2][0]
        pm.update_product_vendor_link(link_v2_id, {'last_price': 4.50}, db_conn=self.conn)
        preferred = pm.get_preferred_vendor(self.product_id, db_conn=self.conn)
        self.assertEqual(preferred['vendor_id'], self.vendor2)

        pm.update_product_vendor_link(link_v2_id, {'last_price': 5.00}, db_conn=self.conn)
        preferred = pm.get_preferred_vendor(self.product_id, db_conn=self.conn)
        self.assertEqual(preferred['vendor_id'], self.vendor2)

    def test_get_products_for_vendor(self):
        product2_id = pm.create_product({'sku': 'VENDPROD2', 'name': 'Vendor Product 2'}, db_conn=self.conn)
        pm.link_product_to_vendor({'product_id': self.product_id, 'vendor_id': self.vendor1}, db_conn=self.conn)
        pm.link_product_to_vendor({'product_id': product2_id, 'vendor_id': self.vendor1}, db_conn=self.conn)
        pm.link_product_to_vendor({'product_id': self.product_id, 'vendor_id': self.vendor2}, db_conn=self.conn)

        v1_products = pm.get_products_for_vendor(self.vendor1, db_conn=self.conn)
        self.assertEqual(len(v1_products), 2)
        self.assertTrue(any(p['product_id'] == self.product_id for p in v1_products))
        self.assertTrue(any(p['product_id'] == product2_id for p in v1_products))

        v2_products = pm.get_products_for_vendor(self.vendor2, db_conn=self.conn)
        self.assertEqual(len(v2_products), 1)
        self.assertEqual(v2_products[0]['product_id'], self.product_id)

    def test_link_product_to_non_existent_product(self):
        link_id = pm.link_product_to_vendor({
            'product_id': 99999, 'vendor_id': self.vendor1, 'vendor_sku': 'GHOSTPROD'
        }, db_conn=self.conn)
        self.assertIsNone(link_id, "Should not link to non-existent product")

    def test_get_preferred_vendor_multiple_identical_best(self):
        # V1 and V2 have same best price and lead time
        pm.link_product_to_vendor({
            'product_id': self.product_id, 'vendor_id': self.vendor1,
            'last_price': 4.00, 'lead_time': 5
        }, db_conn=self.conn)
        pm.link_product_to_vendor({ # Link ID will be higher for this one
            'product_id': self.product_id, 'vendor_id': self.vendor2,
            'last_price': 4.00, 'lead_time': 5
        }, db_conn=self.conn)

        preferred = pm.get_preferred_vendor(self.product_id, db_conn=self.conn)
        # Tie-breaker is link ID ascending, so the first one linked (vendor1 here if its link ID is lower)
        # The get_vendors_for_product sorts by id ASC as the final tie-breaker.
        # Assuming vendor1 was linked first, its ID would be lower.
        self.assertIsNotNone(preferred)
        # This assertion depends on the auto-increment ID behavior.
        # If vendor1's link_id is indeed lower than vendor2's link_id.
        # Let's get them to confirm
        v1_link = next(v for v in pm.get_vendors_for_product(self.product_id, db_conn=self.conn) if v['vendor_id'] == self.vendor1)
        v2_link = next(v for v in pm.get_vendors_for_product(self.product_id, db_conn=self.conn) if v['vendor_id'] == self.vendor2)

        if v1_link['id'] < v2_link['id']:
            self.assertEqual(preferred['vendor_id'], self.vendor1, "Vendor with lower link ID should be preferred on tie")
        else:
            self.assertEqual(preferred['vendor_id'], self.vendor2, "Vendor with lower link ID should be preferred on tie")


    def test_get_preferred_vendor_null_prices_or_lead_times(self):
        pm.link_product_to_vendor({ # Only lead time
            'product_id': self.product_id, 'vendor_id': self.vendor1, 'lead_time': 5
        }, db_conn=self.conn)
        pm.link_product_to_vendor({ # Only price
            'product_id': self.product_id, 'vendor_id': self.vendor2, 'last_price': 10.00
        }, db_conn=self.conn)

        preferred = pm.get_preferred_vendor(self.product_id, db_conn=self.conn)
        # Vendor2 should be preferred as it has a price, and price is the primary sort key (NULLs last)
        self.assertIsNotNone(preferred)
        self.assertEqual(preferred['vendor_id'], self.vendor2)

        # Clear V2's price, now V1 should be preferred (shorter lead time, V2 lead time is NULL)
        v2_link_id = next(v['id'] for v in pm.get_vendors_for_product(self.product_id, db_conn=self.conn) if v['vendor_id'] == self.vendor2)
        pm.update_product_vendor_link(v2_link_id, {'last_price': None}, db_conn=self.conn)

        preferred_after_null_price = pm.get_preferred_vendor(self.product_id, db_conn=self.conn)
        self.assertIsNotNone(preferred_after_null_price)
        self.assertEqual(preferred_after_null_price['vendor_id'], self.vendor1, "V1 should be preferred (has lead time, V2 price is null, V2 lead time is null)")

class TestIntegrationScenarios(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.product_id_integration = pm.create_product({
            'sku': 'INTEG-001',
            'name': 'Integration Test Product',
            'unit_of_measure': 'EA'
        }, db_conn=self.conn)
        self.assertIsNotNone(self.product_id_integration, "Failed to create product for integration tests")

        self.location_id_main_wh = 501 # Main Warehouse

    def test_purchase_order_increases_inventory(self):
        """Simulate a purchase order receipt increasing inventory."""
        po_quantity = 50

        initial_inv_record = pm.get_inventory_at_location(self.product_id_integration, self.location_id_main_wh, db_conn=self.conn)
        initial_quantity = initial_inv_record['quantity'] if initial_inv_record else 0
        self.assertEqual(initial_quantity, 0, "Initial quantity should be 0 before PO receipt")

        updated_inv_record = pm.adjust_inventory(
            self.product_id_integration,
            self.location_id_main_wh,
            po_quantity,
            min_stock=10,
            max_stock=200,
            db_conn=self.conn
        )

        self.assertIsNotNone(updated_inv_record, "Inventory adjustment for PO failed")
        self.assertEqual(updated_inv_record['quantity'], po_quantity, "Inventory not increased correctly after PO")

        final_inv_record = pm.get_inventory_at_location(self.product_id_integration, self.location_id_main_wh, db_conn=self.conn)
        self.assertEqual(final_inv_record['quantity'], po_quantity, "Inventory quantity mismatch after PO when re-fetched")
        self.assertEqual(final_inv_record['min_stock'], 10)

    def test_sales_order_deducts_inventory(self):
        """Simulate a sales order fulfillment deducting inventory and checking low stock."""
        initial_stock = 100
        sale_quantity = 75
        min_stock_level = 30

        pm.adjust_inventory(
            self.product_id_integration,
            self.location_id_main_wh,
            initial_stock,
            min_stock=min_stock_level,
            max_stock=200,
            db_conn=self.conn
        )

        updated_inv_record = pm.adjust_inventory(
            self.product_id_integration,
            self.location_id_main_wh,
            -sale_quantity,
            db_conn=self.conn
        )

        expected_quantity_after_sale = initial_stock - sale_quantity
        self.assertIsNotNone(updated_inv_record, "Inventory adjustment for Sale failed")
        self.assertEqual(updated_inv_record['quantity'], expected_quantity_after_sale, "Inventory not deducted correctly after Sale")
        self.assertEqual(updated_inv_record['min_stock'], min_stock_level, "Min stock level should be preserved")

        final_inv_record = pm.get_inventory_at_location(self.product_id_integration, self.location_id_main_wh, db_conn=self.conn)
        self.assertEqual(final_inv_record['quantity'], expected_quantity_after_sale)

        is_low_stock = final_inv_record['quantity'] < final_inv_record['min_stock']
        self.assertTrue(is_low_stock, "Product should be marked as low stock")

        low_stock_alerts = pm.check_low_stock(product_id=self.product_id_integration, location_id=self.location_id_main_wh, db_conn=self.conn)
        self.assertEqual(len(low_stock_alerts), 1, "check_low_stock should report this item as low")
        self.assertEqual(low_stock_alerts[0]['product_id'], self.product_id_integration)
        self.assertEqual(low_stock_alerts[0]['location_id'], self.location_id_main_wh)

    def test_sales_order_fails_if_insufficient_stock(self):
        """Simulate a sales order that cannot be fulfilled due to insufficient stock."""
        initial_stock = 20
        sale_quantity = 25

        pm.adjust_inventory(
            self.product_id_integration,
            self.location_id_main_wh,
            initial_stock,
            db_conn=self.conn
        )

        updated_inv_record = pm.adjust_inventory(
            self.product_id_integration,
            self.location_id_main_wh,
            -sale_quantity,
            db_conn=self.conn
        )

        self.assertIsNone(updated_inv_record, "Inventory adjustment should fail for insufficient stock")

        final_inv_record = pm.get_inventory_at_location(self.product_id_integration, self.location_id_main_wh, db_conn=self.conn)
        self.assertEqual(final_inv_record['quantity'], initial_stock, "Inventory should be unchanged after failed deduction")

if __name__ == '__main__':
    unittest.main(verbosity=2)

class TestIntegrationScenarios(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.product_id_integration = pm.create_product({
            'sku': 'INTEG-001',
            'name': 'Integration Test Product',
            'unit_of_measure': 'EA'
        }, db_conn=self.conn)
        self.assertIsNotNone(self.product_id_integration, "Failed to create product for integration tests")

        self.location_id_main_wh = 501 # Main Warehouse

    def test_purchase_order_increases_inventory(self):
        """Simulate a purchase order receipt increasing inventory."""
        po_quantity = 50

        # Initially, no inventory record should exist or quantity is 0
        initial_inv_record = pm.get_inventory_at_location(self.product_id_integration, self.location_id_main_wh, db_conn=self.conn)
        initial_quantity = initial_inv_record['quantity'] if initial_inv_record else 0
        self.assertEqual(initial_quantity, 0, "Initial quantity should be 0 before PO receipt")

        # Simulate PO receipt: adjust inventory upwards
        updated_inv_record = pm.adjust_inventory(
            self.product_id_integration,
            self.location_id_main_wh,
            po_quantity,
            min_stock=10, # Set some min/max for completeness
            max_stock=200,
            db_conn=self.conn
        )

        self.assertIsNotNone(updated_inv_record, "Inventory adjustment for PO failed")
        self.assertEqual(updated_inv_record['quantity'], po_quantity, "Inventory not increased correctly after PO")

        # Verify by fetching again
        final_inv_record = pm.get_inventory_at_location(self.product_id_integration, self.location_id_main_wh, db_conn=self.conn)
        self.assertEqual(final_inv_record['quantity'], po_quantity, "Inventory quantity mismatch after PO when re-fetched")
        self.assertEqual(final_inv_record['min_stock'], 10) # Check min_stock was set

    def test_sales_order_deducts_inventory(self):
        """Simulate a sales order fulfillment deducting inventory and checking low stock."""
        initial_stock = 100
        sale_quantity = 75
        min_stock_level = 30 # Sale should make it go below this if initial stock is 100 and sale is 75 (leaves 25)

        # Setup: Initial stock
        pm.adjust_inventory(
            self.product_id_integration,
            self.location_id_main_wh,
            initial_stock,
            min_stock=min_stock_level,
            max_stock=200,
            db_conn=self.conn
        )

        # Simulate Sale: adjust inventory downwards
        updated_inv_record = pm.adjust_inventory(
            self.product_id_integration,
            self.location_id_main_wh,
            -sale_quantity, # Negative delta for deduction
            db_conn=self.conn
            # Not re-setting min/max here, should use existing
        )

        expected_quantity_after_sale = initial_stock - sale_quantity
        self.assertIsNotNone(updated_inv_record, "Inventory adjustment for Sale failed")
        self.assertEqual(updated_inv_record['quantity'], expected_quantity_after_sale, "Inventory not deducted correctly after Sale")
        self.assertEqual(updated_inv_record['min_stock'], min_stock_level, "Min stock level should be preserved")

        # Verify by fetching again
        final_inv_record = pm.get_inventory_at_location(self.product_id_integration, self.location_id_main_wh, db_conn=self.conn)
        self.assertEqual(final_inv_record['quantity'], expected_quantity_after_sale)

        # Check for low stock alert condition
        is_low_stock = final_inv_record['quantity'] < final_inv_record['min_stock']

        # In this specific scenario: 100 - 75 = 25. min_stock_level = 30. So, it IS low stock.
        self.assertTrue(is_low_stock, "Product should be marked as low stock")

        # Verify with check_low_stock function
        low_stock_alerts = pm.check_low_stock(product_id=self.product_id_integration, location_id=self.location_id_main_wh, db_conn=self.conn)
        self.assertEqual(len(low_stock_alerts), 1, "check_low_stock should report this item as low")
        self.assertEqual(low_stock_alerts[0]['product_id'], self.product_id_integration)
        self.assertEqual(low_stock_alerts[0]['location_id'], self.location_id_main_wh)

    def test_sales_order_fails_if_insufficient_stock(self):
        """Simulate a sales order that cannot be fulfilled due to insufficient stock."""
        initial_stock = 20
        sale_quantity = 25 # More than available

        pm.adjust_inventory(
            self.product_id_integration,
            self.location_id_main_wh,
            initial_stock,
            db_conn=self.conn
        )

        # Attempt to deduct more than available
        updated_inv_record = pm.adjust_inventory(
            self.product_id_integration,
            self.location_id_main_wh,
            -sale_quantity,
            db_conn=self.conn
        )

        self.assertIsNone(updated_inv_record, "Inventory adjustment should fail for insufficient stock")

        # Verify stock remains unchanged
        final_inv_record = pm.get_inventory_at_location(self.product_id_integration, self.location_id_main_wh, db_conn=self.conn)
        self.assertEqual(final_inv_record['quantity'], initial_stock, "Inventory should be unchanged after failed deduction")
