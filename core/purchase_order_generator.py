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

class PDF(FPDF):
    def __init__(self, po_document_number=None, company_name="Your Company Name", company_billing_address_lines=None):
        super().__init__()
        self.po_document_number = po_document_number
        self.company_name = company_name
        self.company_billing_address_lines = company_billing_address_lines if company_billing_address_lines else []

    def header(self):
        header_line_height = 7 # Smaller line height for address details
        title_line_height = 10

        # Company Name (Top Left)
        self.set_font("Arial", "B", 16)
        self.cell(0, title_line_height, self.company_name, 0, 1, "L")

        # Company Billing Address (Below Company Name, Left)
        if self.company_billing_address_lines:
            self.set_font("Arial", "", 10) # Smaller font for address
            for line in self.company_billing_address_lines:
                if line.strip(): # Avoid printing empty lines if address has gaps
                    self.cell(0, header_line_height, line, 0, 1, "L")

        # Store Y position after company name and address to align PO title
        y_after_company_block = self.get_y()

        # Purchase Order Title (Centered)
        # We want this to appear to the right of the company name block, or centered overall
        # For simplicity, let's place it starting near the top, but ensure it's clear
        # Reset Y to a point that makes sense relative to the company name, and X for centering
        # This part might need adjustment for perfect vertical alignment with multi-line addresses

        # Simplified: PO title starts below company block, centered.
        # If we want it "beside" a potentially tall address block, it's more complex.
        # The prompt "directly under the Company name" for address implies PO title might be best after.

        # For now, let's try to keep PO title somewhat aligned with top, but this is tricky with dynamic address height.
        # A common approach is to set a fixed area for left (company) and right (title),
        # or determine max height of left block and center title next to it.

        # Let's try a simpler approach first: Title is below the company block, then centered.
        # This means the "Purchase Order - PO Number" will appear after the company name and its billing address.

        # Reset to a specific Y if needed, or let it flow. For now, let it flow.
        # The self.ln(10) later will provide spacing.

        self.set_font("Arial", "B", 14)
        title = "Purchase Order"
        if self.po_document_number:
            title += f" - {self.po_document_number}"

        # To center it properly after the left-aligned block which used ln=1:
        self.set_xy(0, y_after_company_block) # Reset X to left margin, Y after company block
                                              # Or choose a fixed Y from top: e.g. self.set_xy(0, self.t_margin + title_line_height)
                                              # If setting Y to a fixed top, ensure company block doesn't overwrite.

        # A common pattern for header:
        # 1. Company Name (left)
        # 2. Company Address (left, below name)
        # 3. PO Title (right of company name, or centered in remaining space, or centered on page)
        # Let's try placing PO title at a fixed Y, but ensure X allows it to be centered on page.

        # Store current Y before company name
        initial_y = self.get_y()

        # Company Name
        self.set_font("Arial", "B", 16)
        self.set_xy(self.l_margin, initial_y) # Start at left margin
        self.cell(self.w / 2 - self.l_margin, title_line_height, self.company_name, 0, 1, "L") # Cell takes up half width

        # Company Billing Address
        if self.company_billing_address_lines:
            self.set_font("Arial", "", 10)
            for line in self.company_billing_address_lines:
                if line.strip():
                    self.set_x(self.l_margin) # Ensure address lines also start at left margin
                    self.cell(self.w / 2 - self.l_margin, header_line_height, line, 0, 1, "L")

        y_after_left_block = self.get_y()

        # PO Title - Centered on the page, starting at the same initial Y as company name
        self.set_y(initial_y) # Reset Y to align top of PO title with top of company name
        self.set_font("Arial", "B", 14)
        # Calculate width of title to center it.
        # For self.cell(0, ... "C"), width 0 means full page width.
        # The challenge is the company info on left.
        # Alternative: PO title in the right half of the page.

        # Let's use the original centering approach for the title, but ensure it's placed after the left block or at a fixed Y
        # The original self.cell(0, 10, title, 0, 1, "C") centers it on the full page width.
        # If the company address block is tall, this title might overlap if Y is not managed.

        # New strategy:
        # Company Name (top left)
        # Company Billing Address (below name, left)
        # PO Title (top right, or centered in the right half of the page)

        # Reset font and Y for the title, place it on the right side.
        title_block_width = self.w - self.l_margin - self.r_margin # Full drawable width

        # Company Name
        self.set_font("Arial", "B", 16)
        self.set_xy(self.l_margin, self.t_margin + 5) # Start Y a bit below top margin
        current_y = self.get_y()
        self.multi_cell(title_block_width * 0.6, title_line_height, self.company_name, 0, "L") # Use multi_cell for name in case it wraps
        y_after_name = self.get_y()

        # Company Billing Address (below name)
        if self.company_billing_address_lines:
            self.set_font("Arial", "", 10)
            self.set_x(self.l_margin) # Ensure X is at left margin
            for line in self.company_billing_address_lines:
                if line.strip():
                     # self.set_x(self.l_margin) # Redundant if previous was full width cell with ln=1
                    self.cell(title_block_width * 0.6, header_line_height, line, 0, 1, "L")
        y_after_left_content = self.get_y()

        # PO Title (aligned to top with company name, but on the right)
        self.set_xy(self.l_margin + title_block_width * 0.6, self.t_margin + 5) # X starts after company block, Y same as company name start
        self.set_font("Arial", "B", 14)
        self.multi_cell(title_block_width * 0.4, title_line_height, title, 0, "C") # Centered in the remaining width
        y_after_right_content = self.get_y()

        # Set Y to be after the taller of the two blocks (left: name+address, right: PO title)
        final_y_for_header = max(y_after_left_content, y_after_right_content)
        self.set_y(final_y_for_header)

        self.ln(10) # Space after header

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", 0, 0, "C") # Added total pages

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
        company_info_dict = db_handler.get_company_information()
        company_name_for_header = "Your Company Name" # For PDF Header
        company_phone_pdf = "" # For display under shipping address if available
        company_shipping_address_pdf_lines = ["Shipping address not found."]
        company_billing_address_pdf_lines = ["Billing address not found."]

        if company_info_dict:
            company_name_for_header = company_info_dict.get('name', company_name_for_header)
            company_phone_pdf = company_info_dict.get('phone', "")

            # Fetch Shipping Address
            company_shipping_address_id = company_info_dict.get('shipping_address_id')
            if company_shipping_address_id:
                addr_tuple = db_handler.get_address(company_shipping_address_id)
                if addr_tuple:
                    company_shipping_address_pdf_lines = [
                        addr_tuple[0] or "",
                        f"{addr_tuple[1] or ""}, {addr_tuple[2] or ""} {addr_tuple[3] or ""}",
                        addr_tuple[4] or ""
                    ]
                    company_shipping_address_pdf_lines = [line for line in company_shipping_address_pdf_lines if line.strip()]
                    if not company_shipping_address_pdf_lines:
                         company_shipping_address_pdf_lines = ["Shipping address details missing."]
                else:
                    company_shipping_address_pdf_lines = ["Shipping address not found in DB (ID existed)."]
            else:
                # Fallback for Shipping Address to Billing Address if shipping_id is missing
                temp_billing_id_for_shipping = company_info_dict.get('billing_address_id')
                if temp_billing_id_for_shipping:
                    company_shipping_address_pdf_lines = ["Shipping address not set, using Billing Address:"]
                    addr_tuple = db_handler.get_address(temp_billing_id_for_shipping)
                    if addr_tuple:
                        shipping_fallback_lines = [
                            addr_tuple[0] or "",
                            f"{addr_tuple[1] or ""}, {addr_tuple[2] or ""} {addr_tuple[3] or ""}",
                            addr_tuple[4] or ""
                        ]
                        shipping_fallback_lines = [line for line in shipping_fallback_lines if line.strip()]
                        if not shipping_fallback_lines:
                            company_shipping_address_pdf_lines = ["Shipping address not set, billing address details missing."]
                        else:
                            company_shipping_address_pdf_lines.extend(shipping_fallback_lines)
                    else:
                         company_shipping_address_pdf_lines = ["Shipping address not set, billing address not found."]
                else:
                    company_shipping_address_pdf_lines = ["No shipping or billing address configured for company."]

            # Fetch Billing Address (for Header)
            company_billing_address_id = company_info_dict.get('billing_address_id')
            if company_billing_address_id:
                addr_tuple = db_handler.get_address(company_billing_address_id)
                if addr_tuple:
                    company_billing_address_pdf_lines = [
                        addr_tuple[0] or "",
                        f"{addr_tuple[1] or ""}, {addr_tuple[2] or ""} {addr_tuple[3] or ""}",
                        addr_tuple[4] or ""
                    ]
                    company_billing_address_pdf_lines = [line for line in company_billing_address_pdf_lines if line.strip()]
                    if not company_billing_address_pdf_lines:
                        company_billing_address_pdf_lines = ["Billing address details missing."]
                else:
                    company_billing_address_pdf_lines = ["Billing address not found in DB (ID existed)."]
            else:
                company_billing_address_pdf_lines = ["Billing address ID not configured for company."]
        else:
            company_shipping_address_pdf_lines = ["Company information not found in database."]
            company_billing_address_pdf_lines = ["Company information not found in database."]


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
            po_document_number=doc.document_number,
            company_name=company_name_for_header,
            company_billing_address_lines=company_billing_address_pdf_lines
        )
        pdf.alias_nb_pages() # For total page numbers
        pdf.add_page()

        # --- PDF Content Generation ---
        line_height = 7
        col_width_full = pdf.w - 2 * pdf.l_margin # Full width for content

        # Document Details Section (PO Number, Date, Status)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(col_width_full / 2, line_height, f"PO Number: {doc.document_number}", 0, 0, "L")
        pdf.set_font("Arial", "", 11)
        pdf.cell(col_width_full / 2, line_height, f"Date: {doc.created_date.split('T')[0] if doc.created_date else 'N/A'}", 0, 1, "R")
        pdf.cell(col_width_full / 2, line_height, "", 0, 0, "L") # Empty cell for alignment
        pdf.cell(col_width_full / 2, line_height, f"Status: {doc.status.value if doc.status else 'N/A'}", 0, 1, "R")
        pdf.ln(line_height * 1.5)

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
                pdf.multi_cell(desc_col, line_height, item.product_description or "", 1, "L")
                end_y_desc = pdf.get_y()

                pdf.set_xy(start_x + desc_col, start_y) # Reset X position for next cells in the row

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
