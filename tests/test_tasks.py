import unittest
import datetime
from core.logic import AddressBookLogic
from core.database import DatabaseHandler
from shared.structs import Task, TaskStatus, TaskPriority, Account # Import Account for creating associated company

class TestTaskLogic(unittest.TestCase):

    def setUp(self):
        """Set up an in-memory SQLite database and logic handler for each test."""
        # Using db_name=':memory:' ensures a fresh DB for each test method if DatabaseHandler creates a new conn.
        # If it reuses a class-level conn, then manual reset or careful test design is needed.
        # Based on current DatabaseHandler, ':memory:' gives a distinct in-memory DB.
        self.db_handler = DatabaseHandler(db_name=':memory:')
        self.logic = AddressBookLogic(self.db_handler)

        # Create a default user if one doesn't exist, as tasks require created_by_user_id
        # The main db handler already does this, but for tests, good to ensure.
        try:
            self.db_handler.cursor.execute("INSERT INTO users (username) VALUES (?)", ('test_user',))
            self.db_handler.conn.commit()
        except self.db_handler.conn.IntegrityError:
            pass # User 'test_user' or 'system_user' likely already exists

        self.test_user_id = self.db_handler.get_user_id_by_username('test_user')
        if not self.test_user_id:
             self.test_user_id = self.db_handler.get_user_id_by_username('system_user')


    def tearDown(self):
        """Close the database connection after each test."""
        self.db_handler.close()

    def _create_dummy_task_obj(self, title="Test Task", days_offset=1, company_id=None, contact_id=None, status=TaskStatus.OPEN, priority=TaskPriority.MEDIUM, assigned_to_user_id=None) -> Task:
        due_date = datetime.date.today() + datetime.timedelta(days=days_offset)
        return Task(
            title=title,
            description="Test description",
            due_date=due_date,
            company_id=company_id,
            contact_id=contact_id,
            status=status, # Will be overridden by create_task to OPEN initially
            priority=priority,
            assigned_to_user_id=assigned_to_user_id,
            created_by_user_id=self.test_user_id
        )

    def test_task_creation_valid(self):
        """Test task creation with valid inputs."""
        task_obj = self._create_dummy_task_obj(title="Valid Task")
        created_task = self.logic.create_task(task_obj)

        self.assertIsNotNone(created_task.task_id)
        self.assertEqual(created_task.title, "Valid Task")
        self.assertEqual(created_task.status, TaskStatus.OPEN) # Auto-set by create_task
        self.assertIsNotNone(created_task.created_at)
        self.assertIsNotNone(created_task.updated_at)
        self.assertEqual(created_task.created_by_user_id, self.test_user_id)

    def test_task_creation_invalid_input(self):
        """Test task creation with invalid inputs (e.g., missing title)."""
        with self.assertRaises(ValueError, msg="Task title cannot be empty."):
            Task(title="", due_date=datetime.date.today()) # Direct Task init validation

        # Test create_task pathway if it adds more validation (currently doesn't beyond Task init)
        # For example, if create_task itself checked for empty title:
        # invalid_task_obj = self._create_dummy_task_obj()
        # invalid_task_obj.title = "" # This would be caught by Task.__init__
        # with self.assertRaises(ValueError):
        #    self.logic.create_task(invalid_task_obj)


    def test_get_task_details(self):
        """Test retrieving a task by its ID."""
        task_obj = self._create_dummy_task_obj(title="Detail Test Task")
        created_task = self.logic.create_task(task_obj)

        retrieved_task = self.logic.get_task_details(created_task.task_id)
        self.assertIsNotNone(retrieved_task)
        self.assertEqual(retrieved_task.title, "Detail Test Task")
        self.assertEqual(retrieved_task.task_id, created_task.task_id)

    def test_update_task(self):
        """Test updating various fields of a task."""
        task_obj = self._create_dummy_task_obj(title="Original Title")
        created_task = self.logic.create_task(task_obj)
        original_updated_at = created_task.updated_at

        created_task.title = "Updated Title"
        created_task.priority = TaskPriority.HIGH
        created_task.status = TaskStatus.IN_PROGRESS # Example of direct status change before update

        # Simulate a slight delay for updated_at comparison
        import time
        time.sleep(0.01)

        updated_task = self.logic.update_task_details(created_task)

        self.assertEqual(updated_task.title, "Updated Title")
        self.assertEqual(updated_task.priority, TaskPriority.HIGH)
        self.assertEqual(updated_task.status, TaskStatus.IN_PROGRESS)
        self.assertGreater(updated_task.updated_at, original_updated_at)

    def test_delete_task_soft(self):
        """Test soft deleting a task."""
        task_obj = self._create_dummy_task_obj(title="To Be Soft Deleted")
        created_task = self.logic.create_task(task_obj)
        task_id = created_task.task_id

        self.logic.delete_task_by_id(task_id, soft_delete=True)

        # Should not be retrievable by normal get
        retrieved_task = self.logic.get_task_details(task_id)
        self.assertIsNone(retrieved_task)

        # Verify it's marked as deleted in DB if we were to query with include_deleted
        # For now, this is tested by asserting it's not found by standard get.
        # To fully test, one might add a db_handler.get_task(task_id, include_deleted=True)
        # and check the is_deleted flag.

    def test_delete_task_hard(self):
        """Test hard deleting a task."""
        task_obj = self._create_dummy_task_obj(title="To Be Hard Deleted")
        created_task = self.logic.create_task(task_obj)
        task_id = created_task.task_id

        self.logic.delete_task_by_id(task_id, soft_delete=False)

        retrieved_task = self.logic.get_task_details(task_id)
        self.assertIsNone(retrieved_task)

        # Also check in DB directly (optional, depends on how much to trust the ORM-like layer)
        raw_task = self.db_handler.get_task(task_id) # db_handler.get_task respects is_deleted=0
        self.assertIsNone(raw_task)


    def test_status_transitions(self):
        """Verify proper status transitions (e.g., Open -> Completed)."""
        task_obj = self._create_dummy_task_obj(title="Status Transition Task")
        task = self.logic.create_task(task_obj)
        self.assertEqual(task.status, TaskStatus.OPEN)

        task.status = TaskStatus.IN_PROGRESS
        task = self.logic.update_task_details(task)
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)

        completed_task = self.logic.mark_task_completed(task.task_id)
        self.assertEqual(completed_task.status, TaskStatus.COMPLETED)

        # Try to mark completed again (should remain completed)
        completed_again_task = self.logic.mark_task_completed(task.task_id)
        self.assertEqual(completed_again_task.status, TaskStatus.COMPLETED)


    def test_overdue_logic(self):
        """Test overdue logic and sorting by due date."""
        # Task due yesterday, should become overdue
        overdue_task_obj = self._create_dummy_task_obj(title="Overdue Task", days_offset=-1)
        overdue_task = self.logic.create_task(overdue_task_obj)

        # Task due tomorrow, should not be overdue
        future_task_obj = self._create_dummy_task_obj(title="Future Task", days_offset=1)
        self.logic.create_task(future_task_obj)

        # Task due yesterday but already completed, should not become overdue
        completed_past_due_obj = self._create_dummy_task_obj(title="Completed Past Due", days_offset=-2)
        completed_past_due_task = self.logic.create_task(completed_past_due_obj)
        self.logic.mark_task_completed(completed_past_due_task.task_id)

        updated_count = self.logic.check_and_update_overdue_tasks()
        self.assertEqual(updated_count, 1, "Only one task should have been updated to Overdue")

        retrieved_overdue_task = self.logic.get_task_details(overdue_task.task_id)
        self.assertEqual(retrieved_overdue_task.status, TaskStatus.OVERDUE)

        retrieved_completed_task = self.logic.get_task_details(completed_past_due_task.task_id)
        self.assertEqual(retrieved_completed_task.status, TaskStatus.COMPLETED)


    def test_filtering_and_sorting_tasks(self):
        """Confirm filtering by status, user, priority, and sorting by due date."""
        # Create a company to associate tasks with
        billing_addr_id = self.logic.add_address("123 Billing St", "Test City", "TS", "12345", "TC")
        company = Account(name="Test Company For Tasks", phone="111-222-3333", billing_address_id=billing_addr_id)
        self.logic.save_account(company) # save_account in logic should handle db interaction
        # Retrieve the company to get its ID
        # This assumes get_accounts() returns (id, name) and it's the latest one.
        # A more robust way would be get_account_by_name or similar if it existed.
        all_db_accounts = self.db_handler.get_accounts() # Direct DB call to get (id, name)
        test_company_id = None
        for acc_id, acc_name in all_db_accounts:
            if acc_name == "Test Company For Tasks":
                test_company_id = acc_id
                break
        self.assertIsNotNone(test_company_id, "Test company was not created or found correctly.")


        user1_id = self.test_user_id
        user2_id = self.db_handler.get_user_id_by_username('system_user') # Assuming another user
        if not user2_id or user1_id == user2_id: # Create another user if needed
             self.db_handler.cursor.execute("INSERT INTO users (username) VALUES (?)", ('another_test_user',))
             self.db_handler.conn.commit()
             user2_id = self.db_handler.get_user_id_by_username('another_test_user')
        self.assertNotEqual(user1_id, user2_id, "Need two distinct users for testing assignment.")


        # Task 1 (Company, User1, High, Due Today)
        task1_obj = self._create_dummy_task_obj("Task1-C1-U1-H", days_offset=0, company_id=test_company_id, priority=TaskPriority.HIGH, assigned_to_user_id=user1_id)
        self.logic.create_task(task1_obj)
        # Task 2 (User2, Medium, Due Tomorrow)
        task2_obj = self._create_dummy_task_obj("Task2-U2-M", days_offset=1, priority=TaskPriority.MEDIUM, assigned_to_user_id=user2_id)
        self.logic.create_task(task2_obj)
        # Task 3 (Company, User1, Low, Due Yesterday, will become Overdue)
        task3_obj = self._create_dummy_task_obj("Task3-C1-U1-L", days_offset=-1, company_id=test_company_id, priority=TaskPriority.LOW, assigned_to_user_id=user1_id)
        self.logic.create_task(task3_obj)

        # Mark Task 2 as In Progress
        tasks_u2_medium = self.logic.get_all_tasks(assigned_user_id=user2_id, priority=TaskPriority.MEDIUM)
        task2_retrieved = tasks_u2_medium[0]
        task2_retrieved.status = TaskStatus.IN_PROGRESS
        self.logic.update_task_details(task2_retrieved)


        # Run overdue check to update Task 3 status
        self.logic.check_and_update_overdue_tasks()

        # Filter by company
        company_tasks = self.logic.get_all_tasks(company_id=test_company_id)
        self.assertEqual(len(company_tasks), 2)
        self.assertTrue(any(t.title == "Task1-C1-U1-H" for t in company_tasks))
        self.assertTrue(any(t.title == "Task3-C1-U1-L" for t in company_tasks))

        # Filter by assigned user
        user1_tasks = self.logic.get_all_tasks(assigned_user_id=user1_id)
        self.assertEqual(len(user1_tasks), 2)

        # Filter by priority
        high_priority_tasks = self.logic.get_all_tasks(priority=TaskPriority.HIGH)
        self.assertEqual(len(high_priority_tasks), 1)
        self.assertEqual(high_priority_tasks[0].title, "Task1-C1-U1-H")

        # Filter by status (Task 3 is Overdue, Task 2 is In Progress, Task 1 is Open)
        open_tasks = self.logic.get_all_tasks(status=TaskStatus.OPEN)
        self.assertEqual(len(open_tasks), 1)
        self.assertEqual(open_tasks[0].title, "Task1-C1-U1-H")

        overdue_tasks = self.logic.get_all_tasks(status=TaskStatus.OVERDUE)
        self.assertEqual(len(overdue_tasks), 1)
        self.assertEqual(overdue_tasks[0].title, "Task3-C1-U1-L")

        inprogress_tasks = self.logic.get_all_tasks(status=TaskStatus.IN_PROGRESS)
        self.assertEqual(len(inprogress_tasks), 1)
        self.assertEqual(inprogress_tasks[0].title, "Task2-U2-M")


        # Test sorting by due_date (default ASC)
        all_tasks_sorted_asc = self.logic.get_all_tasks(due_date_sort_order='ASC')
        self.assertEqual(all_tasks_sorted_asc[0].title, "Task3-C1-U1-L") # Due yesterday
        self.assertEqual(all_tasks_sorted_asc[1].title, "Task1-C1-U1-H") # Due today
        self.assertEqual(all_tasks_sorted_asc[2].title, "Task2-U2-M")   # Due tomorrow

        # Test sorting by due_date DESC
        all_tasks_sorted_desc = self.logic.get_all_tasks(due_date_sort_order='DESC')
        self.assertEqual(all_tasks_sorted_desc[0].title, "Task2-U2-M")   # Due tomorrow
        self.assertEqual(all_tasks_sorted_desc[1].title, "Task1-C1-U1-H") # Due today
        self.assertEqual(all_tasks_sorted_desc[2].title, "Task3-C1-U1-L") # Due yesterday

    # Permissions are conceptually tested by ensuring created_by_user_id and assigned_to_user_id are stored.
    # Actual enforcement (e.g. only assigned user can complete) would be in logic methods not yet specified to that level.

if __name__ == '__main__':
    unittest.main()
