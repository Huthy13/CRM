from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

# Path to preferences file at project root
PREFERENCES_FILE = Path(__file__).resolve().parent.parent / 'preferences.json'

# Default preferences
DEFAULT_PREFERENCES: Dict[str, Any] = {
    'require_reference_on_quote_accept': False,
    'default_quote_expiry_days': 30,
}

def load_preferences() -> Dict[str, Any]:
    """Load preferences from JSON file, returning defaults if file missing."""
    if PREFERENCES_FILE.exists():
        try:
            with PREFERENCES_FILE.open('r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception:
            data = {}
    else:
        data = {}
    # merge defaults
    prefs = DEFAULT_PREFERENCES.copy()
    prefs.update({k: v for k, v in data.items() if k in DEFAULT_PREFERENCES})
    return prefs

def save_preferences(prefs: Dict[str, Any]) -> None:
    """Persist preferences to JSON file."""
    PREFERENCES_FILE.write_text(json.dumps(prefs, indent=2))
