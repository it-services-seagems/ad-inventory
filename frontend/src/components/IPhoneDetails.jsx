import React from 'react'
import { Smartphone, Palette, HardDrive, Calendar, Cpu } from 'lucide-react'

const IPhoneDetails = ({ model, className = "" }) => {
  if (!model) return null

  return (
    <div className={`bg-gray-50 border border-gray-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-center space-x-2 mb-3">
        <Smartphone className="w-5 h-5 text-blue-600" />
        <h4 className="font-semibold text-gray-900">Detalhes do {model.model}</h4>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Informações básicas */}
        <div className="space-y-2">
          <div className="flex items-center space-x-2 text-sm">
            <Cpu className="w-4 h-4 text-gray-500" />
            <span className="text-gray-600">Geração:</span>
            <span className="font-medium">{model.generation}</span>
          </div>
          <div className="flex items-center space-x-2 text-sm">
            <Calendar className="w-4 h-4 text-gray-500" />
            <span className="text-gray-600">Lançamento:</span>
            <span className="font-medium">{model.released_year}</span>
          </div>
        </div>

        {/* Cores disponíveis */}
        {model.colors && model.colors.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-sm">
              <Palette className="w-4 h-4 text-gray-500" />
              <span className="text-gray-600">Cores disponíveis:</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {model.colors.map((color, idx) => (
                <span 
                  key={idx}
                  className="text-xs bg-white text-gray-700 px-2 py-1 rounded border"
                >
                  {color}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Armazenamento disponível */}
        {model.storages_gb && model.storages_gb.length > 0 && (
          <div className="space-y-2 md:col-span-2">
            <div className="flex items-center space-x-2 text-sm">
              <HardDrive className="w-4 h-4 text-gray-500" />
              <span className="text-gray-600">Opções de armazenamento:</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {model.storages_gb.map((storage, idx) => (
                <span 
                  key={idx}
                  className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded"
                >
                  {storage}GB
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default IPhoneDetails