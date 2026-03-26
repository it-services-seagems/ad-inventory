import React from 'react'
import OUStatsCard from './OUStatsCard'
import './OUStatsGrid.css'

interface OUStatsGridProps {
  data: { name: string; count: number; color?: string }[]
}

const OUStatsGrid: React.FC<OUStatsGridProps> = ({ data = [] }) => {
  return (
    <div className="ou-grid">
      {data.map((d) => (
        <OUStatsCard key={d.name} name={d.name} count={d.count} color={d.color} />
      ))}
    </div>
  )
}

export default OUStatsGrid
