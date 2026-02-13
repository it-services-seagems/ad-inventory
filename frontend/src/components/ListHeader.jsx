import React, { useRef } from 'react'
import { Search, RefreshCw, Filter } from 'lucide-react'

const ListHeader = ({
  title = '',
  searchTerm = '',
  onSearchChange = () => {},
  sections = [],
  filterDept = 'all',
  setFilterDept = () => {},
  tipos = [],
  filterTipo = 'all',
  setFilterTipo = () => {},
  funcionarios = [],
  filterFuncionario = 'all',
  setFilterFuncionario = () => {},
  onAdd = null,
  onRefresh = null,
  onFuncionariosFocus = null
}) => {
  const lastRefreshRef = useRef(0)

  const handleRefresh = () => {
    const now = Date.now()
    if (now - lastRefreshRef.current < 2000) return
    lastRefreshRef.current = now
    if (onRefresh) onRefresh()
  }

  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center space-x-4">
        <h1 className="text-2xl font-bold">{title}</h1>
        <div className="flex items-center bg-white rounded border px-2 py-1">
          <Search className="w-4 h-4 text-gray-500 mr-2" />
          <input placeholder="Pesquisar..." value={searchTerm} onChange={e => onSearchChange(e.target.value)} className="outline-none" />
        </div>
        <button onClick={handleRefresh} title="Recarregar" className="p-2 bg-white border rounded"><RefreshCw className="w-4 h-4"/></button>
      </div>
      <div className="flex items-center space-x-2">
        {(sections?.length > 0 || funcionarios?.length > 0 || tipos?.length > 0) && (
          <div className="flex items-center space-x-2 bg-white border rounded p-1">
            <Filter className="w-4 h-4 text-gray-500" />
            {sections?.length > 0 && (
              <select value={filterDept} onChange={e => setFilterDept(e.target.value)} className="p-1">
                <option value="all">Todos departamentos</option>
                {sections.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            )}
            {funcionarios?.length > 0 && (
              <select value={filterFuncionario} onChange={e => setFilterFuncionario(e.target.value)} onFocus={onFuncionariosFocus} className="p-1">
                <option value="all">Todos funcionários</option>
                {funcionarios.map(f => <option key={f} value={f}>{f}</option>)}
              </select>
            )}
            {tipos?.length > 0 && (
              <select value={filterTipo} onChange={e => setFilterTipo(e.target.value)} className="p-1">
                <option value="all">Todos tipos</option>
                {tipos.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            )}
          </div>
        )}
        {onAdd && (
          <button 
            onClick={onAdd} 
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all duration-200 shadow-md hover:shadow-lg font-medium"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Adicionar
          </button>
        )}
      </div>
    </div>
  )
}

export default ListHeader
