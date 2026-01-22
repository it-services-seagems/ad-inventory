import api from './api'

// Serviço para interagir com o catálogo de iPhones
export const iphoneCatalogService = {
  // Buscar todo o catálogo
  async getCatalog() {
    try {
      const response = await api.get('/iphone-catalog/catalog')
      return response.data
    } catch (error) {
      console.error('Erro ao buscar catálogo de iPhones:', error)
      throw error
    }
  },

  // Pesquisar modelo específico
  async searchModel(query) {
    try {
      const response = await api.get(`/iphone-catalog/search?q=${encodeURIComponent(query)}`)
      return response.data
    } catch (error) {
      console.error('Erro ao pesquisar modelo:', error)
      throw error
    }
  },

  // Sugerir melhor match para texto livre
  async suggestMatch(modelText) {
    try {
      const response = await api.post('/iphone-catalog/suggest-match', modelText, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      return response.data
    } catch (error) {
      console.error('Erro ao sugerir modelo:', error)
      throw error
    }
  }
}

// Hook customizado para usar o catálogo
import { useState, useEffect } from 'react'

export const useIPhoneCatalog = () => {
  const [catalog, setCatalog] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const loadCatalog = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await iphoneCatalogService.getCatalog()
      if (data.success) {
        setCatalog(data.catalog || [])
      }
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCatalog()
  }, [])

  return { catalog, loading, error, refetch: loadCatalog }
}

// Hook para pesquisa em tempo real
export const useIPhoneSearch = (query, debounceMs = 500) => {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!query || query.trim().length < 2) {
      setResults([])
      return
    }

    const timeoutId = setTimeout(async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await iphoneCatalogService.searchModel(query.trim())
        if (data.success) {
          setResults(data.matches || [])
        }
      } catch (err) {
        setError(err)
        setResults([])
      } finally {
        setLoading(false)
      }
    }, debounceMs)

    return () => clearTimeout(timeoutId)
  }, [query, debounceMs])

  return { results, loading, error }
}

// Utilitário para sugestão de modelo
export const useSuggestModel = () => {
  const [suggestion, setSuggestion] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const getSuggestion = async (modelText) => {
    if (!modelText || modelText.trim().length < 2) {
      setSuggestion(null)
      return
    }

    setLoading(true)
    setError(null)
    try {
      const data = await iphoneCatalogService.suggestMatch(modelText.trim())
      if (data.success) {
        setSuggestion(data)
      }
    } catch (err) {
      setError(err)
      setSuggestion(null)
    } finally {
      setLoading(false)
    }
  }

  return { suggestion, loading, error, getSuggestion }
}

export default iphoneCatalogService