/**
 * PDFUpload — drag & drop or click-to-upload for IDEXX PDF reports.
 * Calls onParsed(PDFParseResponse) when parsing is complete.
 */

import React, { useState, useCallback } from 'react'
import { parsePDF } from '../services/api'
import './PDFUpload.css'

export default function PDFUpload({ onParsed, disabled }) {
  const [dragging, setDragging] = useState(false)
  const [status, setStatus] = useState('')
  const [fileName, setFileName] = useState('')

  const processFile = useCallback(
    async (file) => {
      if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
        setStatus('נדרש קובץ PDF')
        return
      }
      setFileName(file.name)
      setStatus('מנתח PDF...')
      try {
        const result = await parsePDF(file)
        onParsed(result)
        setStatus('✅ הפענוח הסתיים')
      } catch (err) {
        setStatus(`שגיאה: ${err.message}`)
        console.error(err)
      }
    },
    [onParsed]
  )

  function onDragOver(e) {
    e.preventDefault()
    setDragging(true)
  }

  function onDragLeave() {
    setDragging(false)
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    processFile(file)
  }

  function onChange(e) {
    processFile(e.target.files[0])
    e.target.value = '' // reset so same file can be re-uploaded
  }

  return (
    <div
      className={`pdf-drop ${dragging ? 'drag-over' : ''} ${disabled ? 'disabled' : ''}`}
      onDragOver={disabled ? undefined : onDragOver}
      onDragLeave={disabled ? undefined : onDragLeave}
      onDrop={disabled ? undefined : onDrop}
    >
      <label className="pdf-drop-label">
        <input
          type="file"
          accept=".pdf,application/pdf"
          onChange={onChange}
          disabled={disabled}
          className="pdf-input-hidden"
        />
        <span className="pdf-icon">📄</span>
        <span className="pdf-text">
          {fileName
            ? `קובץ: ${fileName}`
            : 'גרור PDF לכאן או לחץ להעלאה'}
        </span>
      </label>
      {status && <p className="pdf-status">{status}</p>}
    </div>
  )
}
