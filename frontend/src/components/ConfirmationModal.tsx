import React from 'react'
import './ConfirmationModal.css'

interface ConfirmationModalProps {
  open: boolean
  title?: string
  message?: string
  onConfirm?: () => void
  onCancel?: () => void
}

const ConfirmationModal: React.FC<ConfirmationModalProps> = ({ open, title = 'Confirmar', message = '', onConfirm = () => {}, onCancel = () => {} }) => {
  if (!open) return null
  return (
    <div className="cm-backdrop">
      <div className="cm-modal">
        <h3 className="cm-title">{title}</h3>
        <div className="cm-body">{message}</div>
        <div className="cm-actions">
          <button className="cm-btn cm-cancel" onClick={onCancel}>Cancelar</button>
          <button className="cm-btn cm-confirm" onClick={onConfirm}>Confirmar</button>
        </div>
      </div>
    </div>
  )
}

export default ConfirmationModal
