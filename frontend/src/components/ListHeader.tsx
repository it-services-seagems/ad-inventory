import React from 'react'
import './ListHeader.css'

interface ListHeaderProps {
  title?: string
  total?: number
  onSearch?: (q:string) => void
  onToggleFilters?: () => void
  searchValue?: string
}

const ListHeader: React.FC<ListHeaderProps> = ({ title = 'Computadores', total = 0, onSearch = () => {}, onToggleFilters = () => {}, searchValue = '' }) => {
  return (
    <div className="list-header">
      <div className="list-title">
        <h2>{title}</h2>
        <div className="list-count">{total} items</div>
      </div>

      <div className="list-controls">
        <input className="search-input" placeholder="Buscar por hostname, usuário..." value={searchValue} onChange={(e) => onSearch(e.target.value)} />
        <button className="btn-filters" onClick={onToggleFilters}>Filtros</button>
      </div>
    </div>
  )
}

export default ListHeader
