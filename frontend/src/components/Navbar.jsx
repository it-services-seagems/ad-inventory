import React, { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { BarChart3, Computer, Bell } from 'lucide-react'
import logo from '../assets/LogoSeagems.png'
import api from '../services/api'

const Navbar = () => {
  const location = useLocation()

  const navItems = [
    { path: '/dashboard', name: 'Dashboard', icon: BarChart3 },
    { path: '/computers', name: 'Máquinas', icon: Computer }
  ]

  return (
    <nav className="shadow-lg border-b" style={{ backgroundColor: '#073776' }}>
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <img src={logo} alt="Logo" className="h-8 w-auto" />
            <span className="text-xl font-bold text-white">Gerenciador AD</span>
          </div>

          <div className="flex items-center space-x-4">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${isActive ? 'bg-white bg-opacity-10 text-white font-medium' : 'text-white hover:bg-white hover:bg-opacity-10'}`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.name}</span>
                </Link>
              )
            })}

            {/* Notification bell (reads /notifications/unread-count) */}
            <NotificationBell />
          </div>
        </div>
      </div>
    </nav>
  )
}

const NotificationBell = () => {
  const [count, setCount] = useState(0)

  useEffect(() => {
    let mounted = true
    const fetchCount = async () => {
      try {
        const resp = await api.get('/notifications/unread-count')
        if (mounted && resp?.data?.count != null) setCount(resp.data.count)
      } catch (e) {
        // endpoint may not exist yet — keep count at 0
        if (mounted) setCount(0)
      }
    }
    fetchCount()
    const t = setInterval(fetchCount, 60000)
    return () => { mounted = false; clearInterval(t) }
  }, [])

  return (
    <div className="relative">
      <Bell className="h-5 w-5 text-white" />
      <span className="absolute -top-1 -right-1 bg-red-600 text-white text-xs rounded-full px-1">{count}</span>
    </div>
  )
}

export default Navbar