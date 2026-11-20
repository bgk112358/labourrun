import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { AdminInfo, LoginResponse } from '../api/types'

function readAdmin(): AdminInfo | null {
  const raw = sessionStorage.getItem('admin_info')
  if (!raw) return null
  try {
    return JSON.parse(raw) as AdminInfo
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(sessionStorage.getItem('admin_token') || '')
  const admin = ref<AdminInfo | null>(readAdmin())

  const isLoggedIn = computed(() => Boolean(token.value))
  const isSuperAdmin = computed(() => admin.value?.role === 'super_admin')

  function setAuth(payload: LoginResponse) {
    token.value = payload.token
    admin.value = payload.admin
    sessionStorage.setItem('admin_token', payload.token)
    sessionStorage.setItem('admin_info', JSON.stringify(payload.admin))
  }

  function setAdmin(value: AdminInfo) {
    admin.value = value
    sessionStorage.setItem('admin_info', JSON.stringify(value))
  }

  function clear() {
    token.value = ''
    admin.value = null
    sessionStorage.removeItem('admin_token')
    sessionStorage.removeItem('admin_info')
  }

  return {
    token,
    admin,
    isLoggedIn,
    isSuperAdmin,
    setAuth,
    setAdmin,
    clear,
  }
})
