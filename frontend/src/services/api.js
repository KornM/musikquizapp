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
    // Check for admin token first, then participant token
    const adminToken = localStorage.getItem('authToken')
    const participantToken = localStorage.getItem('globalParticipantToken')
    
    const token = adminToken || participantToken
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
      // Check if this is an admin or participant request
      const isAdminRoute = window.location.pathname.startsWith('/admin')
      
      if (isAdminRoute) {
        // Clear admin token and redirect to admin login
        localStorage.removeItem('authToken')
        router.push('/admin/login')
      } else {
        // For participant routes, clear participant data
        // But don't redirect if we're on the registration page - just clear the data
        // so they can re-register
        if (window.location.pathname.includes('/register')) {
          // On registration page - just clear expired data, don't redirect
          localStorage.removeItem('globalParticipantId')
          localStorage.removeItem('globalParticipantToken')
          localStorage.removeItem('globalParticipantTenantId')
        } else {
          // Not on registration page - clear data and redirect
          localStorage.removeItem('globalParticipantId')
          localStorage.removeItem('globalParticipantToken')
          localStorage.removeItem('globalParticipantTenantId')
          
          // Try to preserve session ID if available
          const sessionId = window.location.pathname.match(/\/quiz\/([^/]+)/)?.[1]
          if (sessionId) {
            router.push(`/register?sessionId=${sessionId}`)
          }
        }
      }
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

  // Image
  uploadImage(file, sessionId) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = async () => {
        try {
          const base64Data = reader.result.split(',')[1]
          const response = await apiClient.post('/admin/image', {
            imageData: base64Data,
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

  // QR Code
  getQRData(sessionId) {
    return apiClient.get(`/quiz-sessions/${sessionId}/qr`)
  },

  // Participants - Global Registration
  registerGlobalParticipant(tenantId, name, avatar) {
    return apiClient.post('/participants/register', { tenantId, name, avatar })
  },

  getGlobalParticipant(participantId) {
    return apiClient.get(`/participants/${participantId}`)
  },

  updateGlobalParticipant(participantId, data) {
    return apiClient.put(`/participants/${participantId}`, data)
  },

  // Session Participation
  joinSession(sessionId, participantToken) {
    return apiClient.post(`/sessions/${sessionId}/join`, {}, {
      headers: {
        'Authorization': `Bearer ${participantToken}`
      }
    })
  },

  // Legacy - Session-specific registration (for backward compatibility)
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

  // Admin - Participant Management
  getParticipants(sessionId) {
    return apiClient.get(`/admin/quiz-sessions/${sessionId}/participants`)
  },

  updateParticipant(sessionId, participantId, data) {
    return apiClient.put(`/admin/quiz-sessions/${sessionId}/participants/${participantId}`, data)
  },

  deleteParticipant(sessionId, participantId) {
    return apiClient.delete(`/admin/quiz-sessions/${sessionId}/participants/${participantId}`)
  },

  clearParticipants(sessionId) {
    return apiClient.delete(`/admin/quiz-sessions/${sessionId}/participants`)
  },

  // Delete
  deleteSession(sessionId) {
    return apiClient.delete(`/admin/quiz-sessions/${sessionId}`)
  },

  completeSession(sessionId) {
    return apiClient.post(`/admin/quiz-sessions/${sessionId}/complete`)
  },

  updateSession(sessionId, data) {
    return apiClient.put(`/admin/quiz-sessions/${sessionId}`, data)
  },

  deleteRound(sessionId, roundNumber) {
    return apiClient.delete(`/admin/quiz-sessions/${sessionId}/rounds/${roundNumber}`)
  },

  // Super Admin - Tenant Management
  getTenants() {
    return apiClient.get('/super-admin/tenants')
  },

  getTenant(tenantId) {
    return apiClient.get(`/super-admin/tenants/${tenantId}`)
  },

  createTenant(data) {
    return apiClient.post('/super-admin/tenants', data)
  },

  updateTenant(tenantId, data) {
    return apiClient.put(`/super-admin/tenants/${tenantId}`, data)
  },

  deleteTenant(tenantId) {
    return apiClient.delete(`/super-admin/tenants/${tenantId}`)
  },

  // Super Admin - Tenant Admin Management
  getTenantAdmins(tenantId) {
    return apiClient.get(`/super-admin/tenants/${tenantId}/admins`)
  },

  createTenantAdmin(tenantId, data) {
    return apiClient.post(`/super-admin/tenants/${tenantId}/admins`, data)
  },

  updateTenantAdmin(adminId, data) {
    return apiClient.put(`/super-admin/admins/${adminId}`, data)
  },

  deleteTenantAdmin(adminId) {
    return apiClient.delete(`/super-admin/admins/${adminId}`)
  },

  resetAdminPassword(adminId, newPassword) {
    return apiClient.post(`/super-admin/admins/${adminId}/reset-password`, { newPassword })
  }
}
