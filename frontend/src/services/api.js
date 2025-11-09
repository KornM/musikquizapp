import axios from 'axios'
import router from '@/router'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('authToken')
      router.push('/admin/login')
    }
    return Promise.reject(error)
  }
)

export default {
  // Admin Auth
  login(username, password) {
    return apiClient.post('/admin/login', { username, password })
  },

  // Sessions
  getSessions() {
    return apiClient.get('/quiz-sessions')
  },

  getSession(id) {
    return apiClient.get(`/quiz-sessions/${id}`)
  },

  createSession(data) {
    return apiClient.post('/admin/quiz-sessions', data)
  },

  // Rounds
  addRound(sessionId, roundData) {
    return apiClient.post(`/admin/quiz-sessions/${sessionId}/rounds`, roundData)
  },

  // Audio
  uploadAudio(file, sessionId) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = async () => {
        try {
          const base64Data = reader.result.split(',')[1]
          const response = await apiClient.post('/admin/audio', {
            audioData: base64Data,
            fileName: file.name,
            sessionId
          })
          resolve(response)
        } catch (error) {
          reject(error)
        }
      }
      reader.onerror = reject
      reader.readAsDataURL(file)
    })
  },

  getAudioUrl(audioKey) {
    return apiClient.get(`/audio?key=${encodeURIComponent(audioKey)}`)
  },

  // QR Code
  getQRData(sessionId) {
    return apiClient.get(`/quiz-sessions/${sessionId}/qr`)
  },

  // Participants
  registerParticipant(sessionId, name, avatar) {
    return apiClient.post('/participants/register', { sessionId, name, avatar })
  },

  submitAnswer(participantId, sessionId, roundNumber, answer) {
    return apiClient.post('/participants/answers', {
      participantId,
      sessionId,
      roundNumber,
      answer
    })
  },

  // Admin - Start Round
  startRound(sessionId, roundNumber) {
    return apiClient.post(`/admin/quiz-sessions/${sessionId}/rounds/${roundNumber}/start`)
  },

  // Scoreboard
  getScoreboard(sessionId) {
    return apiClient.get(`/quiz-sessions/${sessionId}/scoreboard`)
  },

  // Admin - Reset Points
  resetPoints(sessionId) {
    return apiClient.delete(`/admin/quiz-sessions/${sessionId}/points`)
  },

  // Admin - Clear Participants
  clearParticipants(sessionId) {
    return apiClient.delete(`/admin/quiz-sessions/${sessionId}/participants`)
  },

  // Delete
  deleteSession(sessionId) {
    return apiClient.delete(`/admin/quiz-sessions/${sessionId}`)
  },

  deleteRound(sessionId, roundNumber) {
    return apiClient.delete(`/admin/quiz-sessions/${sessionId}/rounds/${roundNumber}`)
  }
}
