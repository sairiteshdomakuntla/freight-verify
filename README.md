# FreightVerify - AI-Powered Logistics Document Validator

A vertical validator for logistics that uses **Google Gemini 1.5 Flash** to extract and validate data across three critical shipping documents: Commercial Invoice, Packing List, and Bill of Lading.

## 🚀 Features

- **AI-Powered Extraction**: Uses Google Gemini 1.5 Flash with strict JSON schema validation
- **Cross-Document Validation**: Validates weight and package count consistency across documents
- **Modern UI**: Clean React interface with TailwindCSS and Lucide icons
- **PDF Processing**: Converts PDF pages to images using PyMuPDF (fitz)
- **Real-time Results**: Instant validation feedback with color-coded status badges

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **Google Generative AI** - Gemini 1.5 Flash model
- **PyMuPDF (fitz)** - PDF to image conversion
- **Pydantic** - Data validation with strict schemas

### Frontend
- **React** - UI library
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Lucide React** - Icon library
- **Axios** - HTTP client

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- Google Gemini API Key

## 🔧 Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```

5. Start the backend server:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at `http://127.0.0.1:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## 🎯 Usage

1. Open the application in your browser at `http://localhost:5173`
2. Upload three PDF documents:
   - **Commercial Invoice** - Contains invoice number, total amount, and currency
   - **Packing List** - Contains gross weight and total packages
   - **Bill of Lading** - Contains BoL number, weight, and package count
3. Click the **AUDIT DOCUMENTS** button
4. View the results:
   - ✅ **Green Badge** - All validations passed
   - ❌ **Red Badge** - Validation errors found with detailed error list

## 🔍 Validation Rules

The system performs two critical validations:

1. **Weight Validation**: 
   - Checks if `|BoL.gross_weight_kg - PackingList.gross_weight_kg| > 1.0`
   - Error if weight difference exceeds 1 kg

2. **Package Count Validation**:
   - Checks if `BoL.package_count != PackingList.total_packages`
   - Error if package counts don't match exactly

## 📊 API Endpoints

### `POST /audit`
Upload and validate three shipping documents.

**Request:**
- `invoice`: PDF file (multipart/form-data)
- `packing_list`: PDF file (multipart/form-data)
- `bill_of_lading`: PDF file (multipart/form-data)

**Response:**
```json
{
  "data": {
    "invoice": {
      "invoice_number": "INV-2024-001",
      "total_amount": 15000.50,
      "currency": "USD"
    },
    "packing_list": {
      "gross_weight_kg": 2500.0,
      "total_packages": 25
    },
    "bill_of_lading": {
      "gross_weight_kg": 2500.0,
      "package_count": 25,
      "bol_number": "BOL-2024-001"
    }
  },
  "passed": true,
  "errors": []
}
```

### `GET /`
Health check endpoint.

## 🏗️ Project Structure

```
freight-verify/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Environment variables (not in git)
│   └── venv/                # Virtual environment
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── main.jsx         # Entry point
│   │   └── assets/
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 🔐 Security Notes

- Never commit your `.env` file or API keys to version control
- The API key in `.env` is loaded using `python-dotenv`
- CORS is configured to allow requests only from `http://localhost:5173`

## 🐛 Troubleshooting

### Backend Issues

**Error: "GEMINI_API_KEY not found"**
- Ensure `.env` file exists in the `backend/` directory
- Verify the API key is correctly set in `.env`

**Error: "Module not found"**
- Run `pip install -r requirements.txt` in the backend directory
- Activate your virtual environment if using one

### Frontend Issues

**Error: "axios is not defined"**
- Run `npm install` in the frontend directory

**CORS errors**
- Ensure backend is running on `http://127.0.0.1:8000`
- Check CORS settings in `main.py`

## 📝 Development Notes

- The Google Gemini model uses **response_schema** to enforce strict Pydantic JSON output
- PDF processing converts only the first page to an image
- Images are converted to PNG format at 150 DPI for optimal OCR quality
- The validation logic is extensible for additional business rules

## 🚦 Current Status

✅ Backend API running on http://127.0.0.1:8000  
✅ Frontend running on http://localhost:5173  
✅ Ready to upload and validate documents!

## 📄 License

This project is for demonstration purposes.

---

**Built with ❤️ using FastAPI, React, and Google Gemini**
