from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
from pydantic import BaseModel
from typing import List, Optional
import fitz  # PyMuPDF
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from report_generator import generate_audit_pdf

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Google Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Pydantic Models
class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total_price: float

class Invoice(BaseModel):
    invoice_number: str
    currency: str
    total_amount: float
    line_items: List[LineItem]

class PackingList(BaseModel):
    gross_weight_kg: float
    total_packages: int
    total_units_count: float

class BillOfLading(BaseModel):
    gross_weight_kg: float
    package_count: int
    bol_number: str

class ExtractionData(BaseModel):
    invoice: Invoice
    packing_list: PackingList
    bill_of_lading: BillOfLading

class AuditResponse(BaseModel):
    data: ExtractionData
    passed: bool
    errors: List[str]
    report_base64: Optional[str] = None

def pdf_to_image_parts(file_bytes: bytes) -> List[dict]:
    """Convert ALL pages of a PDF to image parts for Gemini"""
    # Open PDF with PyMuPDF
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    image_parts = []
    
    # Process every page in the PDF
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Convert to pixmap then to PIL Image
        pix = page.get_pixmap(dpi=150)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Convert to bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        
        # Add Gemini-compatible image part
        image_parts.append({
            'mime_type': 'image/png',
            'data': img_bytes.read()
        })
    
    doc.close()
    return image_parts

@app.post("/audit", response_model=AuditResponse)
async def audit_documents(
    invoice: UploadFile = File(...),
    packing_list: UploadFile = File(...),
    bill_of_lading: UploadFile = File(...)
):
    # Read PDF files
    invoice_bytes = await invoice.read()
    packing_bytes = await packing_list.read()
    bol_bytes = await bill_of_lading.read()
    
    # Convert PDFs to image parts (handles multi-page documents)
    invoice_parts = pdf_to_image_parts(invoice_bytes)
    packing_parts = pdf_to_image_parts(packing_bytes)
    bol_parts = pdf_to_image_parts(bol_bytes)
    
    # Initialize Gemini model with response schema
    model = genai.GenerativeModel(
        "models/gemini-2.5-flash",
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": ExtractionData
        }
    )
    
    # Craft the prompt
    prompt = f"""Analyze these 3 shipping documents and extract the data perfectly.

The documents are provided as images in this order:
- Commercial Invoice: {len(invoice_parts)} page(s)
- Packing List: {len(packing_parts)} page(s)  
- Bill of Lading: {len(bol_parts)} page(s)

From the Commercial Invoice (first {len(invoice_parts)} image(s)):
- invoice_number: The invoice number as a string
- currency: The currency code (e.g., "USD", "EUR")
- total_amount: The total invoice amount as a float
- line_items: Extract EVERY line item from the invoice table as an array. For each item:
  * description: Item description/product name
  * quantity: Quantity ordered (as float)
  * unit_price: Price per unit (as float)
  * total_price: Total price for that line (as float)

From the Packing List (next {len(packing_parts)} image(s)):
- gross_weight_kg: The gross weight in kilograms as a float
- total_packages: The total number of packages as an integer
- total_units_count: Sum of ALL quantities of goods listed (count every single unit across all items)

From the Bill of Lading (last {len(bol_parts)} image(s)):
- gross_weight_kg: The gross weight in kilograms as a float
- package_count: The package count as an integer
- bol_number: The Bill of Lading number as a string

IMPORTANT: Scan through ALL pages of each document to find the required information. Tables and data may span multiple pages.
Extract all values accurately from the documents."""
    
    # Generate content with all pages from all 3 documents
    content = [prompt] + invoice_parts + packing_parts + bol_parts
    response = model.generate_content(content)
    
    # Parse the JSON response into ExtractionData
    import json
    extraction = ExtractionData.model_validate_json(response.text)
    
    # Deep Audit Logic - Validation with Enhanced Checks
    errors = []
    
    # 1. Line Item Math Check - Verify quantity * unit_price == total_price for each item
    for item in extraction.invoice.line_items:
        calculated_total = item.quantity * item.unit_price
        if abs(calculated_total - item.total_price) > 0.05:
            errors.append(
                f"Math Error in '{item.description}': {item.quantity} × {item.unit_price} = {calculated_total:.2f} "
                f"but total shows {item.total_price}"
            )
    
    # 2. Invoice Sum Check - Verify line items sum matches invoice total
    line_items_sum = sum(item.total_price for item in extraction.invoice.line_items)
    if abs(line_items_sum - extraction.invoice.total_amount) > 0.05:
        errors.append(
            f"Invoice Mismatch: Line items sum to {line_items_sum:.2f} "
            f"but Total is {extraction.invoice.total_amount}"
        )
    
    # 3. Unit Match Check - Verify invoice quantities match packing list total units
    invoice_total_units = sum(item.quantity for item in extraction.invoice.line_items)
    if abs(invoice_total_units - extraction.packing_list.total_units_count) > 0.01:
        errors.append(
            f"Quantity Mismatch: Invoice has {invoice_total_units} units, "
            f"Packing List has {extraction.packing_list.total_units_count} units"
        )
    
    # 4. Weight Check (Existing v1 Logic)
    if abs(extraction.bill_of_lading.gross_weight_kg - extraction.packing_list.gross_weight_kg) > 1.0:
        errors.append("Weight mismatch between Bill of Lading and Packing List")
    
    # 5. Package Count Check (Existing v1 Logic)
    if extraction.bill_of_lading.package_count != extraction.packing_list.total_packages:
        errors.append("Package count mismatch between Bill of Lading and Packing List")
    
    passed = len(errors) == 0
    
    # Generate PDF audit certificate
    report_base64 = generate_audit_pdf(extraction, errors)
    
    return AuditResponse(
        data=extraction,
        passed=passed,
        errors=errors,
        report_base64=report_base64
    )

@app.get("/")
async def root():
    return {"message": "FreightVerify API is running"}
