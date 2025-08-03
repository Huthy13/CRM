import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.database import DatabaseHandler
from core.sales_logic import SalesLogic
from core.address_book_logic import AddressBookLogic
from shared.structs import SalesDocumentItem, Account, Address
from shared.utils import sanitize_filename, address_has_type, address_is_primary_for
from core.pdf_generator import PDF, get_company_pdf_context
from core.repositories import AddressRepository, AccountRepository
from core.address_service import AddressService
from core.company_repository import CompanyRepository
from core.company_service import CompanyService


def generate_packing_slip_pdf(
    sales_document_id: int,
    shipments: dict[int, float],
    shipment_number: str,
    output_path: str | None = None,
    db_handler: DatabaseHandler | None = None,
):
    """Generate a packing slip PDF for the specified shipment.

    Args:
        sales_document_id: ID of the sales order.
        shipments: Mapping of sales document item IDs to shipped quantities.
        shipment_number: Identifier for this shipment used in the document header.
        output_path: Optional explicit path for the resulting PDF file.
    """
    close_db = False
    try:
        if db_handler is None:
            db_handler = DatabaseHandler()
            close_db = True
        sales_logic = SalesLogic(db_handler)
        address_book_logic = AddressBookLogic(db_handler)

        address_repo = AddressRepository(db_handler)
        account_repo = AccountRepository(db_handler)
        address_service = AddressService(address_repo, account_repo)
        company_repo = CompanyRepository(db_handler)
        company_service = CompanyService(company_repo, address_service)

        doc = sales_logic.get_sales_document_details(sales_document_id)
        if not doc:
            print(f"Error: Sales document with ID {sales_document_id} not found.")
            return

        (
            company_name_for_header,
            _company_phone,
            company_shipping_address_pdf_lines,
            _company_remittance_address_pdf_lines,
            _company_billing_address_pdf_lines,
        ) = get_company_pdf_context(company_service)

        customer: Account | None = None
        customer_shipping_address: Address | None = None
        if doc.customer_id:
            customer = address_book_logic.get_account_details(doc.customer_id)
            if customer:
                for addr in customer.addresses:
                    if address_is_primary_for(addr, "Shipping"):
                        customer_shipping_address = addr
                        break
                if (
                    not customer_shipping_address
                    and any(address_has_type(addr, "Shipping") for addr in customer.addresses)
                ):
                    customer_shipping_address = next(
                        addr for addr in customer.addresses if address_has_type(addr, "Shipping")
                    )

        shipped_items: list[tuple[str, float]] = []
        for item_id, qty in shipments.items():
            item: SalesDocumentItem = sales_logic.get_sales_document_item_details(item_id)
            if not item:
                continue
            description = item.product_description
            if item.product_id:
                prod = sales_logic.product_repo.get_product_details(item.product_id)
                if prod and prod.get("name"):
                    description = prod["name"]
            shipped_items.append((description, qty))

        pdf = PDF(
            document_number=shipment_number,
            company_name=company_name_for_header,
            company_billing_address_lines=company_shipping_address_pdf_lines,
            document_type="Packing Slip",
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
        pdf.set_font("Arial", "B", 11)
        pdf.cell(col_width_half, line_height, "Ship To:", 0, 1, "L")
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
        pdf.ln(line_height)

        pdf.set_font("Arial", "B", 10)
        desc_col = col_width_full * 0.80
        qty_col = col_width_full * 0.20
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(desc_col, line_height, "Product/Service Description", 1, 0, "C", 1)
        pdf.cell(qty_col, line_height, "Qty Shipped", 1, 1, "C", 1)
        pdf.set_font("Arial", "", 9)
        if shipped_items:
            for desc, qty in shipped_items:
                pdf.cell(desc_col, line_height, desc, 1, 0, "L")
                pdf.cell(qty_col, line_height, f"{qty:.2f}", 1, 1, "R")
        else:
            pdf.cell(col_width_full, line_height, "No items in this shipment.", 1, 1, "C")

        pdf.ln(line_height * 1.5)

        if output_path:
            filename = output_path
        else:
            sanitized_doc_number = sanitize_filename(shipment_number)
            filename = f"PackingSlip_{sanitized_doc_number}.pdf"

        pdf.output(filename, "F")
        print(f"PDF generated: {filename}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if db_handler and close_db:
            db_handler.close()


__all__ = ["generate_packing_slip_pdf"]
