import argparse
import os
import sys
from fpdf import FPDF

# Ensure the project root is in sys.path for absolute imports like 'from shared.structs'
# This helps when the script is run directly or imported by other modules.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # Points to /app/core
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) # Points to /app
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from .database import DatabaseHandler # Relative import for modules within the same package (core)
from .purchase_logic import PurchaseLogic # Relative import
from .address_book_logic import AddressBookLogic # Relative import
from shared.structs import PurchaseDocument, PurchaseDocumentItem, Account, Address, PurchaseDocumentStatus # Absolute import from project root
from .pdf_generator import PDF, get_company_pdf_context
from .company_repository import CompanyRepository
from .company_service import CompanyService
from .address_service import AddressService
from .repositories import AddressRepository, AccountRepository

def generate_po_pdf(purchase_document_id: int, output_path: str = None):
    """
    Generates a PDF for a given purchase_document_id using data
    from the existing application's database and logic.
    """
    db_handler = None
    try:
        # Initialize database handler and logic classes
        # The DatabaseHandler will find 'address_book.db' in its own directory (core/)
        db_handler = DatabaseHandler()
        purchase_logic = PurchaseLogic(db_handler)
        address_book_logic = AddressBookLogic(db_handler) # Instantiate corrected class

        # 1. Fetch Purchase Document data
        doc: PurchaseDocument = purchase_logic.get_purchase_document_details(purchase_document_id)
        if not doc:
            print(f"Error: Purchase document with ID {purchase_document_id} not found.")
            return

        
        # 2. Fetch Company Information
        address_repo = AddressRepository(db_handler)
        account_repo = AccountRepository(db_handler)
        address_service = AddressService(address_repo, account_repo)
        company_repo = CompanyRepository(db_handler)
        company_service = CompanyService(company_repo, address_service)
        (
            company_name_for_header,
            company_phone_pdf,
            company_shipping_address_pdf_lines,
            company_remittance_address_pdf_lines,
            company_billing_address_pdf_lines,
        ) = get_company_pdf_context(company_service)
        
        # 3. Fetch Vendor details

        vendor: Account = None
        vendor_address: Address = None
        if doc.vendor_id:
            vendor = address_book_logic.get_account_details(doc.vendor_id) # Use AddressBookLogic
            if vendor:
                if vendor.billing_address_id:
                    # get_address_obj returns an Address object or None
                    vendor_address = address_book_logic.get_address_obj(vendor.billing_address_id)
            else:
                print(f"Warning: Vendor with ID {doc.vendor_id} not found for document {doc.document_number}.")

        # 4. Fetch Line Items
        items: list[PurchaseDocumentItem] = purchase_logic.get_items_for_document(doc.id)

        # 5. Initialize PDF (pass document number, company name, and billing address for header)
        pdf = PDF(
            document_number=doc.document_number,
            company_name=company_name_for_header,
            company_billing_address_lines=company_billing_address_pdf_lines,
            document_type="Purchase Order"
        )
        pdf.alias_nb_pages() # For total page numbers
        pdf.add_page()

        # --- PDF Content Generation ---
        line_height = 7
        col_width_full = pdf.w - 2 * pdf.l_margin # Full width for content

        # Document Details Section (Date only)
        pdf.set_font("Arial", "", 11) # Font for the Date
        date_str = f"Date: {doc.created_date.split('T')[0] if doc.created_date else 'N/A'}"
        # Full width cell, right aligned, with line break after.
        pdf.cell(0, line_height, date_str, 0, 1, "R")
        pdf.ln(line_height * 1.5) # Keep the spacing after this section

        # Company Shipping and Vendor Information Section (Two Columns)
        col_width_half = col_width_full / 2 - 5  # Half width for each column, with a small gap

        # --- Left Column: Company Shipping Information ---
        current_x = pdf.get_x()
        current_y = pdf.get_y()

        pdf.set_font("Arial", "B", 11)
        pdf.cell(col_width_half, line_height, "Shipping Address:", 0, 1, "L") # Changed title
        pdf.set_font("Arial", "", 11)

        # Display Company Name above its shipping address
        pdf.cell(col_width_half, line_height, company_name_for_header, 0, 1, "L")

        # Company Shipping Address
        temp_x_offset = pdf.get_x()
        pdf.multi_cell(col_width_half, line_height, "\n".join(company_shipping_address_pdf_lines), 0, "L")
        y_after_company_address = pdf.get_y()
        pdf.set_xy(temp_x_offset, y_after_company_address)

        if company_phone_pdf: # Display company phone if available
            pdf.cell(col_width_half, line_height, f"Phone: {company_phone_pdf}", 0, 1, "L")

        y_after_company_info = pdf.get_y()

        # --- Right Column: Vendor Information ---
        pdf.set_xy(current_x + col_width_half + 10, current_y) # Move to start of right column

        pdf.set_font("Arial", "B", 11)
        # Vendor Title - still use ln=1 to move below, but X will be reset for next element.
        pdf.cell(col_width_half, line_height, "Vendor:", 0, 1, "L")
        pdf.set_font("Arial", "", 11)

        right_column_x = current_x + col_width_half + 10

        if vendor:
            pdf.set_x(right_column_x)
            pdf.cell(col_width_half, line_height, vendor.name or "N/A", 0, 1, "L") # ln=1, so next line starts at margin

            if vendor_address:
                pdf.set_x(right_column_x) # <<< CRITICAL: Set X before multi_cell
                pdf.multi_cell(col_width_half, line_height,
                               f"{vendor_address.street or ''}\n"
                               f"{vendor_address.city or ''}, {vendor_address.state or ''} {vendor_address.zip_code or ''}\n"
                               f"{vendor_address.country or ''}".strip(), # Use strip to remove trailing newlines if country is empty
                               0, "L")
                # After multi_cell, Y is updated. X might be unpredictable or at left margin.
                # We need to set X again if something follows in this column on a *new* line created by multi_cell.
                # However, the phone number should appear directly after the address block, aligned to right_column_x.
                # multi_cell moves Y. We just need to ensure X is correct for the *next* element.
            else:
                pdf.set_x(right_column_x)
                pdf.cell(col_width_half, line_height, "No address on file.", 0, 1, "L")

            if vendor.phone:
                pdf.set_x(right_column_x) # Ensure X for phone
                pdf.cell(col_width_half, line_height, f"Phone: {vendor.phone}", 0, 1, "L")
            # y_after_vendor_info will be determined by the last element in this block.
            # The set_y(max(...)) call later will handle overall alignment.
        else:
            pdf.set_x(right_column_x)
            pdf.cell(col_width_half, line_height, "Vendor details not available.", 0, 1, "L")

        y_after_vendor_info = pdf.get_y() # Get Y after the vendor block is complete

        # Ensure the cursor is below the taller of the two columns before proceeding
        pdf.set_y(max(y_after_company_info, y_after_vendor_info))
        pdf.ln(line_height * 1.5) # Add some space before the line items table

        # Line Items Table
        pdf.set_font("Arial", "B", 10)
        # Define column widths - adjust as needed
        desc_col = col_width_full * 0.50  # 50%
        qty_col = col_width_full * 0.10   # 10%
        price_col = col_width_full * 0.20 # 20%
        total_col = col_width_full * 0.20 # 20%

        # Table Header
        pdf.set_fill_color(220, 220, 220) # Light grey for header
        pdf.cell(desc_col, line_height, "Product/Service Description", 1, 0, "C", 1)
        pdf.cell(qty_col, line_height, "Qty", 1, 0, "C", 1)
        pdf.cell(price_col, line_height, "Unit Price", 1, 0, "C", 1)
        pdf.cell(total_col, line_height, "Line Total", 1, 1, "C", 1)

        pdf.set_font("Arial", "", 9)
        document_subtotal = 0.0
        if items:
            for item in items:
                item_total = item.total_price if item.total_price is not None else 0.0
                if item.unit_price is None and item.quantity is not None and item_total != 0.0 and item.quantity != 0: # Try to infer unit price if missing but total exists
                    effective_unit_price = item_total / item.quantity
                else:
                    effective_unit_price = item.unit_price if item.unit_price is not None else 0.0

                document_subtotal += item_total

                # Handle multi-line descriptions
                start_x = pdf.get_x()
                start_y = pdf.get_y()
                product_info = (
                    purchase_logic.product_repo.get_product_details(item.product_id)
                    if item.product_id
                    else None
                )
                product_name = product_info.get("name") if product_info else None
                product_description = (
                    product_info.get("description") if product_info else item.product_description
                )
                lines = []
                if product_name:
                    lines.append(("B", product_name))
                if product_description:
                    lines.append(("", product_description))
                if item.note:
                    lines.append(("I", item.note))
                desc_line_height = 5
                for idx, (style, text) in enumerate(lines):
                    border = "LTR" if idx == 0 else ("LBR" if idx == len(lines) - 1 else "LR")
                    pdf.set_font("Arial", style, 9)
                    pdf.multi_cell(desc_col, desc_line_height, text, border, "L")
                    pdf.set_x(start_x)
                end_y_desc = pdf.get_y()

                pdf.set_xy(start_x + desc_col, start_y) # Reset X position for next cells in the row
                pdf.set_font("Arial", "", 9)

                pdf.cell(qty_col, end_y_desc - start_y, f"{item.quantity:.2f}" if item.quantity is not None else "0.00", 1, 0, "R")
                pdf.cell(price_col, end_y_desc - start_y, f"${effective_unit_price:.2f}", 1, 0, "R")
                pdf.cell(total_col, end_y_desc - start_y, f"${item_total:.2f}", 1, 0, "R")
                pdf.ln(end_y_desc - start_y) # Move to next line based on height of multi_cell

        else:
            pdf.cell(col_width_full, line_height, "No items in this document.", 1, 1, "C")

        # Document Subtotal
        pdf.set_font("Arial", "B", 10)
        pdf.cell(desc_col + qty_col + price_col, line_height, "Subtotal:", 1, 0, "R")
        pdf.cell(total_col, line_height, f"${document_subtotal:.2f}", 1, 1, "R")

        # Placeholder for Tax and Grand Total (as per popup, these are not directly available)
        # You can add logic here if tax calculation is needed
        # pdf.cell(desc_col + qty_col + price_col, line_height, "Tax (0%):", 1, 0, "R")
        # pdf.cell(total_col, line_height, "$0.00", 1, 1, "R")
        # pdf.set_font_size(11) # Slightly larger for grand total
        # pdf.cell(desc_col + qty_col + price_col, line_height, "Grand Total:", 1, 0, "R")
        # pdf.cell(total_col, line_height, f"${document_subtotal:.2f}", 1, 1, "R")
        pdf.ln(line_height * 1.5)

        # Notes Section
        if doc.notes and doc.notes.strip():
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, line_height, "Notes:", 0, 1, "L")
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(0, line_height, doc.notes.strip(), 0, "L")
        # --- End PDF Content Generation ---

        # 5. Determine output filename and save
        filename = output_path or f"purchase_order_{doc.document_number.replace('/', '_')}.pdf" # Sanitize filename
        pdf.output(filename, "F")
        print(f"PDF generated: {filename}")

    except ImportError as e:
        print(f"Error importing application modules: {e}")
        print("Ensure this script is run from the project root or the PYTHONPATH is correctly set.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if db_handler:
            db_handler.close()

def main():
    parser = argparse.ArgumentParser(description="Generate a Purchase Order PDF from existing application data.")
    parser.add_argument("purchase_document_id", type=int, help="The ID of the purchase document to generate.")
    parser.add_argument("--output", type=str, help="Optional: Full path for the output PDF file.")
    args = parser.parse_args()

    # It's assumed that the script, when run, can access the application's
    # database configuration and core logic. This might require some setup
    # or ensuring it's run in an environment where core modules are importable.

    if args.list_documents:
        list_existing_documents()
    elif args.purchase_document_id:
        generate_po_pdf(args.purchase_document_id, args.output)
    else:
        parser.print_help()

def list_existing_documents():
    """Lists some existing purchase documents to help find an ID for testing."""
    db_handler = None
    print("Attempting to list existing purchase documents...")
    try:
        db_handler = DatabaseHandler() # Uses default path to address_book.db
        purchase_logic = PurchaseLogic(db_handler)

        # Fetch a few documents (e.g., first 5 or so)
        # get_all_documents_by_criteria can be used without args for all, or with some limits
        # For simplicity, let's try to get all and print a few.
        # The method in DB handler is get_all_purchase_documents
        all_docs_raw = db_handler.get_all_purchase_documents() # Returns list of dicts

        if not all_docs_raw:
            print("No purchase documents found in the database.")
            return

        print("Found Purchase Documents (ID - Number - Status):")
        for i, doc_data in enumerate(all_docs_raw):
            if i >= 10: # Print details for up to 10 documents
                print(f"...and {len(all_docs_raw) - 10} more.")
                break
            status_val = doc_data.get('status', 'N/A')
            print(f"  ID: {doc_data['id']} - {doc_data['document_number']} - Status: {status_val}")

            # For more detailed check, fetch items for the first one
            if i == 0:
                items = db_handler.get_items_for_document(doc_data['id'])
                print(f"    Items for Doc ID {doc_data['id']}: {len(items)}")
                for item_idx, item_data in enumerate(items):
                    if item_idx >=2:
                        print(f"    ... and {len(items) - 2} more items.")
                        break
                    print(f"      - {item_data['product_description'][:30]}... Qty: {item_data['quantity']}")


    except ImportError as e:
        print(f"Error importing application modules: {e}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if db_handler:
            db_handler.close()

def main_logic(args, parser):
    if args.list_documents:
        list_existing_documents()
    elif args.purchase_document_id:
        generate_po_pdf(args.purchase_document_id, args.output)
    else:
        # If not listing and no ID provided, print help
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate or list Purchase Order PDFs from existing application data.")
    parser.add_argument("--list-documents", action="store_true", help="List existing purchase document IDs and numbers.")
    # Made purchase_document_id truly optional by providing default=None and checking its value in main_logic
    parser.add_argument("purchase_document_id", type=int, nargs='?', default=None, help="The ID of the purchase document to generate.")
    parser.add_argument("--output", type=str, help="Optional: Full path for the output PDF file.")

    args = parser.parse_args()
    main_logic(args, parser)