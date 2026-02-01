from fpdf import FPDF
from typing import List
from datetime import datetime
import base64
from io import BytesIO


def generate_audit_pdf(data, errors: List[str]) -> str:
    """
    Generate a professional audit certificate PDF and return it as a Base64 string.
    
    Args:
        data: ExtractionData object containing invoice, packing_list, and bill_of_lading
        errors: List of error strings (empty if audit passed)
    
    Returns:
        Base64 encoded PDF string
    """
    pdf = FPDF()
    pdf.add_page()
    
    # ==================== HEADER ====================
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "YOUR-COMPANY-NAME", ln=True, align="C")
    
    # Sub-header
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 6, "OFFICIAL AUDIT CERTIFICATE", ln=True, align="C")
    pdf.ln(5)
    
    # ==================== STATUS BOX ====================
    pdf.set_text_color(0, 0, 0)
    
    if len(errors) == 0:
        # PASSED - Green Box
        pdf.set_fill_color(34, 197, 94)  # Green
        pdf.set_text_color(255, 255, 255)  # White text
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 12, "PASSED / COMPLIANT", ln=True, align="C", fill=True)
    else:
        # FAILED - Red Box
        pdf.set_fill_color(239, 68, 68)  # Red
        pdf.set_text_color(255, 255, 255)  # White text
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 12, "FAILED / DISCREPANCIES FOUND", ln=True, align="C", fill=True)
    
    pdf.ln(8)
    pdf.set_text_color(0, 0, 0)  # Reset to black
    
    # ==================== SUMMARY TABLE ====================
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Document Summary", ln=True)
    pdf.ln(2)
    
    # Table styling
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    
    # Table header
    pdf.cell(70, 8, "Field", border=1, fill=True)
    pdf.cell(120, 8, "Value", border=1, fill=True, ln=True)
    
    # Table rows
    pdf.set_font("Arial", "", 10)
    
    # Invoice Number
    pdf.cell(70, 8, "Invoice Number", border=1)
    pdf.cell(120, 8, data.invoice.invoice_number, border=1, ln=True)
    
    # BOL Number
    pdf.cell(70, 8, "Bill of Lading Number", border=1)
    pdf.cell(120, 8, data.bill_of_lading.bol_number, border=1, ln=True)
    
    # Total Weight
    pdf.cell(70, 8, "Total Weight (kg)", border=1)
    pdf.cell(120, 8, f"{data.packing_list.gross_weight_kg} kg", border=1, ln=True)
    
    # Total Packages
    pdf.cell(70, 8, "Total Packages", border=1)
    pdf.cell(120, 8, str(data.packing_list.total_packages), border=1, ln=True)
    
    # Invoice Total
    pdf.cell(70, 8, "Invoice Total Amount", border=1)
    pdf.cell(120, 8, f"{data.invoice.total_amount} {data.invoice.currency}", border=1, ln=True)
    
    # Total Units
    pdf.cell(70, 8, "Total Units Count", border=1)
    pdf.cell(120, 8, str(data.packing_list.total_units_count), border=1, ln=True)
    
    pdf.ln(8)
    
    # ==================== ERROR LIST (if failed) ====================
    if len(errors) > 0:
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(239, 68, 68)  # Red
        pdf.cell(0, 8, "Discrepancies Found:", ln=True)
        pdf.ln(2)
        
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(239, 68, 68)  # Red
        
        for i, error in enumerate(errors, 1):
            # Bullet point (using asterisk for latin-1 compatibility)
            pdf.cell(5, 6, "", ln=False)  # Indent
            pdf.multi_cell(0, 6, f"* {error}")
        
        pdf.ln(3)
        pdf.set_text_color(0, 0, 0)  # Reset to black
    
    # ==================== LINE ITEMS SECTION ====================
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Invoice Line Items", ln=True)
    pdf.ln(2)
    
    # Line items table header
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(80, 7, "Description", border=1, fill=True)
    pdf.cell(25, 7, "Quantity", border=1, fill=True, align="R")
    pdf.cell(30, 7, "Unit Price", border=1, fill=True, align="R")
    pdf.cell(35, 7, "Total Price", border=1, fill=True, align="R", ln=True)
    
    # Line items data
    pdf.set_font("Arial", "", 9)
    for item in data.invoice.line_items:
        # Handle long descriptions with multi_cell
        x_before = pdf.get_x()
        y_before = pdf.get_y()
        
        # Description (may wrap)
        pdf.multi_cell(80, 7, item.description, border=1)
        y_after = pdf.get_y()
        height = y_after - y_before
        
        # Move back up for other cells
        pdf.set_xy(x_before + 80, y_before)
        
        # Other cells with same height
        pdf.cell(25, height, str(item.quantity), border=1, align="R")
        pdf.cell(30, height, f"{item.unit_price:.2f}", border=1, align="R")
        pdf.cell(35, height, f"{item.total_price:.2f}", border=1, align="R", ln=True)
    
    # Total row
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(135, 7, "TOTAL", border=1, fill=True, align="R")
    pdf.cell(35, 7, f"{data.invoice.total_amount:.2f} {data.invoice.currency}", border=1, fill=True, align="R", ln=True)
    
    pdf.ln(10)
    
    # ==================== FOOTER ====================
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 5, f"Generated by YOUR-COMPANY-NAME AI Compliance Engine | {timestamp}", ln=True, align="C")
    
    # ==================== CONVERT TO BASE64 ====================
    # Generate PDF in memory
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    
    # Convert to Base64
    base64_string = base64.b64encode(pdf_bytes).decode('utf-8')
    
    return base64_string
