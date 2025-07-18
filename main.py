import tkinter as tk
from ui.main_view import AddressBookView
from core.address_book_logic import AddressBookLogic
from core.database import DatabaseHandler

if __name__ == '__main__':
    # Initialize database and logic
    # The DatabaseHandler path for the DB file will be fixed in a later step.
    db_handler = DatabaseHandler()
    logic = AddressBookLogic(db_handler)

    # Setup main Tkinter window and application view
    root = tk.Tk()
    # Pass logic to the main view, AddressBookView will need to be updated to accept it
    app = AddressBookView(root, logic)
    root.mainloop()

    # Close database connection when the application exits
    # This might cause an error if root.mainloop() exits and db_handler is already closed by AddressBookView
    # or if AddressBookView itself tries to close it.
    # For now, following the prompt's structure.
    db_handler.close()
