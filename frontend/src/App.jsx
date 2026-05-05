import { useState, useCallback } from 'react'
import RecordButton from './components/RecordButton.jsx'
import PDFUpload from './components/PDFUpload.jsx'
import SOAPEditor from './components/SOAPEditor.jsx'
import { structureSOAP } from './services/api.js'

const EMPTY = {
  subjective: [],
  objective: {
    physical_exam: [],
    vitals: { temp: '', hr: '', rr: '', weight: '', bp: '' },
    lab_results: { cbc: [], chemistry: [], electrolytes: [], snap: [], urinalysis: [] },
  },
  assessment: '',
  plan: '',
  flags: [],
}

function formatSOAP(d) {
  const lr = d.objective.lab_results
  const v  = d.objective.vitals
  const lines = [
    'S (Subjective):',
    ...d.subjective.map((s) => `  - ${s}`),
    '',
    'O (Objective):',
    '',
    '  בדיקה גופנית:',
    ...d.objective.physical_exam.map((e) => `  - ${e}`),
    '',
    '  מדדים:',
    `  - Temp:   ${v.temp || 'לא נמסר'}`,
    `  - HR:     ${v.hr   || 'לא נמסר'}`,
    `  - RR:     ${v.rr   || 'לא נמסר'}`,
    `  - Weight: ${v.weight || 'לא נמסר'}`,
    ...(v.bp ? [`  - BP:     ${v.bp}`] : []),
  ]

  const labSection = (title, rows) => {
    if (!rows?.length) return []
    return ['', `  ${title}:`, ...rows.map((r) => `  - ${r.formatted}`)]
  }

  lines.push(
    ...labSection('CBC', lr.cbc),
    ...labSection('Chemistry', lr.chemistry),
    ...labSection('Electrolytes', lr.electrolytes),
    ...labSection('SNAP', lr.snap),
    ...labSection('Urinalysis', lr.urinalysis),
    '',
    'A (Assessment):',
    d.assessment ? `  ${d.assessment}` : '',
    '',
    'P (Plan):',
    d.plan ? `  ${d.plan}` : '',
  )
  return lines.join('\n')
}

export default function App() {
  const [soap, setSoap]           = useState(EMPTY)
  const [rawText, setRawText]     = useState('')
  const [loading, setLoading]     = useState(false)
  const [loadMsg, setLoadMsg]     = useState('')
  const [hasData, setHasData]     = useState(false)
  const [copied, setCopied]       = useState(false)

  const setLoad = (on, msg = '') => { setLoading(on); setLoadMsg(msg) }

  const processText = useCallback(async (text) => {
    if (!text.trim()) return
    setLoad(true, 'מבנה SOAP...')
    try {
      const result = await structureSOAP(text)
      setSoap((prev) => ({
        ...result,
        objective: {
          ...result.objective,
          lab_results: prev.objective.lab_results, // keep existing labs
        },
      }))
      setHasData(true)
    } catch {
      // keep existing state
    } finally {
      setLoad(false)
    }
  }, [])

  const handleTranscript = useCallback(
    (text) => { setRawText(text); processText(text) },
    [processText],
  )

  const handlePDF = useCallback((result) => {
    setSoap((prev) => ({
      ...prev,
      objective: { ...prev.objective, lab_results: result.lab_results },
      flags: [...new Set([...prev.flags, ...(result.flags || [])])],
    }))
    setHasData(true)
  }, [])

  const copyAll = () => {
    navigator.clipboard.writeText(formatSOAP(soap)).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  const reset = () => { setSoap(EMPTY); setRawText(''); setHasData(false) }

  return (
    <div className="app">
      {/* ── Header ────────────────────────────────── */}
      <header className="app-hdr">
        <div className="hdr-inner">
          <span className="logo">🩺</span>
          <div>
            <h1 className="app-title">SOAP Writer</h1>
            <p className="app-sub">מערכת תמלול ועיבוד רשומה וטרינרית</p>
          </div>
        </div>
      </header>

      {/* ── Main grid ─────────────────────────────── */}
      <main className="app-main">

        {/* Input panel */}
        <div className="panel input-panel">
          <h2 className="panel-title">קלט</h2>

          <div className="inp-sec">
            <label className="inp-label">🎙️ הקלטה קולית</label>
            <RecordButton onTranscript={handleTranscript} onLoading={setLoad} />
          </div>

          <div className="inp-sec">
            <label className="inp-label">✏️ טקסט חופשי</label>
            <textarea
              className="raw-ta"
              rows={7}
              value={rawText}
              placeholder="הקלד תיאור קליני בעברית / אנגלית..."
              onChange={(e) => setRawText(e.target.value)}
            />
            <button
              className="submit-btn"
              disabled={loading || !rawText.trim()}
              onClick={() => processText(rawText)}
            >
              {loading ? loadMsg || 'מעבד...' : 'בנה SOAP ←'}
            </button>
          </div>

          <div className="inp-sec">
            <label className="inp-label">📄 בדיקות דם (PDF)</label>
            <PDFUpload onParsed={handlePDF} onLoading={setLoad} />
          </div>
        </div>

        {/* Output panel */}
        <div className="panel output-panel">
          <div className="out-hdr">
            <h2 className="panel-title">רשומת SOAP</h2>
            <div className="out-actions">
              <button className="copy-btn" disabled={!hasData} onClick={copyAll}>
                {copied ? '✓ הועתק!' : '📋 העתק הכל'}
              </button>
              <button className="reset-btn" onClick={reset}>איפוס</button>
            </div>
          </div>

          {loading && (
            <div className="loading">
              <div className="spinner" />
              <p>{loadMsg}</p>
            </div>
          )}

          {!loading && !hasData && (
            <div className="empty-state">
              <p>הזן טקסט, הקלט שמע, או העלה PDF בדיקות כדי להתחיל</p>
            </div>
          )}

          {!loading && hasData && (
            <SOAPEditor soapData={soap} onUpdate={setSoap} flags={soap.flags} />
          )}
        </div>

      </main>
    </div>
  )
}
