import React, { FC } from 'react'
import { Filter, ChevronDown, Loader2 } from 'lucide-react'
import './FilterBar.css'

interface FilterBarProps {
  filters: any
  setFilters: (fn: any) => void
  advancedFilters: any
  setAdvancedFilters: (fn: any) => void
  showFilters: boolean
  setShowFilters: (v: boolean) => void
  activeFiltersInfo: string[]
  uniqueOUList: any[]
  uniqueOSList: any[]
  processedData?: any
  stats: any
  resetFilters: () => void
  isSearching: boolean
  totalCount: number
  computersLength: number
  navigationState?: any
}

const FilterBar: FC<FilterBarProps> = ({ filters, setFilters, advancedFilters, setAdvancedFilters, showFilters, setShowFilters, activeFiltersInfo, uniqueOUList, uniqueOSList, processedData, stats, resetFilters, isSearching, totalCount, computersLength, navigationState }) => {
  return (
    <div className="filterbar-card">
      <div className="filterbar-header">
        <button className="filter-toggle" onClick={() => setShowFilters(!showFilters)}>
          <Filter className="filter-icon" />
          <span>Filtros Avançados</span>
          <ChevronDown className={`chev-icon ${showFilters ? 'chev-rotated' : ''}`} />
          {activeFiltersInfo.length > 0 && (
            <span className="active-count">{activeFiltersInfo.length} ativo{activeFiltersInfo.length > 1 ? 's' : ''}</span>
          )}
        </button>
      </div>

      <div className={`filter-collapse ${showFilters ? 'open' : 'closed'}`}>
        <div className="filter-grid">
          <div className="filter-cell">
            <label className="label">Status</label>
            <select value={filters.status} onChange={(e) => setFilters((prev:any) => ({ ...prev, status: e.target.value }))} className="select">
              <option value="all">Todos ({computersLength})</option>
              <option value="enabled">Ativadas ({stats.enabled})</option>
              <option value="disabled">Desativadas ({stats.disabled})</option>
            </select>
          </div>

          <div className="filter-cell">
            <label className="label">Unidade Organizacional {navigationState?.filterOU && (<span className="small-note">(filtro do dashboard)</span>)}</label>
            <select value={filters.ou} onChange={(e) => setFilters((prev:any) => ({ ...prev, ou: e.target.value }))} className={`select ${navigationState?.filterOU && filters.ou !== 'all' ? 'select-highlight' : ''}`}>
              <option value="all">Todas as OUs</option>
              {uniqueOUList.map(ou => (<option key={ou.code} value={ou.code}>{ou.name} ({ou.count})</option>))}
            </select>
          </div>

          <div className="filter-cell">
            <label className="label">Modelo</label>
            <select value={filters.model} onChange={(e) => setFilters((prev:any) => ({ ...prev, model: e.target.value }))} className="select">
              <option value="all">Todos os modelos</option>
              {(processedData?.uniqueModelList || []).map((m:any) => (<option key={m} value={m}>{m}</option>))}
            </select>
          </div>

          <div className="filter-cell">
            <label className="label">Último login</label>
            <select value={advancedFilters.lastLoginDays} onChange={(e) => setAdvancedFilters((prev:any) => ({ ...prev, lastLoginDays: e.target.value }))} className="select">
              <option value="all">Qualquer data</option>
              <option value="7">Últimos 7 dias</option>
              <option value="30">Até 30 dias</option>
              <option value="60">Até 60 dias</option>
              <option value="90">Até 90 dias</option>
              <option value="120+">120+ dias (possível remoção)</option>
            </select>
          </div>

          <div className="filter-cell">
            <label className="label">Inventário</label>
            <select value={advancedFilters.inventory} onChange={(e) => setAdvancedFilters((prev:any) => ({ ...prev, inventory: e.target.value }))} className="select">
              <option value="all">Todos</option>
              <option value="in_use">Em uso</option>
              <option value="spare">Spare</option>
            </select>
          </div>

          <div className="filter-cell">
            <label className="label">Atribuído a (usuário atual)</label>
            <input type="text" value={advancedFilters.assignedTo} onChange={(e) => setAdvancedFilters((prev:any) => ({ ...prev, assignedTo: e.target.value }))} placeholder="Nome ou email" className="input" />
          </div>

          <div className="filter-cell">
            <label className="label">Usuário anterior</label>
            <input type="text" value={advancedFilters.prevUser} onChange={(e) => setAdvancedFilters((prev:any) => ({ ...prev, prevUser: e.target.value }))} placeholder="Nome ou email" className="input" />
          </div>

          <div className="filter-cell">
            <label className="label">Sistema Operacional {navigationState?.filterOS && (<span className="small-note">(filtro do dashboard)</span>)}</label>
            <select value={filters.os} onChange={(e) => setFilters((prev:any) => ({ ...prev, os: e.target.value }))} className={`select ${navigationState?.filterOS && filters.os !== 'all' ? 'select-highlight' : ''}`}>
              <option value="all">Todos os SOs</option>
              {uniqueOSList.map((os:any) => (<option key={os} value={os}>{os}</option>))}
            </select>
          </div>

          <div className="filter-cell">
            <label className="label">Último Login {navigationState?.filterLastLogin && (<span className="small-note">(filtro do dashboard)</span>)}</label>
            <select value={filters.lastLogin} onChange={(e) => setFilters((prev:any) => ({ ...prev, lastLogin: e.target.value }))} className={`select ${navigationState?.filterLastLogin && filters.lastLogin !== 'all' ? 'select-highlight' : ''}`}>
              <option value="all">Todos</option>
              <option value="recent">Recente (7 dias) ({stats.recent})</option>
              <option value="moderate">Moderado (8-30 dias)</option>
              <option value="old">Antigo (31-90 dias) ({stats.old})</option>
              <option value="never">Nunca ({stats.never})</option>
            </select>
          </div>

          <div className="filter-cell">
            <label className="label">Garantia Dell {navigationState?.filterWarranty && (<span className="small-note">(filtro do dashboard)</span>)}</label>
            <select value={filters.warranty} onChange={(e) => setFilters((prev:any) => ({ ...prev, warranty: e.target.value }))} className={`select ${navigationState?.filterWarranty && filters.warranty !== 'all' ? 'select-highlight' : ''}`}>
              <option value="all">Todas</option>
              <option value="active">Ativa ({stats.warrantyActive})</option>
              <option value="expiring_30">Expirando 30 dias ({stats.warrantyExpiring30})</option>
              <option value="expiring_60">Expirando 60 dias ({stats.warrantyExpiring60})</option>
              <option value="expired">Expirada ({stats.warrantyExpired})</option>
              <option value="unknown">Desconhecida ({stats.warrantyUnknown})</option>
            </select>
          </div>
        </div>

        <div className="filter-actions">
          <button onClick={resetFilters} className="link-reset">Limpar Filtros</button>
          <div className="filter-summary">
            {isSearching && (
              <span className="searching"><Loader2 className="loader-icon" /> Pesquisando...</span>
            )}
            <span>Mostrando {totalCount} de {computersLength} máquinas</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default React.memo(FilterBar)
