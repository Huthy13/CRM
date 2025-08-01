import tkinter as tk
from tkinter import messagebox

class PopupBase(tk.Toplevel):
    """Base class for popup dialogs providing common Tkinter helpers."""

    def __init__(self, master, *args, title: str | None = None, **kwargs):
        super().__init__(master, *args, **kwargs)
        if title:
            self.title(title)

    def _create_entry(self, label_text: str, row: int, initial_value: str | float | None = "", width: int = 40):
        """Create a labeled entry widget and return the entry."""
        label = tk.Label(self, text=label_text)
        label.grid(row=row, column=0, padx=5, pady=5, sticky="e")
        entry = tk.Entry(self, width=width)
        if initial_value is not None:
            entry.insert(0, initial_value)
        entry.grid(row=row, column=1, padx=5, pady=5)
        return entry

    def validate_not_empty(self, value: str, field_name: str) -> bool:
        """Validate that ``value`` is not empty. Return True if valid."""
        if not value.strip():
            messagebox.showerror("Validation Error", f"{field_name} cannot be empty.")
            return False
        return True
