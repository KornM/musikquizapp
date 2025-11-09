import { defineStore } from 'pinia'
import api from '@/services/api'

export const useSessionsStore = defineStore('sessions', {
  state: () => ({
    sessions: [],
    currentSession: null,
    loading: false,
    error: null
  }),

  actions: {
    async fetchSessions() {
      this.loading = true
      this.error = null
      try {
        const response = await api.getSessions()
        this.sessions = response.data.sessions
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.error?.message || 'Failed to fetch sessions'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async fetchSession(id) {
      this.loading = true
      this.error = null
      try {
        const response = await api.getSession(id)
        this.currentSession = response.data
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data?.error?.message || 'Failed to fetch session'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async createSession(data) {
      this.loading = true
      this.error = null
      try {
        const response = await api.createSession(data)
        this.sessions.unshift(response.data)
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data?.error?.message || 'Failed to create session'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async addRound(sessionId, roundData) {
      this.loading = true
      this.error = null
      try {
        const response = await api.addRound(sessionId, roundData)
        
        // Update current session if it's loaded
        if (this.currentSession && this.currentSession.sessionId === sessionId) {
          if (!this.currentSession.rounds) {
            this.currentSession.rounds = []
          }
          this.currentSession.rounds.push(response.data)
          this.currentSession.roundCount = this.currentSession.rounds.length
        }
        
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data?.error?.message || 'Failed to add round'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async uploadAudio(file, sessionId) {
      this.loading = true
      this.error = null
      try {
        const response = await api.uploadAudio(file, sessionId)
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data?.error?.message || 'Failed to upload audio'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async uploadImage(file, sessionId) {
      this.loading = true
      this.error = null
      try {
        const response = await api.uploadImage(file, sessionId)
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data?.error?.message || 'Failed to upload image'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async deleteSession(sessionId) {
      this.loading = true
      this.error = null
      try {
        await api.deleteSession(sessionId)
        this.sessions = this.sessions.filter(s => s.sessionId !== sessionId)
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.error?.message || 'Failed to delete session'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async deleteRound(sessionId, roundId) {
      this.loading = true
      this.error = null
      try {
        // Find the round to get its roundNumber
        const round = this.currentSession?.rounds?.find(r => r.roundId === roundId)
        if (!round) {
          throw new Error('Round not found')
        }
        
        await api.deleteRound(sessionId, round.roundNumber)
        
        // Update current session if it's loaded
        if (this.currentSession && this.currentSession.sessionId === sessionId) {
          this.currentSession.rounds = this.currentSession.rounds.filter(r => r.roundId !== roundId)
          this.currentSession.roundCount = this.currentSession.rounds.length
        }
        
        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.error?.message || 'Failed to delete round'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    }
  }
})
