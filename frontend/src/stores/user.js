import { defineStore } from 'pinia'
import { ref } from 'vue'
import router from '@/router'

export const usersStore = defineStore('education-users', () => {
  const user = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchUser() {
    loading.value = true
    error.value = null
    try {
      // Usamos GET para evitar el error de CSRFToken
      const res = await fetch('/api/method/education.education.api.get_user_info', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
      })
      
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }

      const data = await res.json()
      
      if (data.exc) {
        throw new Error(data.exc)
      }
      
      user.value = data.message
    } catch (err) {
      console.error('Error fetching user:', err)
      error.value = err
      if (err.message && (err.message.includes('Authentication') || err.message.includes('Guest'))) {
        router.push('/login')
      }
    } finally {
      loading.value = false
    }
  }

  return {
    user,
    loading,
    error,
    fetchUser,
  }
})
