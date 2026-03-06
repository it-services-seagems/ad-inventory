import React, { useState, useEffect } from 'react'
import SimpleIPhoneSelector from './SimpleIPhoneSelector'
import { formatPhoneNumber, unformatPhoneNumber, phoneNumberMask } from '../utils/formatters'
import api from '../services/api'

const IphoneModal = ({ open, mode = 'add', initialData = null, onClose = () => {}, onSaved = () => {}, onDeleted = () => {}, funcionarios = [], funcionariosCompletos = [], fetchFuncionarios = null }) => {
  const [form, setForm] = useState({
    model: '', brand: '', imei: '', departamento: '', tipo: '', number: '', eid: '', funcionario_nome: ''
  })
  const [inputMode, setInputMode] = useState('search')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (mode === 'edit' && initialData) {
      setForm({
        model: initialData.model || initialData.modelo || '',
        brand: initialData.brand || initialData.marca || '',
        imei: initialData.imei || '',
        departamento: initialData.departamento || initialData.secao_atual_descricao || '',
        tipo: initialData.tipo || '',
        number: initialData.number || initialData.numero || '',
        eid: initialData.eid || '',
        funcionario_nome: initialData.funcionario_nome || ''
      })
      setInputMode('search')
    }

    if (mode === 'add') {
      setForm({ model: '', brand: '', imei: '', departamento: '', tipo: '', number: '', eid: '', funcionario_nome: '' })
      setInputMode('search')
    }
  }, [mode, initialData, open])

  if (!open) return null

  const handlePhoneChange = (value) => {
    const masked = phoneNumberMask(value)
    setForm({...form, number: masked})
  }

  const handleSave = async (e) => {
    e && e.preventDefault()
    try {
      setLoading(true)
      const payload = {
        model: form.model,
        brand: form.brand,
        imei: form.imei,
        departamento: form.departamento,
        tipo: form.tipo,
        number: unformatPhoneNumber(form.number),
        eid: form.eid,
        funcionario_nome: form.funcionario_nome
      }

      if (mode === 'add') {
        await api.post('/mobiles/', payload)
      } else if (mode === 'edit' && initialData && initialData.id) {
        await api.put(`/mobiles/${initialData.id}`, payload)
      }

      onSaved()
      onClose()
    } catch (err) {
      console.error('Erro ao salvar iPhone:', err)
      alert('Erro ao salvar: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!initialData || !initialData.id) return
    try {
      setLoading(true)
      await api.delete(`/mobiles/${initialData.id}`)
      onDeleted()
      onClose()
    } catch (err) {
      console.error('Erro ao deletar iPhone:', err)
      alert('Erro ao deletar: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-auto">
        {mode === 'confirm-delete' ? (
          <>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Confirmar exclusão</h3>
            <p>Você tem certeza que deseja excluir este aparelho <strong>{initialData?.model || ''}</strong> (ID: {initialData?.id})?</p>
            <div className="flex justify-end space-x-3 pt-6">
              <button onClick={onClose} className="px-4 py-2 bg-gray-100 rounded">Cancelar</button>
              <button onClick={handleDelete} disabled={loading} className="px-4 py-2 bg-red-600 text-white rounded">{loading ? 'Excluindo...' : 'Confirmar exclusão'}</button>
            </div>
          </>
        ) : (
          <>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{mode === 'add' ? 'Adicionar Novo Aparelho' : 'Editar Aparelho'}</h3>
            <form onSubmit={handleSave} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Modelo *</label>
                  <SimpleIPhoneSelector
                    value={form.model}
                    onChange={(value, modelData) => {
                      setForm({ ...form, model: value, brand: modelData?.finalModel && value.toLowerCase().includes('iphone') ? 'Apple' : form.brand })
                    }}
                    placeholder="Digite o modelo do aparelho"
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Marca</label>
                  <input value={form.brand} onChange={e => setForm({...form, brand: e.target.value})} className="w-full p-3 border border-gray-300 rounded-md" />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Funcionário</label>
                  <div className="flex space-x-4 mb-3">
                    <label className="flex items-center">
                      <input type="radio" name="inputMode" value="search" checked={inputMode === 'search'} onChange={(e) => setInputMode(e.target.value)} className="mr-2" /> Buscar no PortalRH
                    </label>
                    <label className="flex items-center">
                      <input type="radio" name="inputMode" value="manual" checked={inputMode === 'manual'} onChange={(e) => setInputMode(e.target.value)} className="mr-2" /> Entrada Manual
                    </label>
                  </div>
                  {inputMode === 'search' ? (
                    <select value={form.funcionario_nome} onChange={e => setForm({...form, funcionario_nome: e.target.value})} className="w-full p-3 border border-gray-300 rounded-md">
                      <option value="">— Selecione o funcionário —</option>
                      {funcionarios.map(f => <option key={f} value={f}>{f}</option>)}
                    </select>
                  ) : (
                    <input value={form.funcionario_nome} onChange={e => setForm({...form, funcionario_nome: e.target.value})} className="w-full p-3 border border-gray-300 rounded-md" />
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Número</label>
                  <input value={form.number} onChange={e => {
                    const masked = phoneNumberMask(e.target.value)
                    setForm({...form, number: masked})
                  }} className="w-full p-3 border border-gray-300 rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
                  <input value={form.tipo} onChange={e => setForm({...form, tipo: e.target.value})} className="w-full p-3 border border-gray-300 rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">EID</label>
                  <input value={form.eid} onChange={e => setForm({...form, eid: e.target.value})} className="w-full p-3 border border-gray-300 rounded-md" />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">IMEI</label>
                  <input value={form.imei} onChange={e => setForm({...form, imei: e.target.value})} className="w-full p-3 border border-gray-300 rounded-md" />
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200 mt-6">
                <button type="button" onClick={onClose} className="flex items-center px-4 py-2.5 text-gray-700 bg-gray-100 rounded-lg">Cancelar</button>
                <button type="submit" disabled={loading} className="flex items-center px-4 py-2.5 bg-green-600 text-white rounded-lg">{loading ? 'Salvando...' : (mode === 'add' ? 'Salvar Aparelho' : 'Salvar alterações')}</button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  )
}

export default IphoneModal
