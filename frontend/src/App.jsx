/**
 * App — main application component.
 *
 * Input panel:
 *   1. Free-text textarea
 *   2. RecordButton (Whisper STT)
 *   3. PDFUpload (IDEXX labs)
 *   4. "Process" button → calls /api/process
 *
 * Output panel:
 *   SOAPDisplay (S, O, A-empty, P-empty)
 */

import React, { useState, useCallback } from 'react'
import RecordButton from './components/RecordButton'
import PDFUpload from './components/PDFUpload'
import SOAPDisplay from './components/SOAPDisplay'
import { structureText } from './services/api'
import './App.css'

const EMPTY_NOTE = {
  subjective: [],
  objective: {
    physical_exam: [],
    vitals: { temp: null, hr: null, rr: null, weight: null },
    lab_results: { cbc: [], chemistry: [], electrolytes: [], snap: [], urinalysis: [] },
  },
  assessment: '',
  plan: '',
  flags: [],
}

export default function App() {
  const [inputText, setInputText] = useState('')
  const [pdfResult, setPdfResult] = useState(null)
  const [note, setNote] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Called when recording is transcribed
  function onTranscribed(text) {
    setInputText((prev) => (prev ? prev + '\n' + text : text))
  }

  // Called when PDF is parsed
  function onParsed(result) {
    setPdfResult(result)
    // Merge PDF labs into existing note if present
    setNote((prev) => {
      const base = prev || { ...EMPTY_NOTE }
      return {
        ...base,
        objective: {
          ...base.objective,
          lab_results: result.lab_results,
        },
        flags: [...new Set([...(base.flags || []), ...(result.flags || [])])],
      }
    })
  }

  async function handleProcess() {
    if (!inputText.trim() && !pdfResult) {
      setError('נדרש טקסט, הקלטה או קובץ PDF')
      return
    }
    setError('')
    setLoading(true)
    try {
      let newNote
      if (inputText.trim()) {
        newNote = await structureText(inputText)
      } else {
        newNote = { ...EMPTY_NOTE }
      }
      // Merge PDF lab results
      if (pdfResult) {
        newNote.objective.lab_results = pdfResult.lab_results
        newNote.flags = [...new Set([...(newNote.flags || []), ...(pdfResult.flags || [])])]
      }
      setNote(newNote)
    } catch (err) {
      setError(`שגיאה: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  function handleReset() {
    setInputText('')
    setPdfResult(null)
    setNote(null)
    setError('')
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-inner">
          <span className="app-logo">🐾</span>
          <div>
            <h1 className="app-title">SOAP Writer — תמלול וטרינרי</h1>
            <p className="app-subtitle">
              המרת קלט קולי / טקסט / PDF לרישום SOAP וטרינרי מסודר
            </p>
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="app-layout">
          {/* Input Panel */}
          <section className="panel input-panel">
            <h2 className="panel-title">קלט</h2>

            {/* Text input */}
            <div className="input-group">
              <label className="input-label">טקסט חופשי</label>
              <textarea
                className="text-input"
                rows={6}
                placeholder="הקלד תיאור ביקור וטרינרי (עברית / אנגלית / משולב)..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                dir="auto"
              />
            </div>

            {/* Recording */}
            <div className="input-group">
              <label className="input-label">הקלטה קולית</label>
              <RecordButton onTranscribed={onTranscribed} disabled={loading} />
            </div>

            {/* PDF upload */}
            <div className="input-group">
              <label className="input-label">בדיקות דם IDEXX (PDF)</label>
              <PDFUpload onParsed={onParsed} disabled={loading} />
              {pdfResult && (
                <p className="pdf-indicator">
                  ✅ PDF נטען — {pdfResult.report_type !== 'unknown' ? pdfResult.report_type : 'פורמט לא מוכר'}
                </p>
              )}
            </div>

            {/* Error */}
            {error && <p className="input-error">{error}</p>}

            {/* Actions */}
            <div className="input-actions">
              <button
                className="btn btn-primary"
                onClick={handleProcess}
                disabled={loading}
              >
                {loading ? 'מעבד...' : '⚡ עיבוד SOAP'}
              </button>
              <button
                className="btn btn-secondary"
                onClick={handleReset}
                disabled={loading}
              >
                🔄 איפוס
              </button>
            </div>
          </section>

          {/* Output Panel */}
          <section className="panel output-panel">
            <h2 className="panel-title">רישום SOAP</h2>
            {note ? (
              <SOAPDisplay note={note} onChange={setNote} />
            ) : (
              <div className="output-placeholder">
                <span className="placeholder-icon">📋</span>
                <p>הכנס קלט ולחץ על "עיבוד SOAP" לקבלת הרישום</p>
              </div>
            )}
          </section>
        </div>
      </main>

      <footer className="app-footer">
        <p>
          מערכת תמלול בלבד — ללא פרשנות רפואית, ללא אבחנות, ללא המלצות
        </p>
      </footer>
    </div>
  )
}
