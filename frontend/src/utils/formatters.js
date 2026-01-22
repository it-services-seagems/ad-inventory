// Utilitários para formatação de dados

/**
 * Formata número de celular brasileiro
 * Exemplo: "21987654321" -> "(21) 98765-4321"
 */
export const formatPhoneNumber = (number) => {
  if (!number) return ''
  
  // Remove todos os caracteres não numéricos
  const cleaned = number.replace(/\D/g, '')
  
  // Se tem 11 dígitos (celular com DDD)
  if (cleaned.length === 11) {
    return `(${cleaned.slice(0, 2)}) ${cleaned.slice(2, 7)}-${cleaned.slice(7)}`
  }
  
  // Se tem 10 dígitos (fixo com DDD) 
  if (cleaned.length === 10) {
    return `(${cleaned.slice(0, 2)}) ${cleaned.slice(2, 6)}-${cleaned.slice(6)}`
  }
  
  // Se tem apenas 9 dígitos (celular sem DDD)
  if (cleaned.length === 9) {
    return `${cleaned.slice(0, 5)}-${cleaned.slice(5)}`
  }
  
  // Se tem apenas 8 dígitos (fixo sem DDD)
  if (cleaned.length === 8) {
    return `${cleaned.slice(0, 4)}-${cleaned.slice(4)}`
  }
  
  // Retorna como está se não se encaixa nos padrões
  return cleaned
}

/**
 * Remove formatação de número de telefone
 * Exemplo: "(21) 98765-4321" -> "21987654321"
 */
export const unformatPhoneNumber = (formatted) => {
  if (!formatted) return ''
  return formatted.replace(/\D/g, '')
}

/**
 * Máscara de entrada para número de telefone
 */
export const phoneNumberMask = (value) => {
  const cleaned = value.replace(/\D/g, '')
  
  if (cleaned.length <= 2) {
    return cleaned
  } else if (cleaned.length <= 7) {
    return `(${cleaned.slice(0, 2)}) ${cleaned.slice(2)}`
  } else if (cleaned.length <= 11) {
    return `(${cleaned.slice(0, 2)}) ${cleaned.slice(2, 7)}-${cleaned.slice(7)}`
  }
  
  return `(${cleaned.slice(0, 2)}) ${cleaned.slice(2, 7)}-${cleaned.slice(7, 11)}`
}