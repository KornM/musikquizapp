import { defineStore } from 'pinia'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('authToken') || null,
    isAuthenticated: !!localStorage.getItem('authToken'),
    tenantId: localStorage.getItem('tenantId') || null,
    tenantName: localStorage.getItem('tenantName') || null,
    role: localStorage.getItem('role') || null,
    user: null
  }),

  actions: {
    async login(username, password) {
      try {
        const response = await api.login(username, password)
        const { token, tenantId, tenantName, role } = response.data
        
        this.token = token
        this.isAuthenticated = true
        this.tenantId = tenantId
        this.tenantName = tenantName
        this.role = role
        
        localStorage.setItem('authToken', token)
        if (tenantId) {
          localStorage.setItem('tenantId', tenantId)
        }
        if (tenantName) {
          localStorage.setItem('tenantName', tenantName)
        }
        if (role) {
          localStorage.setItem('role', role)
        }
        
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
      this.tenantId = null
      this.tenantName = null
      this.role = null
      this.user = null
      localStorage.removeItem('authToken')
      localStorage.removeItem('tenantId')
      localStorage.removeItem('tenantName')
      localStorage.removeItem('role')
    },

    checkAuth() {
      const token = localStorage.getItem('authToken')
      this.isAuthenticated = !!token
      this.token = token
      this.tenantId = localStorage.getItem('tenantId')
      this.tenantName = localStorage.getItem('tenantName')
      this.role = localStorage.getItem('role')
    }
  }
})
