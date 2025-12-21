import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    redirect: '/admin/login'
  },
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('@/views/admin/LoginView.vue')
  },
  {
    path: '/admin/dashboard',
    name: 'AdminDashboard',
    component: () => import('@/views/admin/DashboardView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/sessions/:id',
    name: 'SessionDetail',
    component: () => import('@/views/admin/SessionDetailView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin/sessions/:id/present',
    name: 'Presentation',
    component: () => import('@/views/admin/PresentationView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/super-admin/tenants',
    name: 'TenantManagement',
    component: () => import('@/views/admin/TenantManagementView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/super-admin/tenants/:tenantId/admins',
    name: 'TenantAdminManagement',
    component: () => import('@/views/admin/TenantAdminManagementView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/register',
    name: 'Registration',
    component: () => import('@/views/participant/RegisterView.vue')
  },
  {
    path: '/lobby',
    name: 'ParticipantLobby',
    component: () => import('@/views/participant/LobbyView.vue')
  },
  {
    path: '/profile',
    name: 'ParticipantProfile',
    component: () => import('@/views/participant/ProfileView.vue')
  },
  {
    path: '/quiz/:id',
    name: 'Quiz',
    component: () => import('@/views/participant/QuizView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard for authentication
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/admin/login')
  } else {
    next()
  }
})

export default router
