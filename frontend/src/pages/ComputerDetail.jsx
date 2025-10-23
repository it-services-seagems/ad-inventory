import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Monitor, Calendar, Shield, RefreshCw, AlertTriangle, ShieldOff, ShieldAlert, Network, Server, Search, MapPin, CheckCircle } from 'lucide-react'
import api from '../services/api'


const ComputerDetail = () => {
  const { computerName } = useParams()
  const navigate = useNavigate()
  const [computer, setComputer] = useState(null)
  const [warranty, setWarranty] = useState(null)
  const [dhcpInfo, setDhcpInfo] = useState(null)
  const [lastUserInfo, setLastUserInfo] = useState(null)  // NOVO ESTADO
  const [currentUserLive, setCurrentUserLive] = useState(null) // usuário atual obtido via PowerShell
  const [currentUserLiveLoading, setCurrentUserLiveLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [warrantyLoading, setWarrantyLoading] = useState(false)
  const [dhcpLoading, setDhcpLoading] = useState(false)
  const [lastUserLoading, setLastUserLoading] = useState(false)  // NOVO ESTADO
  
  // Estados para atribuição de usuário
  const [showUserAssignModal, setShowUserAssignModal] = useState(false)
  const [availableUsers, setAvailableUsers] = useState([])
  const [selectedUser, setSelectedUser] = useState(null)
  const [userSearchTerm, setUserSearchTerm] = useState('')
  const [assignmentLoading, setAssignmentLoading] = useState(false)

  useEffect(() => {
    fetchComputerData()
  }, [computerName])

  const fetchComputerData = async () => {
    try {
      setLoading(true)
      // Prefer the detailed endpoint which includes os and osVersion
      let computerData = null
      try {
        const resp = await api.get(`/computers/details/${encodeURIComponent(computerName)}`)
        computerData = resp.data
        console.log('✅ Carregou detalhes completos da máquina via /computers/details')
      } catch (err) {
        console.warn('⚠️ Endpoint de detalhes não disponível, caindo para /computers list:', err?.response?.status)
        const listResp = await api.get('/computers')
        computerData = listResp.data.find(c => c.name === computerName)
      }

      setComputer(computerData)
      
      if (computerData) {
        // Normalize common AD/DB column name differences so the UI gets `os` and `osVersion`
        try {
          const normalized = { ...computerData }
          // OS fallbacks
          if (!normalized.os) {
            normalized.os = normalized.operating_system || normalized.operatingSystem || (normalized.operating_system_id ? `OS id: ${normalized.operating_system_id}` : null) || 'N/A'
          }
          if (!normalized.osVersion) {
            normalized.osVersion = normalized.operating_system_version || normalized.operatingSystemVersion || normalized.osVersion || 'N/A'
          }

          // MAC fallback: populate `mac` if backend uses other names
          if (!normalized.mac) {
            normalized.mac = normalized.mac_address || normalized.macAddress || normalized.physical_mac || null
          }

          // Apply the normalized object to state so rest of UI can use consistent keys
          setComputer(normalized)
        } catch (e) {
          console.warn('Failed to normalize computer data:', e)
          setComputer(computerData)
        }
        // Não buscar garantia automaticamente - usar cache do SQL por padrão
        fetchDHCPInfo()
        fetchLastUserInfo()
        fetchCurrentUser()
        try {
          fetchWarrantyInfo(false)
        } catch (err) {
          console.warn('Erro ao iniciar fetchWarrantyInfo automático:', err)
        }
      }
    } catch (error) {
      console.error('Erro ao carregar dados da máquina:', error)
    } finally {
      setLoading(false)
    }
  }

  // NOVA FUNÇÃO
  const fetchLastUserInfo = async () => {
    try {
      setLastUserLoading(true)
      console.log(`🔍 Buscando último usuário para: ${computerName}`)
      
      // Primeiro tentar pela service tag se conseguirmos extrair
      const serviceTag = extractServiceTagFromComputerName(computerName)
      
      let response
      if (serviceTag && serviceTag !== computerName) {
        console.log(`📋 Tentando buscar por service tag: ${serviceTag}`)
        try {
          response = await api.get(`/service-tag/${serviceTag}/last-user?days=30`)
          console.log('✅ Resposta por service tag:', response.data)
        } catch (serviceTagError) {
          console.log('❌ Erro na busca por service tag, tentando por nome da máquina:', serviceTagError)
          response = await api.get(`/computers/${computerName}/last-user?days=30`)
          console.log('✅ Resposta por nome da máquina:', response.data)
        }
      } else {
        console.log(`💻 Buscando diretamente por nome da máquina: ${computerName}`)
        response = await api.get(`/computers/${computerName}/last-user?days=30`)
        console.log('✅ Resposta por nome da máquina:', response.data)
      }
      
      setLastUserInfo(response.data)
      console.log('✅ Dados do último usuário definidos:', response.data)
    } catch (error) {
      console.error('❌ Erro ao carregar informações do último usuário:', error)
      setLastUserInfo({ 
        success: false,
        error: error.response?.data?.error || error.message,
        computer_name: computerName,
        search_method: 'api_error'
      })
    } finally {
      setLastUserLoading(false)
      console.log('🏁 Busca do último usuário finalizada')
    }
  }

  // NOVA FUNÇÃO: busca o usuário atualmente logado na máquina via endpoint criado
  const fetchCurrentUser = async (force = false) => {
    try {
      setCurrentUserLiveLoading(true)
      console.log(`🔍 Buscando usuário atual da máquina: ${computerName}`)

      const resp = await api.get(`/computers/${encodeURIComponent(computerName)}/current-user${force ? '?force=true' : ''}`)

      // A API retorna diferentes formatos dependendo do resultado
      // Ex.: { status: 'ok', usuario_atual: 'DOMAIN\\user', serial_number: 'XYZ', saved: true }
      // ou { status: 'unreachable', message: 'Could not connect' }
      // ou { status: 'skipped', message: 'Machine is server or domain controller - skipped' }

      if (resp.status === 200 && resp.data) {
        const d = resp.data
        console.log('📊 Resposta da API current-user:', d)
        // Store the full response object so display logic can handle all statuses properly
        setCurrentUserLive(d)
      } else {
        setCurrentUserLive({ status: 'error', message: 'Erro na comunicação com a API' })
      }
    } catch (error) {
      console.error('Erro ao buscar usuário atual:', error)
      // Se servidor responder com 412 (skipped), axios rejeita. Tratamos aqui.
      if (error.response && error.response.status === 412) {
        setCurrentUserLive({ status: 'skipped', message: 'Servidor/DC (não aplicável)' })
      } else if (error.response && (error.response.status === 503 || error.response.status === 504)) {
        setCurrentUserLive({ status: 'unreachable', message: 'Serviço indisponível' })
      } else {
        setCurrentUserLive({ status: 'error', message: 'Erro de conexão' })
      }
    } finally {
      setCurrentUserLiveLoading(false)
    }
  }

  // NOVA FUNÇÃO AUXILIAR
  const extractServiceTagFromComputerName = (computerName) => {
    // Tentar extrair service tag do nome da máquina
    const name = computerName.toUpperCase()
    
    // Prefixos conhecidos
    const prefixes = ['SHQ', 'ESM', 'DIA', 'TOP', 'RUB', 'JAD', 'ONI', 'CLO']
    
    for (const prefix of prefixes) {
      if (name.startsWith(prefix)) {
        const possibleServiceTag = name.substring(prefix.length)
        // Se sobrou algo que parece service tag (letras e números)
        if (possibleServiceTag && possibleServiceTag.length >= 5) {
          return possibleServiceTag
        }
      }
    }
    
    return computerName // Retorna o nome original se não conseguir extrair
  }

  const fetchWarrantyInfo = async (force = false) => {
    // Mantemos a função para consulta manual via botões na UI
    try {
      setWarrantyLoading(true)
  const url = `/computers/${computerName}/warranty${force ? '?force=true' : ''}`
  const response = await api.get(url)
      // Normalizar vários formatos que o backend pode retornar
      const raw = response.data || {}

      // Alguns endpoints retornam { status: 'success', warranty_data: {...} }
      const candidate = raw.warranty_data || raw.warranty || raw

      // Função utilitária para mapear snake_case -> camelCase esperados pela UI
      const normalize = (r) => {
        if (!r) return null
        return {
          serviceTag: r.service_tag || r.serviceTag || r.serviceTagClean || r.serviceTag_clean || null,
          productLineDescription: r.product_line_description || r.productLineDescription || r.product_description || r.productDescription || '',
          systemDescription: r.system_description || r.systemDescription || '',
          warrantyStartDate: r.warranty_start_date || r.warrantyStartDate || r.warrantyStart || null,
          warrantyEndDate: r.warranty_end_date || r.warrantyEndDate || r.warrantyEnd || r.expiration_date_formatted || null,
          warrantyStatus: r.warranty_status || r.warrantyStatus || r.status || null,
          entitlements: r.entitlements || r.entitlements_list || r.entitlementsList || [],
          lastUpdated: r.last_updated || r.lastUpdated || null,
          cacheExpiresAt: r.cache_expires_at || r.cacheExpiresAt || null,
          dataSource: r.data_source || r.dataSource || 'api'
        }
      }

      const normalized = normalize(candidate)
      if (normalized) {
        // garantir que entitlements seja sempre array
        let ent = normalized.entitlements
        try {
          if (typeof ent === 'string') {
            ent = JSON.parse(ent)
          }
        } catch (e) {
          // se parse falhar, fallback para array vazio
          ent = []
        }
        normalized.entitlements = Array.isArray(ent) ? ent : []
        setWarranty(normalized)
      } else {
        setWarranty({ error: 'Informações de garantia não encontradas' })
      }
    } catch (error) {
      console.error('Erro ao carregar informações de garantia:', error)
      setWarranty({ error: 'Informações de garantia não encontradas' })
    } finally {
      setWarrantyLoading(false)
    }
  }

  const fetchDHCPInfo = async () => {
    try {
      setDhcpLoading(true)
      console.log(`🔍 Buscando informações DHCP para: ${computerName}`)

      // Extrair prefixo do nome da máquina para identificar o navio
      const shipPrefix = getShipFromComputerName(computerName)
      console.log(`🚢 Prefixo identificado: ${shipPrefix}`)
      
      if (shipPrefix) {
        console.log(`✅ Navio identificado: ${shipPrefix}`)
        
        // Primeira tentativa: buscar nos filtros DHCP do navio correspondente
        try {
          console.log(`📡 Tentativa 1: Buscando em /api/dhcp/filters/${shipPrefix}`)
          const response = await api.get(`/dhcp/filters/${shipPrefix}?service_tag=${computerName}&include_filters=false`)
          console.log('✅ Resposta DHCP por navio:', response.data)
          
          // Verificar se a resposta tem dados válidos
          if (response.data && response.data.dhcp_server) {
            setDhcpInfo(response.data)
            console.log('✅ Dados DHCP definidos com sucesso')
            return
          } else {
            console.log('⚠️ Resposta DHCP inválida, tentando busca geral')
            throw new Error('Resposta DHCP inválida')
          }
        } catch (error) {
          console.log('❌ Erro na busca por navio:', error.response?.status, error.response?.data || error.message)
          // Continue para a segunda tentativa independente do tipo de erro (404, 500, etc.)
          
          // Segunda tentativa: busca geral em todos os servidores
          try {
            console.log(`📡 Tentativa 2: Busca geral via /api/dhcp/search`)
            const searchResponse = await api.post('/dhcp/search', {
              service_tag: computerName,
              ships: [shipPrefix] // Limitar busca ao navio identificado
            })
            console.log('✅ Resposta da busca DHCP geral:', searchResponse.data)
            
            // Processar resposta da busca
            const searchData = searchResponse.data
            
            // A API retorna { results: [...] }
            if (searchData && searchData.results && Array.isArray(searchData.results) && searchData.results.length > 0) {
              // Encontrar o primeiro resultado que tenha dados
              const validResult = searchData.results.find(result => 
                result && result.status === 'encontrado' && result.macs && result.macs.length > 0
              )
              
              if (validResult) {
                // Converter para o formato esperado pelo frontend
                const convertedData = {
                  ship_name: shipPrefix,
                  dhcp_server: validResult.servidor || 'N/A',
                  service_tag: computerName,
                  service_tag_found: true,
                  search_results: validResult.macs.map(mac => ({
                    filter_type: mac.filter_type || 'Allow',
                    mac_address: mac.mac || mac.mac_address,
                    match_field: mac.match_field || 'description',
                    description: mac.description,
                    name: mac.name || computerName
                  })),
                  filters: {
                    total: validResult.macs.length,
                    allow_count: validResult.macs.filter(m => m.filter_type === 'Allow').length,
                    deny_count: validResult.macs.filter(m => m.filter_type === 'Deny').length
                  },
                  timestamp: new Date().toISOString(),
                  source: 'search'
                }
                
                setDhcpInfo(convertedData)
                console.log('✅ Dados DHCP convertidos e definidos:', convertedData)
                return
              }
            }
            
            // Se chegou aqui, não encontrou resultados válidos
            console.log('⚠️ Máquina não encontrada na busca geral')
            setDhcpInfo({
              ship_name: shipPrefix,
              dhcp_server: 'N/A',
              service_tag: computerName,
              service_tag_found: false,
              search_results: [],
              error: 'Máquina não encontrada nos filtros DHCP',
              source: 'search_not_found'
            })
            return
          } catch (searchError) {
            console.error('❌ Erro na busca DHCP geral:', searchError.response?.status, searchError.response?.data || searchError.message)
            setDhcpInfo({
              ship_name: shipPrefix,
              error: `Erro ao consultar filtros DHCP: ${searchError.response?.data?.error || searchError.message}`,
              debug_info: {
                ship_prefix: shipPrefix,
                computer_name: computerName,
                error_details: searchError.response?.data
              }
            })
            return
          }
        }
      } else {
        console.log('❌ Não foi possível identificar o navio pelo nome da máquina')
        
        // Terceira tentativa: busca em todos os navios se não conseguir identificar
        try {
          console.log(`📡 Tentativa 3: Busca em todos os navios`)
          const searchResponse = await api.post('/dhcp/search', {
            service_tag: computerName
            // Sem especificar ships = busca em todos
          })
          console.log('✅ Resposta da busca DHCP em todos os navios:', searchResponse.data)
          
          const searchData = searchResponse.data
          if (searchData && searchData.results && Array.isArray(searchData.results) && searchData.results.length > 0) {
            const validResult = searchData.results.find(result => 
              result && result.status === 'encontrado' && result.macs && result.macs.length > 0
            )
            
            if (validResult) {
              const convertedData = {
                ship_name: validResult.servidor || 'N/A',
                dhcp_server: validResult.servidor || 'N/A',
                service_tag: computerName,
                service_tag_found: true,
                search_results: validResult.macs.map(mac => ({
                  filter_type: mac.filter_type || 'Allow',
                  mac_address: mac.mac || mac.mac_address,
                  match_field: mac.match_field || 'description',
                  description: mac.description,
                  name: mac.name || computerName
                })),
                filters: {
                  total: validResult.macs.length,
                  allow_count: validResult.macs.filter(m => m.filter_type === 'Allow').length,
                  deny_count: validResult.macs.filter(m => m.filter_type === 'Deny').length
                },
                timestamp: new Date().toISOString(),
                source: 'search_all'
              }
              setDhcpInfo(convertedData)
              console.log('✅ Dados DHCP encontrados em busca geral:', convertedData)
              return
            }
          }
          
          setDhcpInfo({
            error: 'Não foi possível identificar o navio e máquina não encontrada nos filtros DHCP',
            debug_info: {
              computer_name: computerName,
              identified_ship: null,
              search_attempted: true
            }
          })
          return
        } catch (allSearchError) {
          console.error('❌ Erro na busca geral em todos os navios:', allSearchError)
          setDhcpInfo({
            error: `Erro ao consultar filtros DHCP: ${allSearchError.response?.data?.error || allSearchError.message}`,
            debug_info: {
              computer_name: computerName,
              identified_ship: null,
              error_details: allSearchError.response?.data
            }
          })
          return
        }
      }
    } catch (error) {
      console.error('❌ Erro geral ao carregar informações DHCP:', error)
      setDhcpInfo({ 
        error: `Erro geral ao consultar informações DHCP: ${error.message}`,
        debug_info: {
          computer_name: computerName,
          error_type: 'general_error',
          error_details: error.response?.data
        }
      })
    } finally {
      setDhcpLoading(false)
      console.log('🏁 Busca DHCP finalizada')
    }
  }

  const getShipFromComputerName = (computerName) => {
    const name = computerName.toUpperCase()
    
    // Mapeamento de prefixos para navios
    const shipMapping = {
      'DIA': 'DIAMANTE',
      'ESM': 'ESMERALDA', 
      'JAD': 'JADE',
      'RUB': 'RUBI',
      'ONI': 'ONIX',
      'TOP': 'TOPAZIO',
      'SHQ': 'SHQ',
      'CLO': 'SHQ' // Centro Logístico usa mesmo servidor da sede
    }
    
    for (const [prefix, ship] of Object.entries(shipMapping)) {
      if (name.startsWith(prefix)) {
        return ship
      }
    }
    
    return null
  }

  // Funções para atribuição de usuário
  const fetchAvailableUsers = async () => {
    try {
      // Simulated API call - implementar endpoint real posteriormente
      const mockUsers = [
        { id: 1, name: 'João Silva', email: 'joao.silva@empresa.com', position: 'Analista', base: 'SHQ' },
        { id: 2, name: 'Maria Santos', email: 'maria.santos@empresa.com', position: 'Coordenadora', base: 'DIAMANTE' },
        { id: 3, name: 'Pedro Costa', email: 'pedro.costa@empresa.com', position: 'Técnico', base: 'ESMERALDA' }
      ]
      setAvailableUsers(mockUsers)
    } catch (error) {
      console.error('Erro ao buscar usuários:', error)
      setAvailableUsers([])
    }
  }

  const handleAssignUser = async () => {
    if (!selectedUser) return

    try {
      setAssignmentLoading(true)
      
      // Simulated API call for user assignment
      console.log('Atribuindo usuário:', selectedUser, 'à máquina:', computerName)
      
      // TODO: Implementar chamada real da API
      // await api.post(`/computers/${computerName}/assign-user`, {
      //   user_id: selectedUser.id,
      //   user_email: selectedUser.email
      // })

      // Simulated email sending for term of receipt
      console.log('Enviando email com termo de recebimento para:', selectedUser.email)
      
      // Update computer data locally
      setComputer(prev => ({
        ...prev,
        currentUser: selectedUser.name,
        currentUserEmail: selectedUser.email
      }))

      // Close modal and show success message
      setShowUserAssignModal(false)
      setSelectedUser(null)
      
      alert(`Usuário ${selectedUser.name} atribuído com sucesso! Email com termo de recebimento será enviado para ${selectedUser.email}`)
      
    } catch (error) {
      console.error('Erro ao atribuir usuário:', error)
      alert('Erro ao atribuir usuário. Tente novamente.')
    } finally {
      setAssignmentLoading(false)
    }
  }

  const handleUnassignUser = async () => {
    try {
      setAssignmentLoading(true)
      
      // TODO: Implementar chamada real da API
      // await api.post(`/computers/${computerName}/unassign-user`)

      // Update computer data locally
      setComputer(prev => ({
        ...prev,
        currentUser: null,
        currentUserEmail: null,
        previousUser: prev.currentUser
      }))

      alert('Usuário desvinculado com sucesso!')
      
    } catch (error) {
      console.error('Erro ao desvincular usuário:', error)
      alert('Erro ao desvincular usuário. Tente novamente.')
    } finally {
      setAssignmentLoading(false)
    }
  }

  const openUserAssignModal = () => {
    fetchAvailableUsers()
    setShowUserAssignModal(true)
  }

  const formatDate = (dateString) => {
    if (!dateString || dateString === 'N/A') return 'N/A'
    
    try {
      // Se é uma data no formato dd/mm/yyyy (formato brasileiro)
      if (typeof dateString === 'string' && dateString.match(/^\d{2}\/\d{2}\/\d{4}$/)) {
        const [day, month, year] = dateString.split('/')
        const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day))
        
        // Verificar se a data é válida
        if (isNaN(date.getTime())) {
          return dateString // Retorna a string original se não conseguir converter
        }
        
        return date.toLocaleDateString('pt-BR', {
          year: 'numeric',
          month: 'long',
          day: 'numeric'
        })
      }
      
      // Se é uma data ISO (yyyy-mm-ddThh:mm:ss.sssZ)
      if (typeof dateString === 'string' && (dateString.includes('T') || dateString.includes('-'))) {
        const date = new Date(dateString)
        
        // Verificar se a data é válida
        if (isNaN(date.getTime())) {
          return dateString // Retorna a string original se não conseguir converter
        }
        
        return date.toLocaleDateString('pt-BR', {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })
      }
      
      // Tentar converter diretamente
      const date = new Date(dateString)
      if (isNaN(date.getTime())) {
        return dateString // Retorna a string original se não conseguir converter
      }
      
      return date.toLocaleDateString('pt-BR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    } catch (error) {
      console.warn('Erro ao formatar data:', dateString, error)
      return dateString || 'N/A'
    }
  }

  const formatEntitlementDate = (dateString) => {
    if (!dateString) return 'N/A'
    
    try {
      // Datas dos entitlements vêm no formato ISO: "2024-10-15T04:59:59.402Z"
      const date = new Date(dateString)
      
      if (isNaN(date.getTime())) {
        return 'Data inválida'
      }
      
      return date.toLocaleDateString('pt-BR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      })
    } catch (error) {
      console.warn('Erro ao formatar data do entitlement:', dateString, error)
      return 'Erro na data'
    }
  }

  // NOVA FUNÇÃO
  const formatLogonTime = (timeString) => {
    if (!timeString) return 'N/A'
    
    try {
      const date = new Date(timeString)
      if (isNaN(date.getTime())) return 'Data inválida'
      
      return date.toLocaleString('pt-BR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    } catch (error) {
      console.warn('Erro ao formatar hora de logon:', timeString, error)
      return timeString || 'N/A'
    }
  }

  // Formata MAC para exibição (AA:BB:CC:DD:EE:FF)
  const formatMac = (mac) => {
    if (!mac) return 'N/A'
    try {
      const cleaned = String(mac).replace(/[^a-fA-F0-9]/g, '').toUpperCase()
      if (cleaned.length === 12) {
        return cleaned.match(/.{1,2}/g).join(':')
      }
      return mac
    } catch (e) {
      return mac
    }
  }

  const getLastLoginStatus = (lastLogon) => {
    if (!lastLogon) return { status: 'never', color: 'bg-gray-100 text-gray-800', text: 'Nunca logou' }
    
    const lastLogonDate = new Date(lastLogon)
    const now = new Date()
    const diffDays = Math.floor((now - lastLogonDate) / (1000 * 60 * 60 * 24))
    
    if (diffDays <= 7) {
      return { status: 'recent', color: 'bg-green-100 text-green-800', text: 'Ativo recentemente' }
    } else if (diffDays <= 30) {
      return { status: 'moderate', color: 'bg-yellow-100 text-yellow-800', text: 'Moderadamente ativo' }
    } else {
      return { status: 'old', color: 'bg-red-100 text-red-800', text: 'Inativo há muito tempo' }
    }
  }

  const getWarrantyStatus = (warranty) => {
    if (!warranty || warranty.error) {
      return { color: 'bg-gray-100 text-gray-800', text: 'Não disponível' }
    }
    
    if (warranty.warrantyStatus === 'Active') {
      return { color: 'bg-green-100 text-green-800', text: 'Ativa' }
    } else {
      return { color: 'bg-red-100 text-red-800', text: 'Expirada' }
    }
  }

  const getDHCPStatus = (dhcpInfo) => {
    if (!dhcpInfo || dhcpInfo.error) {
      return { color: 'bg-gray-100 text-gray-800', text: 'Não disponível', icon: AlertTriangle }
    }
    
    if (dhcpInfo.service_tag_found && dhcpInfo.search_results && dhcpInfo.search_results.length > 0) {
      const allowFilters = dhcpInfo.search_results.filter(r => r.filter_type === 'Allow')
      const denyFilters = dhcpInfo.search_results.filter(r => r.filter_type === 'Deny')
      
      if (allowFilters.length > 0) {
        return { color: 'bg-green-100 text-green-800', text: 'Permitido no DHCP', icon: Network }
      } else if (denyFilters.length > 0) {
        return { color: 'bg-red-100 text-red-800', text: 'Bloqueado no DHCP', icon: ShieldOff }
      }
    }
    
    return { color: 'bg-yellow-100 text-yellow-800', text: 'Não encontrado no DHCP', icon: Search }
  }

  // NOVA FUNÇÃO
  const getLastUserStatus = (lastUserInfo) => {
    if (!lastUserInfo || lastUserInfo.error) {
      return { color: 'bg-gray-100 text-gray-800', text: 'Não disponível', icon: AlertTriangle }
    }
    
    if (lastUserInfo.success && lastUserInfo.last_user) {
      // Verificar se o logon é recente (últimas 24 horas)
      if (lastUserInfo.last_logon_time) {
        const logonDate = new Date(lastUserInfo.last_logon_time)
        const now = new Date()
        const hoursDiff = (now - logonDate) / (1000 * 60 * 60)
        
        if (hoursDiff <= 24) {
          return { color: 'bg-green-100 text-green-800', text: 'Logon Recente', icon: Monitor }
        } else if (hoursDiff <= 168) { // 7 dias
          return { color: 'bg-yellow-100 text-yellow-800', text: 'Logon na Semana', icon: Calendar }
        } else {
          return { color: 'bg-orange-100 text-orange-800', text: 'Logon Antigo', icon: Calendar }
        }
      }
      return { color: 'bg-blue-100 text-blue-800', text: 'Usuário Identificado', icon: Monitor }
    }
    
    return { color: 'bg-red-100 text-red-800', text: 'Sem Logons', icon: ShieldOff }
  }

  const getWarrantyIcon = (warrantyStatus) => {
    if (warrantyLoading) {
      return <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
    }
    
    if (warrantyStatus.text === 'Ativa') {
      return <Shield className="h-8 w-8 text-green-600" />
    } else if (warrantyStatus.text === 'Expirada') {
      return <ShieldAlert className="h-8 w-8 text-red-600" />
    } else {
      // Ícone customizado para "Não disponível" - escudo partido
      return (
        <svg className="h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.618 5.984A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 2L12 22" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 8L16 16" />
        </svg>
      )
    }
  }

  const getDHCPIcon = (dhcpStatus) => {
    if (dhcpLoading) {
      return <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
    }
    
    const IconComponent = dhcpStatus.icon || Network
    
    if (dhcpStatus.text === 'Permitido no DHCP') {
      return <IconComponent className="h-8 w-8 text-green-600" />
    } else if (dhcpStatus.text === 'Bloqueado no DHCP') {
      return <IconComponent className="h-8 w-8 text-red-600" />
    } else if (dhcpStatus.text === 'Não encontrado no DHCP') {
      return <IconComponent className="h-8 w-8 text-yellow-600" />
    } else {
      return <IconComponent className="h-8 w-8 text-gray-400" />
    }
  }

  // NOVA FUNÇÃO
  const getLastUserIcon = (lastUserStatus) => {
    if (lastUserLoading) {
      return <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
    }
    
    const IconComponent = lastUserStatus.icon || Monitor
    
    if (lastUserStatus.text === 'Logon Recente') {
      return <IconComponent className="h-8 w-8 text-green-600" />
    } else if (lastUserStatus.text === 'Logon na Semana') {
      return <IconComponent className="h-8 w-8 text-yellow-600" />
    } else if (lastUserStatus.text === 'Logon Antigo') {
      return <IconComponent className="h-8 w-8 text-orange-600" />
    } else if (lastUserStatus.text === 'Usuário Identificado') {
      return <IconComponent className="h-8 w-8 text-blue-600" />
    } else if (lastUserStatus.text === 'Sem Logons') {
      return <IconComponent className="h-8 w-8 text-red-600" />
    } else {
      return <IconComponent className="h-8 w-8 text-gray-400" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Carregando dados da máquina...</span>
      </div>
    )
  }

  if (!computer) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Máquina não encontrada</h3>
        <p className="mt-1 text-sm text-gray-500">
          A máquina "{computerName}" não foi encontrada no Active Directory.
        </p>
        <button
          onClick={() => navigate('/computers')}
          className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
        >
          Voltar para lista
        </button>
      </div>
    )
  }

  const loginStatus = getLastLoginStatus(computer.lastLogon)
  const warrantyStatus = getWarrantyStatus(warranty)
  const dhcpStatus = getDHCPStatus(dhcpInfo)
  const lastUserStatus = getLastUserStatus(lastUserInfo)  // NOVA VARIÁVEL

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate('/computers')}
            className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="h-5 w-5 mr-1" />
            Voltar
          </button>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{computer.name}</h1>
            <p className="text-gray-600">Detalhes da máquina do Active Directory</p>
          </div>
        </div>
        
        <div className="flex items-center">
          <button
            onClick={fetchComputerData}
            className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            <span>Atualizar</span>
          </button>
        </div>
      </div>

      {/* Status Cards - ATUALIZADO COM NOVO CARD */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
          <div className="flex items-center">
            <Monitor className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Status da Máquina</p>
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${loginStatus.color}`}>
                {loginStatus.text}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
          <div className="flex items-center">
            {getWarrantyIcon(warrantyStatus)}
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Status da Garantia</p>
              {warrantyLoading ? (
                <RefreshCw className="h-4 w-4 animate-spin text-gray-400" />
              ) : (
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${warrantyStatus.color}`}>
                  {warrantyStatus.text}
                </span>
              )}
                  {/* Removed cache/force warranty buttons per UX request */}
              {warranty && !warranty.error && (
                <div className="mt-2 text-sm text-gray-700">
                  <div>Service Tag: {warranty.service_tag || warranty.serviceTag || 'N/A'}</div>
                  <div>Status: {warranty.warranty_status || warranty.warrantyStatus || 'N/A'}</div>
                  <div>Expira em: {warranty.warranty_end_date || warranty.warrantyEndDate || 'N/A'}</div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
          <div className="flex items-center">
            {getDHCPIcon(dhcpStatus)}
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Status DHCP</p>
              {dhcpLoading ? (
                <RefreshCw className="h-4 w-4 animate-spin text-gray-400" />
              ) : (
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${dhcpStatus.color}`}>
                  {dhcpStatus.text}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
          <div className="flex items-center">
            <Calendar className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Tempo no AD</p>
              <p className="text-sm text-gray-900">
                {computer.created ? 
                  Math.floor((new Date() - new Date(computer.created)) / (1000 * 60 * 60 * 24)) + ' dias' 
                  : 'N/A'
                }
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Informações Detalhadas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Informações do Sistema */}
        <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Informações do Sistema</h3>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm font-medium text-gray-500">Nome da Máquina</dt>
              <dd className="text-sm text-gray-900 font-medium">{computer.name}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Sistema Operacional</dt>
              <dd className="text-sm text-gray-900">{computer.os}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Endereço MAC</dt>
              <dd className="text-sm text-gray-900 font-mono">{formatMac(computer.mac)}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Versão do OS</dt>
              <dd className="text-sm text-gray-900">{computer.osVersion || 'N/A'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Status da Máquina</dt>
              <dd className="text-sm text-gray-900">
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  computer.disabled ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                }`}>
                  {computer.disabled ? 'Desativada' : 'Ativada'}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Descrição</dt>
              <dd className="text-sm text-gray-900">{computer.description || 'Sem descrição'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">DNS Hostname</dt>
              <dd className="text-sm text-gray-900">{computer.dnsHostName || 'N/A'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Distinguished Name</dt>
              <dd className="text-sm text-gray-900 break-all font-mono bg-gray-50 p-2 rounded">
                {computer.dn}
              </dd>
            </div>
            {/* Inventory & Assignment placeholders */}
            <div>
              <dt className="text-sm font-medium text-gray-500">Inventário</dt>
              <dd className="text-sm text-gray-900">{computer.inventoryStatus || 'N/A'}</dd>
            </div>

            <div>
              <dt className="text-sm font-medium text-gray-500">Usuário atual (atribuição)</dt>
              <dd className="text-sm text-gray-900 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="font-mono">
                    {currentUserLiveLoading ? (
                      'Consultando...'
                    ) : (() => {
                      // Handle live user data with proper status checking
                      if (currentUserLive && typeof currentUserLive === 'object') {
                        if (currentUserLive.status === 'ok' && currentUserLive.usuario_atual) {
                          return currentUserLive.usuario_atual;
                        } else if (currentUserLive.status === 'no_user') {
                          return 'Nenhum usuário logado';
                        } else if (currentUserLive.status === 'unreachable') {
                          return 'Computador inacessível';
                        } else if (currentUserLive.status === 'error') {
                          return `Erro: ${currentUserLive.message || 'Erro desconhecido'}`;
                        }
                      }
                      // Handle simple string values or fallback
                      return currentUserLive || computer.currentUser || 'N/A';
                    })()}
                  </span>
                </div>
                <div className="ml-2 space-x-2">
                  <button
                    onClick={() => fetchCurrentUser(true)}
                    disabled={currentUserLiveLoading}
                    className="px-3 py-1 bg-gray-200 text-gray-800 text-xs rounded hover:bg-gray-300 disabled:opacity-50"
                  >
                    {currentUserLiveLoading ? 'Consultando...' : 'Atualizar Usuário Atual'}
                  </button>
                  {computer.currentUser ? (
                    <button
                      onClick={handleUnassignUser}
                      disabled={assignmentLoading}
                      className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700 disabled:opacity-50"
                    >
                      {assignmentLoading ? 'Desvinculando...' : 'Desvincular'}
                    </button>
                  ) : (
                    <button
                      onClick={openUserAssignModal}
                      disabled={assignmentLoading}
                      className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 disabled:opacity-50"
                    >
                      Vincular Usuário
                    </button>
                  )}
                </div>
              </dd>
            </div>

            <div>
              <dt className="text-sm font-medium text-gray-500">Usuário anterior</dt>
              <dd className="text-sm text-gray-900">{computer.previousUser || 'N/A'}</dd>
            </div>
          </dl>
        </div>

        {/* Informações de Atividade */}
        <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Informações de Atividade</h3>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm font-medium text-gray-500">Último Login</dt>
              <dd className="text-sm text-gray-900">{formatDate(computer.lastLogon)}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Criado em</dt>
              <dd className="text-sm text-gray-900">{formatDate(computer.created)}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Dias desde último login</dt>
              <dd className="text-sm text-gray-900">
                {computer.lastLogon ? 
                  Math.floor((new Date() - new Date(computer.lastLogon)) / (1000 * 60 * 60 * 24)) + ' dias'
                  : 'Nunca logou'
                }
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">User Account Control</dt>
              <dd className="text-sm text-gray-900 font-mono">{computer.userAccountControl || 'N/A'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Primary Group ID</dt>
              <dd className="text-sm text-gray-900">
                {computer.primaryGroupID || 'N/A'}
                {computer.primaryGroupID === 515 && (
                  <span className="ml-2 text-xs text-gray-500">(Domain Computers)</span>
                )}
                {computer.primaryGroupID === 516 && (
                  <span className="ml-2 text-xs text-red-600">(Domain Controllers)</span>
                )}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      {/* NOVA SEÇÃO - Informações do Último Usuário (desabilitada - WIP) */}
      <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow opacity-60 pointer-events-none">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <h3 className="text-lg font-semibold text-gray-900">Informações do Último Usuário</h3>
            <span className="inline-block bg-yellow-100 text-yellow-800 text-xs font-semibold px-2 py-1 rounded">WIP</span>
          </div>
          <button
            onClick={fetchLastUserInfo}
            disabled={lastUserLoading}
            className="flex items-center space-x-2 text-blue-600 hover:text-blue-800 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${lastUserLoading ? 'animate-spin' : ''}`} />
            <span>Atualizar</span>
          </button>
        </div>
        
        {lastUserLoading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
            <span className="ml-2 text-gray-600">Consultando logs de eventos...</span>
          </div>
        ) : lastUserInfo && lastUserInfo.success ? (
          <div className="space-y-6">
            {/* Informações Principais */}
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Último Usuário</dt>
                <dd className="text-sm text-gray-900 font-mono bg-blue-50 px-2 py-1 rounded">
                  {lastUserInfo.last_user}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Data/Hora do Logon</dt>
                <dd className="text-sm text-gray-900">
                  {formatLogonTime(lastUserInfo.last_logon_time)}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Tipo de Logon</dt>
                <dd className="text-sm text-gray-900">{lastUserInfo.logon_type}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Tempo de Pesquisa</dt>
                <dd className="text-sm text-gray-900">{lastUserInfo.total_time || lastUserInfo.search_time} segundos</dd>
              </div>
            </dl>
            
            {/* Histórico de Logons Recentes */}
            {lastUserInfo.recent_logons && lastUserInfo.recent_logons.length > 0 && (
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">Logons Recentes (Últimos 5)</h4>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Usuário
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Data/Hora
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Tipo de Logon
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          IP de Origem
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Processo de Logon
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {lastUserInfo.recent_logons.map((logon, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-6 py-4 text-sm text-gray-900 font-mono">
                            {logon.user}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {formatLogonTime(logon.time)}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {logon.logon_type}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500 font-mono">
                            {logon.source_ip || 'N/A'}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {logon.logon_process || 'N/A'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Informações Técnicas */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Detalhes Técnicos</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Método de Busca:</span>
                  <span className="ml-2 text-gray-900">{lastUserInfo.search_method || 'N/A'}</span>
                </div>
                <div>
                  <span className="text-gray-500">Máquina Encontrada:</span>
                  <span className="ml-2 text-gray-900">
                    {lastUserInfo.computer_found !== undefined ? 
                      (lastUserInfo.computer_found ? 'Sim' : 'Não') : 'N/A'
                    }
                  </span>
                </div>
                {lastUserInfo.service_tag && (
                  <div>
                    <span className="text-gray-500">Service Tag:</span>
                    <span className="ml-2 text-gray-900 font-mono">{lastUserInfo.service_tag}</span>
                  </div>
                )}
                <div>
                  <span className="text-gray-500">Método de Conexão:</span>
                  <span className="ml-2 text-gray-900">{lastUserInfo.connection_method || 'N/A'}</span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <AlertTriangle className="mx-auto h-8 w-8 text-gray-400" />
            <p className="mt-2 text-sm text-gray-500">
              {lastUserInfo?.error || 'Não foi possível obter informações do último usuário'}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Verifique se a máquina está acessível via WinRM e se os logs de eventos estão disponíveis
            </p>
            
            {/* Informações de Debug */}
            {lastUserInfo?.search_method && (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-left">
                <p className="text-xs text-yellow-700 font-medium mb-2">
                  🔍 Informações de Debug:
                </p>
                <div className="text-xs text-yellow-600 space-y-1">
                  <p><strong>Método de busca:</strong> {lastUserInfo.search_method}</p>
                  {lastUserInfo.computer_name && (
                    <p><strong>Nome da máquina:</strong> {lastUserInfo.computer_name}</p>
                  )}
                  {lastUserInfo.service_tag && (
                    <p><strong>Service Tag:</strong> {lastUserInfo.service_tag}</p>
                  )}
                  {lastUserInfo.total_time && (
                    <p><strong>Tempo total:</strong> {lastUserInfo.total_time}s</p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Informações de Garantia Dell */}
      <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Informações de Garantia Dell</h3>
          <div className="flex items-center space-x-2">
            <button
              onClick={fetchWarrantyInfo}
              disabled={warrantyLoading}
              className="flex items-center space-x-2 text-blue-600 hover:text-blue-800 disabled:opacity-50 transition-colors"
              title="Consultar garantia (apenas consulta)"
            >
              <RefreshCw className={`h-4 w-4 ${warrantyLoading ? 'animate-spin' : ''}`} />
              <span>Atualizar</span>
            </button>
            <button
              onClick={async () => {
                try {
                  setWarrantyLoading(true)
                  const resp = await api.post(`/computers/${encodeURIComponent(computerName)}/warranty/refresh`)
                  if (resp.data && resp.data.warranty_data) {
                    // Atualizar estado local com os dados retornados pelo backend
                    // normalize entitlements that might be stringified JSON
                    let ent = resp.data.warranty_data.entitlements
                    try {
                      if (typeof ent === 'string') ent = JSON.parse(ent)
                    } catch (e) {
                      ent = []
                    }

                    const w = {
                      serviceTag: resp.data.warranty_data.service_tag,
                      productLineDescription: resp.data.warranty_data.product_description || resp.data.warranty_data.product_description || '',
                      systemDescription: resp.data.warranty_data.product_description || '',
                      warrantyEndDate: resp.data.warranty_data.warranty_end_date || resp.data.warranty_data.expiration_date_formatted || null,
                      warrantyStatus: resp.data.warranty_data.warranty_status === 'Active' ? 'Active' : 'Expired',
                      entitlements: Array.isArray(ent) ? ent : [],
                      dataSource: 'manual_refresh'
                    }
                    setWarranty(w)
                  }
                } catch (err) {
                  console.error('Erro ao forçar refresh de garantia:', err)
                } finally {
                  setWarrantyLoading(false)
                }
              }}
              disabled={warrantyLoading}
              className="flex items-center space-x-2 text-green-600 hover:text-green-800 disabled:opacity-50 transition-colors"
              title="Sync + (forçar atualização e gravar no banco)"
            >
              <RefreshCw className={`h-4 w-4 ${warrantyLoading ? 'animate-spin' : ''}`} />
              <span>Sync +</span>
            </button>
          </div>
        </div>
        
        {warrantyLoading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
            <span className="ml-2 text-gray-600">Consultando garantia Dell...</span>
          </div>
        ) : warranty && !warranty.error ? (
          <div className="space-y-6">
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Service Tag</dt>
                <dd className="text-sm text-gray-900 font-mono bg-gray-50 px-2 py-1 rounded">
                  {warranty.serviceTag}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Linha de Produto</dt>
                <dd className="text-sm text-gray-900">{warranty.productLineDescription}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Descrição do Sistema</dt>
                <dd className="text-sm text-gray-900">{warranty.systemDescription}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Data de Expiração</dt>
                <dd className="text-sm text-gray-900">
                  {warranty.warrantyEndDate ? formatDate(warranty.warrantyEndDate) : 'N/A'}
                </dd>
              </div>
            </dl>
            
            {Array.isArray(warranty.entitlements) && warranty.entitlements.length > 0 && (
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3">Entitlements Disponíveis</h4>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Serviço
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Tipo
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Data Início
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Data Fim
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {warranty.entitlements.map((entitlement, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-6 py-4 text-sm text-gray-900">
                            {entitlement.serviceLevelDescription}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {entitlement.endDate ? formatEntitlementDate(entitlement.endDate) : 'N/A'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8">
            <AlertTriangle className="mx-auto h-8 w-8 text-gray-400" />
            <p className="mt-2 text-sm text-gray-500">
              {warranty?.error || 'Não foi possível obter informações de garantia'}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Verifique se a API Dell está configurada corretamente
            </p>
          </div>
        )}
      </div>

      {/* Informações de Filtros DHCP */}
      <div className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Informações de Filtros DHCP</h3>
          <button
            onClick={fetchDHCPInfo}
            disabled={dhcpLoading}
            className="flex items-center space-x-2 text-blue-600 hover:text-blue-800 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${dhcpLoading ? 'animate-spin' : ''}`} />
            <span>Atualizar</span>
          </button>
        </div>
        
        {dhcpLoading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
            <span className="ml-2 text-gray-600">Consultando filtros DHCP...</span>
          </div>
        ) : dhcpInfo && !dhcpInfo.error ? (
          <div className="space-y-6">
            {/* Informações do Servidor DHCP */}
            <dl className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Navio/Local</dt>
                <dd className="text-sm text-gray-900 font-medium flex items-center">
                  <MapPin className="h-4 w-4 mr-1 text-blue-600" />
                  {dhcpInfo.ship_name || 'N/A'}
                  {dhcpInfo.source && (
                    <span className="ml-2 text-xs text-gray-500">({dhcpInfo.source})</span>
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Servidor DHCP</dt>
                <dd className="text-sm text-gray-900 font-mono bg-gray-50 px-2 py-1 rounded flex items-center">
                  <Server className="h-4 w-4 mr-1 text-gray-600" />
                  {dhcpInfo.dhcp_server || 'N/A'}
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Status no DHCP</dt>
                <dd className="text-sm text-gray-900">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${dhcpStatus.color}`}>
                    {dhcpStatus.text}
                  </span>
                </dd>
              </div>
            </dl>

            {/* Resultados da Busca */}
            {dhcpInfo.service_tag_found && dhcpInfo.search_results && dhcpInfo.search_results.length > 0 ? (
              <div>
                <h4 className="text-md font-medium text-gray-900 mb-3 flex items-center">
                  <Search className="h-5 w-5 mr-2 text-green-600" />
                  Registros Encontrados nos Filtros DHCP ({dhcpInfo.search_results.length})
                </h4>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Tipo do Filtro
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Endereço MAC
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Campo Encontrado
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Descrição
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Nome
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {dhcpInfo.search_results.map((result, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          <td className="px-6 py-4 text-sm text-gray-900">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              result.filter_type === 'Allow' 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {result.filter_type === 'Allow' ? 'Permitir' : 'Negar'}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-900 font-mono">
                            {result.mac_address}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              result.match_field === 'name' 
                                ? 'bg-blue-100 text-blue-800' 
                                : 'bg-purple-100 text-purple-800'
                            }`}>
                              {result.match_field === 'name' ? 'Nome' : 'Descrição'}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                            {result.description || 'N/A'}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                            {result.name || 'N/A'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <Search className="mx-auto h-8 w-8 text-gray-400" />
                <p className="mt-2 text-sm text-gray-500">
                  Máquina não encontrada nos filtros DHCP
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  A máquina "{computerName}" não foi localizada nos filtros Allow ou Deny do servidor DHCP
                </p>
              </div>
            )}

            {/* Resumo dos Filtros */}
            {dhcpInfo.filters && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Resumo dos Filtros DHCP</h4>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-lg font-semibold text-gray-900">{dhcpInfo.filters.total || 0}</p>
                    <p className="text-xs text-gray-500">Total de Filtros</p>
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-green-600">{dhcpInfo.filters.allow_count || 0}</p>
                    <p className="text-xs text-gray-500">Filtros Allow</p>
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-red-600">{dhcpInfo.filters.deny_count || 0}</p>
                    <p className="text-xs text-gray-500">Filtros Deny</p>
                  </div>
                </div>
              </div>
            )}

            {/* Informações Adicionais */}
            {dhcpInfo.timestamp && (
              <div className="text-xs text-gray-400 text-right">
                Última consulta: {formatDate(dhcpInfo.timestamp)}
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8">
            <AlertTriangle className="mx-auto h-8 w-8 text-gray-400" />
            <p className="mt-2 text-sm text-gray-500">
              {dhcpInfo?.error || 'Não foi possível obter informações dos filtros DHCP'}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Erro de conexão ou máquina nas bases.
            </p>
            
            {/* Informações de Debug Expandidas */}
            {dhcpInfo?.debug_info && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-left">
                <p className="text-xs text-red-700 font-medium mb-2">
                  🔍 Informações de Debug:
                </p>
                <pre className="text-xs text-red-600 whitespace-pre-wrap">
                  {JSON.stringify(dhcpInfo.debug_info, null, 2)}
                </pre>
              </div>
            )}
            
            {/* Informações Básicas de Debug */}
            {dhcpInfo?.ship_name && (
              <div className="mt-4 p-3 bg-yellow-50 rounded-lg">
                <p className="text-xs text-yellow-700">
                  <strong>Debug:</strong> Local identificado como "{dhcpInfo.ship_name}" para a máquina "{computerName}"
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal de Atribuição de Usuário */}
      {showUserAssignModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-lg mx-4">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Vincular Usuário à Máquina</h3>
                <button
                  onClick={() => setShowUserAssignModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>

              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-2">
                  Máquina: <strong>{computerName}</strong>
                </p>
                <p className="text-xs text-gray-500">
                  Ao vincular um usuário, será enviado um email com o termo de recebimento contendo as informações da máquina.
                </p>
              </div>

              {/* Campo de busca de usuários */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Buscar Usuário
                </label>
                <input
                  type="text"
                  value={userSearchTerm}
                  onChange={(e) => setUserSearchTerm(e.target.value)}
                  placeholder="Digite o nome do usuário..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Lista de usuários */}
              <div className="mb-6 max-h-64 overflow-y-auto">
                <div className="space-y-2">
                  {availableUsers
                    .filter(user => 
                      user.name.toLowerCase().includes(userSearchTerm.toLowerCase()) ||
                      user.email.toLowerCase().includes(userSearchTerm.toLowerCase())
                    )
                    .map(user => (
                      <div
                        key={user.id}
                        onClick={() => setSelectedUser(user)}
                        className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                          selectedUser?.id === user.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-gray-900">{user.name}</p>
                            <p className="text-sm text-gray-600">{user.email}</p>
                            <p className="text-xs text-gray-500">{user.position} - {user.base}</p>
                          </div>
                          {selectedUser?.id === user.id && (
                            <CheckCircle className="h-5 w-5 text-blue-600" />
                          )}
                        </div>
                      </div>
                    ))}
                </div>

                {availableUsers.length === 0 && (
                  <div className="text-center py-4">
                    <p className="text-sm text-gray-500">Nenhum usuário encontrado</p>
                  </div>
                )}
              </div>

              {/* Botões de ação */}
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowUserAssignModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleAssignUser}
                  disabled={!selectedUser || assignmentLoading}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {assignmentLoading ? 'Vinculando...' : 'Vincular Usuário'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ComputerDetail