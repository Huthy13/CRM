import re
import unicodedata

# This file will contain common utility functions, constants, enums, etc.
# Placeholder for now.


def ensure_single_primary(addresses):
    """Ensure only one address per type remains marked as primary.

    The last address in the list marked as primary for a given type
    (e.g., "Billing" or "Shipping") is kept as primary and earlier
    ones are demoted. The list is modified in place.
    """
    seen = {}
    for address in reversed(addresses):
        if getattr(address, "is_primary", False):
            addr_type = getattr(address, "address_type", None)
            if addr_type is None:
                continue
            if seen.get(addr_type):
                address.is_primary = False
            else:
                seen[addr_type] = True

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a string to be a valid filename.

    - Replaces whitespace with underscores.
    - Removes characters that are invalid in filenames on Windows and other OSes.
    - Normalizes unicode characters.
    """
    if not isinstance(filename, str):
        filename = str(filename)

    # Normalize unicode characters to their closest ASCII representation
    filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')

    # Replace whitespace and known separators with a single underscore
    filename = re.sub(r'[\s/\\:]+', '_', filename)

    # Remove characters that are invalid in filenames
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)

    # Remove leading/trailing whitespace and underscores
    filename = filename.strip(' ._')

    # Limit filename length (optional, but good practice)
    # max_len = 255 # Common limit
    # if len(filename) > max_len - 4: # Reserve space for extension like .pdf
    #     filename = filename[:max_len - 4]

    return filename or "unnamed_file"


def example_utility_function():
    """
    An example utility function.
    """
    print("Utility function called.")

# Example constant
MAX_RETRIES = 3

class StatusEnum:
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
