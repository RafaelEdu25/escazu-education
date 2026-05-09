import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import router from '@/router'
import { ref, computed } from 'vue'

function getCSRFHeaders() {
  const csrfToken = window.frappe?.csrf_token || document.querySelector('[name="csrf-token"]')?.content
  return csrfToken ? { 'X-Frappe-CSRF-Token': csrfToken } : {}
}

export const sessionStore = defineStore('education-session', () => {
  function sessionUser() {
    let cookies = new URLSearchParams(document.cookie.split('; ').join('&'))
    let _sessionUser = cookies.get('user_id')
    if (_sessionUser === 'Guest') {
      _sessionUser = null
    }
    return _sessionUser
  }

  let user = ref(sessionUser())
  const isLoggedIn = computed(() => !!user.value)
  const login = createResource({
    url: 'login',
    headers: getCSRFHeaders(),
    onError() {
      throw new Error('Invalid email or password')
    },
    onSuccess() {
      window.location.reload()
    },
  })

  const logout = createResource({
    url: 'logout',
    headers: getCSRFHeaders(),
    onSuccess() {
      user.value = null
      window.location.href = '/login'
    },
  })

  return {
    user,
    isLoggedIn,
    login,
    logout,
  }
})
