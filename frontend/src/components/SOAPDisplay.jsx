/**
 * SOAPDisplay — renders the full SOAP note with inline editing support.
 *
 * Sections:
 *   S (Subjective) — editable list
 *   O (Objective)  — physical exam, vitals, lab results (table)
 *   A (Assessment) — empty header only
 *   P (Plan)       — empty header only
 *
 * Features:
 *   - Inline editing for S items and physical exam lines
 *   - Unclear fields highlighted in yellow
 *   - "Copy all" button
 *   - Flag badges
 */

import React, { useState, useCallback } from 'react'
import LabTable from './LabTable'
import './SOAPDisplay.css'

const FLAG_LABELS = {
  missing_data: 'חסר מידע',
  unclear_text: 'טקסט לא ברור',
  ocr_used: 'שימוש ב-OCR',
  partial_extraction: 'חילוץ חלקי',
  unknown_pdf_format: 'פורמט PDF לא מוכר',
}

function isUnclear(text) {
  return typeof text === 'string' && text.includes('[לא ברור]')
}

function EditableItem({ value, onChange }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(value)

  function commit() {
    onChange(draft)
    setEditing(false)
  }

  if (editing) {
    return (
      <span className="editable-active">
        <input
          className="inline-input"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commit}
          onKeyDown={(e) => { if (e.key === 'Enter') commit() }}
          autoFocus
        />
      </span>
    )
  }

  return (
    <span
      className={`editable-item ${isUnclear(value) ? 'unclear' : ''}`}
      onClick={() => { setDraft(value); setEditing(true) }}
      title="לחץ לעריכה"
    >
      {value || <em className="empty-hint">—</em>}
      <span className="edit-icon">✏️</span>
    </span>
  )
}

function EditableList({ items, onChange }) {
  function updateItem(idx, newVal) {
    const updated = [...items]
    updated[idx] = newVal
    onChange(updated)
  }

  if (!items || items.length === 0) {
    return <p className="empty-section">לא נמסר</p>
  }

  return (
    <ul className="soap-list">
      {items.map((item, i) => (
        <li key={i} className={isUnclear(item) ? 'unclear-li' : ''}>
          <EditableItem value={item} onChange={(v) => updateItem(i, v)} />
        </li>
      ))}
    </ul>
  )
}

function VitalsRow({ label, value }) {
  if (!value) return null
  return (
    <div className="vital-row">
      <span className="vital-label">{label}:</span>
      <span className="vital-value">{value}</span>
    </div>
  )
}

export default function SOAPDisplay({ note, onChange }) {
  const setSubjective = useCallback(
    (items) => onChange({ ...note, subjective: items }),
    [note, onChange]
  )

  const setPhysicalExam = useCallback(
    (items) => onChange({ ...note, objective: { ...note.objective, physical_exam: items } }),
    [note, onChange]
  )

  function buildTextOutput() {
    const s = note.subjective.join('\n')
    const v = note.objective.vitals
    const vitalsText = [
      v.temp ? `Temp: ${v.temp}` : '',
      v.hr   ? `HR: ${v.hr}`   : '',
      v.rr   ? `RR: ${v.rr}`   : '',
      v.weight ? `Weight: ${v.weight}` : '',
    ].filter(Boolean).join('\n')

    const exam = note.objective.physical_exam.join('\n')
    const lr = note.objective.lab_results

    function labSection(title, items) {
      if (!items || items.length === 0) return ''
      const rows = items.map((r) => {
        let line = `${r.test}: ${r.value}`
        if (r.unit) line += ` ${r.unit}`
        if (r.reference_range) line += ` (${r.reference_range})`
        if (r.flag) line += ` ${r.flag}`
        return line
      }).join('\n')
      return `${title}:\n${rows}`
    }

    return [
      'S (Subjective):\n' + s,
      'O (Objective):',
      exam ? 'בדיקה גופנית:\n' + exam : '',
      vitalsText ? 'מדדים:\n' + vitalsText : '',
      labSection('CBC', lr.cbc),
      labSection('Chemistry', lr.chemistry),
      labSection('Electrolytes', lr.electrolytes),
      labSection('SNAP', lr.snap),
      labSection('Urinalysis', lr.urinalysis),
      'A (Assessment):\n',
      'P (Plan):\n',
    ].filter(Boolean).join('\n\n')
  }

  async function copyAll() {
    try {
      await navigator.clipboard.writeText(buildTextOutput())
    } catch {
      // Fallback for environments without clipboard API
      const ta = document.createElement('textarea')
      ta.value = buildTextOutput()
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
  }

  if (!note) return null

  const lr = note.objective.lab_results
  const hasLabs =
    lr.cbc.length + lr.chemistry.length + lr.electrolytes.length +
    lr.snap.length + lr.urinalysis.length > 0

  return (
    <div className="soap-display">
      {/* Flags */}
      {note.flags && note.flags.length > 0 && (
        <div className="flags-bar">
          {note.flags.map((f) => (
            <span key={f} className={`flag-chip flag-${f}`}>
              ⚠ {FLAG_LABELS[f] || f}
            </span>
          ))}
        </div>
      )}

      {/* Copy button */}
      <div className="soap-toolbar">
        <button className="copy-btn" onClick={copyAll} title="העתק הכל">
          📋 העתק הכל
        </button>
      </div>

      {/* S */}
      <section className="soap-section">
        <h2 className="soap-heading soap-s">S — סובייקטיבי (Subjective)</h2>
        <EditableList items={note.subjective} onChange={setSubjective} />
      </section>

      {/* O */}
      <section className="soap-section">
        <h2 className="soap-heading soap-o">O — אובייקטיבי (Objective)</h2>

        {/* Physical exam */}
        <div className="soap-subsection">
          <h3 className="soap-sub-heading">בדיקה גופנית</h3>
          <EditableList
            items={note.objective.physical_exam}
            onChange={setPhysicalExam}
          />
        </div>

        {/* Vitals */}
        <div className="soap-subsection">
          <h3 className="soap-sub-heading">מדדים</h3>
          <div className="vitals-grid">
            <VitalsRow label="Temp" value={note.objective.vitals.temp} />
            <VitalsRow label="HR"   value={note.objective.vitals.hr} />
            <VitalsRow label="RR"   value={note.objective.vitals.rr} />
            <VitalsRow label="Weight" value={note.objective.vitals.weight} />
          </div>
          {!note.objective.vitals.temp &&
           !note.objective.vitals.hr &&
           !note.objective.vitals.rr &&
           !note.objective.vitals.weight && (
            <p className="empty-section">לא נמסר</p>
          )}
        </div>

        {/* Lab Results */}
        {hasLabs && (
          <div className="soap-subsection">
            <h3 className="soap-sub-heading">תוצאות בדיקות</h3>
            <LabTable title="CBC" results={lr.cbc} />
            <LabTable title="Chemistry" results={lr.chemistry} />
            <LabTable title="Electrolytes" results={lr.electrolytes} />
            <LabTable title="SNAP" results={lr.snap} />
            <LabTable title="Urinalysis" results={lr.urinalysis} />
          </div>
        )}
      </section>

      {/* A */}
      <section className="soap-section">
        <h2 className="soap-heading soap-a">A — הערכה (Assessment)</h2>
        <p className="empty-section soap-empty-marker">— ריק —</p>
      </section>

      {/* P */}
      <section className="soap-section">
        <h2 className="soap-heading soap-p">P — תכנית (Plan)</h2>
        <p className="empty-section soap-empty-marker">— ריק —</p>
      </section>
    </div>
  )
}
