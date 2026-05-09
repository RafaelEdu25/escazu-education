import './index.css'

import { createApp } from 'vue'
import router from './router'
import App from './App.vue'
import { createPinia } from 'pinia'

import {
  Button,
  Card,
  Input,
  setConfig,
  frappeRequest,
  resourcesPlugin,
} from 'frappe-ui'

// Wrapper para agregar el token CSRF en cada petición
const csrfResourceFetcher = async (options) => {
  const csrfToken = window.frappe?.csrf_token || document.querySelector('[name="csrf-token"]')?.content
  
  const headers = {
    ...options.headers,
  }
  
  if (csrfToken) {
    headers['X-Frappe-CSRF-Token'] = csrfToken
  }
  
  return frappeRequest({
    ...options,
    headers,
  })
}

// create a pinia instance
let pinia = createPinia()

let app = createApp(App)

setConfig('resourceFetcher', csrfResourceFetcher)

app.use(pinia)
app.use(router)
app.use(resourcesPlugin)

app.component('Button', Button)
app.component('Card', Card)
app.component('Input', Input)

router.isReady().then(() => {
  app.mount('#app')
})
