import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Search, RefreshCw, Eye, Calendar, Monitor, Server, Filter, ChevronDown, CheckCircle, XCircle, Database, Clock, ArrowLeft, Power, Loader2, AlertCircle, Building2, Shield, ShieldAlert, ShieldCheck, ShieldOff, ChevronUp, ArrowUpDown, RotateCcw } from 'lucide-react'
import api from '../services/api'
import logo_seagems from '../assets/LogoSeagems.png'

const Computers = () => {
  const location = useLocation()
  const navigationState = location.state
  
  // Estados principais
  const [computers, setComputers] = useState([])
  const [warrantyData, setWarrantyData] = useState(new Map())
  const [loading, setLoading] = useState(true)
  const [warrantyLoading, setWarrantyLoading] = useState(false)
  const [syncCompleteLoading, setSyncCompleteLoading] = useState(false)
  const [lastFetchTime, setLastFetchTime] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [filters, setFilters] = useState({
    status: 'all',
    os: 'all', 
    lastLogin: 'all',
    ou: 'all',
    warranty: 'all'
  })
  // additional advanced filter fields
  // lastLoginDays: 'all' | '7' | '30' | '60' | '90' | '120+'
  // inventory: 'all' | 'spare' | 'in_use'
  // assignedTo / prevUser are free-text placeholders
  const [advancedFilters, setAdvancedFilters] = useState({
    lastLoginDays: 'all',
    inventory: 'all',
    assignedTo: '',
    prevUser: ''
  })
  const [sideTab, setSideTab] = useState('all') // 'all' or 'inventory'
  const [showFilters, setShowFilters] = useState(false)
  
  // Estados de ordenação
  const [sortConfig, setSortConfig] = useState({
    key: 'name',
    direction: 'asc'
  })
  
  
  // Estados de cache e performance
  const [isFromCache, setIsFromCache] = useState(false)
  const [memoryCache, setMemoryCache] = useState(null)
  const [processedData, setProcessedData] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  
  // Estados para ativar/desativar máquinas
  const [toggleStatusLoading, setToggleStatusLoading] = useState(new Set())
  const [statusMessages, setStatusMessages] = useState(new Map())
  const [confirmDialog, setConfirmDialog] = useState({ open: false, computer: null, action: null })
  const [toast, setToast] = useState(null) // { type: 'success'|'error', text: string }
  const [bulkSelection, setBulkSelection] = useState(new Set())
  const [syncMessage, setSyncMessage] = useState(null)
  
  // Estados para atualização de garantias
  const [warrantyRefreshJob, setWarrantyRefreshJob] = useState(null) // { job_id, status, progress_percent, total, processed }
  const [warrantyRefreshPolling, setWarrantyRefreshPolling] = useState(false)
  
  // Refs para otimização
  const initialLoadRef = useRef(false)
  const navigationFiltersApplied = useRef(false)
  const searchTimeoutRef = useRef(null)
  const searchInputRef = useRef(null)
  
  // Configurações
  const CACHE_DURATION = 10 * 60 * 1000 // 10 minutos
  const SEARCH_DEBOUNCE_MS = 300

  // Debounce para pesquisa
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }

    if (searchTerm !== debouncedSearchTerm) {
      setIsSearching(true)
    }

    searchTimeoutRef.current = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm)
      setIsSearching(false)
    }, SEARCH_DEBOUNCE_MS)

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current)
      }
    }
  }, [searchTerm, debouncedSearchTerm])

  // Função para determinar a OU baseada no nome da máquina (memoizada)
  const getComputerOU = useCallback((computerName) => {
    if (!computerName) return { code: 'UNKNOWN', name: 'Desconhecida', color: 'text-gray-600', bgColor: 'bg-gray-100' }
    
    const name = computerName.toUpperCase()
    
    const ouMapping = {
      'DIA': { code: 'DIA', name: 'Diamante', color: 'text-blue-600', bgColor: 'bg-blue-100' },
      'ONI': { code: 'ONI', name: 'Ônix', color: 'text-gray-800', bgColor: 'bg-gray-200' },
      'TOP': { code: 'TOP', name: 'Topázio', color: 'text-yellow-600', bgColor: 'bg-yellow-100' },
      'JAD': { code: 'JAD', name: 'Jade', color: 'text-green-600', bgColor: 'bg-green-100' },
      'ESM': { code: 'ESM', name: 'Esmeralda', color: 'text-emerald-600', bgColor: 'bg-emerald-100' },
      'RUB': { code: 'RUB', name: 'Rubi', color: 'text-red-600', bgColor: 'bg-red-100' },
      'CLO': { code: 'CLOUD', name: 'Servidores Cloud', color: 'text-purple-600', bgColor: 'bg-purple-100' },
      'SHQ': { code: 'ONSHORE', name: 'Base Onshore', color: 'text-indigo-600', bgColor: 'bg-indigo-100' }
    }
    
    for (const [prefix, ou] of Object.entries(ouMapping)) {
      if (name.startsWith(prefix)) {
        return ou
      }
    }
    
    return { code: 'ONSHORE', name: 'Base Onshore', color: 'text-indigo-600', bgColor: 'bg-indigo-100' }
  }, [])

  // Função para calcular status da garantia (memoizada)
  const getWarrantyStatus = useCallback((warranty) => {
    if (!warranty || warranty.last_error) {
      return {
        status: 'unknown',
        text: 'Desconhecido',
        color: 'text-gray-500',
        bgColor: 'bg-gray-100',
        icon: Shield,
        sortValue: 999999
      }
    }

    if (!warranty.warranty_end_date) {
      return {
        status: 'no_data',
        text: 'Sem dados',
        color: 'text-gray-500',
        bgColor: 'bg-gray-100',
        icon: Shield,
        sortValue: 999998
      }
    }

    const now = new Date()
    const endDate = new Date(warranty.warranty_end_date)
    const diffDays = Math.ceil((endDate - now) / (1000 * 60 * 60 * 24))

    if (diffDays < 0) {
      return {
        status: 'expired',
        text: `Expirada há ${Math.abs(diffDays)} dias`,
        color: 'text-red-600',
        bgColor: 'bg-red-100',
        icon: ShieldOff,
        sortValue: diffDays
      }
    } else if (diffDays <= 30) {
      return {
        status: 'expiring_30',
        text: `Expira em ${diffDays} dias`,
        color: 'text-orange-600',
        bgColor: 'bg-orange-100',
        icon: ShieldAlert,
        sortValue: diffDays
      }
    } else if (diffDays <= 60) {
      return {
        status: 'expiring_60',
        text: `Expira em ${diffDays} dias`,
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-100',
        icon: ShieldAlert,
        sortValue: diffDays
      }
    } else {
      return {
        status: 'active',
        text: `Ativa (${diffDays} dias)`,
        color: 'text-green-600',
        bgColor: 'bg-green-100',
        icon: ShieldCheck,
        sortValue: diffDays
      }
    }
  }, [])

  // Função para buscar dados de garantia do banco de dados
  const fetchWarrantyData = useCallback(async () => {
    try {
      setWarrantyLoading(true)
      console.log('🛡️ Buscando dados de garantia do banco de dados...')
      
      // Primeiro, tentar buscar do banco de dados
      const response = await api.get('/warranties/from-database')
      
      if (response.data && response.data.warranties) {
        const warrantyMap = new Map()
        
        response.data.warranties.forEach(warranty => {
          if (warranty.computer_id) {
            // Mapear dados do formato SQL para o formato esperado pelo frontend
            const warrantyInfo = {
              computer_id: warranty.computer_id,
              service_tag: warranty.service_tag,
              warranty_status: warranty.warranty_status,
              warranty_start_date: warranty.warranty_start_date,
              warranty_end_date: warranty.warranty_end_date,
              product_line_description: warranty.product_line_description,
              system_description: warranty.system_description,
              last_updated: warranty.last_updated,
              cache_expires_at: warranty.cache_expires_at,
              needs_update: warranty.needs_update,
              data_source: 'database'
            }
            warrantyMap.set(warranty.computer_id, warrantyInfo)
          }
        })
        
        setWarrantyData(warrantyMap)
        console.log(`✅ ${warrantyMap.size} garantias carregadas do banco de dados`)
        console.log(`📊 Estatísticas: ${response.data.with_warranty_data} com dados, ${response.data.needs_update} precisam atualização`)
      } else {
        console.warn('⚠️ Resposta de garantia em formato inesperado:', response.data)
        setWarrantyData(new Map())
      }
      
    } catch (error) {
      // Fallback para o endpoint legacy se o novo não funcionar
      if (error?.response?.status === 404) {
        console.warn('🔄 Endpoint do banco não encontrado, tentando endpoint legacy...')
        try {
          const legacyResponse = await api.get('/computers/warranty-summary')
          
          if (legacyResponse.data && Array.isArray(legacyResponse.data)) {
            const warrantyMap = new Map()
            legacyResponse.data.forEach(warranty => {
              if (warranty.computer_id) {
                warrantyMap.set(warranty.computer_id, {
                  ...warranty,
                  data_source: 'legacy_api'
                })
              }
            })
            
            setWarrantyData(warrantyMap)
            console.log(`✅ ${warrantyMap.size} garantias carregadas do endpoint legacy`)
          }
        } catch (legacyError) {
          console.error('❌ Erro no endpoint legacy também:', legacyError)
          setWarrantyData(new Map())
        }
      } else {
        console.error('❌ Erro ao buscar garantias:', error)
        setWarrantyData(new Map())
      }
    } finally {
      setWarrantyLoading(false)
    }
  }, [])

  // Função para iniciar atualização de garantias em background
  const startWarrantyRefresh = useCallback(async () => {
    try {
      console.log('🔄 Iniciando atualização de garantias em background...')
      
      // Verificar se já há um job em execução
      const existingJob = await checkForRunningJob()
      if (existingJob) {
        console.log('⚠️ Job já em execução, retomando ao invés de criar novo')
        resumeRunningJob(existingJob)
        return
      }
      
      // Limpar job anterior se existir
      setWarrantyRefreshJob(null)
      setWarrantyRefreshPolling(false)
      
      const response = await api.post('/computers/warranty-refresh', { mode: 'full' })
      console.log('📡 Resposta do servidor:', response.data)
      
      if (response.data && response.data.job_id) {
        const jobId = response.data.job_id
        const initialJob = {
          job_id: jobId,
          status: 'pending',
          progress_percent: 0,
          total: 0,
          processed: 0,
          success_count: 0,
          error_count: 0,
          current_batch: 0,
          total_batches: 0,
          current_processing: null,
          current_batch_items: [],
          estimated_time_remaining: null
        }
        
        setWarrantyRefreshJob(initialJob)
        setWarrantyRefreshPolling(true)
        
        // Salvar job ID no localStorage para persistência entre sessões
        localStorage.setItem('warranty_job_id', jobId)
        localStorage.setItem('warranty_job_start', Date.now().toString())
        
        console.log(`✅ Job de atualização iniciado: ${jobId}`)
        console.log('🔄 Estado inicial do job:', initialJob)
        console.log('💾 Job salvo no localStorage para persistência')
        
        // Iniciar polling do status imediatamente
        setTimeout(() => {
          pollWarrantyRefreshStatus(jobId)
        }, 1000)
      } else {
        console.error('❌ Resposta inválida do servidor:', response.data)
        setToast({ 
          type: 'error', 
          text: 'Resposta inválida do servidor ao iniciar atualização de garantias.' 
        })
        setTimeout(() => setToast(null), 5000)
      }
    } catch (error) {
      console.error('❌ Erro ao iniciar atualização de garantias:', error)
      setToast({ 
        type: 'error', 
        text: `Erro ao iniciar atualização de garantias: ${error.response?.data?.detail || error.message}` 
      })
      setTimeout(() => setToast(null), 8000)
    }
  }, [])

  // Função para fazer polling do status da atualização de garantias
  const pollWarrantyRefreshStatus = useCallback(async (jobId) => {
    try {
      console.log(`🔍 Verificando status do job: ${jobId}`)
      const response = await api.get(`/computers/warranty-refresh/${jobId}`)
      
      if (response.data) {
        const jobData = response.data
        console.log('📊 Dados do job recebidos:', jobData)
        setWarrantyRefreshJob(jobData)
        
        // Log detalhado do progresso
        if (jobData.status === 'running') {
          console.log(`🔄 Status: ${jobData.status}`)
          console.log(`📈 Progresso: ${jobData.processed}/${jobData.total} (${jobData.progress_percent}%)`)
          console.log(`📦 Lote: ${jobData.current_batch}/${jobData.total_batches}`)
          
          if (jobData.current_processing) {
            console.log(`⚙️ Processando: ${jobData.current_processing}`)
          }
          
          if (jobData.success_count !== undefined && jobData.error_count !== undefined) {
            console.log(`✅ Sucessos: ${jobData.success_count}, ❌ Erros: ${jobData.error_count}`)
          }
          
          if (jobData.last_batch_duration) {
            console.log(`⏱️ Duração do último lote: ${jobData.last_batch_duration.toFixed(1)}s`)
          }
          
          if (jobData.estimated_time_remaining) {
            const minutes = Math.floor(jobData.estimated_time_remaining / 60)
            const seconds = jobData.estimated_time_remaining % 60
            console.log(`⏳ Tempo estimado restante: ${minutes}min ${seconds}s`)
          }
        } else if (jobData.status === 'pending') {
          console.log('⏳ Job ainda pendente, aguardando início...')
        }
        
        if (jobData.status === 'completed') {
          setWarrantyRefreshPolling(false)
          console.log('✅ Atualização de garantias concluída com sucesso!')
          
          // Limpar localStorage
          localStorage.removeItem('warranty_job_id')
          localStorage.removeItem('warranty_job_start')
          console.log('🧹 Job concluído, localStorage limpo')
          
          const successMsg = jobData.success_count !== undefined ? 
            `${jobData.success_count} sucessos, ${jobData.error_count} erros` : 
            `${jobData.processed}/${jobData.total} processadas`
          
          setToast({ 
            type: 'success', 
            text: `Atualização de garantias concluída! ${successMsg}.` 
          })
          setTimeout(() => setToast(null), 10000)
          
          // Recarregar dados de garantia após conclusão
          setTimeout(() => {
            console.log('🔄 Recarregando dados de garantia...')
            fetchWarrantyData()
          }, 2000)
        } else if (jobData.status === 'failed') {
          setWarrantyRefreshPolling(false)
          console.error('❌ Atualização de garantias falhou:', jobData.error)
          
          // Limpar localStorage em caso de falha
          localStorage.removeItem('warranty_job_id')
          localStorage.removeItem('warranty_job_start')
          console.log('🧹 Job falhou, localStorage limpo')
          
          setToast({ 
            type: 'error', 
            text: `Erro na atualização de garantias: ${jobData.error || 'Erro desconhecido'}` 
          })
          setTimeout(() => setToast(null), 12000)
        } else if (jobData.status === 'running' || jobData.status === 'pending') {
          // Continuar polling com intervalo dinâmico
          let pollInterval = 3000 // Default 3 segundos
          
          if (jobData.status === 'pending') {
            pollInterval = 2000 // Mais rápido quando pendente
          } else if (jobData.current_processing) {
            pollInterval = 2500 // Mais rápido quando processando item
          } else if (jobData.current_batch && jobData.total_batches) {
            pollInterval = 3500 // Um pouco mais lento entre lotes
          }
          
          setTimeout(() => {
            if (warrantyRefreshPolling) {
              pollWarrantyRefreshStatus(jobId)
            }
          }, pollInterval)
        }
      } else {
        console.error('❌ Resposta vazia do servidor para status do job')
        setWarrantyRefreshPolling(false)
      }
    } catch (error) {
      console.error('❌ Erro ao verificar status da atualização:', error)
      
      if (error.response?.status === 404) {
        console.error('❌ Job não encontrado no servidor')
        setWarrantyRefreshPolling(false)
        setToast({ 
          type: 'error', 
          text: 'Job de atualização não encontrado no servidor' 
        })
      } else {
        setWarrantyRefreshPolling(false)
        setToast({ 
          type: 'error', 
          text: `Erro ao verificar status: ${error.response?.data?.detail || error.message}` 
        })
      }
      setTimeout(() => setToast(null), 8000)
    }
  }, [warrantyRefreshPolling, fetchWarrantyData])

  // Aplicar filtros vindos da navegação do Dashboard
  useEffect(() => {
    if (navigationState && !navigationFiltersApplied.current) {
      const newFilters = { ...filters }
      let shouldShowFilters = false
      
      if (navigationState.filterOS) {
        newFilters.os = navigationState.filterOS
        shouldShowFilters = true
      }
      
      if (navigationState.filterLastLogin) {
        newFilters.lastLogin = navigationState.filterLastLogin
        shouldShowFilters = true
      }
      
      if (navigationState.filterOU) {
        newFilters.ou = navigationState.filterOU
        shouldShowFilters = true
      }

      if (navigationState.filterWarranty) {
        newFilters.warranty = navigationState.filterWarranty
        shouldShowFilters = true
      }
      
      if (shouldShowFilters) {
        setFilters(newFilters)
        setShowFilters(true)
        navigationFiltersApplied.current = true
      }
    }
  }, [navigationState])

  // Função para processar dados uma única vez (otimizada)
  const processComputersData = useCallback((computersData) => {
    if (!computersData || computersData.length === 0) return null
    
    console.time('🔧 Processing computers data')
    setIsProcessing(true)
    
        const processed = {
      computersWithIndex: computersData.map((computer, index) => {
        const loginStatus = (() => {
          if (!computer.lastLogon) return { 
            status: 'never', 
            color: 'text-gray-500', 
            text: 'Nunca', 
            bgColor: 'bg-gray-100',
            sortValue: 999999 
          }

          const diffDays = Math.floor((Date.now() - new Date(computer.lastLogon)) / (1000 * 60 * 60 * 24))

          // Classificação extendida para possível remoção (90+ dias)
          if (diffDays <= 7) {
            return { 
              status: 'recent', 
              color: 'text-green-600', 
              text: `${diffDays} dias atrás`, 
              bgColor: 'bg-green-100',
              sortValue: diffDays 
            }
          } else if (diffDays <= 30) {
            return { 
              status: 'moderate', 
              color: 'text-yellow-600', 
              text: `${diffDays} dias atrás`, 
              bgColor: 'bg-yellow-100',
              sortValue: diffDays 
            }
          } else if (diffDays <= 90) {
            return {
              status: 'old',
              color: 'text-red-600',
              text: `${diffDays} dias atrás`,
              bgColor: 'bg-red-100',
              sortValue: diffDays
            }
          } else {
            return {
              status: 'possible_removal',
              color: 'text-red-800',
              text: `Possível Remoção (${diffDays} dias)`,
              bgColor: 'bg-red-200',
              sortValue: diffDays
            }
          }
        })()
        
        const isEnabled = !computer.disabled && computer.name
        const ou = getComputerOU(computer.name)
        const warranty = warrantyData.get(computer.id)
        const warrantyStatus = getWarrantyStatus(warranty)
        
        const searchableText = [
          computer.name,
          computer.os,
          computer.description || '',
          computer.dnsHostName || '',
          computer.osVersion || '',
          ou.name,
          ou.code,
          warrantyStatus.text
        ].join(' ').toLowerCase()
        
        return {
          ...computer,
          index,
          isEnabled,
          loginStatus,
          ou,
          warranty,
          warrantyStatus,
          searchableText
        }
      }),
      
      uniqueOSList: [...new Set(computersData.map(c => c.os).filter(os => os && os !== 'N/A'))].sort(),
      
      uniqueOUList: (() => {
        const ouCounts = {}
        computersData.forEach(computer => {
          const ou = getComputerOU(computer.name)
          if (ouCounts[ou.code]) {
            ouCounts[ou.code].count++
          } else {
            ouCounts[ou.code] = { ...ou, count: 1 }
          }
        })
        return Object.values(ouCounts).sort((a, b) => a.name.localeCompare(b.name))
      })(),
      
  stats: (() => {
  let enabled = 0, disabled = 0, recent = 0, moderate = 0, old = 0, possibleRemoval = 0, never = 0
  let warrantyActive = 0, warrantyExpired = 0, warrantyExpiring30 = 0, warrantyExpiring60 = 0, warrantyUnknown = 0
        const ouStats = {}
        
        computersData.forEach(computer => {
          const isEnabled = !computer.disabled && computer.name
          if (isEnabled) enabled++; else disabled++
          
          const ou = getComputerOU(computer.name)
          if (!ouStats[ou.code]) {
            ouStats[ou.code] = { 
              ...ou, 
              total: 0, 
              enabled: 0, 
              disabled: 0 
            }
          }
          ouStats[ou.code].total++
          if (isEnabled) ouStats[ou.code].enabled++; else ouStats[ou.code].disabled++
          
          if (!computer.lastLogon) {
            never++
          } else {
            const diffDays = Math.floor((Date.now() - new Date(computer.lastLogon)) / (1000 * 60 * 60 * 24))
            if (diffDays <= 7) recent++
            else if (diffDays <= 30) moderate++
            else if (diffDays <= 90) old++
            else possibleRemoval++
          }

          const warranty = warrantyData.get(computer.id)
          const warrantyStatus = getWarrantyStatus(warranty)
          
          switch (warrantyStatus.status) {
            case 'active':
              warrantyActive++
              break
            case 'expired':
              warrantyExpired++
              break
            case 'expiring_30':
              warrantyExpiring30++
              break
            case 'expiring_60':
              warrantyExpiring60++
              break
            default:
              warrantyUnknown++
          }
        })
        
        return { 
          enabled, disabled, recent, moderate, old, possibleRemoval, never, 
          warrantyActive, warrantyExpired, warrantyExpiring30, warrantyExpiring60, warrantyUnknown,
          byOU: ouStats 
        }
      })(),
      
      processedAt: Date.now()
    }
    
    console.timeEnd('🔧 Processing computers data')
    setIsProcessing(false)
    
    return processed
  }, [getComputerOU, warrantyData, getWarrantyStatus])

  // Função de ordenação
  const handleSort = useCallback((key) => {
    setSortConfig(prevConfig => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'asc' ? 'desc' : 'asc'
    }))
  }, [])

  // Função para obter valor de ordenação
  const getSortValue = useCallback((computer, key) => {
    switch (key) {
      case 'name':
        return computer.name?.toLowerCase() || ''
      case 'ou':
        return computer.ou?.name?.toLowerCase() || ''
      case 'os':
        return computer.os?.toLowerCase() || ''
      case 'warranty':
        return computer.warrantyStatus?.sortValue || 999999
      case 'lastLogin':
        return computer.loginStatus?.sortValue || 999999
      case 'status':
        return computer.isEnabled ? 0 : 1
      case 'created':
        return computer.created ? new Date(computer.created).getTime() : 0
      default:
        return ''
    }
  }, [])

  // Função de busca e filtro ultra-otimizada com debounce e ordenação
  const filteredComputers = useMemo(() => {
    if (!processedData) return []
    
    const hasSearch = debouncedSearchTerm.trim().length > 0
    const hasFilters = Object.values(filters).some(f => f !== 'all')
    
    console.time('🚀 Filter and sort performance')
    
    let filtered = processedData.computersWithIndex
    
    // Aplicar filtros se necessário
    if (hasSearch || hasFilters) {
      const searchLower = debouncedSearchTerm.toLowerCase()
      
      filtered = processedData.computersWithIndex.filter(computer => {
        if (hasSearch && !computer.searchableText.includes(searchLower)) {
          return false
        }
        
        if (filters.status !== 'all') {
          if (filters.status === 'enabled' && !computer.isEnabled) return false
          if (filters.status === 'disabled' && computer.isEnabled) return false
        }
        
        if (filters.os !== 'all') {
          if (navigationState && navigationState.filterOS === filters.os) {
            if (computer.os !== filters.os) return false
          } else {
            if (!computer.os.toLowerCase().includes(filters.os.toLowerCase())) return false
          }
        }
        
        if (filters.lastLogin !== 'all') {
          if (computer.loginStatus.status !== filters.lastLogin) return false
        }
        
        if (filters.ou !== 'all') {
          if (computer.ou.code !== filters.ou) return false
        }

        if (filters.warranty !== 'all') {
          if (computer.warrantyStatus.status !== filters.warranty) return false
        }

        // Advanced filters: lastLoginDays
        if (advancedFilters.lastLoginDays && advancedFilters.lastLoginDays !== 'all') {
          const val = advancedFilters.lastLoginDays
          const lastLogon = computer.lastLogon ? new Date(computer.lastLogon) : null
          const diffDays = lastLogon ? Math.floor((Date.now() - lastLogon.getTime()) / (1000 * 60 * 60 * 24)) : null
          if (val === '7' && (diffDays === null || diffDays > 7)) return false
          if (val === '30' && (diffDays === null || diffDays > 30)) return false
          if (val === '60' && (diffDays === null || diffDays > 60)) return false
          if (val === '90' && (diffDays === null || diffDays > 90)) return false
          if (val === '120+' && (diffDays === null || diffDays < 120)) return false
        }

        // Inventory separation placeholder (requires backend fields)
        if (advancedFilters.inventory && advancedFilters.inventory !== 'all') {
          // assume computer.inventoryStatus exists ('spare'|'in_use') otherwise skip
          if (computer.inventoryStatus) {
            if (advancedFilters.inventory === 'spare' && computer.inventoryStatus !== 'spare') return false
            if (advancedFilters.inventory === 'in_use' && computer.inventoryStatus !== 'in_use') return false
          }
        }

        // AssignedTo / prevUser placeholders (search against owner fields if present)
        if (advancedFilters.assignedTo && advancedFilters.assignedTo.trim() !== '') {
          const q = advancedFilters.assignedTo.toLowerCase()
          if (!computer.currentUser || !computer.currentUser.toLowerCase().includes(q)) return false
        }

        if (advancedFilters.prevUser && advancedFilters.prevUser.trim() !== '') {
          const q = advancedFilters.prevUser.toLowerCase()
          if (!computer.previousUser || !computer.previousUser.toLowerCase().includes(q)) return false
        }
        
        return true
      })
    }
    
    // Aplicar ordenação
    filtered.sort((a, b) => {
      const aValue = getSortValue(a, sortConfig.key)
      const bValue = getSortValue(b, sortConfig.key)
      
      let comparison = 0
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        comparison = aValue.localeCompare(bValue)
      } else if (typeof aValue === 'number' && typeof bValue === 'number') {
        comparison = aValue - bValue
      } else {
        comparison = String(aValue).localeCompare(String(bValue))
      }
      
      return sortConfig.direction === 'asc' ? comparison : -comparison
    })
    
    console.timeEnd('🚀 Filter and sort performance')
    console.log(`🔍 Filtered: ${filtered.length}/${processedData.computersWithIndex.length}, Sorted by: ${sortConfig.key} ${sortConfig.direction}`)
    
    return filtered
  }, [processedData, debouncedSearchTerm, filters, navigationState, sortConfig, getSortValue])

  // Cache functions
  const getCachedData = useCallback(() => {
    try {
      const cached = sessionStorage.getItem('computers-memory-cache')
      const cacheTime = sessionStorage.getItem('computers-memory-time')
      
      if (cached && cacheTime) {
        const timeDiff = Date.now() - parseInt(cacheTime)
        if (timeDiff < CACHE_DURATION) {
          return {
            data: JSON.parse(cached),
            timestamp: parseInt(cacheTime),
            isValid: true
          }
        }
      }
      
      return { data: null, timestamp: null, isValid: false }
    } catch (error) {
      console.error('❌ Erro no cache de memória:', error)
      return { data: null, timestamp: null, isValid: false }
    }
  }, [])

  const setCachedData = useCallback((data) => {
    try {
      const timestamp = Date.now()
      sessionStorage.setItem('computers-memory-cache', JSON.stringify(data))
      sessionStorage.setItem('computers-memory-time', timestamp.toString())
      return timestamp
    } catch (error) {
      console.error('❌ Erro ao salvar cache:', error)
      return Date.now()
    }
  }, [])

  // Função principal para buscar dados
  const fetchComputers = useCallback(async (useCache = true, inventoryFilter = null) => {
    if (useCache && memoryCache && processedData && !inventoryFilter) {
      console.log('⚡ Usando dados da memória da sessão')
      return
    }
    
    try {
      setLoading(true)
      setIsFromCache(false)

      if (useCache && !inventoryFilter) {
        const cached = getCachedData()
        if (cached.isValid && cached.data) {
          console.log('📦 Carregando do cache de sessão...')
          setComputers(cached.data)
          setMemoryCache(cached.data)
          setLastFetchTime(new Date(cached.timestamp))
          setIsFromCache(true)
          
          fetchWarrantyData()
          
          setTimeout(() => {
            const processed = processComputersData(cached.data)
            setProcessedData(processed)
          }, 0)
          
          setLoading(false)
          return
        }
      }

      console.log('🌐 Buscando dados do servidor...')
      console.time('API Request')
      
      let computerData = []
      let dataSource = 'unknown'
      
      try {
        console.log('🗄️ Tentando buscar do SQL...')
        let sqlUrl = '/computers?source=sql'
        if (inventoryFilter) {
          sqlUrl += `&inventory_filter=${inventoryFilter}`
        }
        const sqlResponse = await api.get(sqlUrl)
        
        if (sqlResponse.data && Array.isArray(sqlResponse.data)) {
          computerData = sqlResponse.data
          dataSource = 'sql'
          console.log(`📊 SQL retornou ${computerData.length} máquinas`)
        } else if (sqlResponse.data && sqlResponse.data.computers && Array.isArray(sqlResponse.data.computers)) {
          computerData = sqlResponse.data.computers
          dataSource = 'sql'
          console.log(`📊 SQL retornou ${computerData.length} máquinas (formato estruturado)`)
        } else {
          throw new Error('SQL retornou dados em formato inesperado')
        }
        
      } catch (sqlError) {
        console.warn('⚠️ SQL falhou, tentando AD como fallback:', sqlError.message)
        
        try {
          const adResponse = await api.get('/computers?source=ad')
          
          if (adResponse.data && Array.isArray(adResponse.data)) {
            computerData = adResponse.data
            dataSource = 'ad'
            console.log(`📊 AD retornou ${computerData.length} máquinas`)
          } else {
            throw new Error('AD também falhou')
          }
          
        } catch (adError) {
          console.error('❌ Ambos SQL e AD falharam:', adError.message)
          throw new Error('Não foi possível carregar dados de nenhuma fonte')
        }
      }

      console.timeEnd('API Request')
      console.log(`✅ ${computerData.length} máquinas carregadas (fonte: ${dataSource})`)

      if (!Array.isArray(computerData)) {
        throw new Error('Dados recebidos não são um array válido')
      }

      const timestamp = setCachedData(computerData)
      setMemoryCache(computerData)
      setComputers(computerData)
      setLastFetchTime(new Date(timestamp))
      setIsFromCache(false)
      
      fetchWarrantyData()
      
      const processed = processComputersData(computerData)
      setProcessedData(processed)
      
    } catch (error) {
      console.error('❌ Erro ao carregar máquinas:', error)
      
      const cached = getCachedData()
      if (cached.data && Array.isArray(cached.data)) {
        console.log('📦 Usando cache como último recurso...')
        setComputers(cached.data)
        setMemoryCache(cached.data)
        setLastFetchTime(new Date(cached.timestamp))
        setIsFromCache(true)
        
        fetchWarrantyData()
        
        const processed = processComputersData(cached.data)
        setProcessedData(processed)
      } else {
        console.error('💥 Erro total: nem API nem cache funcionaram')
        setComputers([])
        setMemoryCache(null)
        setProcessedData(null)
      }
    } finally {
      setLoading(false)
    }
  }, [getCachedData, setCachedData, processComputersData, memoryCache, processedData, fetchWarrantyData])

  // Reprocessar dados quando garantias mudarem
  useEffect(() => {
    if (computers.length > 0 && warrantyData.size > 0) {
      const processed = processComputersData(computers)
      setProcessedData(processed)
    }
  }, [warrantyData, computers, processComputersData])

  // Função para sincronização completa (limpeza total do SQL)
  const handleSyncCompleteAD = useCallback(async () => {
    try {
      setSyncCompleteLoading(true)
      setSyncMessage({ type: 'info', text: 'Iniciando sincronização completa com limpeza total do SQL...' })
      
      console.log('🔄 Iniciando sincronização completa AD → SQL (limpeza total)')
      
      const response = await api.post('/computers/sync-complete')
      
      if (response.data.success) {
        const stats = response.data.stats
        setSyncMessage({ 
          type: 'success', 
          text: `Sincronização completa realizada! ${stats.computers_deleted} removidas, ${stats.computers_added} adicionadas do AD. Total atual: ${stats.computers_after_sync}`
        })
        
        console.log('✅ Sincronização completa com limpeza concluída:', stats)
        
        // Limpar completamente o cache e forçar recarregamento
        setMemoryCache(null)
        setProcessedData(null)
        setWarrantyData(new Map())
        sessionStorage.removeItem('computers-memory-cache')
        sessionStorage.removeItem('computers-memory-time')
        
        // Recarregar dados após 2 segundos
        setTimeout(() => {
          fetchComputers(false)
          setSyncMessage(null)
        }, 2000)
        
      } else {
        setSyncMessage({ 
          type: 'error', 
          text: `Erro na sincronização: ${response.data.message}`
        })
        setTimeout(() => setSyncMessage(null), 5000)
      }
      
    } catch (error) {
      console.error('❌ Erro na sincronização completa:', error)
      setSyncMessage({ 
        type: 'error', 
        text: `Erro na sincronização: ${error.response?.data?.message || error.message}`
      })
      setTimeout(() => setSyncMessage(null), 5000)
    } finally {
      setSyncCompleteLoading(false)
    }
  }, [fetchComputers])

  // Função para sincronização incremental (tradicional)
  const handleSyncIncremental = useCallback(async () => {
    try {
      setSyncCompleteLoading(true)
      setSyncMessage({ type: 'info', text: 'Iniciando sincronização incremental...' })
      
      const response = await api.post('/computers/sync-incremental')
      
      if (response.data.success) {
        setSyncMessage({ 
          type: 'success', 
          text: 'Sincronização incremental concluída! Dados atualizados sem remoções.'
        })
        
        // Recarregar dados
        setTimeout(() => {
          fetchComputers(false)
          setSyncMessage(null)
        }, 1500)
        
      } else {
        setSyncMessage({ 
          type: 'error', 
          text: `Erro na sincronização: ${response.data.message}`
        })
        setTimeout(() => setSyncMessage(null), 5000)
      }
      
    } catch (error) {
      console.error('❌ Erro na sincronização incremental:', error)
      setSyncMessage({ 
        type: 'error', 
        text: `Erro na sincronização: ${error.response?.data?.message || error.message}`
      })
      setTimeout(() => setSyncMessage(null), 5000)
    } finally {
      setSyncCompleteLoading(false)
    }
  }, [fetchComputers])

  // Função para chamar a API de toggle
  const performToggle = useCallback(async (computerName, action) => {
    setToggleStatusLoading(prev => new Set(prev).add(computerName))
    try {
      const resp = await api.post(`/computers/${encodeURIComponent(computerName)}/toggle-status`, { action })
      return resp.data
    } catch (error) {
      throw error
    } finally {
      setToggleStatusLoading(prev => {
        const copy = new Set(prev)
        copy.delete(computerName)
        return copy
      })
    }
  }, [])

  // Função para verificar se há job em execução
  const checkForRunningJob = useCallback(async () => {
    try {
      console.log('🔍 Verificando se há job de garantia em execução...')
      
      // Primeiro tentar recuperar job ID do localStorage
      const storedJobId = localStorage.getItem('warranty_job_id')
      const storedJobStart = localStorage.getItem('warranty_job_start')
      
      if (storedJobId) {
        console.log(`📋 Job encontrado no localStorage: ${storedJobId}`)
        
        // Verificar se o job ainda está válido (não mais que 2 horas)
        const jobStartTime = parseInt(storedJobStart) || Date.now()
        const twoHoursAgo = Date.now() - (2 * 60 * 60 * 1000)
        
        if (jobStartTime < twoHoursAgo) {
          console.log('⏰ Job muito antigo, removendo do localStorage')
          localStorage.removeItem('warranty_job_id')
          localStorage.removeItem('warranty_job_start')
          return null
        }
        
        // Tentar buscar status do job
        try {
          const response = await api.get(`/computers/warranty-refresh/${storedJobId}`)
          const jobData = response.data
          
          console.log('📊 Status do job recuperado:', jobData)
          
          if (jobData.status === 'running' || jobData.status === 'pending') {
            console.log('✅ Job ainda em execução, retomando acompanhamento')
            return jobData
          } else {
            console.log('✅ Job já finalizado, limpando localStorage')
            localStorage.removeItem('warranty_job_id')
            localStorage.removeItem('warranty_job_start')
            return null
          }
        } catch (error) {
          if (error.response?.status === 404) {
            console.log('❌ Job não encontrado no servidor, limpando localStorage')
            localStorage.removeItem('warranty_job_id')
            localStorage.removeItem('warranty_job_start')
          } else {
            console.error('❌ Erro ao verificar job:', error)
          }
          return null
        }
      }
      
      console.log('ℹ️ Nenhum job em execução encontrado')
      return null
    } catch (error) {
      console.error('❌ Erro ao verificar job em execução:', error)
      return null
    }
  }, [])

  // Função para retomar job em execução
  const resumeRunningJob = useCallback((jobData) => {
    console.log('🔄 Retomando job em execução:', jobData)
    
    setWarrantyRefreshJob(jobData)
    setWarrantyRefreshPolling(true)
    
    // Mostrar notificação de que o job foi retomado
    setToast({ 
      type: 'info', 
      text: `Retomando atualização de garantias em progresso... ${jobData.processed || 0}/${jobData.total || 0} processadas` 
    })
    setTimeout(() => setToast(null), 5000)
    
    // Iniciar polling imediatamente
    setTimeout(() => {
      pollWarrantyRefreshStatus(jobData.job_id)
    }, 1000)
  }, [pollWarrantyRefreshStatus])

  // Função para testar conectividade com o backend
  const testBackendConnectivity = useCallback(async () => {
    try {
      console.log('🔗 Testando conectividade com o backend...')
      const response = await api.get('/computers/warranty-debug')
      console.log('✅ Backend conectado:', response.data)
      return true
    } catch (error) {
      console.error('❌ Erro de conectividade com backend:', error)
      return false
    }
  }, [])

  // Forçar refresh limpa toda a memória e inicia atualização de garantias
  const forceRefresh = useCallback(async () => {
    setMemoryCache(null)
    setProcessedData(null)
    setWarrantyData(new Map())
    sessionStorage.removeItem('computers-memory-cache')
    sessionStorage.removeItem('computers-memory-time')
    
    // Testar conectividade antes de iniciar
    const isConnected = await testBackendConnectivity()
    
    fetchComputers(false)
    
    // Só iniciar atualização de garantias se backend estiver acessível
    if (isConnected) {
      startWarrantyRefresh()
    } else {
      console.warn('⚠️ Backend não está acessível, pulando atualização de garantias')
      setToast({ 
        type: 'error', 
        text: 'Backend não está acessível. Atualização de garantias não será iniciada.' 
      })
      setTimeout(() => setToast(null), 8000)
    }
  }, [fetchComputers, startWarrantyRefresh, testBackendConnectivity])

  // Handler de busca otimizado
  const handleSearchChange = useCallback((value) => {
    setSearchTerm(value)
  }, [])

  const resetFilters = useCallback(() => {
    setFilters({
      status: 'all',
      os: 'all',
      lastLogin: 'all',
      ou: 'all',
      warranty: 'all'
    })
    setSearchTerm('')
    setDebouncedSearchTerm('')
    setSortConfig({ key: 'name', direction: 'asc' })
    navigationFiltersApplied.current = false
  }, [])

  const formatDate = useCallback((dateString) => {
    if (!dateString) return 'N/A'
    try {
      return new Date(dateString).toLocaleDateString('pt-BR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return 'N/A'
    }
  }, [])

  const getCacheStatus = useCallback(() => {
    if (!lastFetchTime) return null
    
    const now = new Date()
    const timeDiff = now - lastFetchTime
    const minutesAgo = Math.floor(timeDiff / (1000 * 60))
    
    return {
      isExpired: timeDiff > CACHE_DURATION,
      minutesAgo,
      isFromCache,
      hasMemoryCache: !!memoryCache
    }
  }, [lastFetchTime, isFromCache, memoryCache])

  // Componente para header de coluna ordenável
  const SortableHeader = ({ sortKey, children, className = "" }) => (
    <th
      className={`px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors ${className}`}
      onClick={() => handleSort(sortKey)}
    >
      <div className="flex items-center space-x-1">
        <span>{children}</span>
        {sortConfig.key === sortKey ? (
          sortConfig.direction === 'asc' ? (
            <ChevronUp className="h-3 w-3" />
          ) : (
            <ChevronDown className="h-3 w-3" />
          )
        ) : (
          <ArrowUpDown className="h-3 w-3 opacity-30" />
        )}
      </div>
    </th>
  )

  useEffect(() => {
    if (!initialLoadRef.current) {
      initialLoadRef.current = true
      
      const initializePage = async () => {
        // Primeiro carregar os dados
        fetchComputers(true)
        
        // Verificar se há job em execução
        const runningJob = await checkForRunningJob()
        
        if (runningJob) {
          console.log('🔄 Job em execução detectado, retomando acompanhamento')
          resumeRunningJob(runningJob)
        } else {
          console.log('🆕 Nenhum job em execução. Atualizações automáticas de garantias estão desabilitadas no momento.')
          // Não iniciar startWarrantyRefresh automaticamente enquanto estiver desabilitado
        }
      }
      
      initializePage()
    }
  }, [fetchComputers, startWarrantyRefresh, checkForRunningJob, resumeRunningJob])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <div className="flex items-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">
            {isFromCache ? 'Carregando do cache...' : 'Carregando máquinas...'}
          </span>
          {isProcessing && (
            <span className="ml-2 text-orange-600">• Processando dados...</span>
          )}
        </div>
        {warrantyLoading && (
          <div className="flex items-center text-sm">
            <Shield className="h-4 w-4 animate-pulse text-green-600 mr-2" />
            <span className="text-gray-600">Carregando garantias Dell...</span>
          </div>
        )}
      </div>
    )
  }

  if (!loading && (!computers || computers.length === 0)) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Máquinas do Active Directory</h1>
          <button
            onClick={forceRefresh}
            className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Tentar Novamente</span>
          </button>
          {/* Cache controls removed per UX request - cache still used internally */}
          <p className="mt-2 text-sm text-gray-500">Não foi possível carregar dados do SQL Server nem do Active Directory.</p>
        </div>
      </div>
    )
  }

  const cacheStatus = getCacheStatus()
  const stats = processedData?.stats || { 
    enabled: 0, disabled: 0, recent: 0, old: 0, never: 0, 
    warrantyActive: 0, warrantyExpired: 0, warrantyExpiring30: 0, warrantyExpiring60: 0, warrantyUnknown: 0,
    byOU: {} 
  }
  const uniqueOSList = processedData?.uniqueOSList || []
  const uniqueOUList = processedData?.uniqueOUList || []

  const getActiveFiltersInfo = () => {
    const activeFilters = []
    
    if (navigationState?.filterOS && filters.os !== 'all') {
      activeFilters.push(`Sistema: ${filters.os}`)
    }
    
    if (navigationState?.filterLastLogin && filters.lastLogin !== 'all') {
      const statusMap = {
        'recent': 'Login Recente (7 dias)',
        'old': 'Inativo (30+ dias)',
        'never': 'Nunca fez login'
      }
      activeFilters.push(`Status: ${statusMap[filters.lastLogin] || filters.lastLogin}`)
    }
    
    if (navigationState?.filterOU && filters.ou !== 'all') {
      const ou = uniqueOUList.find(ou => ou.code === filters.ou)
      activeFilters.push(`OU: ${ou?.name || filters.ou}`)
    }

    if (navigationState?.filterWarranty && filters.warranty !== 'all') {
      const warrantyMap = {
        'active': 'Garantia Ativa',
        'expired': 'Garantia Expirada',
        'expiring_30': 'Expirando em 30 dias',
        'expiring_60': 'Expirando em 60 dias'
      }
      activeFilters.push(`Garantia: ${warrantyMap[filters.warranty] || filters.warranty}`)
    }

    if (advancedFilters.lastLoginDays && advancedFilters.lastLoginDays !== 'all') {
      activeFilters.push(`Último login: ${advancedFilters.lastLoginDays} dias+`)
    }

    if (advancedFilters.inventory && advancedFilters.inventory !== 'all') {
      activeFilters.push(`Inventário: ${advancedFilters.inventory === 'spare' ? 'Spare' : 'Em Uso'}`)
    }

    if (advancedFilters.assignedTo) {
      activeFilters.push(`Atribuído: ${advancedFilters.assignedTo}`)
    }

    if (advancedFilters.prevUser) {
      activeFilters.push(`Usuário anterior: ${advancedFilters.prevUser}`)
    }
    
    return activeFilters
  }

  const activeFiltersInfo = getActiveFiltersInfo()

  return (
    <div className="space-y-6">
      {/* Toast */}
      {toast && (
        <div className={`fixed bottom-6 right-6 z-50 max-w-sm w-full p-3 rounded-md shadow-lg ${toast.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'}`}>
          <div className="flex items-center justify-between">
            <div className="text-sm">{toast.text}</div>
            <button onClick={() => setToast(null)} className="ml-4 text-white opacity-80 hover:opacity-100">✕</button>
          </div>
        </div>
      )}
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <div className="flex items-center space-x-3">
            {navigationState?.fromDashboard && (
              <Link
                to="/"
                className="flex items-center text-blue-600 hover:text-blue-800 transition-colors"
                title="Voltar ao Dashboard"
              >
                <ArrowLeft className="h-5 w-5" />
              </Link>
            )}
            <h1 className="text-3xl font-bold text-gray-900">Máquinas do Active Directory</h1>
          </div>
          
          {activeFiltersInfo.length > 0 && (
            <div className="flex items-center space-x-2 text-sm text-blue-600 mt-2">
              <Filter className="h-4 w-4" />
              <span>Filtros aplicados: {activeFiltersInfo.join(', ')}</span>
            </div>
          )}
          
          {cacheStatus && (
            <div className="flex items-center space-x-2 text-sm text-gray-500 mt-1">
              <Database className="h-4 w-4" />
              <span>
                {cacheStatus.hasMemoryCache ? 'Memória' : (isFromCache ? 'Cache' : 'Servidor')} • 
                {cacheStatus.minutesAgo === 0 ? 'agora' : `${cacheStatus.minutesAgo}min`}
              </span>
              {cacheStatus.isExpired && (
                <span className="text-orange-600">• Cache expirado</span>
              )}
              {warrantyLoading && (
                <span className="text-green-600">• Carregando garantias</span>
              )}
            </div>
          )}

          {/* Barra de progresso da atualização de garantias */}
          {warrantyRefreshJob && (warrantyRefreshJob.status === 'running' || warrantyRefreshJob.status === 'pending') && (
            <div className="mt-3 p-4 bg-blue-50 border border-blue-200 rounded-md">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <Shield className="h-4 w-4 text-blue-600 animate-pulse" />
                  <span className="text-sm font-medium text-blue-800">
                    {warrantyRefreshJob.status === 'pending' ? 'Preparando atualização de garantias...' : 'Atualizando garantias Dell'}
                  </span>
                  {localStorage.getItem('warranty_job_id') && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                      <div className="w-1 h-1 bg-green-600 rounded-full mr-1"></div>
                      Persistente
                    </span>
                  )}
                  {warrantyRefreshJob.current_processing && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800 animate-bounce">
                      <div className="w-1 h-1 bg-blue-600 rounded-full mr-1 animate-pulse"></div>
                      Processando
                    </span>
                  )}
                  {warrantyRefreshJob.status === 'pending' && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-yellow-100 text-yellow-800">
                      <div className="w-1 h-1 bg-yellow-600 rounded-full mr-1 animate-pulse"></div>
                      Iniciando...
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-blue-600 font-mono">
                    {warrantyRefreshJob.processed || 0}/{warrantyRefreshJob.total || '?'} ({warrantyRefreshJob.progress_percent || 0}%)
                  </span>
                  <button
                    onClick={() => {
                      setWarrantyRefreshPolling(false)
                      setWarrantyRefreshJob(null)
                      
                      // Limpar localStorage
                      localStorage.removeItem('warranty_job_id')
                      localStorage.removeItem('warranty_job_start')
                      
                      console.log('🛑 Atualização de garantias cancelada pelo usuário')
                      console.log('🧹 localStorage limpo')
                      
                      setToast({ 
                        type: 'info', 
                        text: 'Acompanhamento da atualização cancelado (processo continua no servidor)' 
                      })
                      setTimeout(() => setToast(null), 5000)
                    }}
                    className="text-xs text-red-600 hover:text-red-800 px-2 py-1 rounded bg-red-50 hover:bg-red-100 transition-colors"
                    title="Parar acompanhamento (processo continua no servidor)"
                  >
                    ✕
                  </button>
                </div>
              </div>
              
              {/* Barra de progresso principal */}
              <div className="w-full bg-blue-200 rounded-full h-3 mb-2">
                <div 
                  className="bg-blue-600 h-3 rounded-full transition-all duration-500 ease-in-out" 
                  style={{ width: `${warrantyRefreshJob.progress_percent || 0}%` }}
                ></div>
              </div>
              
              {/* Informações detalhadas */}
              <div className="space-y-1">
                {/* Lote atual */}
                {warrantyRefreshJob.status === 'running' && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-blue-700">
                      📦 Lote: {warrantyRefreshJob.current_batch || 0}/{warrantyRefreshJob.total_batches || '?'}
                    </span>
                    {warrantyRefreshJob.estimated_time_remaining && warrantyRefreshJob.estimated_time_remaining > 0 && (
                      <span className="text-blue-600">
                        ⏱️ ~{Math.floor(warrantyRefreshJob.estimated_time_remaining / 60)}min {warrantyRefreshJob.estimated_time_remaining % 60}s restantes
                      </span>
                    )}
                  </div>
                )}
                
                {/* Status quando pendente */}
                {warrantyRefreshJob.status === 'pending' && (
                  <div className="text-xs text-blue-700">
                    🔄 Preparando lista de computadores para atualização...
                  </div>
                )}
                
                {/* Item atual sendo processado */}
                {warrantyRefreshJob.current_processing && (
                  <div className="text-xs text-blue-700">
                    ⚙️ Processando: <span className="font-mono">{warrantyRefreshJob.current_processing}</span>
                  </div>
                )}
                
                {/* Estatísticas de sucesso/erro */}
                {(warrantyRefreshJob.success_count !== undefined || warrantyRefreshJob.error_count !== undefined) && (
                  <div className="flex items-center space-x-4 text-xs">
                    <span className="text-green-700">
                      ✅ Sucessos: {warrantyRefreshJob.success_count || 0}
                    </span>
                    <span className="text-red-700">
                      ❌ Erros: {warrantyRefreshJob.error_count || 0}
                    </span>
                  </div>
                )}
                
                {/* Performance do batch */}
                {warrantyRefreshJob.last_batch_duration && (
                  <div className="text-xs text-blue-700">
                    ⏱️ Último lote: {warrantyRefreshJob.last_batch_duration.toFixed(1)}s
                  </div>
                )}
                
                {/* Informações do lote atual */}
                {warrantyRefreshJob.current_batch_items && warrantyRefreshJob.current_batch_items.length > 0 && (
                  <div className="mt-2 p-2 bg-white bg-opacity-50 rounded text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <div className="font-medium text-blue-800">Lote atual ({warrantyRefreshJob.current_batch_items.length} itens):</div>
                      {warrantyRefreshJob.last_batch_duration && (
                        <div className="text-blue-600 text-xs">
                          {warrantyRefreshJob.last_batch_duration.toFixed(1)}s
                        </div>
                      )}
                    </div>
                    <div className="space-y-1 max-h-24 overflow-y-auto">
                      {warrantyRefreshJob.current_batch_items.map((item, index) => (
                        <div key={index} className="flex items-center justify-between text-xs">
                          <div className="flex items-center space-x-2 flex-1 min-w-0">
                            <span className="font-mono text-blue-700 text-xs truncate">
                              {item.service_tag}
                            </span>
                            {item.computer_name && item.computer_name !== 'Unknown' && (
                              <span className="text-gray-600 text-xs truncate">
                                ({item.computer_name})
                              </span>
                            )}
                          </div>
                          <div className="flex items-center space-x-1 flex-shrink-0">
                            {item.status === 'success' && (
                              <>
                                <span className="text-green-600">✅</span>
                                <span className={`text-xs px-1 rounded ${
                                  item.warranty_status === 'Active' ? 'bg-green-100 text-green-700' :
                                  item.warranty_status === 'Expired' ? 'bg-red-100 text-red-700' :
                                  'bg-gray-100 text-gray-700'
                                }`}>
                                  {item.warranty_status}
                                </span>
                                {item.end_date && (
                                  <span className="text-xs text-gray-500">
                                    {item.end_date}
                                  </span>
                                )}
                              </>
                            )}
                            {item.status !== 'success' && (
                              <>
                                <span className="text-red-600">❌</span>
                                <span className="text-red-600 text-xs truncate max-w-20" title={item.error}>
                                  {item.error}
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              
              <div className="text-xs text-blue-600 mt-2 border-t border-blue-200 pt-2">
                💡 Processamento em background (10 itens por lote) - Outras ações permanecem disponíveis
                {warrantyRefreshJob.job_id && (
                  <div className="text-xs text-gray-500 mt-1">
                    Job ID: {warrantyRefreshJob.job_id} | Status: {warrantyRefreshJob.status}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Ordenação atual */}
          {sortConfig.key !== 'name' || sortConfig.direction !== 'asc' ? (
            <div className="flex items-center space-x-2 text-sm text-purple-600 mt-1">
              <ArrowUpDown className="h-4 w-4" />
              <span>
                Ordenado por: {sortConfig.key === 'name' ? 'Nome' : 
                             sortConfig.key === 'ou' ? 'OU' :
                             sortConfig.key === 'os' ? 'Sistema Op.' :
                             sortConfig.key === 'warranty' ? 'Garantia' :
                             sortConfig.key === 'lastLogin' ? 'Último Login' :
                             sortConfig.key === 'status' ? 'Status' :
                             sortConfig.key === 'created' ? 'Criação' : sortConfig.key}
                ({sortConfig.direction === 'asc' ? 'crescente' : 'decrescente'})
              </span>
            </div>
          ) : null}
        </div>
        
          <div className="flex space-x-2">
          <button
            onClick={handleSyncIncremental}
            disabled={syncCompleteLoading || loading}
            className="flex items-center space-x-2 bg-yellow-600 text-white px-4 py-2 rounded-md hover:bg-yellow-700 transition-colors disabled:opacity-50"
            title="Sincronização incremental (apenas adiciona/atualiza, não remove)"
          >
            <RefreshCw className={`h-4 w-4 ${syncCompleteLoading ? 'animate-spin' : ''}`} />
            <span>Sync +</span>
          </button>

          <button
            onClick={handleSyncCompleteAD}
            disabled={syncCompleteLoading || loading}
            className="flex items-center space-x-2 bg-orange-600 text-white px-4 py-2 rounded-md hover:bg-orange-700 transition-colors disabled:opacity-50"
            title="Sincronização completa (limpa SQL e reconstrói do AD)"
          >
            <RotateCcw className={`h-4 w-4 ${syncCompleteLoading ? 'animate-spin' : ''}`} />
            <span>Reset AD</span>
          </button>
          
          <button
            onClick={forceRefresh}
            disabled={loading}
            className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
            title="Atualizar do servidor e limpar cache"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Atualizar</span>
          </button>
        </div>
      </div>
      {/* Confirm Dialog Modal */}
      {confirmDialog.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900">Confirmação</h3>
            <p className="mt-2 text-sm text-gray-600">Você tem certeza que deseja {confirmDialog.action === 'disable' ? 'desativar' : 'ativar'} a máquina <strong>{confirmDialog.computer.name}</strong>?</p>
            <div className="mt-4 flex justify-end space-x-2">
              <button
                onClick={() => setConfirmDialog({ open: false, computer: null, action: null })}
                className="px-3 py-2 rounded-md bg-gray-100 hover:bg-gray-200 text-sm"
              >
                Cancelar
              </button>
              <button
                onClick={async () => {
                  const { computer, action } = confirmDialog
                  try {
                    const result = await performToggle(computer.name, action)
                    const msgType = result.success ? 'success' : 'error'
                    const messageText = result.message || (result.success ? 'Operação realizada' : 'Falha')
                    setStatusMessages(prev => new Map(prev).set(computer.name, { type: msgType, text: messageText }))
                    // show toast
                    setToast({ type: msgType, text: `${action === 'disable' ? 'Desativação' : 'Ativação'}: ${computer.name} — ${messageText}` })
                    setTimeout(() => setToast(null), 4000)
                    // Atualizar cache simples para refletir mudança imediata
                    setProcessedData(prev => {
                      if (!prev) return prev
                      const newProcessed = { ...prev }
                      newProcessed.computersWithIndex = newProcessed.computersWithIndex.map(c => c.name === computer.name ? { ...c, isEnabled: action === 'enable' } : c)
                      return newProcessed
                    })
                  } catch (err) {
                    const messageText = err.message || 'Erro na requisição'
                    setStatusMessages(prev => new Map(prev).set(computer.name, { type: 'error', text: messageText }))
                    setToast({ type: 'error', text: `${action === 'disable' ? 'Desativação' : 'Ativação'} falhou: ${computer.name} — ${messageText}` })
                    setTimeout(() => setToast(null), 4000)
                  } finally {
                    setConfirmDialog({ open: false, computer: null, action: null })
                  }
                }}
                className="px-3 py-2 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-sm"
              >
                Confirmar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mensagem de sincronização */}
      {syncMessage && (
        <div className={`p-4 rounded-md ${
          syncMessage.type === 'success' ? 'bg-green-50 border border-green-200' :
          syncMessage.type === 'error' ? 'bg-red-50 border border-red-200' :
          'bg-blue-50 border border-blue-200'
        }`}>
          <div className="flex items-center">
            {syncMessage.type === 'success' ? (
              <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
            ) : syncMessage.type === 'error' ? (
              <XCircle className="h-5 w-5 text-red-600 mr-2" />
            ) : (
              <AlertCircle className="h-5 w-5 text-blue-600 mr-2" />
            )}
            <span className={`text-sm font-medium ${
              syncMessage.type === 'success' ? 'text-green-800' :
              syncMessage.type === 'error' ? 'text-red-800' :
              'text-blue-800'
            }`}>
              {syncMessage.text}
            </span>
          </div>
        </div>
      )}

      {/* Barra de Pesquisa Otimizada */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
        <input
          ref={searchInputRef}
          type="text"
          placeholder="Pesquisar por nome, sistema operacional, descrição, DNS, OU ou garantia..."
          className="w-full pl-10 pr-20 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
          value={searchTerm}
          onChange={(e) => handleSearchChange(e.target.value)}
        />
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center space-x-2">
          {isSearching && (
            <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
          )}
          {(searchTerm || debouncedSearchTerm) && !isSearching && (
            <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
              {filteredComputers.length}
            </span>
          )}
          {!searchTerm && !debouncedSearchTerm && Object.values(filters).some(f => f !== 'all') && (
            <span className="text-xs text-orange-600 bg-orange-100 px-2 py-1 rounded">
              Filtrado
            </span>
          )}
        </div>
      </div>

      {/* Filtros Avançados */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-4 py-3 border-b border-gray-200">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 text-gray-700 hover:text-gray-900 transition-colors"
          >
            <Filter className="h-4 w-4" />
            <span>Filtros Avançados</span>
            <ChevronDown className={`h-4 w-4 transition-transform duration-200 ${showFilters ? 'rotate-180' : ''}`} />
            {activeFiltersInfo.length > 0 && (
              <span className="ml-2 bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                {activeFiltersInfo.length} ativo{activeFiltersInfo.length > 1 ? 's' : ''}
              </span>
            )}
          </button>
        </div>
        
        <div className={`transition-all duration-300 ease-in-out overflow-hidden ${
          showFilters ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}>
          <div className="p-4 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                <select
                  value={filters.status}
                  onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                >
                  <option value="all">Todos ({computers.length})</option>
                  <option value="enabled">Ativadas ({stats.enabled})</option>
                  <option value="disabled">Desativadas ({stats.disabled})</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Unidade Organizacional
                  {navigationState?.filterOU && (
                    <span className="ml-2 text-xs text-blue-600">(filtro do dashboard)</span>
                  )}
                </label>
                <select
                  value={filters.ou}
                  onChange={(e) => setFilters(prev => ({ ...prev, ou: e.target.value }))}
                  className={`w-full border rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors ${
                    navigationState?.filterOU && filters.ou !== 'all' 
                      ? 'border-blue-300 bg-blue-50' 
                      : 'border-gray-300'
                  }`}
                >
                  <option value="all">Todas as OUs</option>
                  {uniqueOUList.map(ou => (
                    <option key={ou.code} value={ou.code}>
                      {ou.name} ({ou.count})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Último login</label>
                <select
                  value={advancedFilters.lastLoginDays}
                  onChange={(e) => setAdvancedFilters(prev => ({ ...prev, lastLoginDays: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                >
                  <option value="all">Qualquer data</option>
                  <option value="7">Últimos 7 dias</option>
                  <option value="30">Até 30 dias</option>
                  <option value="60">Até 60 dias</option>
                  <option value="90">Até 90 dias</option>
                  <option value="120+">120+ dias (possível remoção)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Inventário</label>
                <select
                  value={advancedFilters.inventory}
                  onChange={(e) => setAdvancedFilters(prev => ({ ...prev, inventory: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                >
                  <option value="all">Todos</option>
                  <option value="in_use">Em uso</option>
                  <option value="spare">Spare</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Atribuído a (usuário atual)</label>
                <input
                  type="text"
                  value={advancedFilters.assignedTo}
                  onChange={(e) => setAdvancedFilters(prev => ({ ...prev, assignedTo: e.target.value }))}
                  placeholder="Nome ou email"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Usuário anterior</label>
                <input
                  type="text"
                  value={advancedFilters.prevUser}
                  onChange={(e) => setAdvancedFilters(prev => ({ ...prev, prevUser: e.target.value }))}
                  placeholder="Nome ou email"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sistema Operacional
                  {navigationState?.filterOS && (
                    <span className="ml-2 text-xs text-blue-600">(filtro do dashboard)</span>
                  )}
                </label>
                <select
                  value={filters.os}
                  onChange={(e) => setFilters(prev => ({ ...prev, os: e.target.value }))}
                  className={`w-full border rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors ${
                    navigationState?.filterOS && filters.os !== 'all' 
                      ? 'border-blue-300 bg-blue-50' 
                      : 'border-gray-300'
                  }`}
                >
                  <option value="all">Todos os SOs</option>
                  {uniqueOSList.map(os => (
                    <option key={os} value={os}>{os}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Último Login
                  {navigationState?.filterLastLogin && (
                    <span className="ml-2 text-xs text-blue-600">(filtro do dashboard)</span>
                  )}
                </label>
                <select
                  value={filters.lastLogin}
                  onChange={(e) => setFilters(prev => ({ ...prev, lastLogin: e.target.value }))}
                  className={`w-full border rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors ${
                    navigationState?.filterLastLogin && filters.lastLogin !== 'all' 
                      ? 'border-blue-300 bg-blue-50' 
                      : 'border-gray-300'
                  }`}
                >
                  <option value="all">Todos</option>
                  <option value="recent">Recente (7 dias) ({stats.recent})</option>
                  <option value="moderate">Moderado (8-30 dias)</option>
                  <option value="old">Antigo (31-90 dias) ({stats.old})</option>
                  {/* Possível Remoção agora disponível somente nos Filtros Avançados */}
                  <option value="never">Nunca ({stats.never})</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Garantia Dell
                  {navigationState?.filterWarranty && (
                    <span className="ml-2 text-xs text-blue-600">(filtro do dashboard)</span>
                  )}
                </label>
                <select
                  value={filters.warranty}
                  onChange={(e) => setFilters(prev => ({ ...prev, warranty: e.target.value }))}
                  className={`w-full border rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors ${
                    navigationState?.filterWarranty && filters.warranty !== 'all' 
                      ? 'border-blue-300 bg-blue-50' 
                      : 'border-gray-300'
                  }`}
                >
                  <option value="all">Todas</option>
                  <option value="active">Ativa ({stats.warrantyActive})</option>
                  <option value="expiring_30">Expirando 30 dias ({stats.warrantyExpiring30})</option>
                  <option value="expiring_60">Expirando 60 dias ({stats.warrantyExpiring60})</option>
                  <option value="expired">Expirada ({stats.warrantyExpired})</option>
                  <option value="unknown">Desconhecida ({stats.warrantyUnknown})</option>
                </select>
              </div>
            </div>

            <div className="flex justify-between items-center pt-2 border-t border-gray-200">
              <button
                onClick={resetFilters}
                className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
              >
                Limpar Filtros
              </button>
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                {isSearching && (
                  <span className="flex items-center text-blue-600">
                    <Loader2 className="h-3 w-3 animate-spin mr-1" />
                    Pesquisando...
                  </span>
                )}
                <span>
                  Mostrando {filteredComputers.length} de {computers.length} máquinas
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Estatísticas por OU */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
          <Building2 className="h-5 w-5 mr-2" />
          Distribuição por Unidade Organizacional
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
          {Object.values(stats.byOU).map(ou => (
            <div 
              key={ou.code} 
              className={`p-3 rounded-lg border-2 transition-all hover:shadow-md cursor-pointer ${
                filters.ou === ou.code 
                  ? 'border-blue-300 bg-blue-50' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
              onClick={() => setFilters(prev => ({ 
                ...prev, 
                ou: filters.ou === ou.code ? 'all' : ou.code 
              }))}
            >
              <div className={`text-xs font-medium mb-1 ${ou.color}`}>
                {ou.name}
              </div>
              <div className="text-lg font-bold text-gray-900">
                {ou.total}
              </div>
              <div className="text-xs text-gray-500">
                {ou.enabled} ativas • {ou.disabled} inativas
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Estatísticas Gerais */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
        <div className="bg-white p-4 rounded-lg shadow text-center transition-all hover:shadow-md">
          <div className="text-2xl font-bold text-blue-600">{computers.length}</div>
          <div className="text-sm text-gray-600">Total</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow text-center transition-all hover:shadow-md">
          <div className="text-2xl font-bold text-green-600">{stats.enabled}</div>
          <div className="text-sm text-gray-600">Ativadas</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow text-center transition-all hover:shadow-md">
          <div className="text-2xl font-bold text-red-600">{stats.disabled}</div>
          <div className="text-sm text-gray-600">Desativadas</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow text-center transition-all hover:shadow-md">
          <div className="text-2xl font-bold text-green-600">{stats.recent}</div>
          <div className="text-sm text-gray-600">Ativas (7 dias)</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow text-center transition-all hover:shadow-md">
          <div className="text-2xl font-bold text-gray-600">{stats.old}</div>
          <div className="text-sm text-gray-600">Inativas (30+ dias)</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow text-center transition-all hover:shadow-md">
          <div className="text-2xl font-bold text-green-600">{stats.warrantyActive}</div>
          <div className="text-sm text-gray-600">Garantia Ativa</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow text-center transition-all hover:shadow-md">
          <div className="text-2xl font-bold text-red-600">{stats.warrantyExpired}</div>
          <div className="text-sm text-gray-600">Garantia Expirada</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow text-center transition-all hover:shadow-md">
          <div className="text-2xl font-bold text-orange-600">{filteredComputers.length}</div>
          <div className="text-sm text-gray-600">Filtrados</div>
        </div>
      </div>

      {/* Layout: vertical tabs + table */}
      <div className="flex space-x-4">
        {/* Vertical Tabs */}
        <aside className="w-44 bg-white rounded-lg shadow p-2">
          <nav className="flex flex-col space-y-2">
            <button
              className={`text-left px-3 py-2 rounded ${sideTab === 'all' ? 'bg-blue-50 border-l-4 border-blue-600' : 'hover:bg-gray-50'}`}
              onClick={() => { 
                setSideTab('all'); 
                setAdvancedFilters(prev => ({ ...prev, inventory: 'all' }));
                fetchComputers(false, null); // Buscar todas as máquinas
              }}
            >
              <div className="text-sm font-medium">Todas</div>
              <div className="text-xs text-gray-500">Lista completa</div>
            </button>

            <button
              className={`text-left px-3 py-2 rounded ${sideTab === 'inventory' ? 'bg-blue-50 border-l-4 border-blue-600' : 'hover:bg-gray-50'}`}
              onClick={() => { 
                setSideTab('inventory'); 
                setAdvancedFilters(prev => ({ ...prev, inventory: 'spare' }));
                fetchComputers(false, 'spare'); // Buscar apenas máquinas Spare
              }}
            >
              <div className="text-sm font-medium">Inventário</div>
              <div className="text-xs text-gray-500">Apenas Máquinas Spare</div>
            </button>
          </nav>
        </aside>

        <div className="flex-1 bg-white shadow-lg rounded-lg overflow-hidden relative">
          {/* Loading overlay durante pesquisa */}
          {isSearching && (
            <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-20">
              <div className="flex items-center space-x-2 text-blue-600">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span className="text-sm font-medium">Filtrando resultados...</span>
              </div>
            </div>
          )}

          <div className="overflow-x-auto max-h-[70vh] relative" style={{ scrollbarWidth: 'thin' }}>
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50 sticky top-0 z-10">
                <tr>
                  <SortableHeader sortKey="status" className="w-20">Status</SortableHeader>
                  <SortableHeader sortKey="name" className="min-w-48">Máquina</SortableHeader>
                  <SortableHeader sortKey="ou" className="w-32">OU</SortableHeader>
                  <SortableHeader sortKey="os" className="w-40">Sistema Op.</SortableHeader>
                  <SortableHeader sortKey="warranty" className="w-36">Garantia Dell</SortableHeader>
                  <SortableHeader sortKey="lastLogin" className="w-32">Último Login</SortableHeader>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32 sticky right-32 bg-gray-50">Ações</th>
                  <SortableHeader sortKey="created" className="w-32 sticky right-0 bg-gray-50">Criado em</SortableHeader>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredComputers.map((computer) => {
                  const WarrantyIcon = computer.warrantyStatus.icon
                  return (
                    <tr 
                      key={computer.name} 
                      className="hover:bg-blue-50 transition-colors cursor-pointer group"
                      onClick={() => window.location.href = `/computers/${computer.name}`}
                      title={`Clique para ver detalhes de ${computer.name}`}
                    >
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex items-center">
                          {computer.isEnabled ? (
                            <div className="flex items-center text-green-600">
                              <CheckCircle className="h-4 w-4 mr-1" />
                              <span className="text-xs font-medium">Ativa</span>
                            </div>
                          ) : (
                            <div className="flex items-center text-red-600">
                              <XCircle className="h-4 w-4 mr-1" />
                              <span className="text-xs font-medium">Inativa</span>
                            </div>
                          )}
                        </div>
                      </td>

                      <td className="px-4 py-3">
                        <div className="flex items-center">
                          {computer.ou.code === 'CLOUD' || (computer.os && computer.os.toLowerCase().includes('server')) ? (
                            <Server className="h-4 w-4 text-gray-400 mr-2 flex-shrink-0" />
                          ) : (
                            <Monitor className="h-4 w-4 text-gray-400 mr-2 flex-shrink-0" />
                          )}
                          <div className="min-w-0">
                            <div className="text-sm font-medium text-gray-900 truncate">{computer.name}</div>
                            {computer.description && (<div className="text-xs text-gray-500 truncate">{computer.description}</div>)}
                            {computer.dnsHostName && computer.dnsHostName !== computer.name && (<div className="text-xs text-blue-600 truncate">DNS: {computer.dnsHostName}</div>)}
                          </div>
                        </div>
                      </td>

                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${computer.ou.bgColor} ${computer.ou.color} ${
                          navigationState?.filterOU && computer.ou.code === filters.ou ? 'ring-2 ring-blue-300' : ''
                        }`}>
                          <Building2 className="h-3 w-3 mr-1 flex-shrink-0" />
                          <span className="truncate">{computer.ou.name}</span>
                        </div>
                        <div className="text-xs text-gray-500 mt-1 truncate">{computer.ou.code}</div>
                      </td>

                      <td className="px-4 py-3">
                        <div className={`text-sm ${navigationState?.filterOS && computer.os === filters.os ? 'text-blue-700 font-medium bg-blue-50 px-2 py-1 rounded' : 'text-gray-900'} truncate`}>{computer.os}</div>
                        {computer.osVersion && computer.osVersion !== 'N/A' && (<div className="text-xs text-gray-500 truncate">{computer.osVersion}</div>)}
                      </td>

                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${computer.warrantyStatus.bgColor} ${computer.warrantyStatus.color} ${navigationState?.filterWarranty && computer.warrantyStatus.status === filters.warranty ? 'ring-2 ring-blue-300' : ''}`}>
                          <WarrantyIcon className="h-3 w-3 mr-1 flex-shrink-0" />
                          <span className="truncate">{computer.warrantyStatus.text}</span>
                        </div>
                        {computer.warranty && computer.warranty.warranty_end_date && (<div className="text-xs text-gray-500 mt-1 truncate">Expira: {formatDate(computer.warranty.warranty_end_date)}</div>)}
                      </td>

                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${computer.loginStatus.bgColor} ${computer.loginStatus.color} ${navigationState?.filterLastLogin && computer.loginStatus.status === filters.lastLogin ? 'ring-2 ring-blue-300' : ''}`}>
                          <span className="truncate">{computer.loginStatus.text}</span>
                        </div>
                        {computer.lastLogon && (<div className="text-xs text-gray-500 mt-1 truncate">{formatDate(computer.lastLogon)}</div>)}
                      </td>

                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium sticky right-32 bg-white group-hover:bg-blue-50">
                        <div className="flex items-center space-x-2">
                          <Link to={`/computers/${computer.name}`} className="inline-flex items-center text-blue-600 hover:text-blue-900 transition-colors text-xs" onClick={(e) => e.stopPropagation()}>
                            <Eye className="h-3 w-3 mr-1" /> Ver
                          </Link>
                          <button onClick={(e) => { e.stopPropagation(); setConfirmDialog({ open: true, computer, action: computer.isEnabled ? 'disable' : 'enable' }) }} disabled={toggleStatusLoading.has(computer.name)} className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium transition-colors ${computer.isEnabled ? 'bg-red-600 text-white hover:bg-red-700' : 'bg-green-600 text-white hover:bg-green-700'}`}>
                            {toggleStatusLoading.has(computer.name) ? (<Loader2 className="h-3 w-3 mr-1 animate-spin" />) : (<Power className="h-3 w-3 mr-1" />)}
                            <span>{computer.isEnabled ? 'Desativar' : 'Ativar'}</span>
                          </button>
                        </div>
                      </td>

                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 sticky right-0 bg-white group-hover:bg-blue-50">
                        <div className="flex items-center">
                          <Calendar className="h-3 w-3 mr-1 flex-shrink-0" />
                          <span className="truncate">{formatDate(computer.created)}</span>
                        </div>
                        {statusMessages.get(computer.name) && (<div className="mt-1 text-xs"><span className={`${statusMessages.get(computer.name).type === 'success' ? 'text-green-600' : 'text-red-600'}`}>{statusMessages.get(computer.name).text}</span></div>)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {filteredComputers.length === 0 && !loading && !isSearching && (
            <div className="text-center py-12">
              <Monitor className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhuma máquina encontrada</h3>
              <p className="mt-1 text-sm text-gray-500">{searchTerm || debouncedSearchTerm || Object.values(filters).some(f => f !== 'all') ? 'Tente ajustar os filtros de pesquisa.' : 'Não há máquinas registradas no Active Directory.'}</p>
              {(searchTerm || debouncedSearchTerm || Object.values(filters).some(f => f !== 'all')) && (
                <button onClick={resetFilters} className="mt-2 text-blue-600 hover:text-blue-500 text-sm transition-colors">Limpar todos os filtros</button>
              )}
            </div>
          )}

          {/* Footer da tabela com informações de ordenação */}
          {filteredComputers.length > 0 && (
            <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
              <div className="flex items-center justify-between text-sm text-gray-600">
                <div className="flex items-center space-x-4">
                  <span>{filteredComputers.length} máquina{filteredComputers.length !== 1 ? 's' : ''} exibida{filteredComputers.length !== 1 ? 's' : ''}</span>
                  {filteredComputers.length !== computers.length && (
                    <span className="text-orange-600">({computers.length - filteredComputers.length} filtrada{computers.length - filteredComputers.length !== 1 ? 's' : ''})</span>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <ArrowUpDown className="h-4 w-4" />
                  <span>Clique nos cabeçalhos para ordenar</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Computers