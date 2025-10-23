import React, { useEffect, useState } from 'react'
import { checkApiHealth } from '../services/api'

const ApiStatus = ({ pollInterval = 10000 }) => {
  const [status, setStatus] = useState({ isUp: null, lastChecked: null, lastEndpoint: null })

  const refresh = async () => {
    try {
      const res = await checkApiHealth()
      setStatus({ isUp: res.isUp, lastChecked: new Date().toISOString(), lastEndpoint: res.endpoint || null })
    } catch (err) {
      setStatus({ isUp: false, lastChecked: new Date().toISOString(), lastEndpoint: null })
    }
  }

  useEffect(() => {
    refresh()
    const t = setInterval(refresh, pollInterval)
    return () => clearInterval(t)
  }, [])

  if (status.isUp === null) return null

  return (
    <div className={`w-full text-center py-1 text-sm ${status.isUp ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
      {status.isUp ? (
        <span>API Backend: Conectada (último endpoint: {status.lastEndpoint || 'unknown'})</span>
      ) : (
        <span>API Backend: Indisponível - verificando... (última tentativa em {status.lastChecked})</span>
      )}
    </div>
  )
}

export default ApiStatus
