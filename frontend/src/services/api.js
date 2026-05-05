/**
 * API client for the SOAP Writer backend.
 * Base URL auto-detected: proxied through Vite in dev, or set via VITE_API_URL.
 */

const BASE = import.meta.env.VITE_API_URL || ''

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`HTTP ${res.status}: ${body}`)
  }
  return res.json()
}

/**
 * Transcribe an audio Blob via Whisper.
 * @param {Blob} audioBlob
 * @returns {Promise<{text: string, language: string|null}>}
 */
export async function transcribeAudio(audioBlob) {
  const form = new FormData()
  form.append('file', audioBlob, 'recording.webm')
  return request('/api/transcribe', { method: 'POST', body: form })
}

/**
 * Structure free text into a SOAP note.
 * @param {string} text
 * @returns {Promise<SOAPNote>}
 */
export async function structureText(text) {
  return request('/api/structure', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
}

/**
 * Parse an IDEXX PDF file and return lab results.
 * @param {File} pdfFile
 * @returns {Promise<PDFParseResponse>}
 */
export async function parsePDF(pdfFile) {
  const form = new FormData()
  form.append('file', pdfFile)
  return request('/api/parse-pdf', { method: 'POST', body: form })
}

/**
 * Full pipeline: text + optional audio + optional PDF → SOAP note.
 * @param {{text?: string, audio?: Blob, pdf?: File}} params
 * @returns {Promise<SOAPNote>}
 */
export async function processAll({ text = '', audio = null, pdf = null }) {
  const form = new FormData()
  form.append('text', text)
  if (audio) form.append('audio', audio, 'recording.webm')
  if (pdf) form.append('pdf', pdf)
  return request('/api/process', { method: 'POST', body: form })
}
