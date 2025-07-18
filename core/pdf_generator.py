import os
import sys
from fpdf import FPDF

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

class PDF(FPDF):
    def __init__(self, document_number=None, company_name="Your Company Name", company_billing_address_lines=None, document_type="Purchase Order"):
        super().__init__()
        self.document_number = document_number
        self.company_name = company_name
        self.company_billing_address_lines = company_billing_address_lines if company_billing_address_lines else []
        self.document_type = document_type

    def header(self):
        current_page_top_y = self.get_y()
        top_padding = 5

        header_content_start_y = current_page_top_y + top_padding

        address_line_height = 5
        company_name_line_height = 8
        title_line_height = 8

        drawable_width = self.w - self.l_margin - self.r_margin
        left_column_width = drawable_width * 0.6
        right_column_width = drawable_width * 0.4

        self.set_xy(self.l_margin, header_content_start_y)

        self.set_font("Arial", "B", 16)
        self.multi_cell(left_column_width, company_name_line_height, self.company_name, 0, "L")

        if self.company_billing_address_lines:
            self.set_font("Arial", "", 10)
            self.set_x(self.l_margin)
            for line in self.company_billing_address_lines:
                if line.strip():
                    self.multi_cell(left_column_width, address_line_height, line, 0, "L")

        y_after_left_block = self.get_y()

        self.set_xy(self.l_margin + left_column_width, header_content_start_y)

        self.set_font("Arial", "B", 14)
        title = self.document_type
        if self.document_number:
            title += f" - {self.document_number}"
        self.multi_cell(right_column_width, title_line_height, title, 0, "C")

        y_after_right_block = self.get_y()

        final_header_y = max(y_after_left_block, y_after_right_block)
        self.set_y(final_header_y)

        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", 0, 0, "C")
