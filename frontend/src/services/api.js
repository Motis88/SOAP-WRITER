import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120_000, // 2 min — Whisper can be slow on first run
})

export const transcribeAudio = async (blob, filename = 'recording.webm') => {
  const form = new FormData()
  form.append('audio', blob, filename)
  const { data } = await api.post('/transcribe', form)
  return data
}

export const parsePDF = async (file) => {
  const form = new FormData()
  form.append('pdf', file)
  const { data } = await api.post('/parse-pdf', form)
  return data
}

export const structureSOAP = async (text) => {
  const { data } = await api.post('/structure', { text })
  return data
}
