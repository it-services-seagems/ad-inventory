import React, { useMemo, useState } from 'react'
import './VirtualScroller.css'

interface VirtualScrollerProps<T> {
  items: T[]
  pageSize?: number
  renderItem: (item: T, index: number) => React.ReactNode
}

function VirtualScroller<T>({ items, pageSize = 50, renderItem }: VirtualScrollerProps<T>) {
  const [page, setPage] = useState(0)
  const total = items.length
  const pages = Math.max(1, Math.ceil(total / pageSize))

  const visible = useMemo(() => {
    const start = page * pageSize
    const end = Math.min(total, start + pageSize)
    return items.slice(start, end)
  }, [items, page, pageSize, total])

  return (
    <div className="virtual-scroller">
      <div className="virtual-list">
        {visible.map((it, idx) => renderItem(it, page * pageSize + idx))}
      </div>
      <div className="virtual-controls">
        <button onClick={() => setPage(0)} disabled={page === 0}>«</button>
        <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}>‹</button>
        <span className="virtual-page">{page + 1} / {pages}</span>
        <button onClick={() => setPage(p => Math.min(pages - 1, p + 1))} disabled={page >= pages - 1}>›</button>
        <button onClick={() => setPage(pages - 1)} disabled={page >= pages - 1}>»</button>
      </div>
    </div>
  )
}

export default VirtualScroller
