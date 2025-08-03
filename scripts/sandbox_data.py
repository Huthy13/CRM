"""Populate the CRM database with sandbox data.

This script creates sample vendors, customers, products, pricing rules and
payment terms. It is intended for local development and testing so that the
application has meaningful data to interact with.
"""

import os
import sys

# Ensure project root is on the path for absolute imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core.database import DatabaseHandler
from core.address_book_logic import AddressBookLogic
from shared.structs import Account, Address, AccountType, Product


def populate_data() -> None:
    """Populate the database with sample data."""
    print("Connecting to the database…")
    db_handler = DatabaseHandler()
    logic = AddressBookLogic(db_handler)
    print("Database connected.")

    # --- Pricing rules ---
    print("Creating pricing rules…")
    standard_markup_id = logic.create_pricing_rule(
        "Standard Markup", markup_percentage=20.0
    )
    premium_markup_id = logic.create_pricing_rule(
        "Premium Markup", markup_percentage=35.0
    )
    print(
        f"Created pricing rules with IDs: standard={standard_markup_id}, "
        f"premium={premium_markup_id}"
    )

    # --- Payment terms ---
    print("Creating payment terms…")
    pay_on_receipt_id = logic.create_payment_term("Due on Receipt", days=0)
    net30_id = logic.create_payment_term("Net 30", days=30)
    net60_id = logic.create_payment_term("Net 60", days=60)
    net90_id = logic.create_payment_term("Net 90", days=90)
    print("Payment terms created.")

    # --- Vendors ---
    vendors = [
        {
            "name": "Nebula Components Ltd.",
            "phone": "555-1000",
            "street": "10 Orbit Drive",
            "city": "Stellar",
            "state": "CA",
            "zip": "90001",
            "desc": "Supplier of rare electronic components.",
        },
        {
            "name": "Quantum Parts Co.",
            "phone": "555-1001",
            "street": "55 Photon Road",
            "city": "Quantico",
            "state": "NY",
            "zip": "10011",
            "desc": "Specialist in high-frequency parts.",
        },
        {
            "name": "Redwood Manufacturing",
            "phone": "555-1002",
            "street": "800 Redwood Ave",
            "city": "Timber",
            "state": "WA",
            "zip": "98101",
            "desc": "Manufactures sustainable wooden enclosures.",
        },
        {
            "name": "Skyline Fasteners",
            "phone": "555-1003",
            "street": "312 Skyline Blvd",
            "city": "Metropolis",
            "state": "IL",
            "zip": "60601",
            "desc": "Provides industrial fasteners and bolts.",
        },
        {
            "name": "Starlight Industrial Supplies",
            "phone": "555-1004",
            "street": "77 Comet Street",
            "city": "Cosmo",
            "state": "TX",
            "zip": "73301",
            "desc": "Distributor of industrial tools and safety gear.",
        },
    ]

    for v in vendors:
        account = Account(
            name=v["name"],
            phone=v["phone"],
            addresses=[
                Address(
                    street=v["street"],
                    city=v["city"],
                    state=v["state"],
                    zip_code=v["zip"],
                    country="USA",
                    address_types=["Billing"],
                    primary_types=["Billing"],
                )
            ],
            website="",
            description=v["desc"],
            account_type=AccountType.VENDOR,
            payment_term_id=pay_on_receipt_id,
        )
        saved = logic.save_account(account)
        if saved:
            print(f"Vendor '{saved.name}' added with ID {saved.account_id}.")

    # --- Customers ---
    customers = [
        {
            "name": "Blue Horizon LLC",
            "phone": "555-2000",
            "street": "200 Ocean Ave",
            "city": "Seaside",
            "state": "FL",
            "zip": "33101",
            "desc": "Marine research equipment distributor.",
            "term": net30_id,
        },
        {
            "name": "Urban Cycling Co.",
            "phone": "555-2001",
            "street": "15 Pedal Plaza",
            "city": "Portland",
            "state": "OR",
            "zip": "97201",
            "desc": "Retailer of city bicycles and gear.",
            "term": net30_id,
        },
        {
            "name": "Green Fields Market",
            "phone": "555-2002",
            "street": "48 Harvest Lane",
            "city": "Springfield",
            "state": "IL",
            "zip": "62701",
            "desc": "Organic produce grocer.",
            "term": net60_id,
        },
        {
            "name": "Apex Robotics",
            "phone": "555-2003",
            "street": "909 Servo Street",
            "city": "Reno",
            "state": "NV",
            "zip": "89501",
            "desc": "Developer of custom automation robots.",
            "term": net60_id,
        },
        {
            "name": "Sunset Builders",
            "phone": "555-2004",
            "street": "120 Sunset Blvd",
            "city": "Phoenix",
            "state": "AZ",
            "zip": "85001",
            "desc": "Construction firm focused on eco-friendly homes.",
            "term": net90_id,
        },
    ]

    for c in customers:
        account = Account(
            name=c["name"],
            phone=c["phone"],
            addresses=[
                Address(
                    street=c["street"],
                    city=c["city"],
                    state=c["state"],
                    zip_code=c["zip"],
                    country="USA",
                    address_types=["Billing"],
                    primary_types=["Billing"],
                )
            ],
            website="",
            description=c["desc"],
            account_type=AccountType.CUSTOMER,
            pricing_rule_id=standard_markup_id,
            payment_term_id=c["term"],
        )
        saved = logic.save_account(account)
        if saved:
            print(f"Customer '{saved.name}' added with ID {saved.account_id}.")

    # --- Products ---
    products = [
        {
            "name": "Aurora Bolt",
            "description": "High-tensile bolt for aerospace applications.",
            "cost": 0.50,
        },
        {
            "name": "Nebula Nut",
            "description": "Self-locking nut with cosmic durability.",
            "cost": 0.30,
        },
        {
            "name": "Photon Gear",
            "description": "Precision gear that reduces energy loss.",
            "cost": 15.00,
        },
        {
            "name": "Quantum Bearing",
            "description": "Near-frictionless bearing for high-speed rigs.",
            "cost": 8.00,
        },
        {
            "name": "Titanium Rod",
            "description": "Lightweight rod for structural frames.",
            "cost": 12.00,
        },
        {
            "name": "Solar Panel Mini",
            "description": "Compact solar panel for field sensors.",
            "cost": 25.00,
        },
        {
            "name": "Hyperdrive Motor",
            "description": "High-efficiency motor for automation systems.",
            "cost": 55.00,
        },
        {
            "name": "Crimson Paint",
            "description": "Weather-resistant industrial paint.",
            "cost": 5.00,
        },
        {
            "name": "Echo Sensor",
            "description": "Ultrasonic sensor for distance measurement.",
            "cost": 18.00,
        },
        {
            "name": "Glacier Coolant",
            "description": "Long-life coolant for heavy machinery.",
            "cost": 3.50,
        },
    ]

    for p in products:
        sale_price = round(p["cost"] * 1.2, 2)  # Apply standard markup
        product = Product(
            name=p["name"],
            description=p["description"],
            cost=p["cost"],
            sale_price=sale_price,
            category="General",
            unit_of_measure="EA",
        )
        prod_id = logic.save_product(product)
        if prod_id:
            print(f"Product '{p['name']}' added with ID {prod_id}.")

    print("Sandbox data population complete.")
    db_handler.close()


if __name__ == "__main__":
    db_path = os.path.join(PROJECT_ROOT, "core", "address_book.db")
    if os.path.exists(db_path):
        print(f"Deleting existing database file: {db_path}")
        try:
            os.remove(db_path)
            print("Old database file deleted.")
        except OSError as exc:  # pragma: no cover - very unlikely during tests
            print(f"Error deleting database file {db_path}: {exc}")
            sys.exit(1)

    populate_data()

