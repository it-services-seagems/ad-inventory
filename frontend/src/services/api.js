import axios from 'axios'

// Use Vite env variable VITE_API_URL when provided, otherwise use relative '/api'
// Using a relative '/api' lets the dev server proxy (vite) forward requests to Flask,
// avoiding CORS during development. In production you can set VITE_API_URL to the
// full backend URL if needed.
const API_BASE = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000, // 30 segundos para consultas de AD
  headers: {
    'Content-Type': 'application/json',
  },
  // enable this if your Flask backend uses cookies/auth and you need them sent
  // withCredentials: true,
})

// Interceptor para requisições
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to: ${config.url}`)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor para respostas
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    
    // Tratamento de erros específicos
    if (error.response?.status === 500) {
      console.error('Erro interno do servidor')
    } else if (error.response?.status === 404) {
      console.error('Recurso não encontrado')
    } else if (error.code === 'ECONNABORTED') {
      console.error('Timeout na requisição')
    }
    
    return Promise.reject(error)
  }
)

export default api