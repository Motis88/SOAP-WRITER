import { useState } from 'react'
import LabResultsTable from './LabResultsTable.jsx'

/* ── Editable bullet list ───────────────────────────────────────── */
function EditableList({ items, onUpdate, placeholder }) {
  const [editIdx, setEditIdx] = useState(null)
  const [editVal, setEditVal] = useState('')
  const [newItem, setNewItem] = useState('')

  const startEdit = (i) => { setEditIdx(i); setEditVal(items[i]) }
  const saveEdit = (i) => {
    const next = [...items]
    next[i] = editVal
    onUpdate(next.filter(Boolean))
    setEditIdx(null)
  }
  const del = (i) => onUpdate(items.filter((_, idx) => idx !== i))
  const add = () => {
    if (newItem.trim()) { onUpdate([...items, newItem.trim()]); setNewItem('') }
  }

  return (
    <div className="elist">
      {items.map((item, i) => (
        <div key={i} className={`elist-row ${item === 'לא נמסר' ? 'muted' : ''}`}>
          {editIdx === i ? (
            <input
              className="inline-inp full"
              autoFocus
              value={editVal}
              onChange={(e) => setEditVal(e.target.value)}
              onBlur={() => saveEdit(i)}
              onKeyDown={(e) => e.key === 'Enter' && saveEdit(i)}
            />
          ) : (
            <>
              <span className="elist-txt" onClick={() => startEdit(i)}>• {item}</span>
              <button className="del-btn" onClick={() => del(i)}>×</button>
            </>
          )}
        </div>
      ))}
      <div className="add-row">
        <input
          className="add-inp"
          value={newItem}
          placeholder={placeholder || 'הוסף...'}
          onChange={(e) => setNewItem(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && add()}
        />
        <button className="add-btn" onClick={add}>+</button>
      </div>
    </div>
  )
}

/* ── Vitals grid ────────────────────────────────────────────────── */
const VITAL_FIELDS = [
  { key: 'temp', label: 'Temp (°C)' },
  { key: 'hr',   label: 'HR (bpm)' },
  { key: 'rr',   label: 'RR (/min)' },
  { key: 'weight', label: 'Weight (kg)' },
  { key: 'bp',   label: 'BP (mmHg)' },
]

function VitalsGrid({ vitals, onChange }) {
  return (
    <div className="vitals-grid">
      {VITAL_FIELDS.map(({ key, label }) => {
        const val = vitals[key] === 'לא נמסר' ? '' : (vitals[key] || '')
        return (
          <div key={key} className="vital-cell">
            <label>{label}</label>
            <input
              className={`vital-inp ${!val ? 'empty' : ''}`}
              value={val}
              placeholder="—"
              onChange={(e) => onChange({ ...vitals, [key]: e.target.value })}
            />
          </div>
        )
      })}
    </div>
  )
}

/* ── SOAP section wrapper ───────────────────────────────────────── */
function Section({ letter, title, colorClass, children }) {
  return (
    <section className={`soap-sec ${colorClass}`}>
      <div className="sec-hdr">
        <span className={`sec-badge ${letter.toLowerCase()}`}>{letter}</span>
        <h3>{title}</h3>
      </div>
      <div className="sec-body">{children}</div>
    </section>
  )
}

/* ── Main editor ────────────────────────────────────────────────── */
const FLAG_LABELS = {
  missing_data: 'מידע חסר',
  unclear_text: 'טקסט לא ברור',
  ocr_used: 'OCR הופעל',
  partial_extraction: 'חילוץ חלקי',
  unknown_pdf_format: 'פורמט PDF לא מוכר',
}

export default function SOAPEditor({ soapData, onUpdate, flags }) {
  const upd = (patch) => onUpdate({ ...soapData, ...patch })
  const updObj = (patch) => upd({ objective: { ...soapData.objective, ...patch } })

  return (
    <div className="soap-editor">
      {/* Flags */}
      {flags?.length > 0 && (
        <div className="flags-bar">
          {flags.map((f) => (
            <span key={f} className={`flag-chip fc-${f.replace(/_/g, '-')}`}>
              {FLAG_LABELS[f] || f}
            </span>
          ))}
        </div>
      )}

      {/* S */}
      <Section letter="S" title="Subjective — תלונות ואנמנזה" colorClass="sec-s">
        <EditableList
          items={soapData.subjective}
          onUpdate={(v) => upd({ subjective: v })}
          placeholder="הוסף תלונה / מידע מהבעלים..."
        />
      </Section>

      {/* O */}
      <Section letter="O" title="Objective — ממצאים אובייקטיביים" colorClass="sec-o">
        <div className="sub-sec">
          <p className="sub-title">בדיקה גופנית</p>
          <EditableList
            items={soapData.objective.physical_exam}
            onUpdate={(v) => updObj({ physical_exam: v })}
            placeholder="הוסף ממצא פיזיקלי..."
          />
        </div>

        <div className="sub-sec">
          <p className="sub-title">מדדים</p>
          <VitalsGrid
            vitals={soapData.objective.vitals}
            onChange={(v) => updObj({ vitals: v })}
          />
        </div>

        <div className="sub-sec">
          <p className="sub-title">תוצאות מעבדה</p>
          <LabResultsTable
            labResults={soapData.objective.lab_results}
            onUpdate={(v) => updObj({ lab_results: v })}
          />
          {!Object.values(soapData.objective.lab_results).some((a) => a.length > 0) && (
            <p className="no-labs">אין תוצאות מעבדה — העלה PDF להוספה אוטומטית</p>
          )}
        </div>
      </Section>

      {/* A */}
      <Section letter="A" title="Assessment — הערכה" colorClass="sec-a">
        <textarea
          className="soap-ta"
          rows={3}
          value={soapData.assessment}
          placeholder="(ממלא הרופא)"
          onChange={(e) => upd({ assessment: e.target.value })}
        />
      </Section>

      {/* P */}
      <Section letter="P" title="Plan — תוכנית טיפול" colorClass="sec-p">
        <textarea
          className="soap-ta"
          rows={3}
          value={soapData.plan}
          placeholder="(ממלא הרופא)"
          onChange={(e) => upd({ plan: e.target.value })}
        />
      </Section>
    </div>
  )
}
