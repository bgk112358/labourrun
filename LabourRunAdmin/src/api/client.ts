import axios from 'axios'

const client = axios.create({
  baseURL: '/api/v1/admin',
  timeout: 15000,
})

client.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('admin_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => {
    if (response.config.responseType === 'blob') {
      return response
    }
    const body = response.data
    if (body && body.code === 0) {
      return body.data
    }
    return Promise.reject(new Error(body?.message || '请求失败'))
  },
  (error) => {
    const status = error.response?.status
    const body = error.response?.data
    const code = body?.code
    if (status === 401 || code === 1101 || code === 1102) {
      sessionStorage.removeItem('admin_token')
      sessionStorage.removeItem('admin_info')
      if (!window.location.pathname.endsWith('/login')) {
        window.location.href = '/admin/login'
      }
    }
    return Promise.reject(
      new Error(body?.message || error.message || '网络错误'),
    )
  },
)

export default client
