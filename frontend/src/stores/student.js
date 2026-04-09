import { defineStore } from 'pinia'
import { ref } from 'vue'

export const studentStore = defineStore('education-student', () => {
  const studentInfo = ref({})
  const currentProgram = ref({})
  const studentGroups = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchStudent() {
    loading.value = true
    error.value = null
    try {
      const res = await fetch('/api/method/education.education.api.get_student_info', {
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
      
      const info = data.message
      if (!info) {
        window.location.href = '/app'
        return
      }
      
      currentProgram.value = info.current_program
      studentGroups.value = info.student_groups
      
      // Create a copy without the nested arrays for studentInfo
      const { current_program, student_groups, ...rest } = info
      studentInfo.value = rest
      
    } catch (err) {
      console.error('Error fetching student info:', err)
      error.value = err
    } finally {
      loading.value = false
    }
  }

  function getStudentInfo() {
    return studentInfo
  }
  function getCurrentProgram() {
    return currentProgram
  }
  function getStudentGroups() {
    return studentGroups
  }

  return {
    studentInfo,
    currentProgram,
    studentGroups,
    loading,
    error,
    fetchStudent,
    getStudentInfo,
    getCurrentProgram,
    getStudentGroups,
  }
})
