This file documents the agents and tools available within the CRM software project. The CRM project provides functionality for managing accounts, contacts, interactions, product management, purchase documents (such as RFQs and purchase orders), and tasks/reminders.

Core Modules

Database (core/database.py)

Purpose: Handles database connections and operations, including initialization and queries.

Interactions: Provides CRUD operations.

Conventions: Expects structured inputs/outputs aligned with data schemas defined in the application.

Address Book Logic (core/address_book_logic.py)

Purpose: Manages business logic related to accounts and contacts.

Interactions: Facilitates operations like adding, editing, tagging (customer, vendor, contact), and deleting accounts or contacts.

Conventions: Uses structured input data and returns operation statuses and updated data states.

Purchase Logic (core/purchase_logic.py)

Purpose: Manages logic related to purchase documents, including RFQs and Purchase Orders.

Interactions: Creates, updates, and tracks document status changes (RFQ, PO).

Conventions: Clearly structured document states (ENUM: RFQ, PO) and line items.

Sales Logic (core/sales_logic.py)

Purpose: Manages business logic related to sales documents, including Quotes and Invoices.

Interactions: Creates, updates, converts (Quote to Invoice), and tracks document status changes (Quote Draft, Sent, Accepted; Invoice Draft, Sent, Paid, etc.). Handles item management with sale prices and discounts, and calculates document totals.

Conventions: Uses `SalesDocument`, `SalesDocumentItem`, `SalesDocumentStatus`, and `SalesDocumentType` enums from `shared/structs.py`. Interacts with `AccountType.CUSTOMER`. Document numbering follows `QUO-YYYYMMDD-XXXX` for quotes and `INV-YYYYMMDD-XXXX` for invoices.

PDF Generation (core/quote_generator.py, core/invoice_generator.py)

Purpose: Responsible for generating PDF representations of quotes and invoices. (Currently placeholder implementations).

Interactions: Called by the sales document UI to export documents. Fetches necessary data via `SalesLogic`.

Conventions: Uses `reportlab` for PDF creation. Output filenames include document type and number.

User Interface (UI) Modules

Account Management (ui/accounts/)

Purpose: Handles user interactions for accounts.

Modules:

account_popup.py: Popups for detailed account views and edits.

account_tab.py: Displays a summary list and allows basic operations (add, edit, delete).

Contact Management (ui/contacts/)

Purpose: Manages UI interactions for contacts.

Modules:

contact_popup.py: Detailed views and editing of contacts.

contact_tab.py: Lists contacts with quick actions.

Interaction Management (ui/interactions/)

Purpose: Tracks interactions associated with contacts and accounts.

Modules:

interaction_popup.py: Detailed view of individual interactions.

interaction_tab.py: Summarizes and manages interactions.

Product Management (ui/products/)

Purpose: Handles products or parts used in CRM and ERP contexts.

Modules:

product_popup.py: Detailed management of individual products.

product_tab.py: Product summaries, addition, editing, and deletion.

Purchase Documents (ui/purchase_documents/)

Purpose: Interface for managing RFQs and Purchase Orders.

Modules:

purchase_document_popup.py: Detailed view and management.

purchase_document_item_popup.py: Management of line items within documents.

purchase_document_tab.py: Summary of all documents and their statuses.

Sales Documents (ui/sales_documents/)

Purpose: Interface for managing Quotes and Invoices.

Modules:

sales_document_popup.py: Detailed view and management of Quotes and Invoices. Handles document type selection (Quote/Invoice) for new documents and displays relevant fields (e.g., Expiry Date for Quotes, Due Date for Invoices).

sales_document_item_popup.py: Management of line items within sales documents, including discounts and sale prices.

sales_document_tab.py: Summary of all sales documents (Quotes and Invoices) and their statuses, linking to customers.

Task Management (ui/tasks/)

Purpose: Manages tasks and reminders related to accounts and contacts.

Modules:

task_popup.py: Detailed views and editing of tasks.

task_tab.py: Displays and manages lists of tasks, including their statuses and due dates.

Shared Resources

Structs (shared/structs.py)

Purpose: Defines data structures and schema representations used across the project.
    - Includes `SalesDocument`, `SalesDocumentItem`, `SalesDocumentType`, `SalesDocumentStatus` for sales workflow.
    - `Product` struct updated to include `sale_price`.

Conventions: Data structure clarity and consistent schema usage throughout the project.

Utils (shared/utils.py)

Purpose: Provides common utility functions used across various modules, such as formatting, validation, and common operations.

Scripts

Sandbox Data (scripts/sandbox_data.py)

Purpose: Generates mock data for testing and development purposes.

Testing

Integration and Unit Tests (tests/)

Purpose: Ensures robustness through extensive tests covering logic (unit/) and integrated functionalities (integration/).

Conventions: Adheres to structured testing methodologies ensuring comprehensive test coverage.
