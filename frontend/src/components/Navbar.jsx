import React, { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { BarChart3, Computer, Smartphone } from 'lucide-react'
import logo from '../assets/LogoSeagems.png'
import api from '../services/api'

const Navbar = () => {
  const location = useLocation()

  const navItems = [
    { path: '/dashboard', name: 'Dashboard', icon: BarChart3 },
    { path: '/computers', name: 'Máquinas', icon: Computer },
    { path: '/mobiles', name: 'Celulares', icon: Smartphone }
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
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar