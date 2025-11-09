import { defineStore } from 'pinia'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('authToken') || null,
    isAuthenticated: !!localStorage.getItem('authToken'),
    user: null
  }),

  actions: {
    async login(username, password) {
      try {
        const response = await api.login(username, password)
        const { token } = response.data
        
        this.token = token
        this.isAuthenticated = true
        localStorage.setItem('authToken', token)
        
        return { success: true }
      } catch (error) {
        return {
          success: false,
          error: error.response?.data?.error?.message || 'Login failed'
        }
      }
    },

    logout() {
      this.token = null
      this.isAuthenticated = false
      this.user = null
      localStorage.removeItem('authToken')
    },

    checkAuth() {
      const token = localStorage.getItem('authToken')
      this.isAuthenticated = !!token
      this.token = token
    }
  }
})
