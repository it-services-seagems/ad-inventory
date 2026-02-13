import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Computers from './pages/Computers'
import ComputerDetail from './pages/ComputerDetail'
import Mobiles from './pages/Mobiles'
import MobileDetail from './pages/MobileDetail'
import './App.css'

function App() {
  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <Navbar />
        <main className="flex-1 w-full">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<div className="w-full px-4 py-8"><Dashboard /></div>} />
            <Route path="/computers" element={<div className="w-full px-4 py-8"><Computers /></div>} />
            <Route path="/computers/:computerName" element={<div className="w-full px-4 py-8"><ComputerDetail /></div>} />
            <Route path="/mobiles" element={<div className="w-full py-8"><Mobiles /></div>} />
            <Route path="/mobiles/:mobileId" element={<div className="w-full py-8"><MobileDetail /></div>} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App