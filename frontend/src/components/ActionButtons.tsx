import React from 'react'
import { Link } from 'react-router-dom'
import { Eye, Loader2, Power } from 'lucide-react'
import './ActionButtons.css'

interface ActionButtonsProps {
  computer: any
  onToggle: (computer:any) => void
  loadingSet?: Set<any>
  setConfirmDialog?: (payload:any) => void
}

const ActionButtons: React.FC<ActionButtonsProps> = ({ computer, onToggle = () => {}, loadingSet = new Set(), setConfirmDialog = () => {} }) => {
  const loading = loadingSet.has(computer.name)

  return (
    <div className="actions-wrap">
      <Link to={`/computers/${computer.name}`} className="action-view" onClick={(e) => e.stopPropagation()}>
        <Eye className="icon-xsmall" /> Ver
      </Link>

      <button
        onClick={(e) => { e.stopPropagation(); setConfirmDialog({ open: true, computer, action: computer.isEnabled ? 'disable' : 'enable' }) }}
        disabled={loading}
        className={`action-toggle ${computer.isEnabled ? 'action-toggle--disable' : 'action-toggle--enable'}`}
      >
        {loading ? (<Loader2 className="icon-xsmall spin" />) : (<Power className="icon-xsmall" />)}
        <span className="action-label">{computer.isEnabled ? 'Desativar' : 'Ativar'}</span>
      </button>
    </div>
  )
}

export default ActionButtons
