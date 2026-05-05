/**
 * useRecorder — custom hook for audio recording via MediaRecorder API.
 *
 * Returns:
 *   isRecording  — boolean
 *   startRecording()
 *   stopRecording() → Promise<Blob>  (resolves with the recorded audio)
 *   error          — string | null
 */

import { useState, useRef } from 'react'

export default function useRecorder() {
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const resolveRef = useRef(null)

  async function startRecording() {
    setError(null)
    chunksRef.current = []
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const options = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? { mimeType: 'audio/webm;codecs=opus' }
        : {}
      const recorder = new MediaRecorder(stream, options)

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      recorder.onstop = () => {
        const mimeType = recorder.mimeType || 'audio/webm'
        const blob = new Blob(chunksRef.current, { type: mimeType })
        // Stop all tracks to release microphone
        stream.getTracks().forEach((t) => t.stop())
        if (resolveRef.current) {
          resolveRef.current(blob)
          resolveRef.current = null
        }
        setIsRecording(false)
      }

      recorder.start(250) // collect data every 250ms for live feedback
      mediaRecorderRef.current = recorder
      setIsRecording(true)
    } catch (err) {
      setError(err.message || 'Could not access microphone')
    }
  }

  function stopRecording() {
    return new Promise((resolve) => {
      resolveRef.current = resolve
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop()
      } else {
        resolve(null)
        setIsRecording(false)
      }
    })
  }

  return { isRecording, startRecording, stopRecording, error }
}
