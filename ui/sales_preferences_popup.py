import tkinter as tk
from tkinter import ttk

from core.preferences import load_preferences, save_preferences


class SalesPreferencesPopup(tk.Toplevel):
    """Popup window for configuring sales-related preferences."""

    def __init__(self, master: tk.Misc):
        super().__init__(master)
        self.title("Sales Preferences")
        self.resizable(False, False)

        prefs = load_preferences()
        self.require_ref_var = tk.BooleanVar(
            value=prefs.get('require_reference_on_quote_accept', False)
        )
        self.quote_expiry_days_var = tk.IntVar(
            value=prefs.get('default_quote_expiry_days', 30)
        )

        chk = ttk.Checkbutton(
            self,
            text="Require customer reference number to accept a quote",
            variable=self.require_ref_var,
        )
        chk.pack(padx=10, pady=10, anchor="w")

        expiry_frame = ttk.Frame(self)
        expiry_frame.pack(padx=10, pady=(0,10), anchor="w")
        ttk.Label(expiry_frame, text="Default quote expiration (days):").pack(side="left")
        ttk.Spinbox(
            expiry_frame,
            from_=1,
            to=365,
            width=5,
            textvariable=self.quote_expiry_days_var,
        ).pack(side="left", padx=(5,0))

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        save_btn = ttk.Button(btn_frame, text="Save", command=self.save)
        save_btn.pack(side="right", padx=(5, 0))
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.destroy)
        cancel_btn.pack(side="right")

    def save(self):
        prefs = load_preferences()
        prefs['require_reference_on_quote_accept'] = self.require_ref_var.get()
        prefs['default_quote_expiry_days'] = int(self.quote_expiry_days_var.get())
        save_preferences(prefs)
        self.destroy()
