import argparse
import os
import sys
import sqlite3

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.database import DatabaseHandler
from core.sales_logic import SalesLogic
from core.address_book_logic import AddressBookLogic
from shared.structs import SalesDocument, SalesDocumentItem, Account, Address
from shared.utils import sanitize_filename
from core.pdf_generator import PDF, get_company_pdf_context
from core.company_repository import CompanyRepository
from core.company_service import CompanyService
from core.address_service import AddressService
from core.repositories import AddressRepository, AccountRepository


def generate_sales_order_pdf(sales_document_id: int, output_path: str = None):
    db_handler = None
    try:
        db_handler = DatabaseHandler()
        sales_logic = SalesLogic(db_handler)
        address_book_logic = AddressBookLogic(db_handler)

        address_repo = AddressRepository(db_handler)
        account_repo = AccountRepository(db_handler)
        address_service = AddressService(address_repo, account_repo)
        company_repo = CompanyRepository(db_handler)
        company_service = CompanyService(company_repo, address_service)

        doc: SalesDocument = sales_logic.get_sales_document_details(sales_document_id)
        if not doc:
            print(f"Error: Sales document with ID {sales_document_id} not found.")
            return

        (
            company_name_for_header,
            company_phone_pdf,
            company_shipping_address_pdf_lines,
            company_remittance_address_pdf_lines,
            company_billing_address_pdf_lines,
        ) = get_company_pdf_context(company_service)

        customer: Account = None
        customer_billing_address: Address = None
        customer_shipping_address: Address = None
        if doc.customer_id:
            customer = address_book_logic.get_account_details(doc.customer_id)
            if customer:
                for address in customer.addresses:
                    if 'Billing' in address.types and 'Billing' in address.primary_types:
                        customer_billing_address = address
                    if 'Shipping' in address.types and 'Shipping' in address.primary_types:
                        customer_shipping_address = address
                if not customer_billing_address and any('Billing' in addr.types for addr in customer.addresses):
                    customer_billing_address = next(addr for addr in customer.addresses if 'Billing' in addr.types)
                if not customer_shipping_address and any('Shipping' in addr.types for addr in customer.addresses):
                    customer_shipping_address = next(addr for addr in customer.addresses if 'Shipping' in addr.types)

        items: list[SalesDocumentItem] = sales_logic.get_items_for_sales_document(doc.id)

        pdf = PDF(
            document_number=doc.document_number,
            company_name=company_name_for_header,
            company_billing_address_lines=company_remittance_address_pdf_lines,
            document_type="Sales Order",
        )
        pdf.alias_nb_pages()
        pdf.add_page()

        line_height = 7
        col_width_full = pdf.w - 2 * pdf.l_margin

        pdf.set_font("Arial", "", 11)
        date_str = f"Date: {doc.created_date.split('T')[0] if doc.created_date else 'N/A'}"
        pdf.cell(0, line_height, date_str, 0, 1, "R")
        pdf.ln(line_height * 1.5)

        col_width_half = col_width_full / 2 - 5

        current_x = pdf.get_x()
        current_y = pdf.get_y()

        pdf.set_font("Arial", "B", 11)
        pdf.cell(col_width_half, line_height, "Shipping Address:", 0, 1, "L")
        pdf.set_font("Arial", "", 11)

        if customer:
            pdf.cell(col_width_half, line_height, customer.name or "N/A", 0, 1, "L")
            if customer_shipping_address:
                pdf.multi_cell(
                    col_width_half,
                    line_height,
                    "\n".join(
                        filter(
                            None,
                            [
                                customer_shipping_address.street or "",
                                f"{customer_shipping_address.city or ''}, {customer_shipping_address.state or ''} {customer_shipping_address.zip_code or ''}",
                                (customer_shipping_address.country or "").strip(),
                            ],
                        )
                    ),
                    0,
                    "L",
                )
            else:
                pdf.cell(col_width_half, line_height, "No shipping address on file.", 0, 1, "L")
        else:
            pdf.cell(col_width_half, line_height, "Customer details not available.", 0, 1, "L")

        y_after_shipping_info = pdf.get_y()

        pdf.set_xy(current_x + col_width_half + 10, current_y)

        pdf.set_font("Arial", "B", 11)
        pdf.cell(col_width_half, line_height, "Billing Address:", 0, 1, "L")
        pdf.set_font("Arial", "", 11)

        right_column_x = current_x + col_width_half + 10

        if customer:
            pdf.set_x(right_column_x)
            pdf.cell(col_width_half, line_height, customer.name or "N/A", 0, 1, "L")

            if customer_billing_address:
                pdf.set_x(right_column_x)
                billing_lines = [
                    customer_billing_address.street or "",
                    f"{customer_billing_address.city or ''}, {customer_billing_address.state or ''} {customer_billing_address.zip_code or ''}",
                    (customer_billing_address.country or "").strip(),
                ]
                pdf.multi_cell(
                    col_width_half,
                    line_height,
                    "\n".join(filter(None, billing_lines)),
                    0,
                    "L",
                )
            else:
                pdf.set_x(right_column_x)
                pdf.cell(col_width_half, line_height, "No billing address on file.", 0, 1, "L")

            if customer.phone:
                pdf.set_x(right_column_x)
                pdf.cell(col_width_half, line_height, f"Phone: {customer.phone}", 0, 1, "L")
        else:
            pdf.set_x(right_column_x)
            pdf.cell(col_width_half, line_height, "Customer details not available.", 0, 1, "L")

        y_after_billing_info = pdf.get_y()

        pdf.set_y(max(y_after_shipping_info, y_after_billing_info))

        # Reference number and payment terms
        if doc.reference_number:
            pdf.set_font("Arial", "", 11)
            pdf.cell(0, line_height, f"Customer Reference: {doc.reference_number}", 0, 1, "L")
        term_name = None
        if customer and getattr(customer, "payment_term_id", None):
            term = address_book_logic.get_payment_term(customer.payment_term_id)
            if term:
                term_name = term.term_name
        if term_name:
            pdf.set_font("Arial", "", 11)
            pdf.cell(0, line_height, f"Terms: {term_name}", 0, 1, "L")

        pdf.ln(line_height)

        pdf.set_font("Arial", "B", 10)
        desc_col = col_width_full * 0.50
        qty_col = col_width_full * 0.10
        price_col = col_width_full * 0.20
        total_col = col_width_full * 0.20

        pdf.set_fill_color(220, 220, 220)
        pdf.cell(desc_col, line_height, "Product/Service Description", 1, 0, "C", 1)
        pdf.cell(qty_col, line_height, "Qty", 1, 0, "C", 1)
        pdf.cell(price_col, line_height, "Unit Price", 1, 0, "C", 1)
        pdf.cell(total_col, line_height, "Line Total", 1, 1, "C", 1)

        pdf.set_font("Arial", "", 9)
        document_subtotal = 0.0
        if items:
            for item in items:
                item.calculate_line_total()
                item_total = item.line_total if item.line_total is not None else 0.0
                if item.unit_price is None and item.quantity is not None and item_total != 0.0 and item.quantity != 0:
                    effective_unit_price = item_total / item.quantity
                else:
                    effective_unit_price = item.unit_price if item.unit_price is not None else 0.0

                document_subtotal += item_total

                start_x = pdf.get_x()
                start_y = pdf.get_y()
                product_info = (
                    sales_logic.product_repo.get_product_details(item.product_id)
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

                pdf.set_xy(start_x + desc_col, start_y)
                pdf.set_font("Arial", "", 9)
                pdf.cell(qty_col, end_y_desc - start_y, f"{item.quantity:.2f}" if item.quantity is not None else "0.00", 1, 0, "R")
                pdf.cell(price_col, end_y_desc - start_y, f"${effective_unit_price:.2f}", 1, 0, "R")
                pdf.cell(total_col, end_y_desc - start_y, f"${item_total:.2f}", 1, 0, "R")
                pdf.ln(end_y_desc - start_y)
        else:
            pdf.cell(col_width_full, line_height, "No items in this document.", 1, 1, "C")

        pdf.set_font("Arial", "B", 10)
        pdf.cell(desc_col + qty_col + price_col, line_height, "Subtotal:", 1, 0, "R")
        pdf.cell(total_col, line_height, f"${document_subtotal:.2f}", 1, 1, "R")

        pdf.ln(line_height * 1.5)

        if doc.notes and doc.notes.strip():
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, line_height, "Notes:", 0, 1, "L")
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(0, line_height, doc.notes.strip(), 0, "L")

        if output_path:
            filename = output_path
        else:
            sanitized_doc_number = sanitize_filename(doc.document_number)
            filename = f"SalesOrder_{sanitized_doc_number}.pdf"

        pdf.output(filename, "F")
        print(f"PDF generated: {filename}")

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


def main():
    parser = argparse.ArgumentParser(description="Generate a Sales Order PDF from existing application data.")
    parser.add_argument("sales_document_id", type=int, help="The ID of the sales document to generate.")
    parser.add_argument("--output", type=str, help="Optional: Full path for the output PDF file.")
    args = parser.parse_args()

    if args.sales_document_id:
        generate_sales_order_pdf(args.sales_document_id, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
