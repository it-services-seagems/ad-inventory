import React, { useState, useEffect, useRef } from 'react'
import { Search, Smartphone, CheckCircle, AlertCircle, X, Palette, HardDrive } from 'lucide-react'
import { useIPhoneCatalog } from '../services/iphoneCatalog'

const IPhoneModelSelector = ({ 
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
  const [step, setStep] = useState('model') // 'model', 'color', 'storage', 'complete'
  const [filteredModels, setFilteredModels] = useState([])
  const inputRef = useRef(null)
  const dropdownRef = useRef(null)

  // Caregar catálogo apenas uma vez
  const { catalog, loading: catalogLoading } = useIPhoneCatalog()

  // Efeito para sincronizar valor externo
  useEffect(() => {
    setInputValue(value)
  }, [value])

  // Busca local no catálogo
  useEffect(() => {
    if (!catalog || catalog.length === 0 || step !== 'model') return

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
               searchTerm.includes(modelName.split(' ')[0]) // busca por "iphone"
      })
      .sort((a, b) => {
        // Ordenar por relevância
        const aExact = a.model.toLowerCase().startsWith(searchTerm)
        const bExact = b.model.toLowerCase().startsWith(searchTerm)
        if (aExact && !bExact) return -1
        if (!aExact && bExact) return 1
        return a.model.localeCompare(b.model)
      })
      .slice(0, 8) // Limitar a 8 resultados para performance

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
    const newValue = e.target.value
    setInputValue(newValue)
    setSelectedModel(null)
    setShowDropdown(true)
    
    // Chamar onChange para valor livre
    if (onChange) {
      onChange(newValue)
    }
  }

  const handleSelectModel = (model) => {
    setSelectedModel(model)
    setInputValue(model.model)
    setShowDropdown(false)
    setStep('color')
    setSelectedColor('')
    setSelectedStorage('')
  }

  const handleSelectColor = (color) => {
    setSelectedColor(color)
    setStep('storage')
  }

  const handleSelectStorage = (storage) => {
    setSelectedStorage(storage)
    setStep('complete')
    
    // Construir nome final do modelo
    const finalModel = `${selectedModel.model} ${storage}GB ${selectedColor}`
    setInputValue(finalModel)
    
    if (onChange) {
      onChange(finalModel, {
        ...selectedModel,
        selectedColor: selectedColor,
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

  const clearSelection = () => {
    resetSelection()
    inputRef.current?.focus()
  }

  const handleFocus = () => {
    if (step === 'model' && inputValue && filteredModels.length > 0) {
      setShowDropdown(true)
    }
  }

  const ModelCard = ({ model, onClick, isHighlighted = false }) => (
    <div
      onClick={() => onClick(model)}
      className={`
        p-3 border-b border-gray-100 cursor-pointer transition-colors
        ${isHighlighted ? 'bg-blue-50 border-blue-200' : 'hover:bg-gray-50'}
      `}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <Smartphone className="w-4 h-4 text-gray-500" />
            <span className="font-medium text-gray-900">{model.model}</span>
            {model.score && (
              <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">
                {model.score}% match
              </span>
            )}
          </div>
          <div className="text-sm text-gray-500 mt-1">
            Lançado em {model.released_year} • Geração {model.generation}
          </div>
          {model.colors && model.colors.length > 0 && (
            <div className="flex items-center space-x-1 mt-2">
              <span className="text-xs text-gray-400">Cores:</span>
              {model.colors.slice(0, 4).map((color, idx) => (
                <span key={idx} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                  {color}
                </span>
              ))}
              {model.colors.length > 4 && (
                <span className="text-xs text-gray-400">+{model.colors.length - 4}</span>
              )}
            </div>
          )}
          {model.storages_gb && model.storages_gb.length > 0 && (
            <div className="flex items-center space-x-1 mt-1">
              <span className="text-xs text-gray-400">Armazenamento:</span>
              {model.storages_gb.map((storage, idx) => (
                <span key={idx} className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
                  {storage}GB
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )

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
        
        {/* Ícone de busca */}
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          {catalogLoading ? (
            <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full" />
          ) : (
            <Search className="h-4 w-4 text-gray-400" />
          )}
        </div>

        {/* Status icons */}
        <div className="absolute inset-y-0 right-0 pr-3 flex items-center space-x-1">
          {step === 'complete' && (
            <CheckCircle className="h-4 w-4 text-green-500" />
          )}
          {(inputValue || selectedModel) && (
            <button
              type="button"
              onClick={clearSelection}
              className="p-0.5 rounded-full hover:bg-gray-100 transition-colors"
            >
              <X className="h-3 w-3 text-gray-400" />
            </button>
          )}
        </div>
      </div>

      {/* Step indicator */}
      {selectedModel && (
        <div className="flex items-center mt-2 space-x-4 text-sm">
          <div className={`flex items-center space-x-1 ${step === 'model' ? 'text-blue-600' : 'text-green-600'}`}>
            <CheckCircle className="h-4 w-4" />
            <span>Modelo: {selectedModel.model}</span>
          </div>
          {step !== 'model' && (
            <div className={`flex items-center space-x-1 ${step === 'color' ? 'text-blue-600' : selectedColor ? 'text-green-600' : 'text-gray-400'}`}>
              <div className={`h-4 w-4 rounded-full border-2 ${selectedColor ? 'bg-green-500 border-green-500' : step === 'color' ? 'border-blue-500' : 'border-gray-300'}`}>
                {selectedColor && <CheckCircle className="h-4 w-4 text-white" />}
              </div>
              <span>Cor: {selectedColor || 'Selecione'}</span>
            </div>
          )}
          {(step === 'storage' || step === 'complete') && (
            <div className={`flex items-center space-x-1 ${step === 'storage' ? 'text-blue-600' : selectedStorage ? 'text-green-600' : 'text-gray-400'}`}>
              <div className={`h-4 w-4 rounded-full border-2 ${selectedStorage ? 'bg-green-500 border-green-500' : step === 'storage' ? 'border-blue-500' : 'border-gray-300'}`}>
                {selectedStorage && <CheckCircle className="h-4 w-4 text-white" />}
              </div>
              <span>Armazenamento: {selectedStorage ? `${selectedStorage}GB` : 'Selecione'}</span>
            </div>
          )}
        </div>
      )}

      {/* Dropdown para Modelo */}
      {showDropdown && step === 'model' && filteredModels.length > 0 && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-80 overflow-auto">
          <div className="px-3 py-2 bg-gray-50 border-b border-gray-200">
            <span className="text-xs font-medium text-gray-700 uppercase tracking-wide">
              Modelos encontrados ({filteredModels.length})
            </span>
          </div>
          {filteredModels.map((model, index) => (
            <ModelCard
              key={`model-${index}`}
              model={model}
              onClick={handleSelectModel}
              isHighlighted={index === 0}
            />
          ))}
        </div>
      )}

      {/* Mensagem quando não há resultados */}
      {showDropdown && step === 'model' && inputValue.length > 1 && filteredModels.length === 0 && !catalogLoading && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg p-4">
          <div className="text-center text-gray-500">
            <Smartphone className="h-8 w-8 mx-auto mb-2 text-gray-400" />
            <div className="text-sm">Nenhum modelo encontrado</div>
            <div className="text-xs text-gray-400 mt-1">
              Tente pesquisar por "iPhone 13", "SE", "Pro Max", etc.
            </div>
          </div>
        </div>
      )}

      {/* Seleção de Cor */}
      {step === 'color' && selectedModel && selectedModel.colors && (
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-3 flex items-center">
            <Smartphone className="h-4 w-4 mr-2" />
            Selecione a cor do {selectedModel.model}:
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {selectedModel.colors.map((color, idx) => (
              <button
                key={idx}
                onClick={() => handleSelectColor(color)}
                className="p-3 text-left bg-white border border-gray-200 rounded hover:border-blue-400 hover:bg-blue-50 transition-colors"
              >
                <span className="font-medium text-gray-900">{color}</span>
              </button>
            ))}
          </div>
          <button
            onClick={() => setStep('model')}
            className="mt-3 text-sm text-blue-600 hover:text-blue-800"
          >
            ← Voltar ao modelo
          </button>
        </div>
      )}

      {/* Seleção de Armazenamento */}
      {step === 'storage' && selectedModel && selectedModel.storages_gb && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h4 className="font-medium text-green-900 mb-3 flex items-center">
            <Smartphone className="h-4 w-4 mr-2" />
            Selecione o armazenamento do {selectedModel.model} {selectedColor}:
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {selectedModel.storages_gb.map((storage, idx) => (
              <button
                key={idx}
                onClick={() => handleSelectStorage(storage)}
                className="p-3 text-center bg-white border border-gray-200 rounded hover:border-green-400 hover:bg-green-50 transition-colors"
              >
                <span className="font-bold text-gray-900">{storage}GB</span>
              </button>
            ))}
          </div>
          <button
            onClick={() => setStep('color')}
            className="mt-3 text-sm text-green-600 hover:text-green-800"
          >
            ← Voltar à cor
          </button>
        </div>
      )}

      {/* Resumo Final */}
      {step === 'complete' && selectedModel && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-medium text-green-900 flex items-center">
                <CheckCircle className="h-4 w-4 mr-2" />
                Configuração Completa
              </h4>
              <p className="text-green-800 mt-1">
                <strong>{selectedModel.model}</strong> • {selectedColor} • {selectedStorage}GB
              </p>
            </div>
            <button
              onClick={resetSelection}
              className="text-green-600 hover:text-green-800 p-1"
              title="Resetar seleção"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default IPhoneModelSelector