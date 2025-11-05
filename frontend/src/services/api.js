import axios from 'axios'

// NOTE: Force the backend API IP and port for this deployment
// Previously this used Vite's VITE_API_URL fallback; we now explicitly use the
// target IP so the frontend always talks to the backend at 10.15.2.19:42059.
const API_BASE = 'http://10.15.2.19:42059/api'

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

// Funções específicas para API
export const apiMethods = {
  // Buscar usuário atual por service tag
  getCurrentUserByServiceTag: async (serviceTag) => {
    try {
      const response = await api.get(`/computers/user-by-service-tag/${encodeURIComponent(serviceTag)}`)
      return response.data
    } catch (error) {
      console.error('Erro ao buscar usuário por service tag:', error)
      throw error
    }
  },

  // Buscar usuário atual por nome da máquina (método original)
  getCurrentUserByComputerName: async (computerName) => {
    try {
      const response = await api.get(`/computers/${encodeURIComponent(computerName)}/current-user`)
      return response.data
    } catch (error) {
      console.error('Erro ao buscar usuário atual:', error)
      throw error
    }
  },

  // Vincular funcionário a computador
  vincularUsuario: async (computerName, funcionario) => {
    try {
      const payload = {
        computer_name: computerName,
        matricula: funcionario.matricula,
        nome: funcionario.nome,
        email_corporativo: funcionario.email_corporativo || funcionario.email
      }
      const response = await api.post('/funcionarios/vincular-usuario', payload)
      return response.data
    } catch (error) {
      console.error('Erro ao vincular usuário:', error)
      throw error
    }
  },

  // Desvincular usuário de computador
  desvincularUsuario: async (computerName) => {
    try {
      const payload = {
        computer_name: computerName
      }
      const response = await api.post('/funcionarios/desvincular-usuario', payload)
      return response.data
    } catch (error) {
      console.error('Erro ao desvincular usuário:', error)
      throw error
    }
  }
}

export default api