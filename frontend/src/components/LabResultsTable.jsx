import { useState } from 'react'

function LabRow({ item, onEdit }) {
  const [editing, setEditing] = useState(false)
  const [val, setVal] = useState(item.value)

  const save = () => {
    onEdit({ ...item, value: val, formatted: item.formatted.replace(item.value, val) })
    setEditing(false)
  }

  const flagCls = item.flag === 'H' ? 'flag-h' : item.flag === 'L' ? 'flag-l' : ''

  return (
    <tr className={flagCls}>
      <td>{item.name}</td>
      <td>
        {editing ? (
          <input
            className="inline-inp"
            value={val}
            autoFocus
            onChange={(e) => setVal(e.target.value)}
            onBlur={save}
            onKeyDown={(e) => e.key === 'Enter' && save()}
          />
        ) : (
          <span className="editable-val" onClick={() => setEditing(true)}>
            {item.value || '[לא ברור]'}
          </span>
        )}
      </td>
      <td>{item.unit}</td>
      <td>{item.ref_range}</td>
      <td>
        {item.flag && (
          <span className={`flag-badge ${flagCls}`}>{item.flag}</span>
        )}
      </td>
    </tr>
  )
}

const SECTIONS = [
  { key: 'cbc', label: 'CBC — ספירת דם' },
  { key: 'chemistry', label: 'Chemistry — כימיה' },
  { key: 'electrolytes', label: 'Electrolytes — אלקטרוליטים' },
  { key: 'snap', label: 'SNAP' },
  { key: 'urinalysis', label: 'Urinalysis — שתן' },
]

export default function LabResultsTable({ labResults, onUpdate }) {
  const hasAny = SECTIONS.some((s) => labResults[s.key]?.length > 0)
  if (!hasAny) return null

  const editRow = (sectionKey, idx, updated) => {
    const next = { ...labResults, [sectionKey]: [...labResults[sectionKey]] }
    next[sectionKey][idx] = updated
    onUpdate(next)
  }

  return (
    <div className="lab-results">
      {SECTIONS.map(({ key, label }) => {
        const rows = labResults[key] || []
        if (!rows.length) return null
        return (
          <div key={key} className="lab-section">
            <p className="lab-sec-title">{label}</p>
            <table className="lab-tbl">
              <thead>
                <tr>
                  <th>בדיקה</th>
                  <th>ערך</th>
                  <th>יחידה</th>
                  <th>טווח ייחוס</th>
                  <th>דגל</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((item, i) => (
                  <LabRow
                    key={`${key}-${i}`}
                    item={item}
                    onEdit={(u) => editRow(key, i, u)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )
      })}
    </div>
  )
}
