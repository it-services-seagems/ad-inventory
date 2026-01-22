import React, { useState, useEffect, useRef } from 'react'
import { Search, Smartphone, CheckCircle, X } from 'lucide-react'
import api from '../services/api'

const SimpleIPhoneSelector = ({ 
  value = '', 
  onChange, 
  placeholder = "Digite o modelo do iPhone...",
  className = "",
  disabled = false 
}) => {
  const [inputValue, setInputValue] = useState(value)
  const [showDropdown, setShowDropdown] = useState(false)
  const [selectedModel, setSelectedModel] = useState(null)
  const [selectedColor, setSelectedColor] = useState('')
  const [selectedStorage, setSelectedStorage] = useState('')
  const [step, setStep] = useState('model')
  const [catalog, setCatalog] = useState([])
  const [filteredModels, setFilteredModels] = useState([])
  const [loading, setLoading] = useState(false)
  const [catalogLoaded, setCatalogLoaded] = useState(false)
  const inputRef = useRef(null)
  const dropdownRef = useRef(null)

  // Carregar catálogo apenas quando necessário (lazy loading)
  const loadCatalog = async () => {
    if (catalogLoaded || loading) return
    
    try {
      setLoading(true)
      const response = await api.get('/iphone-catalog/catalog')
      if (response.data?.success && response.data?.catalog) {
        setCatalog(response.data.catalog)
        setCatalogLoaded(true)
      }
    } catch (error) {
      console.error('Erro ao carregar catálogo:', error)
    } finally {
      setLoading(false)
    }
  }

  // Sincronizar valor externo
  useEffect(() => {
    setInputValue(value)
  }, [value])

  // Busca local no catálogo
  useEffect(() => {
    if (!catalog.length || step !== 'model') return

    if (!inputValue || inputValue.trim().length < 2) {
      setFilteredModels([])
      return
    }

    const searchTerm = inputValue.toLowerCase().trim()
    const filtered = catalog
      .filter(model => {
        const modelName = model.model.toLowerCase()
        return modelName.includes(searchTerm) || 
               modelName.includes(searchTerm.replace(/\s+/g, '')) ||
               searchTerm.includes('iphone') && modelName.includes('iphone')
      })
      .sort((a, b) => {
        const aExact = a.model.toLowerCase().startsWith(searchTerm)
        const bExact = b.model.toLowerCase().startsWith(searchTerm)
        if (aExact && !bExact) return -1
        if (!aExact && bExact) return 1
        return a.model.localeCompare(b.model)
      })
      .slice(0, 6)

    setFilteredModels(filtered)
  }, [inputValue, catalog, step])

  // Fechar dropdown ao clicar fora
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleInputChange = (e) => {
    if (step !== 'model') return
    
    const newValue = e.target.value
    setInputValue(newValue)
    setSelectedModel(null)
    
    if (newValue.trim().length > 1) {
      loadCatalog()
      setShowDropdown(true)
    } else {
      setShowDropdown(false)
    }
    
    if (onChange) {
      onChange(newValue)
    }
  }

  const handleSelectModel = (model) => {
    setSelectedModel(model)
    setInputValue(model.model)
    setShowDropdown(false)
    
    if (model.colors && model.colors.length > 1) {
      setStep('color')
    } else if (model.storages_gb && model.storages_gb.length > 1) {
      setSelectedColor(model.colors?.[0] || '')
      setStep('storage')
    } else {
      // Modelo sem opções, completar diretamente
      const finalModel = model.model
      setStep('complete')
      if (onChange) {
        onChange(finalModel, model)
      }
    }
  }

  const handleSelectColor = (color) => {
    setSelectedColor(color)
    
    if (selectedModel.storages_gb && selectedModel.storages_gb.length > 1) {
      setStep('storage')
    } else {
      // Só uma opção de armazenamento, completar
      const storage = selectedModel.storages_gb?.[0] || ''
      const finalModel = storage ? 
        `${selectedModel.model} ${storage}GB ${color}` : 
        `${selectedModel.model} ${color}`
      setInputValue(finalModel)
      setStep('complete')
      if (onChange) {
        onChange(finalModel, { ...selectedModel, selectedColor: color, selectedStorage: storage, finalModel })
      }
    }
  }

  const handleSelectStorage = (storage) => {
    setSelectedStorage(storage)
    const finalModel = `${selectedModel.model} ${storage}GB ${selectedColor}`
    setInputValue(finalModel)
    setStep('complete')
    
    if (onChange) {
      onChange(finalModel, {
        ...selectedModel,
        selectedColor,
        selectedStorage: storage,
        finalModel
      })
    }
  }

  const resetSelection = () => {
    setSelectedModel(null)
    setSelectedColor('')
    setSelectedStorage('')
    setStep('model')
    setInputValue('')
    if (onChange) {
      onChange('')
    }
  }

  const handleFocus = () => {
    if (step === 'model') {
      loadCatalog()
      if (inputValue && filteredModels.length > 0) {
        setShowDropdown(true)
      }
    }
  }

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={handleFocus}
          placeholder={placeholder}
          disabled={disabled}
          readOnly={step !== 'model'}
          className={`
            w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md 
            focus:ring-2 focus:ring-blue-500 focus:border-transparent
            ${disabled ? 'bg-gray-50 text-gray-500' : 'bg-white'}
            ${step === 'complete' ? 'border-green-500' : ''}
            ${step !== 'model' ? 'cursor-not-allowed bg-gray-50' : ''}
          `}
        />
        
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          {loading ? (
            <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full" />
          ) : (
            <Search className="h-4 w-4 text-gray-400" />
          )}
        </div>

        <div className="absolute inset-y-0 right-0 pr-3 flex items-center space-x-1">
          {step === 'complete' && (
            <CheckCircle className="h-4 w-4 text-green-500" />
          )}
          {(inputValue || selectedModel) && (
            <button
              type="button"
              onClick={resetSelection}
              className="p-0.5 rounded-full hover:bg-gray-100 transition-colors"
            >
              <X className="h-3 w-3 text-gray-400" />
            </button>
          )}
        </div>
      </div>

      {/* Progress indicator */}
      {selectedModel && (
        <div className="mt-2 text-xs space-y-1">
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-3 w-3 text-green-500" />
            <span className="text-green-700">Modelo: {selectedModel.model}</span>
          </div>
          {selectedColor && (
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-3 w-3 text-green-500" />
              <span className="text-green-700">Cor: {selectedColor}</span>
            </div>
          )}
          {selectedStorage && (
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-3 w-3 text-green-500" />
              <span className="text-green-700">Armazenamento: {selectedStorage}GB</span>
            </div>
          )}
        </div>
      )}

      {/* Dropdown para modelos */}
      {showDropdown && step === 'model' && filteredModels.length > 0 && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-auto">
          <div className="px-3 py-2 bg-gray-50 border-b border-gray-200">
            <span className="text-xs font-medium text-gray-700">
              {filteredModels.length} modelos encontrados
            </span>
          </div>
          {filteredModels.map((model, index) => {
            const currentYear = new Date().getFullYear()
            const isSupported = !model.support_end_year || model.support_end_year >= currentYear
            const yearsOld = currentYear - model.released_year
            
            return (
              <div
                key={index}
                onClick={() => handleSelectModel(model)}
                className="p-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{model.model}</div>
                    <div className="text-sm text-gray-500 flex items-center space-x-3 mt-1">
                      <span>Geração {model.generation}</span>
                      <span>•</span>
                      <span>{model.released_year} ({yearsOld} anos)</span>
                      <span>•</span>
                      <span className={`flex items-center ${
                        isSupported ? 'text-green-600' : 'text-red-600'
                      }`}>
                        <div className={`w-2 h-2 rounded-full mr-1 ${
                          isSupported ? 'bg-green-500' : 'bg-red-500'
                        }`}></div>
                        {isSupported ? 'Com suporte' : 'Sem suporte'}
                      </span>
                    </div>
                  </div>
                  <Smartphone className="w-4 h-4 text-gray-400" />
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Seleção de cores */}
      {step === 'color' && selectedModel?.colors && selectedModel.colors.length > 1 && (
        <div className="mt-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-3">
            Escolha a cor do {selectedModel.model}:
          </h4>
          <div className="grid grid-cols-2 gap-2">
            {selectedModel.colors.map((color, idx) => (
              <button
                key={idx}
                onClick={() => handleSelectColor(color)}
                className="p-2 text-sm bg-white border border-gray-200 rounded hover:border-blue-400 hover:bg-blue-50 transition-colors"
              >
                {color}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Seleção de armazenamento */}
      {step === 'storage' && selectedModel?.storages_gb && selectedModel.storages_gb.length > 1 && (
        <div className="mt-3 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h4 className="font-medium text-green-900 mb-3">
            Escolha o armazenamento:
          </h4>
          <div className="grid grid-cols-3 gap-2">
            {selectedModel.storages_gb.map((storage, idx) => (
              <button
                key={idx}
                onClick={() => handleSelectStorage(storage)}
                className="p-2 text-sm font-medium bg-white border border-gray-200 rounded hover:border-green-400 hover:bg-green-50 transition-colors"
              >
                {storage}GB
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default SimpleIPhoneSelector