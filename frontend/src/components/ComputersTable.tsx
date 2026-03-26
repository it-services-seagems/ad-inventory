import React, { FC } from 'react'
import { Link } from 'react-router-dom'
import { CheckCircle, XCircle, Server, Monitor, Building2, Calendar, Eye, Loader2, Power } from 'lucide-react'
import './ComputersTable.css'
import ComputerRow from './ComputerRow'

interface ComputersTableProps {
  filteredComputers?: any[]
  formatDate?: (d: any) => string
  navigationState?: any
  filters?: any
  toggleStatusLoading?: Set<any>
  statusMessages?: Map<any, any>
  setConfirmDialog?: (arg0: any) => void
  onOpenAssign?: (...args: any[]) => void
  onUnassign?: (...args: any[]) => void
  beforeHeight?: number
  afterHeight?: number
  startIndex?: number
}

const ComputersTable: FC<ComputersTableProps> = ({ filteredComputers = [], formatDate = (d:any) => d ? new Date(d).toLocaleDateString('pt-BR') : '—', navigationState = {}, filters = {}, toggleStatusLoading = new Set(), statusMessages = new Map(), setConfirmDialog = () => {}, onOpenAssign = () => {}, onUnassign = () => {}, beforeHeight = 0, afterHeight = 0, startIndex = 0 }) => {
  return (
    <div className="computers-table-wrapper" style={{ scrollbarWidth: 'thin' }}>
      <table className="computers-table">
        <thead className="computers-thead">
          <tr>
            <th className="computers-th computers-th--status">Status</th>
            <th className="computers-th">Máquina</th>
            <th className="computers-th">Modelo</th>
            <th className="computers-th computers-th--ou">OU</th>
            <th className="computers-th computers-th--os">Sistema Op.</th>
            <th className="computers-th computers-th--warranty">Garantia Dell</th>
            <th className="computers-th computers-th--product">Linha de Produto</th>
            <th className="computers-th computers-th--user">Usuário Atual</th>
            <th className="computers-th computers-th--actions">Ações</th>
            <th className="computers-th computers-th--created">Criado em</th>
          </tr>
        </thead>
        <tbody className="computers-tbody">
          {typeof (beforeHeight) === 'number' && beforeHeight > 0 && (
            <tr style={{ height: `${beforeHeight}px` }}>
              <td colSpan={10} className="p-0"></td>
            </tr>
          )}

          {filteredComputers.map((computer, idx) => (
            <ComputerRow
              key={computer.name}
              computer={{ ...computer, index: (startIndex || 0) + idx }}
              formatDate={formatDate}
              navigationState={navigationState}
              filters={filters}
              toggleStatusLoading={toggleStatusLoading}
              statusMessages={statusMessages}
              setConfirmDialog={setConfirmDialog}
              onOpenAssign={onOpenAssign}
              onUnassign={onUnassign}
            />
          ))}

          {typeof (afterHeight) === 'number' && afterHeight > 0 && (
            <tr style={{ height: `${afterHeight}px` }}>
              <td colSpan={10} className="p-0"></td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

export default React.memo(ComputersTable)
