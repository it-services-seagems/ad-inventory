import React from 'react'
import { Link } from 'react-router-dom'
import { CheckCircle, XCircle, Server, Monitor, Building2, Calendar, Eye, Loader2, Power, ArrowUpDown } from 'lucide-react'

const ComputersTable = ({ filteredComputers = [], formatDate, navigationState = {}, filters = {}, toggleStatusLoading = new Set(), statusMessages = new Map(), setConfirmDialog = () => {}, onOpenAssign = () => {}, onUnassign = () => {} }) => {
  return (
    <div className="overflow-x-auto max-h-[70vh] relative" style={{ scrollbarWidth: 'thin' }}>
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50 sticky top-0 z-10">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-20">Status</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Máquina</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Modelo</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">OU</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-40">Sistema Op.</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-36">Garantia Dell</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">Linha de Produto</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-40">Usuário Atual</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">Ações</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-32">Criado em</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {filteredComputers.map((computer) => {
            const WarrantyIcon = computer.warrantyStatus?.icon || (() => null)
            return (
              <tr
                key={computer.name}
                className="hover:bg-blue-50 transition-colors cursor-pointer group"
                onClick={() => window.location.href = `/computers/${computer.name}`}
                title={`Clique para ver detalhes de ${computer.name}`}
              >
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="flex items-center">
                    {computer.isEnabled ? (
                      <div className="flex items-center text-green-600">
                        <CheckCircle className="h-4 w-4 mr-1" />
                        <span className="text-xs font-medium">Ativa</span>
                      </div>
                    ) : (
                      <div className="flex items-center text-red-600">
                        <XCircle className="h-4 w-4 mr-1" />
                        <span className="text-xs font-medium">Inativa</span>
                      </div>
                    )}
                  </div>
                </td>

                <td className="px-4 py-3">
                  <div className="flex items-center">
                    {computer.ou?.code === 'CLOUD' || (computer.os && computer.os.toLowerCase().includes('server')) ? (
                      <Server className="h-4 w-4 text-gray-400 mr-2 flex-shrink-0" />
                    ) : (
                      <Monitor className="h-4 w-4 text-gray-400 mr-2 flex-shrink-0" />
                    )}
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-gray-900 truncate">{computer.name}</div>
                      {computer.description && (<div className="text-xs text-gray-500 truncate">{computer.description}</div>)}
                      {computer.dnsHostName && computer.dnsHostName !== computer.name && (<div className="text-xs text-blue-600 truncate">DNS: {computer.dnsHostName}</div>)}
                    </div>
                  </div>
                </td>

                <td className="px-4 py-3">
                  <div className="text-sm text-gray-900 truncate">{computer.model || computer.modelo || '—'}</div>
                </td>

                <td className="px-4 py-3 whitespace-nowrap">
                  <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${computer.ou?.bgColor || ''} ${computer.ou?.color || ''} ${navigationState?.filterOU && computer.ou?.code === filters.ou ? 'ring-2 ring-blue-300' : ''}`}>
                    <Building2 className="h-3 w-3 mr-1 flex-shrink-0" />
                    <span className="truncate">{computer.ou?.name}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1 truncate">{computer.ou?.code}</div>
                </td>

                <td className="px-4 py-3">
                  <div className={`text-sm ${navigationState?.filterOS && computer.os === filters.os ? 'text-blue-700 font-medium bg-blue-50 px-2 py-1 rounded' : 'text-gray-900'} truncate`}>{computer.os}</div>
                  {computer.osVersion && computer.osVersion !== 'N/A' && (<div className="text-xs text-gray-500 truncate">{computer.osVersion}</div>)}
                </td>

                <td className="px-4 py-3 whitespace-nowrap">
                  <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${computer.warrantyStatus?.bgColor || ''} ${computer.warrantyStatus?.color || ''} ${navigationState?.filterWarranty && computer.warrantyStatus?.status === filters.warranty ? 'ring-2 ring-blue-300' : ''}`}>
                    <WarrantyIcon className="h-3 w-3 mr-1 flex-shrink-0" />
                    <span className="truncate">{computer.warrantyStatus?.text}</span>
                  </div>
                  {computer.warranty && computer.warranty.warranty_end_date && (<div className="text-xs text-gray-500 mt-1 truncate">Expira: {formatDate(computer.warranty.warranty_end_date)}</div>)}
                  {(computer.warranty && (computer.warranty.product_line_description || computer.warranty.productLineDescription || computer.warranty.product_description || computer.warranty.system_description)) && (
                    <div className="text-xs text-gray-500 mt-1 truncate">Linha: {computer.warranty.product_line_description || computer.warranty.productLineDescription || computer.warranty.product_description || computer.warranty.system_description}</div>
                  )}
                </td>

                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="text-sm text-gray-900 truncate">
                    {(
                      computer.warranty?.product_line_description ||
                      computer.warranty?.productLineDescription ||
                      computer.product_line_description ||
                      computer.productLineDescription ||
                      computer.warranty?.system_description ||
                      '—'
                    )}
                  </div>
                </td>

                <td className="px-4 py-3">
                  <div className="text-sm text-gray-900 truncate">
                    {computer.currentUser ? (
                      <>
                        <div className="font-medium truncate">{computer.currentUser}</div>
                        {computer.previousUser && (
                          <div className="text-xs text-gray-500 truncate">
                            Anterior: {computer.previousUser}
                          </div>
                        )}
                      </>
                    ) : (
                      <span className="text-gray-400 italic text-xs">Usuário não identificado</span>
                    )}
                  </div>
                </td>

                <td className="px-4 py-3 whitespace-nowrap text-sm font-medium sticky right-32 bg-white group-hover:bg-blue-50">
                  <div className="flex items-center space-x-2">
                    <Link to={`/computers/${computer.name}`} className="inline-flex items-center text-blue-600 hover:text-blue-900 transition-colors text-xs" onClick={(e) => e.stopPropagation()}>
                      <Eye className="h-3 w-3 mr-1" /> Ver
                    </Link>
                    {/* Vincular/Desvincular removidos da listagem - usar detalhe da máquina */}
                    <button onClick={(e) => { e.stopPropagation(); setConfirmDialog({ open: true, computer, action: computer.isEnabled ? 'disable' : 'enable' }) }} disabled={toggleStatusLoading.has(computer.name)} className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium transition-colors ${computer.isEnabled ? 'bg-red-600 text-white hover:bg-red-700' : 'bg-green-600 text-white hover:bg-green-700'}`}>
                      {toggleStatusLoading.has(computer.name) ? (<Loader2 className="h-3 w-3 mr-1 animate-spin" />) : (<Power className="h-3 w-3 mr-1" />)}
                      <span>{computer.isEnabled ? 'Desativar' : 'Ativar'}</span>
                    </button>
                  </div>
                </td>

                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 sticky right-0 bg-white group-hover:bg-blue-50">
                  <div className="flex items-center">
                    <Calendar className="h-3 w-3 mr-1 flex-shrink-0" />
                    <span className="truncate">{formatDate(computer.created)}</span>
                  </div>
                  {statusMessages.get(computer.name) && (<div className="mt-1 text-xs"><span className={`${statusMessages.get(computer.name).type === 'success' ? 'text-green-600' : 'text-red-600'}`}>{statusMessages.get(computer.name).text}</span></div>)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default React.memo(ComputersTable)
