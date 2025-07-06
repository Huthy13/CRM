import tkinter as tk
from tkinter import ttk, messagebox
from ui.task_popup import TaskDetailsPopup
from shared.structs import TaskStatus, TaskPriority # For potential direct use, though logic layer should handle most

import datetime # Import the datetime module

class TaskTab(tk.Frame): # Inherit from tk.Frame directly
    def __init__(self, master, logic):
        super().__init__(master) # Initialize the Frame
        self.logic = logic
        self.selected_task_id = None

        self.setup_task_tab()
        self.load_tasks()

        # Optional: Bind FocusIn to reload if needed, similar to AccountTab
        # self.bind("<FocusIn>", lambda event: self.load_tasks())


    def setup_task_tab(self):
        """Setup the Task Management tab with task fields and task list."""

        # Top frame for buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=5, padx=5)

        button_width = 20 # Consistent button width

        self.add_task_button = ttk.Button(
            button_frame, text="Add New Task",
            command=self.create_new_task, width=button_width)
        self.add_task_button.pack(side=tk.LEFT, padx=5)

        self.edit_task_button = ttk.Button(
            button_frame, text="Edit Task",
            command=self.edit_existing_task, width=button_width)
        self.edit_task_button.pack(side=tk.LEFT, padx=5)

        self.delete_task_button = ttk.Button(
            button_frame, text="Delete Task",
            command=self.remove_task, width=button_width)
        self.delete_task_button.pack(side=tk.LEFT, padx=5)

        self.complete_task_button = ttk.Button(
            button_frame, text="Mark Completed",
            command=self.mark_task_completed, width=button_width)
        self.complete_task_button.pack(side=tk.LEFT, padx=5)


        # Treeview for displaying tasks
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("id", "title", "due_date", "status", "priority", "company", "contact", "assigned_user")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        self.tree.column("id", width=0, stretch=False) # Hidden ID column
        self.tree.heading("title", text="Title", command=lambda: self.sort_column("title", False))
        self.tree.heading("due_date", text="Due Date", command=lambda: self.sort_column("due_date", False))
        self.tree.heading("status", text="Status", command=lambda: self.sort_column("status", False))
        self.tree.heading("priority", text="Priority", command=lambda: self.sort_column("priority", False))
        self.tree.heading("company", text="Company", command=lambda: self.sort_column("company", False))
        self.tree.heading("contact", text="Contact", command=lambda: self.sort_column("contact", False))
        self.tree.heading("assigned_user", text="Assigned To", command=lambda: self.sort_column("assigned_user", False))

        self.tree.column("title", width=200)
        self.tree.column("due_date", width=100)
        self.tree.column("status", width=100)
        self.tree.column("priority", width=80)
        self.tree.column("company", width=120)
        self.tree.column("contact", width=120)
        self.tree.column("assigned_user", width=100)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.select_task)

        # Configure resizing for the tree_frame and the tree itself within this tab
        # The TaskTab (self) is a Frame, its parent (notebook) will handle its expansion.
        # We need to make sure tree_frame expands within TaskTab.
        # And the tree expands within tree_frame.
        # Since tree_frame uses pack fill=BOTH, expand=True, it should handle its part.
        # The tree itself is packed into tree_frame also with fill=BOTH, expand=True.
        # This setup should inherently support resizing if the parent tab in the notebook resizes.

    def sort_column(self, col, reverse):
        """Sort the Treeview column when clicked."""
        try:
            # For date sorting, it's better to convert to actual date objects if possible
            if col == "due_date":
                data = []
                for k in self.tree.get_children(""):
                    date_str = self.tree.set(k, col)
                    try:
                        # Attempt to parse date for proper sorting, handle potential errors
                        parsed_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                        data.append((parsed_date, k))
                    except ValueError:
                        data.append((date_str, k)) # Fallback to string sort if format is unexpected
            else:
                data = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]

            data.sort(key=lambda item: item[0], reverse=reverse)

            for index, (val, k) in enumerate(data):
                self.tree.move(k, "", index)
            self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))
        except Exception as e:
            print(f"Error sorting column {col}: {e}")


    def create_new_task(self):
        # Pass `self` as master so popup can call `self.load_tasks()`
        TaskDetailsPopup(self, self.logic, task_id=None)

    def edit_existing_task(self):
        if not self.selected_task_id:
            messagebox.showwarning("No Selection", "Please select a task to edit.")
            return
        TaskDetailsPopup(self, self.logic, task_id=self.selected_task_id)

    def remove_task(self):
        if not self.selected_task_id:
            messagebox.showwarning("No Selection", "Please select a task to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this task?", parent=self)
        if confirm:
            try:
                self.logic.delete_task_by_id(self.selected_task_id) # Defaults to soft delete
                self.load_tasks()
                self.selected_task_id = None # Clear selection
                messagebox.showinfo("Success", "Task deleted successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete task: {e}")

    def mark_task_completed(self):
        if not self.selected_task_id:
            messagebox.showwarning("No Selection", "Please select a task to mark as completed.")
            return
        try:
            self.logic.mark_task_completed(self.selected_task_id)
            self.load_tasks()
            messagebox.showinfo("Success", "Task marked as completed.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mark task as completed: {e}")


    def load_tasks(self):
        """Load tasks into the Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            tasks = self.logic.get_all_tasks() # This should return list of Task objects

            # For displaying company, contact, user names, we might need to fetch them
            # This can be inefficient if done per task.
            # Consider if logic.get_all_tasks could return enriched data, or cache lookups.
            # For now, let's assume we can get names or make placeholder calls.

            # Pre-fetch related data to avoid multiple DB calls in a loop (conceptual)
            # Pre-fetch related data to avoid multiple DB calls in a loop
            accounts_list = self.logic.get_accounts() # list of (id, name)
            accounts_map = {acc_id: acc_name for acc_id, acc_name in accounts_list}

            contacts_list = self.logic.get_all_contacts() # list of Contact objects
            contacts_map = {contact.contact_id: contact.name for contact in contacts_list}

            users_list = []
            if hasattr(self.logic, 'get_all_users'): # Check if method exists
                users_list = self.logic.get_all_users() # list of (id, username)
            users_map = {user_id: username for user_id, username in users_list}


            for task in tasks:
                company_name = accounts_map.get(task.company_id, "N/A") if task.company_id else "N/A"
                contact_name = contacts_map.get(task.contact_id, "N/A") if task.contact_id else "N/A"
                assigned_user_name = users_map.get(task.assigned_to_user_id, "N/A") if task.assigned_to_user_id else "N/A"

                due_date_str = task.due_date.strftime('%Y-%m-%d') if task.due_date else "N/A"

                self.tree.insert("", "end", values=(
                    task.task_id,
                    task.title,
                    due_date_str,
                    task.status.value if task.status else "N/A",
                    task.priority.value if task.priority else "N/A",
                    company_name,
                    contact_name,
                    assigned_user_name
                ))
        except Exception as e:
            messagebox.showerror("Error Loading Tasks", f"An error occurred: {e}")
            print(f"Error loading tasks: {e}") # For console debugging


    def select_task(self, event=None):
        """Store the ID of the selected task."""
        selected_item = self.tree.selection()
        if selected_item:
            self.selected_task_id = self.tree.item(selected_item[0], 'values')[0]
            # print(f"Selected Task ID: {self.selected_task_id}") # For debugging
        else:
            self.selected_task_id = None

if __name__ == '__main__':
    # For standalone testing of TaskTab
    import datetime

    class MockLogic:
        def get_all_tasks(self):
            # Return a list of mock Task objects
            return [
                Task(task_id=1, title="Test Task 1", due_date=datetime.date(2024, 7, 15), status=TaskStatus.OPEN, priority=TaskPriority.HIGH, company_id=1, contact_id=10, assigned_to_user_id=100, created_by_user_id=1, created_at=datetime.datetime.now()),
                Task(task_id=2, title="Another Task - Follow up", due_date=datetime.date(2024, 7, 20), status=TaskStatus.IN_PROGRESS, priority=TaskPriority.MEDIUM, company_id=2, created_by_user_id=1, created_at=datetime.datetime.now()),
                Task(task_id=3, title="Check on Proposal", due_date=datetime.date(2024, 6, 30), status=TaskStatus.OVERDUE, created_by_user_id=1, created_at=datetime.datetime.now())
            ]
        def get_account_details(self, acc_id): # Mock
            if acc_id == 1: return type('Account', (), {'name': 'Company Alpha'})()
            if acc_id == 2: return type('Account', (), {'name': 'Company Beta'})()
            return None
        def get_contact_details(self, con_id): # Mock
            if con_id == 10: return type('Contact', (), {'name': 'John Doe'})()
            return None
        # Mock other methods needed by popup or tab actions
        def delete_task_by_id(self, task_id): print(f"Mock: Delete task {task_id}")
        def mark_task_completed(self, task_id): print(f"Mock: Mark task {task_id} completed")
        def get_task_details(self, task_id): # For popup edit
            if task_id == 1: return self.get_all_tasks()[0]
            return None
        def get_accounts(self): return [(1, "Company Alpha"), (2, "Company Beta")]
        def get_all_contacts(self): return [type('obj', (object,), {'contact_id': 10, 'name': 'John Doe'})()]
        # get_all_users would be needed for the popup's assigned user dropdown
        def get_all_users(self): return [(100, "TestUser")]


    root = tk.Tk()
    root.title("Task Tab Test")
    root.geometry("800x600")

    mock_logic_instance = MockLogic()
    task_tab_view = TaskTab(root, mock_logic_instance)
    task_tab_view.pack(fill=tk.BOTH, expand=True)

    root.mainloop()
