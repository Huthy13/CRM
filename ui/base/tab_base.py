import tkinter as tk
import datetime

class TabBase(tk.Frame):
    """Base class for tab frames with shared helpers."""

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

    def sort_column(self, col: str, reverse: bool):
        """Generic Treeview column sorter.

        Attempts to sort numerically, handling currency strings and ISO dates
        before falling back to a case-insensitive string comparison.
        Assumes a ``ttk.Treeview`` widget assigned to ``self.tree``.
        """
        data = []
        for k in self.tree.get_children(""):
            value = self.tree.set(k, col)
            sort_val = value
            if isinstance(value, str):
                try:
                    sort_val = float(value.lstrip("$"))
                except ValueError:
                    try:
                        sort_val = datetime.datetime.strptime(value, "%Y-%m-%d")
                    except ValueError:
                        sort_val = value.lower()
            data.append((sort_val, k))

        data.sort(key=lambda item: item[0], reverse=reverse)
        for index, (_, k) in enumerate(data):
            self.tree.move(k, "", index)
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))
