import React, { memo } from 'react'
import { CheckCircle, XCircle, Server, Monitor, Building2, Calendar } from 'lucide-react'
import './ComputersTable.css'
import ActionButtons from './ActionButtons'
import './ActionButtons.css'

interface ComputerRowProps {
  computer: any
  formatDate: (d:any) => string
  navigationState?: any
  filters?: any
  toggleStatusLoading?: Set<any>
  statusMessages?: Map<any, any>
  setConfirmDialog?: (arg0:any) => void
  onOpenAssign?: (...args:any[]) => void
  onUnassign?: (...args:any[]) => void
}

const ComputerRow = ({ computer, formatDate, navigationState = {}, filters = {}, toggleStatusLoading = new Set(), statusMessages = new Map(), setConfirmDialog = () => {}, onOpenAssign = () => {}, onUnassign = () => {} }: ComputerRowProps) => {
  const WarrantyIcon = computer.warrantyStatus?.icon || (() => null)

  const handleRowClick = () => {
    window.location.href = `/computers/${computer.name}`
  }

  return (
    <tr className="computers-row" onClick={handleRowClick} title={`Clique para ver detalhes de ${computer.name}`}>
      <td className="computers-td computers-td--status">
        <div className="status-wrap">
          {computer.isEnabled ? (
            <div className="status status--active">
              <CheckCircle className="icon-sm" />
              <span className="status-label">Ativa</span>
            </div>
          ) : (
            <div className="status status--inactive">
              <XCircle className="icon-sm" />
              <span className="status-label">Inativa</span>
            </div>
          )}
        </div>
      </td>

      <td className="computers-td computers-td--machine">
        <div className="machine-wrap">
          {computer.ou?.code === 'CLOUD' || (computer.os && computer.os.toLowerCase().includes('server')) ? (
            <Server className="icon-sm icon-muted" />
          ) : (
            <Monitor className="icon-sm icon-muted" />
          )}
          <div className="machine-info">
            <div className="machine-name">{computer.name}</div>
            {computer.description && (<div className="machine-desc">{computer.description}</div>)}
            {computer.dnsHostName && computer.dnsHostName !== computer.name && (<div className="machine-dns">DNS: {computer.dnsHostName}</div>)}
          </div>
        </div>
      </td>

      <td className="computers-td computers-td--model">
        <div className="model-text">{computer.model || computer.modelo || '—'}</div>
      </td>

      <td className="computers-td computers-td--ou">
        <div className={`ou-badge ${computer.ou?.bgColor || ''} ${computer.ou?.color || ''} ${navigationState?.filterOU && computer.ou?.code === filters.ou ? 'ou-badge--highlight' : ''}`}>
          <Building2 className="icon-xsmall" />
          <span className="ou-name">{computer.ou?.name}</span>
        </div>
        <div className="ou-code">{computer.ou?.code}</div>
      </td>

      <td className="computers-td computers-td--os">
        <div className={`os-text ${navigationState?.filterOS && computer.os === filters.os ? 'os-text--active' : ''}`}>{computer.os}</div>
        {computer.osVersion && computer.osVersion !== 'N/A' && (<div className="os-version">{computer.osVersion}</div>)}
      </td>

      <td className="computers-td computers-td--warranty">
        <div className={`warranty-badge ${computer.warrantyStatus?.bgColor || ''} ${computer.warrantyStatus?.color || ''} ${navigationState?.filterWarranty && computer.warrantyStatus?.status === filters.warranty ? 'warranty-badge--highlight' : ''}`}>
          <WarrantyIcon className="icon-xsmall" />
          <span className="warranty-text">{computer.warrantyStatus?.text}</span>
        </div>
        {computer.warranty && computer.warranty.warranty_end_date && (<div className="warranty-expire">Expira: {formatDate(computer.warranty.warranty_end_date)}</div>)}
        {(computer.warranty && (computer.warranty.product_line_description || computer.warranty.productLineDescription || computer.warranty.product_description || computer.warranty.system_description)) && (
          <div className="warranty-line">Linha: {computer.warranty.product_line_description || computer.warranty.productLineDescription || computer.warranty.product_description || computer.warranty.system_description}</div>
        )}
      </td>

      <td className="computers-td computers-td--product">
        <div className="product-text">{(
          computer.warranty?.product_line_description ||
          computer.warranty?.productLineDescription ||
          computer.product_line_description ||
          computer.productLineDescription ||
          computer.warranty?.system_description ||
          '—'
        )}</div>
      </td>

      <td className="computers-td computers-td--user">
        <div className="user-text">
          {(computer.currentUser) ? (
            <>
              <div className="user-current">{computer.currentUser}</div>
              {computer.previousUser && (<div className="user-previous">Anterior: {computer.previousUser}</div>)}
            </>
          ) : (
            <span className="user-empty">Usuário não identificado</span>
          )}
        </div>
      </td>

      <td className="computers-td computers-td--actions sticky-right">
        <ActionButtons
          computer={computer}
          loadingSet={toggleStatusLoading}
          setConfirmDialog={setConfirmDialog}
        />
      </td>

      <td className="computers-td computers-td--created sticky-right">
        <div className="created-wrap">
          <Calendar className="icon-xsmall" />
          <span className="created-text">{formatDate(computer.created)}</span>
        </div>
        {statusMessages.get(computer.name) && (<div className="created-status"><span className={`${statusMessages.get(computer.name).type === 'success' ? 'created-success' : 'created-error'}`}>{statusMessages.get(computer.name).text}</span></div>)}
      </td>
    </tr>
  )
}

export default memo(ComputerRow)
