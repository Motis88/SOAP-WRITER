/**
 * LabTable — renders a panel of LabResult objects as a formatted table.
 * Highlights flagged (H/L) values in the appropriate color.
 */

import React from 'react'
import './LabTable.css'

function formatResult(r) {
  let display = r.value
  if (r.unit) display += ` ${r.unit}`
  if (r.reference_range) display += ` (${r.reference_range})`
  return display
}

function flagClass(flag) {
  if (!flag) return ''
  const upper = flag.toUpperCase()
  if (upper === 'H' || upper === 'HH' || upper === 'HIGH' || upper === 'CRITICAL') return 'flag-high'
  if (upper === 'L' || upper === 'LL' || upper === 'LOW') return 'flag-low'
  return 'flag-other'
}

export default function LabTable({ title, results }) {
  if (!results || results.length === 0) return null

  return (
    <div className="lab-table-wrap">
      <h4 className="lab-table-title">{title}</h4>
      <table className="lab-table">
        <thead>
          <tr>
            <th>בדיקה</th>
            <th>ערך</th>
            <th>יחידות</th>
            <th>טווח</th>
            <th>דגל</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r, i) => (
            <tr key={i} className={r.flag ? 'flagged-row' : ''}>
              <td className="lab-test-name">{r.test}</td>
              <td className={`lab-value ${flagClass(r.flag)}`}>
                {r.value === '[unclear value]' ? (
                  <span className="unclear-cell">[לא ברור]</span>
                ) : (
                  r.value
                )}
              </td>
              <td>{r.unit || '—'}</td>
              <td>{r.reference_range || '—'}</td>
              <td>
                {r.flag ? (
                  <span className={`flag-badge ${flagClass(r.flag)}`}>{r.flag}</span>
                ) : (
                  '—'
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
