import { useState, useRef } from "react"
import { uploadAudio } from "../api/cogniscribe"
import LoadingSpinner from "./LoadingSpinner"

const SUBJECTS = [
  { value: "", label: "General" },
  { value: "anatomy", label: "Anatomy" },
  { value: "physiology", label: "Physiology" },
  { value: "pharmacology", label: "Pharmacology" },
  { value: "pathophysiology", label: "Pathophysiology" },
  { value: "clinical skills", label: "Clinical Skills" },
  { value: "nursing fundamentals", label: "Nursing Fundamentals" },
  { value: "biochemistry", label: "Biochemistry" },
  { value: "microbiology", label: "Microbiology" },
]

export default function UploadCard({ onResult, onUploadStart, onError, isProcessing }) {
  const [file, setFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [subject, setSubject] = useState("")
  const [ratio, setRatio] = useState(0.15)
  const [error, setError] = useState("")
  const fileInputRef = useRef(null)

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      handleFileSelect(droppedFile)
    }
  }

  const handleFileSelect = (selectedFile) => {
    const validTypes = ['audio/wav', 'audio/mpeg', 'audio/mp4', 'audio/flac', 'audio/ogg', 'audio/aac', 'audio/x-m4a']
    
    if (!validTypes.includes(selectedFile.type) && !selectedFile.name.match(/\.(wav|mp3|m4a|flac|ogg|aac|wma)$/i)) {
      setError('Please upload a valid audio file (MP3, WAV, M4A, FLAC, OGG, AAC, WMA)')
      return
    }

    const maxSize = 500 * 1024 * 1024 // 500MB
    if (selectedFile.size > maxSize) {
      setError('File size exceeds 500MB limit')
      return
    }

    setFile(selectedFile)
    setError("")
  }

  const handleFileInput = (e) => {
    if (e.target.files[0]) {
      handleFileSelect(e.target.files[0])
    }
  }

  const handleSubmit = async () => {
    if (!file) {
      setError('Please select a file first')
      return
    }

    onUploadStart()
    setError("")

    try {
      const result = await uploadAudio(file, ratio, subject)
      onResult(result)
    } catch (err) {
      setError(err.message || 'Failed to process audio. Please try again.')
      onError()
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`
          border-3 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all
          ${isDragging 
            ? 'border-blue-500 bg-blue-50' 
            : file 
            ? 'border-green-400 bg-green-50'
            : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*"
          onChange={handleFileInput}
          className="hidden"
          disabled={isProcessing}
        />
        
        {file ? (
          <div className="space-y-3">
            <div className="text-5xl">🎵</div>
            <div>
              <p className="text-lg font-semibold text-gray-800">{file.name}</p>
              <p className="text-sm text-gray-500 mt-1">{formatFileSize(file.size)}</p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation()
                setFile(null)
              }}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              disabled={isProcessing}
            >
              Change file
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="text-5xl">🎙️</div>
            <div>
              <p className="text-lg font-semibold text-gray-800">Drop your lecture audio here</p>
              <p className="text-sm text-gray-500 mt-1">or click to browse files</p>
            </div>
            <p className="text-xs text-gray-400">MP3, WAV, M4A, FLAC, OGG, AAC, WMA (up to 500MB)</p>
          </div>
        )}
      </div>

      <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-800">
        Educational use only. Do not upload live clinical data or PHI. Not for diagnosis, treatment, or clinical decision-making.
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm whitespace-pre-wrap">
          ⚠️ {error}
        </div>
      )}

      {/* Settings */}
      <div className="mt-8 space-y-6">
        {/* Subject Selector */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            📚 Subject (Optional)
          </label>
          <select
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            disabled={isProcessing}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            {SUBJECTS.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">Helps tailor the summary to your specific subject</p>
        </div>

        {/* Summary Length Slider */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            📝 Summary Length: {ratio === 0.05 ? 'Very Brief' : ratio === 0.10 ? 'Brief' : ratio === 0.15 ? 'Balanced' : ratio === 0.20 ? 'Detailed' : 'Comprehensive'}
          </label>
          <input
            type="range"
            min="0.05"
            max="0.30"
            step="0.05"
            value={ratio}
            onChange={(e) => setRatio(parseFloat(e.target.value))}
            disabled={isProcessing}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Quick</span>
            <span>Balanced</span>
            <span>Thorough</span>
          </div>
        </div>
      </div>

      {/* Submit Button */}
      <button
        onClick={handleSubmit}
        disabled={!file || isProcessing}
        className="w-full mt-8 bg-gradient-to-r from-blue-600 to-teal-600 text-white font-semibold py-4 px-6 rounded-xl hover:from-blue-700 hover:to-teal-700 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
      >
        {isProcessing ? (
          <span className="flex items-center justify-center gap-3">
            <LoadingSpinner />
            Processing your lecture...
          </span>
        ) : (
          <span className="flex items-center justify-center gap-2">
            ✨ Generate Study Notes
          </span>
        )}
      </button>

      {isProcessing && (
        <div className="mt-4 text-center">
          <p className="text-sm text-gray-600">This may take a few minutes depending on the audio length...</p>
          <div className="mt-3 flex justify-center gap-2">
            <span className="inline-block w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
            <span className="inline-block w-2 h-2 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
            <span className="inline-block w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
          </div>
        </div>
      )}
    </div>
  )
}
