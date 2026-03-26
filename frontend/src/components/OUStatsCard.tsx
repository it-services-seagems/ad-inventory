import React from 'react'
import './OUStatsCard.css'

interface OUStatsCardProps {
  name: string
  count: number
  color?: string
}

const OUStatsCard: React.FC<OUStatsCardProps> = ({ name, count, color = '#2563EB' }) => {
  return (
    <div className="ou-card" style={{ borderColor: color }}>
      <div className="ou-card-name">{name}</div>
      <div className="ou-card-count">{count}</div>
    </div>
  )
}

export default OUStatsCard
