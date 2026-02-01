import { useState } from 'react'
import axios from 'axios'
import { FileText, Upload, CheckCircle2, XCircle, AlertCircle, Download } from 'lucide-react'

function App() {
  const [files, setFiles] = useState({
    invoice: null,
    packing_list: null,
    bill_of_lading: null
  })
  
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleDownload = () => {
    if (!result?.report_base64) return

    // Convert Base64 to binary
    const binaryString = atob(result.report_base64)
    const bytes = new Uint8Array(binaryString.length)
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i)
    }
    
    // Create Blob
    const blob = new Blob([bytes], { type: 'application/pdf' })
    
    // Create download link
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `Audit_Report_${result.data.invoice.invoice_number}.pdf`
    
    // Trigger download
    document.body.appendChild(link)
    link.click()
    
    // Cleanup
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  }

  const handleFileChange = (type, file) => {
    setFiles(prev => ({ ...prev, [type]: file }))
    setResult(null)
    setError(null)
  }

  const handleAudit = async () => {
    if (!files.invoice || !files.packing_list || !files.bill_of_lading) {
      setError('Please upload all three documents')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('invoice', files.invoice)
    formData.append('packing_list', files.packing_list)
    formData.append('bill_of_lading', files.bill_of_lading)

    try {
      const response = await axios.post('http://127.0.0.1:8000/audit', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to audit documents')
    } finally {
      setLoading(false)
    }
  }

  const FileUploadCard = ({ title, type, icon: Icon }) => (
    <div className="bg-white rounded-lg shadow-md p-6 border-2 border-gray-200 hover:border-blue-400 transition-all">
      <div className="flex items-center gap-3 mb-4">
        <Icon className="w-6 h-6 text-blue-600" />
        <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
      </div>
      <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors">
        <div className="flex flex-col items-center justify-center pt-5 pb-6">
          <Upload className="w-8 h-8 text-gray-400 mb-2" />
          <p className="text-sm text-gray-500">
            {files[type] ? files[type].name : 'Click to upload PDF'}
          </p>
        </div>
        <input
          type="file"
          className="hidden"
          accept=".pdf"
          onChange={(e) => handleFileChange(type, e.target.files[0])}
        />
      </label>
    </div>
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-3">FreightVerify</h1>
          <p className="text-xl text-gray-600">AI-Powered Logistics Document Validator</p>
        </div>

        {/* Upload Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <FileUploadCard title="Commercial Invoice" type="invoice" icon={FileText} />
          <FileUploadCard title="Packing List" type="packing_list" icon={FileText} />
          <FileUploadCard title="Bill of Lading" type="bill_of_lading" icon={FileText} />
        </div>

        {/* Audit Button */}
        <div className="flex justify-center mb-8">
          <button
            onClick={handleAudit}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold text-lg px-16 py-4 rounded-lg shadow-lg transition-all transform hover:scale-105 disabled:transform-none disabled:cursor-not-allowed"
          >
            {loading ? 'ANALYZING...' : 'AUDIT DOCUMENTS'}
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border-2 border-red-300 rounded-lg p-4 mb-8">
            <div className="flex items-center gap-2 text-red-800">
              <AlertCircle className="w-5 h-5" />
              <p className="font-semibold">{error}</p>
            </div>
          </div>
        )}

        {/* Results Display */}
        {result && (
          <div className="bg-white rounded-lg shadow-xl p-8">
            {/* Status Badge */}
            <div className="flex items-center justify-center gap-3 mb-6">
              {result.passed ? (
                <div className="flex items-center gap-2 bg-green-100 text-green-800 px-6 py-3 rounded-full">
                  <CheckCircle2 className="w-6 h-6" />
                  <span className="font-bold text-lg">VALIDATION PASSED</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 bg-red-100 text-red-800 px-6 py-3 rounded-full">
                  <XCircle className="w-6 h-6" />
                  <span className="font-bold text-lg">VALIDATION FAILED</span>
                </div>
              )}
            </div>

            {/* Download Certificate Button */}
            {result.report_base64 && (
              <div className="flex justify-center mb-6">
                <button
                  onClick={handleDownload}
                  className="flex items-center gap-2 bg-slate-800 hover:bg-slate-900 text-white font-bold px-8 py-3 rounded-lg shadow-lg transition-all transform hover:scale-105"
                >
                  <Download className="w-5 h-5" />
                  Download Certificate
                </button>
              </div>
            )}

            {/* Errors List */}
            {!result.passed && result.errors.length > 0 && (
              <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4">
                <h4 className="font-bold text-red-800 mb-2">Validation Errors:</h4>
                <ul className="list-disc list-inside space-y-1">
                  {result.errors.map((err, idx) => (
                    <li key={idx} className="text-red-700">{err}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Extracted Data */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              {/* Invoice */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="font-bold text-blue-900 mb-3">Commercial Invoice</h4>
                <div className="space-y-2 text-sm">
                  <p><span className="font-semibold">Number:</span> {result.data.invoice.invoice_number}</p>
                  <p><span className="font-semibold">Amount:</span> {result.data.invoice.total_amount} {result.data.invoice.currency}</p>
                  <p><span className="font-semibold">Line Items:</span> {result.data.invoice.line_items.length}</p>
                </div>
              </div>

              {/* Packing List */}
              <div className="bg-green-50 rounded-lg p-4">
                <h4 className="font-bold text-green-900 mb-3">Packing List</h4>
                <div className="space-y-2 text-sm">
                  <p><span className="font-semibold">Weight:</span> {result.data.packing_list.gross_weight_kg} kg</p>
                  <p><span className="font-semibold">Packages:</span> {result.data.packing_list.total_packages}</p>
                  <p><span className="font-semibold">Total Units:</span> {result.data.packing_list.total_units_count}</p>
                </div>
              </div>

              {/* Bill of Lading */}
              <div className="bg-purple-50 rounded-lg p-4">
                <h4 className="font-bold text-purple-900 mb-3">Bill of Lading</h4>
                <div className="space-y-2 text-sm">
                  <p><span className="font-semibold">Number:</span> {result.data.bill_of_lading.bol_number}</p>
                  <p><span className="font-semibold">Weight:</span> {result.data.bill_of_lading.gross_weight_kg} kg</p>
                  <p><span className="font-semibold">Packages:</span> {result.data.bill_of_lading.package_count}</p>
                </div>
              </div>
            </div>

            {/* Line Items Table */}
            <div className="mt-6">
              <h4 className="font-bold text-gray-900 mb-4 text-lg">Invoice Line Items Breakdown</h4>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse border border-gray-300">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border border-gray-300 px-4 py-2 text-left">Description</th>
                      <th className="border border-gray-300 px-4 py-2 text-right">Quantity</th>
                      <th className="border border-gray-300 px-4 py-2 text-right">Unit Price</th>
                      <th className="border border-gray-300 px-4 py-2 text-right">Total Price</th>
                      <th className="border border-gray-300 px-4 py-2 text-center">Math Check</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.data.invoice.line_items.map((item, idx) => {
                      const calculated = item.quantity * item.unit_price
                      const hasMathError = Math.abs(calculated - item.total_price) > 0.05
                      const rowClass = hasMathError ? 'bg-red-100' : 'bg-white hover:bg-gray-50'
                      
                      return (
                        <tr key={idx} className={rowClass}>
                          <td className="border border-gray-300 px-4 py-2">{item.description}</td>
                          <td className="border border-gray-300 px-4 py-2 text-right">{item.quantity}</td>
                          <td className="border border-gray-300 px-4 py-2 text-right">
                            {item.unit_price.toFixed(2)} {result.data.invoice.currency}
                          </td>
                          <td className="border border-gray-300 px-4 py-2 text-right font-semibold">
                            {item.total_price.toFixed(2)} {result.data.invoice.currency}
                          </td>
                          <td className="border border-gray-300 px-4 py-2 text-center">
                            {hasMathError ? (
                              <span className="text-red-600 font-bold">❌ Error</span>
                            ) : (
                              <span className="text-green-600">✓</span>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                    <tr className="bg-gray-200 font-bold">
                      <td colSpan="3" className="border border-gray-300 px-4 py-2 text-right">TOTAL:</td>
                      <td className="border border-gray-300 px-4 py-2 text-right">
                        {result.data.invoice.total_amount.toFixed(2)} {result.data.invoice.currency}
                      </td>
                      <td className="border border-gray-300 px-4 py-2"></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
