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
from core.pdf_generator import PDF

def generate_quote_pdf(sales_document_id: int, output_path: str = None):
    db_handler = None
    try:
        db_handler = DatabaseHandler()
        sales_logic = SalesLogic(db_handler)
        address_book_logic = AddressBookLogic(db_handler)

        doc: SalesDocument = sales_logic.get_sales_document_details(sales_document_id)
        if not doc:
            print(f"Error: Sales document with ID {sales_document_id} not found.")
            return

        company_info_dict = db_handler.get_company_information()
        company_name_for_header = "Your Company Name"
        company_phone_pdf = ""
        company_shipping_address_pdf_lines = ["Shipping address not found."]
        company_billing_address_pdf_lines = ["Billing address not found."]

        if company_info_dict:
            company_name_for_header = company_info_dict.get('name', company_name_for_header)
            company_phone_pdf = company_info_dict.get('phone', "")

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

        customer: Account = None
        customer_address: Address = None
        if doc.customer_id:
            customer = address_book_logic.get_account_details(doc.customer_id)
            if customer and customer.billing_address_id:
                customer_address = address_book_logic.get_address_obj(customer.billing_address_id)

        items: list[SalesDocumentItem] = sales_logic.get_items_for_sales_document(doc.id)

        pdf = PDF(
            document_number=doc.document_number,
            company_name=company_name_for_header,
            company_billing_address_lines=company_billing_address_pdf_lines,
            document_type="Quote"
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

        pdf.cell(col_width_half, line_height, company_name_for_header, 0, 1, "L")

        temp_x_offset = pdf.get_x()
        pdf.multi_cell(col_width_half, line_height, "\n".join(company_shipping_address_pdf_lines), 0, "L")
        y_after_company_address = pdf.get_y()
        pdf.set_xy(temp_x_offset, y_after_company_address)

        if company_phone_pdf:
            pdf.cell(col_width_half, line_height, f"Phone: {company_phone_pdf}", 0, 1, "L")

        y_after_company_info = pdf.get_y()

        pdf.set_xy(current_x + col_width_half + 10, current_y)

        pdf.set_font("Arial", "B", 11)
        pdf.cell(col_width_half, line_height, "Customer:", 0, 1, "L")
        pdf.set_font("Arial", "", 11)

        right_column_x = current_x + col_width_half + 10

        if customer:
            pdf.set_x(right_column_x)
            pdf.cell(col_width_half, line_height, customer.name or "N/A", 0, 1, "L")

            if customer_address:
                pdf.set_x(right_column_x)
                pdf.multi_cell(col_width_half, line_height,
                               f"{customer_address.street or ''}\n"
                               f"{customer_address.city or ''}, {customer_address.state or ''} {customer_address.zip_code or ''}\n"
                               f"{customer_address.country or ''}".strip(),
                               0, "L")
            else:
                pdf.set_x(right_column_x)
                pdf.cell(col_width_half, line_height, "No address on file.", 0, 1, "L")

            if customer.phone:
                pdf.set_x(right_column_x)
                pdf.cell(col_width_half, line_height, f"Phone: {customer.phone}", 0, 1, "L")
        else:
            pdf.set_x(right_column_x)
            pdf.cell(col_width_half, line_height, "Customer details not available.", 0, 1, "L")

        y_after_customer_info = pdf.get_y()

        pdf.set_y(max(y_after_company_info, y_after_customer_info))
        pdf.ln(line_height * 1.5)

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
                pdf.multi_cell(desc_col, line_height, item.product_description or "", 1, "L")
                end_y_desc = pdf.get_y()

                pdf.set_xy(start_x + desc_col, start_y)

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

        filename = output_path or f"quote_{doc.document_number.replace('/', '_')}.pdf"
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
    parser = argparse.ArgumentParser(description="Generate a Quote PDF from existing application data.")
    parser.add_argument("sales_document_id", type=int, help="The ID of the sales document to generate.")
    parser.add_argument("--output", type=str, help="Optional: Full path for the output PDF file.")
    args = parser.parse_args()

    if args.sales_document_id:
        generate_quote_pdf(args.sales_document_id, args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
