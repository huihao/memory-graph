import { useState, useEffect, useRef } from 'react'
import axios from 'axios'

const TYPE_STYLES = {
  article: { color: '#2f80ed', icon: '📄' },
  domain: { color: '#9b51e0', icon: '🧭' },
  knowledge_point: { color: '#f2994a', icon: '💡' }
}

const NODE_RADIUS = {
  article: 16,
  domain: 18,
  knowledge_point: 16
}

function KnowledgeGraph({ apiUrl }) {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [], context: {} })
  const [loading, setLoading] = useState(true)
  const [draggingNode, setDraggingNode] = useState(null)
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 })
  const [filters, setFilters] = useState({ domainId: '', knowledgePointId: '' })
  const [domains, setDomains] = useState([])
  const [knowledgePoints, setKnowledgePoints] = useState([])
  const [selectedEdge, setSelectedEdge] = useState(null)
  const canvasRef = useRef(null)
  const dragStartRef = useRef(null)

  useEffect(() => {
    loadFilters()
  }, [])

  useEffect(() => {
    loadGraphData()
  }, [filters])

  useEffect(() => {
    if (graphData.nodes.length > 0) {
      drawGraph()
    }
  }, [graphData, transform, selectedEdge])

  useEffect(() => {
    if (graphData.nodes.length > 0) {
      applyLayout()
    }
  }, [graphData])

  const loadFilters = async () => {
    try {
      const [domainRes, kpRes] = await Promise.all([
        axios.get(`${apiUrl}/domains`),
        axios.get(`${apiUrl}/knowledge-points`)
      ])
      setDomains(domainRes.data)
      setKnowledgePoints(kpRes.data)
    } catch (err) {
      console.error('Error loading filters:', err)
    }
  }

  const loadGraphData = async () => {
    setLoading(true)
    setSelectedEdge(null)
    try {
      const params = {}
      if (filters.domainId) params.domain_id = filters.domainId
      if (filters.knowledgePointId) params.knowledge_point_id = filters.knowledgePointId
      const response = await axios.get(`${apiUrl}/knowledge-graph`, { params })
      setGraphData(response.data)
    } catch (err) {
      console.error('Error loading graph data:', err)
    } finally {
      setLoading(false)
    }
  }

  const getCanvasPosition = (event) => {
    const canvas = canvasRef.current
    const rect = canvas.getBoundingClientRect()
    return {
      x: (event.clientX - rect.left - transform.x) / transform.scale,
      y: (event.clientY - rect.top - transform.y) / transform.scale
    }
  }

  const getNodeAtPosition = (x, y) => {
    return graphData.nodes.find(node => {
      const dx = x - node.x
      const dy = y - node.y
      const radius = NODE_RADIUS[node.type] || 14
      return Math.sqrt(dx * dx + dy * dy) <= radius
    })
  }

  const handleMouseDown = (event) => {
    const pos = getCanvasPosition(event)
    const node = getNodeAtPosition(pos.x, pos.y)
    if (node) {
      setDraggingNode(node)
    } else {
      dragStartRef.current = { x: event.clientX, y: event.clientY }
    }
  }

  const handleMouseMove = (event) => {
    if (draggingNode) {
      const pos = getCanvasPosition(event)
      draggingNode.x = pos.x
      draggingNode.y = pos.y
      drawGraph()
      return
    }
    if (!dragStartRef.current) return
    const dx = event.clientX - dragStartRef.current.x
    const dy = event.clientY - dragStartRef.current.y
    dragStartRef.current = { x: event.clientX, y: event.clientY }
    setTransform(prev => ({ ...prev, x: prev.x + dx, y: prev.y + dy }))
  }

  const handleMouseUp = () => {
    setDraggingNode(null)
    dragStartRef.current = null
  }

  const handleClick = (event) => {
    const pos = getCanvasPosition(event)
    const clickedNode = getNodeAtPosition(pos.x, pos.y)
    if (clickedNode && clickedNode.url) {
      window.open(clickedNode.url, '_blank', 'noopener,noreferrer')
    }
  }

  const handleWheel = (event) => {
    event.preventDefault()
    const delta = event.deltaY > 0 ? 0.9 : 1.1
    setTransform(prev => ({
      ...prev,
      scale: Math.min(2, Math.max(0.5, prev.scale * delta))
    }))
  }

  const resetView = () => {
    setTransform({ x: 0, y: 0, scale: 1 })
  }

  const applyLayout = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const width = canvas.width
    const height = canvas.height
    const centerX = width / 2
    const centerY = height / 2

    const domainNodes = graphData.nodes.filter(node => node.type === 'domain')
    const kpNodes = graphData.nodes.filter(node => node.type === 'knowledge_point')
    const articleNodes = graphData.nodes.filter(node => node.type === 'article')

    const domainRadius = Math.min(width, height) * 0.28
    const kpRadius = Math.min(width, height) * 0.18
    const articleRadius = Math.min(width, height) * 0.38

    domainNodes.forEach((node, index) => {
      const angle = (index / Math.max(domainNodes.length, 1)) * 2 * Math.PI
      node.x = centerX + Math.cos(angle) * domainRadius
      node.y = centerY + Math.sin(angle) * domainRadius
    })

    kpNodes.forEach((node, index) => {
      const angle = (index / Math.max(kpNodes.length, 1)) * 2 * Math.PI
      node.x = centerX + Math.cos(angle) * kpRadius
      node.y = centerY + Math.sin(angle) * kpRadius
    })

    articleNodes.forEach((node, index) => {
      const angle = (index / Math.max(articleNodes.length, 1)) * 2 * Math.PI
      node.x = centerX + Math.cos(angle) * articleRadius
      node.y = centerY + Math.sin(angle) * articleRadius
    })

    drawGraph()
  }

  const drawGraph = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const width = canvas.width
    const height = canvas.height

    ctx.setTransform(1, 0, 0, 1, 0, 0)
    ctx.clearRect(0, 0, width, height)
    ctx.translate(transform.x, transform.y)
    ctx.scale(transform.scale, transform.scale)

    if (!graphData.nodes.every(node => node.x !== undefined)) {
      return
    }

    graphData.edges.forEach(edge => {
      const source = graphData.nodes.find(node => node.id === edge.source)
      const target = graphData.nodes.find(node => node.id === edge.target)
      if (!source || !target) return
      const isSelected = selectedEdge && selectedEdge.type === edge.type
      ctx.strokeStyle = isSelected ? '#2f80ed' : '#cfd8dc'
      ctx.lineWidth = isSelected ? 2.5 : edge.type === 'related_articles' ? 1.5 : 1
      ctx.beginPath()
      ctx.moveTo(source.x, source.y)
      ctx.lineTo(target.x, target.y)
      ctx.stroke()
    })

    graphData.nodes.forEach(node => {
      const { color, icon } = TYPE_STYLES[node.type] || TYPE_STYLES.article
      const radius = NODE_RADIUS[node.type] || 14
      ctx.fillStyle = color
      ctx.beginPath()
      ctx.arc(node.x, node.y, radius, 0, Math.PI * 2)
      ctx.fill()

      ctx.fillStyle = '#fff'
      ctx.font = '12px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(icon || '•', node.x, node.y + 1)

      ctx.fillStyle = '#333'
      ctx.font = '11px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      ctx.fillText(node.label.substring(0, 24), node.x, node.y + radius + 4)
    })
  }

  const selectEdgeDetails = (edgeType) => {
    const edge = graphData.edges.find(item => item.type === edgeType)
    setSelectedEdge(edge || null)
  }

  if (loading) return <div className="loading">Loading knowledge graph...</div>

  return (
    <div>
      <h2>Knowledge Graph</h2>
      <p style={{ marginBottom: '10px', color: '#666' }}>
        Visualizing connections between articles, domains, and knowledge points.
      </p>

      <div className="graph-controls">
        <div className="graph-filter">
          <label>Domain</label>
          <select
            value={filters.domainId}
            onChange={(event) => setFilters({ domainId: event.target.value, knowledgePointId: '' })}
          >
            <option value="">All domains</option>
            {domains.map(domain => (
              <option key={domain.id} value={domain.id}>{domain.name}</option>
            ))}
          </select>
        </div>
        <div className="graph-filter">
          <label>Knowledge Point</label>
          <select
            value={filters.knowledgePointId}
            onChange={(event) => setFilters({ domainId: '', knowledgePointId: event.target.value })}
          >
            <option value="">All knowledge points</option>
            {knowledgePoints.map(kp => (
              <option key={kp.id} value={kp.id}>{kp.name}</option>
            ))}
          </select>
        </div>
        <div className="graph-actions">
          <button onClick={applyLayout}>🔄 Re-layout</button>
          <button onClick={resetView}>🧭 Reset View</button>
        </div>
      </div>

      {graphData.context?.domain && (
        <div className="graph-context">Current domain: {graphData.context.domain}</div>
      )}
      {graphData.context?.knowledge_point && (
        <div className="graph-context">Current knowledge point: {graphData.context.knowledge_point}</div>
      )}

      <div className="graph-container">
        <canvas
          ref={canvasRef}
          width={1100}
          height={650}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onClick={handleClick}
          onWheel={handleWheel}
          style={{ width: '100%', height: '100%', cursor: draggingNode ? 'grabbing' : 'grab' }}
        />
      </div>

      <div className="graph-legend">
        {Object.entries(TYPE_STYLES).map(([key, style]) => (
          <div key={key} className="legend-item">
            <span className="legend-icon" style={{ background: style.color }}>{style.icon}</span>
            {key.replace('_', ' ')}
          </div>
        ))}
      </div>

      <div className="graph-edge-details">
        <h3>Connections</h3>
        <div className="edge-tags">
          <button onClick={() => selectEdgeDetails('related_articles')}>Article ↔ Article</button>
          <button onClick={() => selectEdgeDetails('belongs_to')}>Article → Domain</button>
          <button onClick={() => selectEdgeDetails('covers')}>Article → Knowledge Point</button>
        </div>
        {selectedEdge ? (
          <div className="edge-detail-card">
            <div className="edge-type">Selected edge type: {selectedEdge.type}</div>
            {selectedEdge.shared_domains?.length > 0 && (
              <div>Shared domains: {selectedEdge.shared_domains.join(', ')}</div>
            )}
            {selectedEdge.shared_knowledge_points?.length > 0 && (
              <div>Shared knowledge points: {selectedEdge.shared_knowledge_points.join(', ')}</div>
            )}
          </div>
        ) : (
          <div className="edge-detail-card">Select a connection type to highlight in the graph.</div>
        )}
      </div>

      {graphData.nodes.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          No graph data available. Add some articles first.
        </div>
      )}
    </div>
  )
}

export default KnowledgeGraph
