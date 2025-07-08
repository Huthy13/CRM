import tkinter as tk
from tkinter import ttk
# from core.address_book_logic import AddressBookLogic # No longer needed directly for this popup
from core.logic.product_management import ProductLogic # Import ProductLogic
from tkinter import simpledialog, messagebox

class CategoryListPopup(tk.Toplevel):
    def __init__(self, master_window, product_logic: ProductLogic): # Changed to product_logic
        super().__init__(master_window)
        self.product_logic = product_logic # Store and use product_logic
        self.title("Manage Product Categories")
        self.geometry("500x450")

        self.setup_ui()
        self.load_categories_to_treeview()

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Treeview frame
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=("name",), show="tree headings") # Show tree for hierarchy
        self.tree.heading("#0", text="Category Name") # Column for tree labels
        self.tree.column("#0", width=300)
        # self.tree.heading("name", text="Name") # This would be an actual data column if needed

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.add_root_button = ttk.Button(button_frame, text="Add Top-Level", command=self.add_top_level_category)
        self.add_root_button.pack(side=tk.LEFT, padx=5)

        self.add_child_button = ttk.Button(button_frame, text="Add Sub-category", command=self.add_subcategory)
        self.add_child_button.pack(side=tk.LEFT, padx=5)

        self.edit_button = ttk.Button(button_frame, text="Edit Name", command=self.edit_category_name)
        self.edit_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = ttk.Button(button_frame, text="Delete Selected", command=self.delete_selected_category)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        # Close button (bottom)
        close_button = ttk.Button(main_frame, text="Close", command=self.destroy)
        close_button.pack(pady=10, side=tk.RIGHT)

    def _populate_tree(self, parent_node_id, categories_list):
        """Helper to recursively populate the treeview."""
        for category_data in categories_list:
            # category_data is a dict: {'id': cat_id, 'name': name, 'parent_id': parent_id, 'children': []}
            node_id = self.tree.insert(parent_node_id, 'end', iid=category_data['id'], text=category_data['name'], open=False)
            if category_data['children']:
                self._populate_tree(node_id, category_data['children'])

    def load_categories_to_treeview(self):
        for i in self.tree.get_children(): # Clear existing items
            self.tree.delete(i)
        try:
            hierarchical_categories = self.product_logic.get_hierarchical_categories() # Use product_logic
            self._populate_tree('', hierarchical_categories) # '' is the root for treeview items
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load categories: {e}")
            print(f"Error loading categories to treeview: {e}")
            import traceback
            traceback.print_exc()

    def get_selected_category_id(self):
        selected_item = self.tree.focus() # Gets the iid of the focused item
        if not selected_item:
            messagebox.showwarning("Selection Required", "Please select a category first.")
            return None
        return selected_item # Assuming iid is the category_id (integer)

    def add_top_level_category(self):
        name = simpledialog.askstring("New Top-Level Category", "Enter category name:", parent=self)
        if name:
            try:
                self.product_logic.add_category(name, parent_id=None) # Use product_logic
                self.load_categories_to_treeview()
            except ValueError as ve:
                 messagebox.showerror("Validation Error", str(ve), parent=self)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add category: {e}", parent=self)

    def add_subcategory(self):
        parent_id = self.get_selected_category_id()
        if parent_id is None:
            return

        parent_name = self.tree.item(parent_id, "text")
        name = simpledialog.askstring("New Sub-category", f"Enter name for sub-category under '{parent_name}':", parent=self)
        if name:
            try:
                self.product_logic.add_category(name, parent_id=int(parent_id)) # Use product_logic
                self.load_categories_to_treeview()
                # Optionally, try to expand the parent node here
                self.tree.item(parent_id, open=True)
            except ValueError as ve:
                 messagebox.showerror("Validation Error", str(ve), parent=self)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add sub-category: {e}", parent=self)

    def edit_category_name(self):
        category_id = self.get_selected_category_id()
        if category_id is None:
            return

        current_name = self.tree.item(category_id, "text")
        new_name = simpledialog.askstring("Edit Category Name", "Enter new name:", initialvalue=current_name, parent=self)
        if new_name and new_name != current_name:
            try:
                self.product_logic.update_category_name(int(category_id), new_name) # Use product_logic
                self.load_categories_to_treeview()
            except ValueError as ve:
                 messagebox.showerror("Validation Error", str(ve), parent=self)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update category name: {e}", parent=self)

    def delete_selected_category(self):
        category_id = self.get_selected_category_id()
        if category_id is None:
            return

        category_name = self.tree.item(category_id, "text")
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete category '{category_name}'?\nProducts using this category will be unassigned.\nChild categories will become top-level.", parent=self):
            try:
                self.product_logic.delete_category(int(category_id)) # Use product_logic
                self.load_categories_to_treeview()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete category: {e}", parent=self)


if __name__ == '__main__':
    # This is for testing purposes. Requires a more complete MockProductLogic for hierarchy.
    class MockProductLogic: # Renamed to MockProductLogic
        def get_hierarchical_categories(self): # Mock this method
            print("MockProductLogic: get_hierarchical_categories called")
            # Return a simple hierarchy for testing
            return [
                {'id': 1, 'name': 'Electronics', 'parent_id': None, 'children': [
                    {'id': 2, 'name': 'Laptops', 'parent_id': 1, 'children': []}
                ]},
                {'id': 3, 'name': 'Books', 'parent_id': None, 'children': []}
            ]
        # Add other methods if their calls are not guarded by user interaction in this test script
        def add_category(self, name, parent_id=None): print(f"Mock: Add category {name}, parent {parent_id}")
        def update_category_name(self, cat_id, name): print(f"Mock: Update cat {cat_id} to {name}")
        def delete_category(self, cat_id): print(f"Mock: Delete cat {cat_id}")


    class MockMaster(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Mock Master for Category Popup")
            self.geometry("200x100")
            tk.Button(self, text="Show Categories", command=self.show_category_popup).pack(pady=20)

        def show_category_popup(self):
            popup = CategoryListPopup(self, MockProductLogic()) # Use MockProductLogic
            self.wait_window(popup)

    app = MockMaster()
    app.mainloop()
