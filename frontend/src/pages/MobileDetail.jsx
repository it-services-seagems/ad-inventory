import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Edit3, Trash2, Smartphone, User, Building, Hash, Cpu, Phone, Calendar } from 'lucide-react'
import api from '../services/api'
import SimpleIPhoneSelector from '../components/SimpleIPhoneSelector'
import { formatPhoneNumber, unformatPhoneNumber, phoneNumberMask } from '../utils/formatters'

// Componente para exibir informações técnicas do iPhone
const IPhoneTechnicalInfo = ({ model }) => {
  const [iphoneInfo, setIphoneInfo] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const fetchIPhoneInfo = async () => {
      if (!model || !model.toLowerCase().includes('iphone')) return
      
      try {
        setLoading(true)
        const response = await api.get('/iphone-catalog/catalog')
        if (response.data?.success && response.data?.catalog) {
          // Buscar informações do modelo no catálogo
          const foundModel = response.data.catalog.find(item => 
            model.toLowerCase().includes(item.model.toLowerCase())
          )
          setIphoneInfo(foundModel)
        }
      } catch (error) {
        console.error('Erro ao buscar informações do iPhone:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchIPhoneInfo()
  }, [model])

  if (loading) {
    return (
      <div className="col-span-full">
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <span className="text-sm text-blue-700">Buscando informações do iPhone...</span>
          </div>
        </div>
      </div>
    )
  }

  if (!iphoneInfo) return null

  const currentYear = new Date().getFullYear()
  const isSupported = !iphoneInfo.support_end_year || iphoneInfo.support_end_year >= currentYear
  const yearsSupported = iphoneInfo.support_end_year ? iphoneInfo.support_end_year - iphoneInfo.released_year : null

  return (
    <>
      <div>
        <label className="block text-sm font-medium text-gray-500 mb-1">Geração</label>
        <p className="text-sm text-gray-900 bg-gray-50 p-2 rounded border flex items-center">
          <Smartphone className="w-4 h-4 text-gray-400 mr-2" />
          Geração {iphoneInfo.generation}
        </p>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-500 mb-1">Lançamento</label>
        <p className="text-sm text-gray-900 bg-gray-50 p-2 rounded border flex items-center">
          <Calendar className="w-4 h-4 text-gray-400 mr-2" />
          {iphoneInfo.released_year}
        </p>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-500 mb-1">Suporte Apple</label>
        <p className={`text-sm p-2 rounded border flex items-center ${
          isSupported 
            ? 'text-green-900 bg-green-50 border-green-200' 
            : 'text-red-900 bg-red-50 border-red-200'
        }`}>
          <div className={`w-2 h-2 rounded-full mr-2 ${
            isSupported ? 'bg-green-500' : 'bg-red-500'
          }`}></div>
          {iphoneInfo.support_end_year ? (
            isSupported 
              ? `Até ${iphoneInfo.support_end_year}${yearsSupported ? ` (${yearsSupported} anos)` : ''}` 
              : `Encerrado em ${iphoneInfo.support_end_year}`
          ) : 'Suporte ativo'}
        </p>
      </div>
    </>
  )
}

const MobileDetail = () => {
  const { mobileId } = useParams()
  const navigate = useNavigate()
  const [mobile, setMobile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [funcionarioCompleto, setFuncionarioCompleto] = useState(null)
  const [buscandoFuncionario, setBuscandoFuncionario] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [sections, setSections] = useState([])
  const [funcionarios, setFuncionarios] = useState([])
  const [funcionariosCompletos, setFuncionariosCompletos] = useState([])
  const [editForm, setEditForm] = useState({ 
    model: '', 
    brand: '', 
    imei: '', 
    departamento: '', 
    tipo: '', 
    number: '', 
    eid: '',
    funcionario_nome: '',
    funcionario_matricula: ''
  })

  const fetchMobile = async () => {
    try {
      setLoading(true)
      setFuncionarioCompleto(null) // Limpar funcionário anterior
      setBuscandoFuncionario(false)
      const resp = await api.get(`/mobiles/${mobileId}`)
      if (resp.data && resp.data.success) {
        setMobile(resp.data.mobile)
      }
    } catch (e) {
      console.error(e)
      alert('Erro ao carregar aparelho')
    } finally { setLoading(false) }
  }

  const fetchFuncionarioCompleto = async (nomeFuncionario) => {
    if (buscandoFuncionario) return // Evitar múltiplas chamadas simultâneas
    
    try {
      setBuscandoFuncionario(true)
      
      // Dividir o nome em termos para buscar de forma mais flexível
      const termos = nomeFuncionario.trim().split(/\s+/).filter(t => t.length > 1)
      const termoPrincipal = termos[0] // Primeiro nome
      
      let funcionario = null
      let melhorScore = 0
      
      // Função para calcular score de similaridade
      const calcularScore = (nomeFunc, termosOriginais) => {
        if (!nomeFunc) return 0
        
        const nomeNormalizado = nomeFunc.toLowerCase().trim()
        const termosFunc = nomeNormalizado.split(/\s+/)
        let score = 0
        
        termosOriginais.forEach((termo, index) => {
          const termoLower = termo.toLowerCase()
          
          // Verifica se alguma palavra do funcionário começa com o termo (mais peso)
          const iniciaComTermo = termosFunc.some(palavra => palavra.startsWith(termoLower))
          if (iniciaComTermo) {
            score += (index === 0 ? 10 : 5) // Primeiro nome tem mais peso
          }
          
          // Verifica se alguma palavra contém o termo (menos peso)
          const contemTermo = termosFunc.some(palavra => palavra.includes(termoLower))
          if (contemTermo && !iniciaComTermo) {
            score += 2
          }
        })
        
        // Bonus se encontrou todos os termos
        const termosEncontrados = termosOriginais.filter(termo => 
          nomeNormalizado.includes(termo.toLowerCase())
        ).length
        
        if (termosEncontrados === termosOriginais.length) {
          score += 15 // Grande bonus para match completo
        }
        
        // Penalidade por diferença no tamanho do nome
        const diferencaTamanho = Math.abs(termosFunc.length - termosOriginais.length)
        score -= diferencaTamanho * 2
        
        return Math.max(0, score)
      }
      
      // 1. Busca pelo nome completo
      let resp = await api.get(`/funcionarios/?search=${encodeURIComponent(nomeFuncionario)}&limit=10`)
      if (resp.data && resp.data.funcionarios && resp.data.funcionarios.length > 0) {
        // Encontrar o melhor match baseado no score
        resp.data.funcionarios.forEach(f => {
          const score = calcularScore(f.nome, termos)
          if (score > melhorScore) {
            melhorScore = score
            funcionario = f
          }
        })
      }
      
      // 2. Se não encontrou um bom match, busca pelo primeiro nome
      if (!funcionario && termoPrincipal.length > 2) {
        resp = await api.get(`/funcionarios/?search=${encodeURIComponent(termoPrincipal)}&limit=20`)
        if (resp.data && resp.data.funcionarios && resp.data.funcionarios.length > 0) {
          resp.data.funcionarios.forEach(f => {
            const score = calcularScore(f.nome, termos)
            if (score > melhorScore) {
              melhorScore = score
              funcionario = f
            }
          })
        }
      }
      
      // Só aceita se o score for razoável (pelo menos 5)
      if (melhorScore < 5) {
        funcionario = null
      }
      
      if (funcionario) {
        setFuncionarioCompleto(funcionario)
      } else {
        setFuncionarioCompleto({}); // Objeto vazio para indicar que foi buscado mas não encontrado
      }
    } catch (e) {
      console.error('Erro ao buscar funcionário:', e)
      setFuncionarioCompleto({}); // Objeto vazio em caso de erro
    } finally {
      setBuscandoFuncionario(false)
    }
  }

  useEffect(() => { fetchMobile() }, [mobileId])

  useEffect(() => {
    if (mobile && mobile.funcionario_nome && funcionarioCompleto === null && !buscandoFuncionario) {
      fetchFuncionarioCompleto(mobile.funcionario_nome)
    }
  }, [mobile, funcionarioCompleto, buscandoFuncionario])

  const fetchSections = async () => {
    try {
      const resp = await api.get('/funcionarios/?limit=1000')
      if (resp.data && resp.data.funcionarios) {
        const set = new Set()
        resp.data.funcionarios.forEach(f => {
          const val = (f.secao_atual_descricao || '').trim()
          if (val) set.add(val)
        })
        setSections(Array.from(set).sort())
      }
    } catch (e) { console.error('Erro ao buscar seções', e) }
  }

  const fetchFuncionarios = async () => {
    try {
      const resp = await api.get('/funcionarios/?limit=1000')
      if (resp.data && resp.data.funcionarios) {
        setFuncionariosCompletos(resp.data.funcionarios)
        const list = resp.data.funcionarios.map(f => (f.nome || '').trim()).filter(Boolean)
        setFuncionarios(Array.from(new Set(list)).sort())
      }
    } catch (e) {
      console.error('Erro ao carregar funcionarios', e)
    }
  }

  const handleFuncionarioChange = (funcionarioNome) => {
    const funcionario = funcionariosCompletos.find(f => f.nome === funcionarioNome)
    if (funcionario) {
      setEditForm({
        ...editForm,
        funcionario_nome: funcionarioNome,
        funcionario_matricula: funcionario.matricula || '',
        departamento: funcionario.secao_atual_descricao || ''
      })
    } else {
      setEditForm({
        ...editForm,
        funcionario_nome: funcionarioNome,
        funcionario_matricula: '',
        departamento: ''
      })
    }
  }

  const handlePhoneChange = (value) => {
    const masked = phoneNumberMask(value)
    setEditForm({...editForm, number: masked})
  }

  const openEditModal = () => {
    fetchSections()
    fetchFuncionarios()
    setEditForm({
      model: mobile?.model || mobile?.modelo || '',
      brand: mobile?.brand || mobile?.marca || '',
      imei: mobile?.imei || '',
      departamento: mobile?.departamento || mobile?.secao_atual_descricao || '',
      tipo: mobile?.tipo || '',
      number: formatPhoneNumber(mobile?.number || mobile?.numero) || '',
      eid: mobile?.eid || '',
      funcionario_nome: mobile?.funcionario_nome || '',
      funcionario_matricula: mobile?.funcionario_matricula || ''
    })
    setShowEditModal(true)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    try {
      await api.put(`/mobiles/${mobileId}`, {
        model: editForm.model,
        brand: editForm.brand,
        imei: editForm.imei,
        departamento: editForm.departamento,
        tipo: editForm.tipo,
        number: unformatPhoneNumber(editForm.number),
        eid: editForm.eid,
        funcionario_nome: editForm.funcionario_nome,
        funcionario_matricula: editForm.funcionario_matricula
      })
      setShowEditModal(false)
      fetchMobile()
      alert('Aparelho atualizado com sucesso!')
    } catch (err) {
      alert('Erro ao salvar: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleDelete = async () => {
    if (!confirm('Tem certeza que deseja excluir este aparelho? Esta ação não pode ser desfeita.')) return
    try {
      await api.delete(`/mobiles/${mobileId}`)
      navigate('/mobiles')
    } catch (e) {
      alert('Erro ao deletar: ' + (e.response?.data?.detail || e.message))
    }
  }

  if (loading) return (
    <div className="flex justify-center items-center py-12">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Carregando detalhes do aparelho...</p>
      </div>
    </div>
  )
  
  if (!mobile) return (
    <div className="text-center py-12">
      <Smartphone className="h-16 w-16 text-gray-400 mx-auto mb-4" />
      <h2 className="text-xl font-semibold text-gray-900 mb-2">Aparelho não encontrado</h2>
      <p className="text-gray-600 mb-4">O aparelho solicitado não existe ou foi removido.</p>
      <button 
        onClick={() => navigate('/mobiles')} 
        className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all duration-200 shadow-md hover:shadow-lg font-medium"
      >
        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Voltar para Lista
      </button>
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => navigate('/mobiles')} 
              className="p-2 rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                <Smartphone className="w-7 h-7 text-blue-600 mr-3" />
                {mobile.model || mobile.modelo || 'Aparelho'}
              </h1>
              <p className="text-gray-600 mt-1">ID: #{mobile.id} • {mobile.brand || mobile.marca || 'Marca não informada'}</p>
            </div>
          </div>
          <div className="flex space-x-3">
            <button 
              onClick={openEditModal} 
              className="flex items-center px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all duration-200 shadow-md hover:shadow-lg font-medium border border-blue-700 hover:border-blue-800"
            >
              <Edit3 className="w-4 h-4 mr-2" />
              Editar
            </button>
            <button 
              onClick={handleDelete} 
              className="flex items-center px-4 py-2.5 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all duration-200 shadow-md hover:shadow-lg font-medium border border-red-700 hover:border-red-800"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Excluir
            </button>
          </div>
        </div>
      </div>

      {/* Details Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Basic Info */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Cpu className="w-5 h-5 text-blue-600 mr-2" />
            Informações do Aparelho
          </h2>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Modelo</label>
              <p className="text-sm text-gray-900 font-medium">{mobile.model || mobile.modelo || 'Não informado'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Marca</label>
              <p className="text-sm text-gray-900">{mobile.brand || mobile.marca || 'Não informada'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Tipo</label>
              <p className="text-sm text-gray-900">{mobile.tipo || 'Não informado'}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Número</label>
              <p className="text-sm text-gray-900">{formatPhoneNumber(mobile.number || mobile.numero) || 'Não informado'}</p>
            </div>
          </div>
        </div>

        {/* User Assignment */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <User className="w-5 h-5 text-green-600 mr-2" />
            Funcionário
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Nome</label>
              {mobile.funcionario_nome ? (
                <p className="text-sm text-gray-900 font-medium">{mobile.funcionario_nome}</p>
              ) : (
                <p className="text-sm text-gray-400 italic">Não atribuído</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Cargo</label>
              {buscandoFuncionario ? (
                <p className="text-sm text-blue-600 italic">Carregando cargo...</p>
              ) : funcionarioCompleto && funcionarioCompleto.nome ? (
                funcionarioCompleto.cargo ? (
                  <p className="text-sm text-gray-900 flex items-center">
                    <svg className="w-4 h-4 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0V6a2 2 0 012 2v6.829a2 2 0 01-.518 1.341l-2.143 2.142a2 2 0 01-1.413.586H9.017a2 2 0 01-1.414-.586L5.46 15.17a2 2 0 01-.459-1.341V8a2 2 0 012-2V4z" />
                    </svg>
                    {funcionarioCompleto.cargo}
                  </p>
                ) : (
                  <p className="text-sm text-gray-400 italic">Cargo não informado</p>
                )
              ) : funcionarioCompleto !== null ? (
                <p className="text-sm text-gray-400 italic">Funcionário não encontrado</p>
              ) : mobile.funcionario_nome ? (
                <p className="text-sm text-gray-400 italic">-</p>
              ) : (
                <p className="text-sm text-gray-400 italic">-</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-500 mb-1">Departamento</label>
              <p className="text-sm text-gray-900 flex items-center">
                <Building className="w-4 h-4 text-gray-400 mr-2" />
                {mobile.departamento || mobile.secao_atual_descricao || 'Não informado'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Technical Details */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Phone className="w-5 h-5 text-purple-600 mr-2" />
          Detalhes Técnicos
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">IMEI</label>
            <p className="text-sm text-gray-900 font-mono bg-gray-50 p-2 rounded border">
              {mobile.imei || 'Não informado'}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">EID</label>
            <p className="text-sm text-gray-900 font-mono bg-gray-50 p-2 rounded border">
              {mobile.eid || 'Não informado'}
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-500 mb-1">ID do Sistema</label>
            <p className="text-sm text-gray-900 font-mono bg-gray-50 p-2 rounded border flex items-center">
              <Hash className="w-4 h-4 text-gray-400 mr-1" />
              {mobile.id}
            </p>
          </div>
          {/* Informações do iPhone se disponível */}
          <IPhoneTechnicalInfo model={mobile.model || mobile.modelo} />
        </div>
      </div>

      {/* Edit Modal */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Editar Aparelho</h3>
            <form onSubmit={handleSave} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Modelo *</label>
                  <SimpleIPhoneSelector
                    value={editForm.model}
                    onChange={(value, modelData) => {
                      setEditForm({
                        ...editForm, 
                        model: value,
                        // Auto-completar marca se for iPhone e tiver dados do modelo
                        brand: modelData?.finalModel && value.toLowerCase().includes('iphone') ? 'Apple' : editForm.brand
                      })
                    }}
                    placeholder="Digite o modelo do aparelho (ex: iPhone 13 Pro Max)"
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Marca</label>
                  <input 
                    placeholder="Marca do aparelho" 
                    value={editForm.brand} 
                    onChange={e => setEditForm({...editForm, brand: e.target.value})} 
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Funcionário</label>
                  <select 
                    value={editForm.funcionario_nome} 
                    onChange={e => handleFuncionarioChange(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">— Selecione o funcionário —</option>
                    {funcionarios.map(f => <option key={f} value={f}>{f}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Departamento</label>
                  <input 
                    placeholder="Departamento (preenchido automaticamente)" 
                    value={editForm.departamento} 
                    disabled
                    className="w-full p-3 border border-gray-300 rounded-md bg-gray-50 text-gray-600" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Número</label>
                  <input 
                    placeholder="(21) 98765-4321" 
                    value={editForm.number} 
                    onChange={e => handlePhoneChange(e.target.value)} 
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
                  <input 
                    placeholder="Tipo do aparelho" 
                    value={editForm.tipo} 
                    onChange={e => setEditForm({...editForm, tipo: e.target.value})} 
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">EID</label>
                  <input 
                    placeholder="EID do aparelho" 
                    value={editForm.eid} 
                    onChange={e => setEditForm({...editForm, eid: e.target.value})} 
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">IMEI</label>
                  <input 
                    placeholder="IMEI do aparelho" 
                    value={editForm.imei} 
                    onChange={e => setEditForm({...editForm, imei: e.target.value})} 
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200 mt-6">
                <button 
                  type="button" 
                  onClick={() => setShowEditModal(false)} 
                  className="flex items-center px-4 py-2.5 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-all duration-200 font-medium border border-gray-300 hover:border-gray-400"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  Cancelar
                </button>
                <button 
                  type="submit" 
                  className="flex items-center px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all duration-200 shadow-md hover:shadow-lg font-medium border border-blue-700 hover:border-blue-800"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Salvar Alterações
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default MobileDetail
