import { createRouter, createWebHistory } from 'vue-router'
import { usersStore } from '@/stores/user'
import { sessionStore } from '@/stores/session'
import { studentStore } from '@/stores/student'

const routes = [
  { path: '/', redirect: '/schedule' },
  {
    path: '/schedule',
    name: 'Schedule',
    component: () => import('@/pages/Schedule.vue'),
  },
  {
    path: '/grades',
    name: 'Grades',
    component: () => import('@/pages/Grades.vue'),
  },
  {
    path: '/fees',
    name: 'Fees',
    component: () => import('@/pages/Fees.vue'),
  },
  {
    path: '/attendance',
    name: 'Attendance',
    component: () => import('@/pages/Attendance.vue'),
  },
  {
    path: '/:catchAll(.*)',
    redirect: '/schedule',
  },
]

let router = createRouter({
  history: createWebHistory('/student-portal'),
  routes,
})

router.beforeEach(async (to, from) => {
  const { isLoggedIn } = sessionStore()
  const users = usersStore()
  const students = studentStore()

  if (!isLoggedIn) {
    window.location.href = '/login'
    return false
  }

  if (!users.user) {
    await users.fetchUser()
  }
  
  if (!students.studentInfo || Object.keys(students.studentInfo).length === 0) {
    await students.fetchStudent()
  }
})

export default router
