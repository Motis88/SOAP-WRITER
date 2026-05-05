import { useState, useCallback } from 'react'
import { parsePDF } from '../services/api.js'

export default function PDFUpload({ onParsed, onLoading }) {
  const [dragging, setDragging] = useState(false)
  const [fileName, setFileName] = useState(null)
  const [error, setError] = useState(null)

  const handle = useCallback(
    async (file) => {
      if (!file) return
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        setError('יש להעלות קובץ PDF בלבד')
        return
      }
      setFileName(file.name)
      setError(null)
      onLoading(true, 'מפענח PDF...')
      try {
        const result = await parsePDF(file)
        onParsed(result)
      } catch {
        setError('שגיאה בפענוח ה-PDF')
      } finally {
        onLoading(false, '')
      }
    },
    [onParsed, onLoading],
  )

  return (
    <div
      className={`pdf-drop ${dragging ? 'drag-over' : ''}`}
      onDrop={(e) => { e.preventDefault(); setDragging(false); handle(e.dataTransfer.files[0]) }}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
    >
      <input
        id="pdf-file"
        type="file"
        accept=".pdf"
        style={{ display: 'none' }}
        onChange={(e) => handle(e.target.files[0])}
      />
      <label htmlFor="pdf-file" className="pdf-label">
        <span className="pdf-icon">📄</span>
        <span>{fileName || 'גרור PDF לכאן או לחץ להעלאה'}</span>
      </label>
      {error && <p className="err">{error}</p>}
    </div>
  )
}
