import api from '../services/api'

// Lightweight service for network side-effects used by the Computers page.
// Functions return raw results; callers should set React state as needed.

export async function fetchComputersFromServer(inventoryFilter: string | null = null) {
  try {
    let sqlUrl = '/computers?source=sql'
    if (inventoryFilter) sqlUrl += `&inventory_filter=${inventoryFilter}`

    const sqlResponse = await api.get(sqlUrl)
    if (sqlResponse.data && Array.isArray(sqlResponse.data)) {
      return { computerData: sqlResponse.data, dataSource: 'sql' }
    }

    if (sqlResponse.data && sqlResponse.data.computers && Array.isArray(sqlResponse.data.computers)) {
      return { computerData: sqlResponse.data.computers, dataSource: 'sql' }
    }

    // If SQL returned unexpected format, fall through to AD
    throw new Error('SQL returned unexpected format')
  } catch (sqlError) {
    // Fallback to AD
    try {
      const adResponse = await api.get('/computers?source=ad')
      if (adResponse.data && Array.isArray(adResponse.data)) {
        return { computerData: adResponse.data, dataSource: 'ad' }
      }
      throw new Error('AD returned unexpected format')
    } catch (adError) {
      const err = new Error('Both SQL and AD failed')
      // attach inner errors for debugging
      ;(err as any).sqlError = sqlError
      ;(err as any).adError = adError
      throw err
    }
  }
}

export async function fetchWarrantySummary() {
  try {
    const response = await api.get('/computers/warranty-summary')
    // New structured response expected
    if (response.data && (response.data.with_warranty_data !== undefined || Array.isArray(response.data))) {
      return response.data
    }

    // Unexpected shape, return raw
    return response.data
  } catch (error: any) {
    // Try legacy endpoint fallback if 404
    if (error?.response?.status === 404) {
      try {
        const legacy = await api.get('/computers/warranty-summary-legacy')
        return legacy.data
      } catch (legacyErr) {
        throw legacyErr
      }
    }
    throw error
  }
}

export async function startWarrantyRefresh() {
  const response = await api.post('/computers/warranty-refresh')
  return response.data
}

export async function pollWarrantyRefreshStatus(jobId: string) {
  const response = await api.get(`/computers/warranty-refresh/${encodeURIComponent(jobId)}`)
  return response.data
}

export async function checkForRunningJobFromStorage() {
  try {
    const storedJobId = localStorage.getItem('warranty_job_id')
    const storedJobStart = localStorage.getItem('warranty_job_start')
    if (!storedJobId) return null

    const jobStartTime = parseInt(storedJobStart || '') || Date.now()
    const twoHoursAgo = Date.now() - (2 * 60 * 60 * 1000)
    if (jobStartTime < twoHoursAgo) {
      localStorage.removeItem('warranty_job_id')
      localStorage.removeItem('warranty_job_start')
      return null
    }

    const resp = await api.get(`/computers/warranty-refresh/${encodeURIComponent(storedJobId)}`)
    const jobData = resp.data
    if (jobData && (jobData.status === 'running' || jobData.status === 'pending')) return jobData

    // not running -> cleanup
    localStorage.removeItem('warranty_job_id')
    localStorage.removeItem('warranty_job_start')
    return null
  } catch (error: any) {
    if (error?.response?.status === 404) {
      localStorage.removeItem('warranty_job_id')
      localStorage.removeItem('warranty_job_start')
      return null
    }
    throw error
  }
}

export async function testBackendConnectivity() {
  try {
    await api.get('/computers/warranty-debug')
    return true
  } catch (error) {
    return false
  }
}

export default {
  fetchComputersFromServer,
  fetchWarrantySummary,
  startWarrantyRefresh,
  pollWarrantyRefreshStatus,
  checkForRunningJobFromStorage,
  testBackendConnectivity
}
