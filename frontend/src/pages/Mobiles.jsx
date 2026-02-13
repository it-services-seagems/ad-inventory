import React, { useEffect, useState, useMemo, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Loader2, ChevronUp, ChevronDown, ArrowUpDown, Smartphone } from 'lucide-react'
import api from '../services/api'
import ListHeader from '../components/ListHeader'
import SimpleIPhoneSelector from '../components/SimpleIPhoneSelector'
import { formatPhoneNumber, unformatPhoneNumber, phoneNumberMask } from '../utils/formatters'

const Mobiles = () => {
  const [mobiles, setMobiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('')
  const [showAddForm, setShowAddForm] = useState(false)
  const [funcionarios, setFuncionarios] = useState([])
  const [funcionariosCompletos, setFuncionariosCompletos] = useState([])
  const [form, setForm] = useState({ 
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
  const [sortConfig, setSortConfig] = useState({ key: 'id', direction: 'asc' })
  const navigate = useNavigate()
  const searchTimeoutRef = useRef(null)

  const fetchMobiles = async () => {
    try {
      setLoading(true)
      const resp = await api.get('/mobiles/?limit=200')
      if (resp.data && resp.data.success) {
        setMobiles(resp.data.mobiles || [])
      } else {
        setMobiles([])
      }
    } catch (e) {
      console.error('Erro ao carregar mobiles', e)
      setMobiles([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchMobiles() }, [])

  // debounce search like Computers page
  useEffect(() => {
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current)
    searchTimeoutRef.current = setTimeout(() => setDebouncedSearchTerm((searchTerm || '').trim()), 300)
    return () => { if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current) }
  }, [searchTerm])

  // Sort handler
  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }))
  }

  // Get sort value for mobile
  const getSortValue = (mobile, key) => {
    switch (key) {
      case 'id': return mobile.id || 0
      case 'model': return (mobile.model || mobile.modelo || '').toLowerCase()
      case 'brand': return (mobile.brand || mobile.marca || '').toLowerCase()
      case 'funcionario': return (mobile.funcionario_nome || '').toLowerCase()
      case 'departamento': return (mobile.departamento || mobile.secao_atual_descricao || '').toLowerCase()
      case 'tipo': return (mobile.tipo || '').toLowerCase()
      case 'number': return mobile.number || mobile.numero || ''
      case 'eid': return mobile.eid || ''
      case 'imei': return mobile.imei || ''
      default: return ''
    }
  }



  const filtered = useMemo(() => {
    const q = (debouncedSearchTerm || '').toLowerCase().trim()
    let result = mobiles
    
    if (q) {
      result = mobiles.filter(m => 
        Object.values(m).some(v => (v || '').toString().toLowerCase().includes(q))
      )
    }
    
    // Apply sorting
    result.sort((a, b) => {
      const aValue = getSortValue(a, sortConfig.key)
      const bValue = getSortValue(b, sortConfig.key)
      const comparison = aValue < bValue ? -1 : aValue > bValue ? 1 : 0
      return sortConfig.direction === 'asc' ? comparison : -comparison
    })
    
    return result
  }, [mobiles, debouncedSearchTerm, sortConfig, getSortValue])

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

  const handleAddClick = () => {
    fetchFuncionarios()
    setForm({ 
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
    setShowAddForm(true)
  }

  const handleFuncionarioChange = (funcionarioNome) => {
    const funcionario = funcionariosCompletos.find(f => f.nome === funcionarioNome)
    if (funcionario) {
      setForm({
        ...form,
        funcionario_nome: funcionarioNome,
        funcionario_matricula: funcionario.matricula || '',
        departamento: funcionario.secao_atual_descricao || ''
      })
    } else {
      setForm({
        ...form,
        funcionario_nome: funcionarioNome,
        funcionario_matricula: '',
        departamento: ''
      })
    }
  }

  const handlePhoneChange = (value) => {
    const masked = phoneNumberMask(value)
    setForm({...form, number: masked})
  }

  const handleAddSubmit = async (e) => {
    e.preventDefault()
    try {
      await api.post('/mobiles/', {
        model: form.model,
        brand: form.brand,
        imei: form.imei,
        departamento: form.departamento,
        tipo: form.tipo,
        number: unformatPhoneNumber(form.number),
        eid: form.eid,
        funcionario_nome: form.funcionario_nome,
        funcionario_matricula: form.funcionario_matricula
      })
      setShowAddForm(false)
      fetchMobiles()
    } catch (err) {
      alert('Erro ao adicionar aparelho: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Confirma exclusão deste aparelho?')) return
    try {
      await api.delete(`/mobiles/${id}`)
      fetchMobiles()
    } catch (e) {
      alert('Erro ao deletar: ' + (e.response?.data?.detail || e.message))
    }
  }

  // Sortable header component
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

  return (
    <div className="w-full">
      <div className="px-6 mb-6">
        <ListHeader
          title="Celulares"
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          onAdd={handleAddClick}
          onRefresh={fetchMobiles}
        />
      </div>



      {loading ? (
        <div className="flex justify-center items-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      ) : (
        <div className="w-full">
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto max-h-[70vh] relative" style={{ scrollbarWidth: 'thin' }}>
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50 sticky top-0 z-10">
                  <tr>
                    <SortableHeader sortKey="id" className="w-20">ID</SortableHeader>
                    <SortableHeader sortKey="model" className="min-w-48">Modelo</SortableHeader>
                    <SortableHeader sortKey="brand" className="w-32">Marca</SortableHeader>
                    <SortableHeader sortKey="funcionario" className="w-40">Funcionário</SortableHeader>
                    <SortableHeader sortKey="departamento" className="w-36">Departamento</SortableHeader>
                    <SortableHeader sortKey="tipo" className="w-32">Tipo</SortableHeader>
                    <SortableHeader sortKey="number" className="w-40">Número</SortableHeader>
                    <SortableHeader sortKey="eid" className="w-32">EID</SortableHeader>
                    <SortableHeader sortKey="imei" className="w-32">IMEI</SortableHeader>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32 sticky right-0 bg-gray-50">Ações</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filtered.map(m => (
                    <tr 
                      key={m.id} 
                      className="hover:bg-blue-50 transition-colors cursor-pointer group"
                      onClick={() => navigate(`/mobiles/${m.id}`)}
                      title={`Clique para ver detalhes do aparelho #${m.id}`}
                    >
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{m.id}</td>
                      <td className="px-4 py-3">
                        <div className="text-sm font-medium text-gray-900 truncate">{m.model || m.modelo || ''}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-gray-900 truncate">{m.brand || m.marca || ''}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-gray-900 truncate">
                          {m.funcionario_nome ? (
                            <div className="font-medium truncate">{m.funcionario_nome}</div>
                          ) : (
                            <span className="text-gray-400 italic text-xs">Funcionário não identificado</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-gray-900 truncate">{m.departamento || m.secao_atual_descricao || ''}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-gray-900 truncate">{m.tipo || ''}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-gray-900 truncate">{formatPhoneNumber(m.number || m.numero) || ''}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-gray-900 truncate">{m.eid || ''}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-gray-900 truncate">{m.imei || ''}</div>
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium sticky right-0 bg-white">
                        <button 
                          onClick={(e) => { e.stopPropagation(); handleDelete(m.id) }} 
                          className="flex items-center px-3 py-1.5 text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-all duration-200 text-sm font-medium border border-red-200 hover:border-red-300"
                          title="Excluir aparelho"
                        >
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                          Excluir
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Adicionar */}
      {showAddForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Adicionar Novo Aparelho</h3>
            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Modelo *</label>
                  <SimpleIPhoneSelector
                    value={form.model}
                    onChange={(value, modelData) => {
                      setForm({
                        ...form,
                        model: value,
                        
                        brand: modelData?.finalModel && value.toLowerCase().includes('iphone') ? 'Apple' : form.brand
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
                    value={form.brand} 
                    onChange={e => setForm({...form, brand: e.target.value})} 
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Funcionário</label>
                  <select 
                    value={form.funcionario_nome} 
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
                    value={form.departamento} 
                    disabled
                    className="w-full p-3 border border-gray-300 rounded-md bg-gray-50 text-gray-600" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Número</label>
                  <input 
                    placeholder="(21) 98765-4321" 
                    value={form.number} 
                    onChange={e => handlePhoneChange(e.target.value)} 
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
                  <input 
                    placeholder="Tipo do aparelho" 
                    value={form.tipo} 
                    onChange={e => setForm({...form, tipo: e.target.value})} 
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">EID</label>
                  <input 
                    placeholder="EID do aparelho" 
                    value={form.eid} 
                    onChange={e => setForm({...form, eid: e.target.value})} 
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">IMEI</label>
                  <input 
                    placeholder="IMEI do aparelho" 
                    value={form.imei} 
                    onChange={e => setForm({...form, imei: e.target.value})} 
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" 
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200 mt-6">
                <button 
                  type="button" 
                  onClick={() => setShowAddForm(false)} 
                  className="flex items-center px-4 py-2.5 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-all duration-200 font-medium border border-gray-300 hover:border-gray-400"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  Cancelar
                </button>
                <button 
                  type="submit" 
                  className="flex items-center px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all duration-200 shadow-md hover:shadow-lg font-medium"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Salvar Aparelho
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Mobiles
