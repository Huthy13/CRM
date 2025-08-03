import datetime
import os
from core.pdf_generator import PDF, get_company_pdf_context
from core.company_repository import CompanyRepository
from core.company_service import CompanyService
from core.address_service import AddressService
from core.repositories import AddressRepository, AccountRepository
from shared.structs import SalesDocument


def generate_packing_slip(sales_logic, doc_id: int, shipped_items, remaining_items, output_path: str | None = None):
    """Generate a packing slip PDF for the given shipment data."""
    db = sales_logic.db
    address_repo = AddressRepository(db)
    account_repo = AccountRepository(db)
    address_service = AddressService(address_repo, account_repo)
    company_repo = CompanyRepository(db)
    company_service = CompanyService(company_repo, address_service)

    (
        company_name,
        _company_phone,
        _shipping_lines,
        remittance_lines,
        _billing_lines,
    ) = get_company_pdf_context(company_service)

    doc: SalesDocument = sales_logic.get_sales_document_details(doc_id)

    pdf = PDF(
        document_number=doc.document_number,
        company_name=company_name,
        company_billing_address_lines=remittance_lines,
        document_type="Packing Slip",
    )
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Date: {datetime.date.today().isoformat()}", 0, 1, "R")
    pdf.ln(5)

    line_height = 6
    desc_width = pdf.w - pdf.l_margin - pdf.r_margin - 30
    qty_width = 30

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, line_height, "Shipped Items", 0, 1)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(desc_width, line_height, "Description", 1, 0)
    pdf.cell(qty_width, line_height, "Qty", 1, 1, "R")
    pdf.set_font("Arial", "", 10)
    for desc, qty in shipped_items:
        pdf.cell(desc_width, line_height, str(desc), 1, 0)
        pdf.cell(qty_width, line_height, str(qty), 1, 1, "R")

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, line_height, "Remaining Items", 0, 1)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(desc_width, line_height, "Description", 1, 0)
    pdf.cell(qty_width, line_height, "Qty", 1, 1, "R")
    pdf.set_font("Arial", "", 10)
    for desc, qty in remaining_items:
        pdf.cell(desc_width, line_height, str(desc), 1, 0)
        pdf.cell(qty_width, line_height, str(qty), 1, 1, "R")

    if output_path is None:
        safe_number = doc.document_number.replace("/", "-")
        output_path = os.path.join(os.getcwd(), f"packing_slip_{safe_number}.pdf")
    pdf.output(output_path)
    return output_path
