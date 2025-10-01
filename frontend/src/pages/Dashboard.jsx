import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { Computer, Users, Clock, AlertTriangle, RefreshCw } from 'lucide-react'
import api from '../services/api'

const Dashboard = () => {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchStats = async () => {
    try {
      setLoading(true)
      const response = await api.get('/dashboard/stats')
      setStats(response.data)
      setError(null)
    } catch (err) {
      setError('Erro ao carregar estatísticas')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

  // Função para navegar para a página de computers com filtro de OS
  const handleOSClick = (osName) => {
    // Navegar para /computers e passar o filtro via state
    navigate('/computers', { 
      state: { 
        filterOS: osName,
        fromDashboard: true 
      } 
    })
  }

  // Função para navegar para computers com filtro de status
  const handleStatusClick = (status) => {
    let filterStatus = 'all'
    
    if (status === 'Ativas') {
      filterStatus = 'recent'
    } else if (status === 'Inativas') {
      filterStatus = 'old'
    }
    
    navigate('/computers', { 
      state: { 
        filterLastLogin: filterStatus,
        fromDashboard: true 
      } 
    })
  }

  // Custom tooltip para o gráfico de barras
  const CustomBarTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{label}</p>
          <p className="text-blue-600">
            <span className="font-medium">{payload[0].value}</span> máquinas
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Clique para filtrar na lista de computadores
          </p>
        </div>
      )
    }
    return null
  }

  // Custom tooltip para o gráfico de pizza
  const CustomPieTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{payload[0].name}</p>
          <p className="text-blue-600">
            <span className="font-medium">{payload[0].value}</span> máquinas
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Clique para filtrar na lista de computadores
          </p>
        </div>
      )
    }
    return null
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Carregando estatísticas...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <AlertTriangle className="h-5 w-5 text-red-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Erro</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
            <button
              onClick={fetchStats}
              className="mt-2 text-sm bg-red-100 text-red-800 px-3 py-1 rounded hover:bg-red-200"
            >
              Tentar novamente
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <button
          onClick={fetchStats}
          className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          <span>Atualizar</span>
        </button>
      </div>

      {/* Cards de Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div 
          className="bg-white p-6 rounded-lg shadow cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => navigate('/computers')}
        >
          <div className="flex items-center">
            <Computer className="h-12 w-12 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total de Máquinas</p>
              <p className="text-2xl font-bold text-gray-900">{stats?.totalComputers || 0}</p>
            </div>
          </div>
        </div>

        <div 
          className="bg-white p-6 rounded-lg shadow cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => handleStatusClick('Ativas')}
        >
          <div className="flex items-center">
            <Users className="h-12 w-12 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Login Recente</p>
              <p className="text-2xl font-bold text-gray-900">{stats?.recentLogins || 0}</p>
            </div>
          </div>
        </div>

        <div 
          className="bg-white p-6 rounded-lg shadow cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => handleStatusClick('Inativas')}
        >
          <div className="flex items-center">
            <Clock className="h-12 w-12 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Inativas</p>
              <p className="text-2xl font-bold text-gray-900">{stats?.inactiveComputers || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex items-center">
            <AlertTriangle className="h-12 w-12 text-red-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Taxa de Atividade</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats?.totalComputers ? Math.round((stats.recentLogins / stats.totalComputers) * 100) : 0}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gráfico de Barras - Sistemas Operacionais */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Distribuição por Sistema Operacional
          </h3>
          <p className="text-sm text-gray-500 mb-4">
            Clique em uma barra para filtrar na lista de computadores
          </p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart 
              data={stats?.osDistribution || []}
              onClick={(data) => {
                if (data && data.activeLabel) {
                  handleOSClick(data.activeLabel)
                }
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="name" 
                angle={-45}
                textAnchor="end"
                height={100}
                fontSize={12}
              />
              <YAxis />
              <Tooltip content={<CustomBarTooltip />} />
              <Bar 
                dataKey="value" 
                fill="#3B82F6"
                cursor="pointer"
                onClick={(data) => {
                  if (data && data.name) {
                    handleOSClick(data.name)
                  }
                }}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Gráfico de Pizza - Status de Atividade */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Status de Atividade
          </h3>
          <p className="text-sm text-gray-500 mb-4">
            Clique em uma seção para filtrar na lista de computadores
          </p>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={[
                  { name: 'Ativas', value: stats?.recentLogins || 0 },
                  { name: 'Inativas', value: stats?.inactiveComputers || 0 }
                ]}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                cursor="pointer"
                onClick={(data) => {
                  if (data && data.name) {
                    handleStatusClick(data.name)
                  }
                }}
              >
                {[
                  { name: 'Ativas', value: stats?.recentLogins || 0 },
                  { name: 'Inativas', value: stats?.inactiveComputers || 0 }
                ].map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomPieTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Informações adicionais */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <div className="flex">
          <Computer className="h-5 w-5 text-blue-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-blue-800">Dica de Navegação</h3>
            <div className="text-sm text-blue-700 mt-1 space-y-1">
              <p>• Clique nos cards de estatísticas para ir para a lista de computadores</p>
              <p>• Clique nas barras do gráfico de SO para filtrar por sistema operacional</p>
              <p>• Clique nas seções do gráfico de pizza para filtrar por status de atividade</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard