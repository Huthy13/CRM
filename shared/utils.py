import re
import unicodedata

# This file will contain common utility functions, constants, enums, etc.
# Placeholder for now.

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


def address_has_type(address, addr_type: str) -> bool:
    """Return True if the address is associated with the given type.

    The address may store its types in ``address.address_types`` (a list) or
    in the legacy ``address.address_type`` attribute. This helper normalises
    both representations.
    """
    types = getattr(address, "address_types", None)
    if types:
        return addr_type in types
    return getattr(address, "address_type", "") == addr_type


def address_is_primary_for(address, addr_type: str) -> bool:
    """Return True if the address is the primary one for ``addr_type``.

    Similar to :func:`address_has_type`, this helper understands both the list
    based ``primary_types`` attribute and the legacy ``is_primary``/``address_type``
    combination.
    """
    primary_types = getattr(address, "primary_types", None)
    if primary_types is not None:
        return addr_type in primary_types
    return (
        getattr(address, "is_primary", False)
        and getattr(address, "address_type", "") == addr_type
    )


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
