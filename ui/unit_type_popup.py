import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from core.logic.product_management import ProductLogic

class UnitTypePopup(tk.Toplevel):
    def __init__(self, master_window, product_logic: ProductLogic):
        super().__init__(master_window)
        self.product_logic = product_logic
        self.title("Manage Unit Types")
        self.geometry("400x300")

        self.setup_ui()
        self.load_unit_types()

    def setup_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=("name",), show="headings")
        self.tree.heading("name", text="Unit Type Name")
        self.tree.column("name", width=250)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.add_button = ttk.Button(button_frame, text="Add", command=self.add_unit_type)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.edit_button = ttk.Button(button_frame, text="Edit", command=self.edit_unit_type)
        self.edit_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = ttk.Button(button_frame, text="Delete", command=self.delete_unit_type)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        close_button = ttk.Button(main_frame, text="Close", command=self.destroy)
        close_button.pack(pady=10, side=tk.RIGHT)

    def load_unit_types(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            # We need a method in product_logic to get all unit types with their IDs
            unit_types = self.product_logic.get_all_unit_types()
            for unit_type in unit_types:
                self.tree.insert("", "end", iid=unit_type['id'], values=(unit_type['name'],))
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load unit types: {e}")

    def get_selected_unit_type_id(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Selection Required", "Please select a unit type first.")
            return None
        return selected_item

    def add_unit_type(self):
        name = simpledialog.askstring("New Unit Type", "Enter unit type name:", parent=self)
        if name:
            try:
                # We need a method in product_logic to add a unit type
                self.product_logic.add_unit_type(name)
                self.load_unit_types()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add unit type: {e}", parent=self)

    def edit_unit_type(self):
        unit_type_id = self.get_selected_unit_type_id()
        if unit_type_id is None:
            return

        current_name = self.tree.item(unit_type_id, "values")[0]
        new_name = simpledialog.askstring("Edit Unit Type", "Enter new name:", initialvalue=current_name, parent=self)
        if new_name and new_name != current_name:
            try:
                # We need a method in product_logic to update a unit type
                self.product_logic.update_unit_type(int(unit_type_id), new_name)
                self.load_unit_types()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update unit type: {e}", parent=self)

    def delete_unit_type(self):
        unit_type_id = self.get_selected_unit_type_id()
        if unit_type_id is None:
            return

        unit_type_name = self.tree.item(unit_type_id, "values")[0]
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete unit type '{unit_type_name}'?", parent=self):
            try:
                # We need a method in product_logic to delete a unit type
                self.product_logic.delete_unit_type(int(unit_type_id))
                self.load_unit_types()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete unit type: {e}", parent=self)
