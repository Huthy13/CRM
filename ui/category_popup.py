import tkinter as tk
from tkinter import ttk
from core.logic import AddressBookLogic

class CategoryListPopup(tk.Toplevel):
    def __init__(self, master_window, logic: AddressBookLogic):
        super().__init__(master_window)
        self.logic = logic
        self.title("Product Categories")
        self.geometry("300x400")

        self.setup_ui()
        self.load_categories()

    def setup_ui(self):
        # Frame for the listbox and scrollbar
        list_frame = tk.Frame(self)
        list_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.category_listbox = tk.Listbox(list_frame, width=40, height=15)
        self.category_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.category_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.category_listbox.config(yscrollcommand=scrollbar.set)

        # Close button
        close_button = ttk.Button(self, text="Close", command=self.destroy)
        close_button.pack(pady=10)

    def load_categories(self):
        self.category_listbox.delete(0, tk.END) # Clear existing items
        try:
            categories = self.logic.get_all_product_categories()
            if categories:
                for category in categories:
                    self.category_listbox.insert(tk.END, category)
            else:
                self.category_listbox.insert(tk.END, "No categories found.")
        except Exception as e:
            self.category_listbox.insert(tk.END, "Error loading categories.")
            print(f"Error loading categories: {e}") # For debugging

if __name__ == '__main__':
    # This is for testing purposes
    class MockLogic:
        def get_all_product_categories(self):
            print("Mock: get_all_product_categories called")
            return ["Electronics", "Books", "Home Goods", "Clothing", "Sports"]

    class MockMaster(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Mock Master for Category Popup")
            self.geometry("200x100")
            tk.Button(self, text="Show Categories", command=self.show_category_popup).pack(pady=20)

        def show_category_popup(self):
            popup = CategoryListPopup(self, MockLogic())
            self.wait_window(popup)

    app = MockMaster()
    app.mainloop()
