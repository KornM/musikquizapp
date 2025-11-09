import { defineStore } from 'pinia'
import api from '@/services/api'

export const useParticipantStore = defineStore('participant', {
  state: () => ({
    participantId: localStorage.getItem('participantId') || null,
    participantToken: localStorage.getItem('participantToken') || null,
    sessionId: localStorage.getItem('participantSessionId') || null,
    currentRound: 1,
    selectedAnswers: JSON.parse(localStorage.getItem('selectedAnswers') || '{}')
  }),

  actions: {
    async register(sessionId, name) {
      try {
        const response = await api.registerParticipant(sessionId, name)
        const { participantId, token } = response.data
        
        this.participantId = participantId
        this.participantToken = token
        this.sessionId = sessionId
        this.currentRound = 1
        this.selectedAnswers = {}
        
        localStorage.setItem('participantId', participantId)
        localStorage.setItem('participantToken', token)
        localStorage.setItem('participantSessionId', sessionId)
        localStorage.setItem('selectedAnswers', '{}')
        
        return { success: true, data: response.data }
      } catch (error) {
        return {
          success: false,
          error: error.response?.data?.error?.message || 'Registration failed'
        }
      }
    },

    submitAnswer(roundNumber, answerIndex) {
      this.selectedAnswers[roundNumber] = answerIndex
      localStorage.setItem('selectedAnswers', JSON.stringify(this.selectedAnswers))
    },

    nextRound() {
      this.currentRound++
    },

    previousRound() {
      if (this.currentRound > 1) {
        this.currentRound--
      }
    },

    clearParticipantData() {
      this.participantId = null
      this.participantToken = null
      this.sessionId = null
      this.currentRound = 1
      this.selectedAnswers = {}
      
      localStorage.removeItem('participantId')
      localStorage.removeItem('participantToken')
      localStorage.removeItem('participantSessionId')
      localStorage.removeItem('selectedAnswers')
    }
  }
})
