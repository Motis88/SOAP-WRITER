import { useState, useRef, useCallback } from 'react'

export default function RecordButton({ onTranscript, onLoading }) {
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState(null)
  const recorderRef = useRef(null)
  const chunksRef = useRef([])

  const start = useCallback(async () => {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mimeType = MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/ogg'
      const recorder = new MediaRecorder(stream, { mimeType })
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(chunksRef.current, { type: mimeType })
        const ext = mimeType.includes('webm') ? '.webm' : '.ogg'
        onLoading(true, 'מתמלל...')
        try {
          const { transcribeAudio } = await import('../services/api.js')
          const result = await transcribeAudio(blob, `recording${ext}`)
          onTranscript(result.text)
        } catch {
          setError('שגיאה בתמלול — נסה שוב')
        } finally {
          onLoading(false, '')
        }
      }

      recorderRef.current = recorder
      recorder.start(1000)
      setIsRecording(true)
    } catch {
      setError('לא ניתן לגשת למיקרופון')
    }
  }, [onTranscript, onLoading])

  const stop = useCallback(() => {
    if (recorderRef.current?.state === 'recording') {
      recorderRef.current.stop()
      setIsRecording(false)
    }
  }, [])

  return (
    <div className="record-wrap">
      <button
        className={`record-btn ${isRecording ? 'recording' : ''}`}
        onClick={isRecording ? stop : start}
      >
        {isRecording ? (
          <>
            <span className="dot pulse" />
            עצור הקלטה
          </>
        ) : (
          <>
            <span className="mic">🎙️</span>
            התחל הקלטה
          </>
        )}
      </button>
      {error && <p className="err">{error}</p>}
    </div>
  )
}
