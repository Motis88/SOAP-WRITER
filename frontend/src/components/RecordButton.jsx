/**
 * RecordButton — microphone recording control.
 * Shows a pulsing red button while recording.
 * Calls onTranscribed(text) when done.
 */

import React, { useState } from 'react'
import useRecorder from '../hooks/useRecorder'
import { transcribeAudio } from '../services/api'
import './RecordButton.css'

export default function RecordButton({ onTranscribed, disabled }) {
  const { isRecording, startRecording, stopRecording, error } = useRecorder()
  const [status, setStatus] = useState('')

  async function handleClick() {
    if (isRecording) {
      setStatus('מעבד...')
      const blob = await stopRecording()
      if (blob) {
        try {
          const result = await transcribeAudio(blob)
          onTranscribed(result.text || '')
          setStatus('')
        } catch (err) {
          setStatus('שגיאה בתמלול')
          console.error(err)
        }
      } else {
        setStatus('')
      }
    } else {
      await startRecording()
      setStatus('מקליט...')
    }
  }

  return (
    <div className="record-wrapper">
      <button
        className={`record-btn ${isRecording ? 'recording' : ''}`}
        onClick={handleClick}
        disabled={disabled}
        aria-label={isRecording ? 'עצור הקלטה' : 'התחל הקלטה'}
        title={isRecording ? 'עצור הקלטה' : 'התחל הקלטה'}
      >
        {isRecording ? '⏹ עצור' : '🎙 הקלטה'}
      </button>
      {status && <span className="record-status">{status}</span>}
      {error && <span className="record-error">{error}</span>}
    </div>
  )
}
