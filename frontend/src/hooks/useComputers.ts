import { useCallback, useMemo } from 'react'

interface UseComputersParams {
  processedData: any
  deferredSearchTerm: string
  filters: any
  navigationState: any
  sortConfig: any
  setSortConfig: (c:any) => void
  advancedFilters: any
  visibleRange: { start:number, end:number }
  VIRTUAL_ROW_HEIGHT: number
  VIRTUAL_OVERSCAN: number
  setTotalCount?: (n:number) => void
}

export default function useComputers({ processedData, deferredSearchTerm, filters, navigationState, sortConfig, setSortConfig, advancedFilters, visibleRange, VIRTUAL_ROW_HEIGHT, VIRTUAL_OVERSCAN, setTotalCount }: UseComputersParams) {
  const getSortValue = useCallback((computer:any, key:string) => {
    switch (key) {
      case 'name': return computer.name?.toLowerCase() || ''
      case 'ou': return computer.ou?.name?.toLowerCase() || ''
      case 'os': return computer.os?.toLowerCase() || ''
      case 'warranty': return computer.warrantyStatus?.sortValue || 999999
      case 'lastLogin': return computer.loginStatus?.sortValue || 999999
      case 'currentUser': return computer.currentUser?.toLowerCase() || 'zzz'
      case 'status': return computer.isEnabled ? 0 : 1
      case 'created': return computer.created ? new Date(computer.created).getTime() : 0
      case 'model': return (computer.model || computer.modelo || '').toLowerCase()
      default: return ''
    }
  }, [])

  const handleSort = useCallback((key:string) => {
    setSortConfig((prevConfig:any) => ({ key, direction: prevConfig.key === key && prevConfig.direction === 'asc' ? 'desc' : 'asc' }))
  }, [setSortConfig])

  const filteredComputers = useMemo(() => {
    if (!processedData) return []
    const hasSearch = deferredSearchTerm.trim().length > 0
    const hasFilters = Object.values(filters || {}).some((f:any) => f !== 'all')
    let filtered = processedData.computersWithIndex.slice()

    if (hasSearch || hasFilters) {
      const searchLower = deferredSearchTerm.toLowerCase()
      filtered = processedData.computersWithIndex.filter((computer:any) => {
        if (hasSearch && !computer.searchableText.includes(searchLower)) return false
        if (filters.status !== 'all') {
          if (filters.status === 'enabled' && !computer.isEnabled) return false
          if (filters.status === 'disabled' && computer.isEnabled) return false
        }
        if (filters.os !== 'all') {
          if (navigationState && navigationState.filterOS === filters.os) {
            if (computer.os !== filters.os) return false
          } else {
            if (!computer.os.toLowerCase().includes(filters.os.toLowerCase())) return false
          }
        }
        if (filters.lastLogin !== 'all' && computer.loginStatus?.status !== filters.lastLogin) return false
        if (filters.ou !== 'all' && computer.ou?.code !== filters.ou) return false
        if (filters.warranty !== 'all' && computer.warrantyStatus?.status !== filters.warranty) return false
        if (filters.model !== 'all') {
          const modelValue = (computer.model || computer.modelo || '').toLowerCase()
          if (!modelValue.includes(String(filters.model).toLowerCase())) return false
        }

        if (advancedFilters.lastLoginDays && advancedFilters.lastLoginDays !== 'all') {
          const val = advancedFilters.lastLoginDays
          const lastLogon = computer.lastLogon ? new Date(computer.lastLogon) : null
          const diffDays = lastLogon ? Math.floor((Date.now() - lastLogon.getTime()) / (1000 * 60 * 60 * 24)) : null
          if (val === '7' && (diffDays === null || diffDays > 7)) return false
          if (val === '30' && (diffDays === null || diffDays > 30)) return false
          if (val === '60' && (diffDays === null || diffDays > 60)) return false
          if (val === '90' && (diffDays === null || diffDays > 90)) return false
          if (val === '120+' && (diffDays === null || diffDays < 120)) return false
        }

        return true
      })
    }

    // Apply sort
    filtered.sort((a:any,b:any) => {
      const aValue = getSortValue(a, sortConfig.key)
      const bValue = getSortValue(b, sortConfig.key)
      let comparison = 0
      if (typeof aValue === 'string' && typeof bValue === 'string') comparison = aValue.localeCompare(bValue)
      else if (typeof aValue === 'number' && typeof bValue === 'number') comparison = aValue - bValue
      else comparison = String(aValue).localeCompare(String(bValue))
      return sortConfig.direction === 'asc' ? comparison : -comparison
    })

    return filtered
  }, [processedData, deferredSearchTerm, filters, navigationState, sortConfig, getSortValue, advancedFilters])

  const virtualizedComputers = useMemo(() => {
    if (!filteredComputers.length) return { visible: [], total: 0, startIndex: 0, beforeHeight: 0, afterHeight: 0 }
    const total = filteredComputers.length
    if (typeof setTotalCount === 'function') setTotalCount(total)
    if (total > 100) {
      const start = Math.max(0, visibleRange.start - VIRTUAL_OVERSCAN)
      const end = Math.min(total, visibleRange.end + VIRTUAL_OVERSCAN)
      const beforeHeight = start * VIRTUAL_ROW_HEIGHT
      const afterHeight = Math.max(0, total - end) * VIRTUAL_ROW_HEIGHT
      return { visible: filteredComputers.slice(start, end), total, startIndex: start, beforeHeight, afterHeight }
    }
    return { visible: filteredComputers, total, startIndex: 0, beforeHeight: 0, afterHeight: 0 }
  }, [filteredComputers, visibleRange, VIRTUAL_OVERSCAN, VIRTUAL_ROW_HEIGHT, setTotalCount])

  return { filteredComputers, virtualizedComputers, handleSort, getSortValue }
}
