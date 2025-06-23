import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from shared.structs import Task, TaskStatus, TaskPriority, Account, Contact # Assuming User struct will be added or handled

class TaskDetailsPopup(tk.Toplevel):
    def __init__(self, master, logic, task_id=None):
        super().__init__(master)
        self.logic = logic
        self.task_id = task_id
        self.task_data = None

        if self.task_id:
            self.title("Edit Task")
            self.task_data = self.logic.get_task_details(self.task_id)
            if not self.task_data:
                messagebox.showerror("Error", f"Task with ID {self.task_id} not found.")
                self.destroy()
                return
        else:
            self.title("Add New Task")

        self.geometry("450x550") # Adjusted size
        self.create_widgets()
        if self.task_data:
            self.populate_fields()

    def create_widgets(self):
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        row = 0
        ttk.Label(frame, text="Title:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.title_entry = ttk.Entry(frame, width=40)
        self.title_entry.grid(row=row, column=1, sticky=tk.EW, pady=2)
        row += 1

        ttk.Label(frame, text="Description:").grid(row=row, column=0, sticky=tk.NW, pady=2)
        self.description_text = tk.Text(frame, width=40, height=5)
        self.description_text.grid(row=row, column=1, sticky=tk.EW, pady=2)
        row += 1

        ttk.Label(frame, text="Due Date (YYYY-MM-DD):").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.due_date_entry = ttk.Entry(frame, width=40)
        self.due_date_entry.grid(row=row, column=1, sticky=tk.EW, pady=2)
        row += 1

        ttk.Label(frame, text="Status:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.status_var = tk.StringVar()
        self.status_combo = ttk.Combobox(frame, textvariable=self.status_var, state="readonly",
                                         values=[s.value for s in TaskStatus])
        self.status_combo.grid(row=row, column=1, sticky=tk.EW, pady=2)
        row += 1

        ttk.Label(frame, text="Priority:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.priority_var = tk.StringVar()
        self.priority_combo = ttk.Combobox(frame, textvariable=self.priority_var, state="readonly",
                                           values=[p.value for p in TaskPriority] + [""]) # Allow empty priority
        self.priority_combo.grid(row=row, column=1, sticky=tk.EW, pady=2)
        row += 1

        # Company Association
        ttk.Label(frame, text="Company:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.company_var = tk.StringVar()
        self.company_combo = ttk.Combobox(frame, textvariable=self.company_var, state="readonly")
        self.company_combo.grid(row=row, column=1, sticky=tk.EW, pady=2)
        self.populate_company_dropdown()
        row += 1

        # Contact Association
        ttk.Label(frame, text="Contact:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.contact_var = tk.StringVar()
        self.contact_combo = ttk.Combobox(frame, textvariable=self.contact_var, state="readonly")
        self.contact_combo.grid(row=row, column=1, sticky=tk.EW, pady=2)
        self.populate_contact_dropdown()
        row += 1

        # Assigned User
        ttk.Label(frame, text="Assigned User:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.assigned_user_var = tk.StringVar()
        self.assigned_user_combo = ttk.Combobox(frame, textvariable=self.assigned_user_var, state="readonly")
        self.assigned_user_combo.grid(row=row, column=1, sticky=tk.EW, pady=2)
        self.populate_assigned_user_dropdown() # Placeholder, depends on Step 3
        row += 1


        save_button = ttk.Button(frame, text="Save Task", command=self.save_task)
        save_button.grid(row=row, column=0, columnspan=2, pady=10)

        frame.columnconfigure(1, weight=1) # Allow entry widgets to expand

    def populate_company_dropdown(self):
        try:
            accounts_data = self.logic.get_accounts() # Returns list of (id, name) tuples
            self.company_options = {"": None} # Display name to ID mapping, include "None" option
            company_display_names = [""] # Start with an empty option for "None"
            for acc_id, acc_name in accounts_data:
                self.company_options[acc_name] = acc_id
                company_display_names.append(acc_name)
            self.company_combo['values'] = company_display_names
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load companies: {e}", parent=self)
            self.company_combo['values'] = [""]


    def populate_contact_dropdown(self):
        try:
            contacts_data = self.logic.get_all_contacts() # Returns list of Contact objects
            self.contact_options = {"": None} # Display name to ID mapping
            contact_display_names = [""]
            for contact in contacts_data:
                self.contact_options[contact.name] = contact.contact_id
                contact_display_names.append(contact.name)
            self.contact_combo['values'] = contact_display_names
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load contacts: {e}", parent=self)
            self.contact_combo['values'] = [""]

    def populate_assigned_user_dropdown(self):
        # This will be fully implemented in Step 3 when logic.get_all_users() is available
        try:
            # Assuming logic.get_all_users() will return list of (user_id, username) tuples or similar
            # users_data = self.logic.get_all_users() # Placeholder
            users_data = [] # Placeholder until Step 3
            if hasattr(self.logic, 'get_all_users'):
                users_data = self.logic.get_all_users()

            self.assigned_user_options = {"": None}
            assigned_user_display_names = [""]
            for user_id, username in users_data:
                self.assigned_user_options[username] = user_id
                assigned_user_display_names.append(username)
            self.assigned_user_combo['values'] = assigned_user_display_names
        except AttributeError:
             # This means get_all_users is not yet implemented in logic
            self.assigned_user_combo['values'] = [""] # Default to empty if method not ready
            print("DEBUG: populate_assigned_user_dropdown - logic.get_all_users not yet available.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load users: {e}", parent=self)
            self.assigned_user_combo['values'] = [""]


    def populate_fields(self):
        if not self.task_data:
            return

        self.title_entry.insert(0, self.task_data.title)
        self.description_text.insert(tk.END, self.task_data.description or "")

        if self.task_data.due_date:
            if isinstance(self.task_data.due_date, (datetime.date, datetime.datetime)):
                self.due_date_entry.insert(0, self.task_data.due_date.strftime('%Y-%m-%d'))
            else: # Should be iso string if from_dict was used correctly
                 self.due_date_entry.insert(0, str(self.task_data.due_date))


        self.status_var.set(self.task_data.status.value)
        if self.task_data.priority:
            self.priority_var.set(self.task_data.priority.value)
        else:
            self.priority_var.set("")


        # Set company dropdown
        if self.task_data.company_id:
            for name, id_val in self.company_options.items():
                if id_val == self.task_data.company_id:
                    self.company_var.set(name)
                    break

        # Set contact dropdown
        if self.task_data.contact_id:
            for name, id_val in self.contact_options.items():
                if id_val == self.task_data.contact_id:
                    self.contact_var.set(name)
                    break

        # Set assigned user dropdown
        if self.task_data.assigned_to_user_id and hasattr(self, 'assigned_user_options'):
             for name, id_val in self.assigned_user_options.items():
                if id_val == self.task_data.assigned_to_user_id:
                    self.assigned_user_var.set(name)
                    break


    def save_task(self):
        title = self.title_entry.get().strip()
        description = self.description_text.get("1.0", tk.END).strip()
        due_date_str = self.due_date_entry.get().strip()
        status_val = self.status_var.get()
        priority_val = self.priority_var.get()

        company_name = self.company_var.get()
        company_id = self.company_options.get(company_name)

        contact_name = self.contact_var.get()
        contact_id = self.contact_options.get(contact_name)

        assigned_user_name = self.assigned_user_var.get()
        assigned_to_user_id = self.assigned_user_options.get(assigned_user_name) if hasattr(self, 'assigned_user_options') else None


        if not title:
            messagebox.showerror("Validation Error", "Title cannot be empty.", parent=self)
            return
        if not due_date_str:
            messagebox.showerror("Validation Error", "Due Date cannot be empty.", parent=self)
            return

        try:
            due_date_obj = datetime.datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            messagebox.showerror("Validation Error", "Due Date must be in YYYY-MM-DD format.", parent=self)
            return

        status_enum = TaskStatus(status_val) if status_val else TaskStatus.OPEN
        priority_enum = TaskPriority(priority_val) if priority_val else None

        # created_by_user_id will be handled by logic layer (e.g. current logged in user or default)
        # For now, we assume logic layer handles created_by_user_id on new tasks.
        # If editing, it should remain the same or be handled by logic if it can change.

        task_payload = {
            "task_id": self.task_id,
            "title": title,
            "description": description,
            "due_date": due_date_obj, # Pass as date object
            "status": status_enum,
            "priority": priority_enum,
            "company_id": company_id,
            "contact_id": contact_id,
            "assigned_to_user_id": assigned_to_user_id,
        }

        try:
            if self.task_id: # Editing existing task
                # Logic's update_task_details expects a Task object.
                # We need to preserve created_at and created_by_user_id
                current_task_obj = self.logic.get_task_details(self.task_id)
                if not current_task_obj: # Should not happen if popup opened correctly
                    messagebox.showerror("Error", "Original task not found for update.", parent=self)
                    return

                updated_task_obj = Task(
                    task_id=current_task_obj.task_id,
                    title=title,
                    description=description,
                    due_date=due_date_obj,
                    status=status_enum,
                    priority=priority_enum,
                    company_id=company_id,
                    contact_id=contact_id,
                    assigned_to_user_id=assigned_to_user_id,
                    created_by_user_id=current_task_obj.created_by_user_id, # Preserve
                    created_at=current_task_obj.created_at # Preserve
                )
                self.logic.update_task_details(updated_task_obj)
                messagebox.showinfo("Success", "Task updated successfully.", parent=self)
            else: # Creating new task
                # Logic's create_task expects a Task object.
                # created_by_user_id should be set by logic or passed if available (e.g. current_user_id)
                # For now, create_task in logic sets a default 'system_user' if not provided.
                new_task_obj = Task(**{k:v for k,v in task_payload.items() if k != 'task_id'})
                self.logic.create_task(new_task_obj)
                messagebox.showinfo("Success", "Task created successfully.", parent=self)

            # Refresh parent tab/list (if applicable)
            if hasattr(self.master, 'load_tasks'): # A bit of coupling, but common for popups
                self.master.load_tasks()
            elif hasattr(self.master.master, 'load_tasks'): # If master is a frame within the tab
                 self.master.master.load_tasks()


            self.destroy()
        except ValueError as ve: # Validation errors from Task struct or logic
             messagebox.showerror("Error", f"Validation Error: {ve}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save task: {e}", parent=self)

if __name__ == '__main__':
    # This is for testing the popup independently.
    # You'd need a mock logic and a root window.
    class MockLogic:
        def get_task_details(self, task_id):
            if task_id == 1:
                return Task(task_id=1, title="Test Task 1", due_date=datetime.date.today() + datetime.timedelta(days=1),
                            description="My desc", status=TaskStatus.OPEN, priority=TaskPriority.HIGH,
                            created_by_user_id=1, created_at=datetime.datetime.now())
            return None

        def get_accounts(self): return [(1, "CompA"), (2, "CompB")]
        def get_all_contacts(self): return [Contact(contact_id=10, name="ContactX"), Contact(contact_id=11, name="ContactY")]

        # Updated mock to align with what TaskDetailsPopup expects
        def get_all_users(self):
            print("MockLogic: get_all_users called")
            return [(1, "UserAlpha"), (2, "UserBeta")]

        def create_task(self, task_obj):
            print("Mock create_task called with:", task_obj.to_dict())
            task_obj.task_id = 99 # Simulate ID assignment
            return task_obj

        def update_task_details(self, task_obj):
            print("Mock update_task_details called with:", task_obj.to_dict())
            return task_obj

    root = tk.Tk()
    root.withdraw() # Hide main root window for popup test

    mock_logic = MockLogic()

    # Test adding a new task
    # popup_add = TaskDetailsPopup(root, mock_logic)
    # root.wait_window(popup_add)

    # Test editing an existing task
    popup_edit = TaskDetailsPopup(root, mock_logic, task_id=1)
    root.wait_window(popup_edit)

    root.destroy()
    root.mainloop()
