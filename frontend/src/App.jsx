import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Computers from './pages/Computers'
import ComputerDetail from './pages/ComputerDetail'
import './App.css'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/computers" element={<Computers />} />
            <Route path="/computers/:computerName" element={<ComputerDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App