/**
 * KnowledgeGraph component using InfiniteCanvas
 * 
 * Features:
 * - High-performance rendering of 10k+ nodes
 * - Pan/zoom with mouse wheel
 * - Force-directed layout
 * - Node dragging
 * - Search with fly-to
 * - Minimap navigation
 * - Filter by domain/knowledge point
 */

import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import { InfiniteCanvas, useCanvasStore } from '../canvas'

const TYPE_STYLES = {
  article: { color: '#2f80ed', icon: '📄' },
  domain: { color: '#9b51e0', icon: '🧭' },
  knowledge_point: { color: '#f2994a', icon: '💡' }
}

const NODE_RADIUS = {
  article: 16,
  domain: 20,
  knowledge_point: 16
}

function KnowledgeGraph({ apiUrl }) {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [], context: {} })
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ domainId: '', knowledgePointId: '' })
  const [domains, setDomains] = useState([])
  const [knowledgePoints, setKnowledgePoints] = useState([])
  const [selectedEdgeType, setSelectedEdgeType] = useState(null)
  
  // Load filter options
  useEffect(() => {
    loadFilters()
  }, [])

  // Load graph data when filters change
  useEffect(() => {
    loadGraphData()
  }, [filters])

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
    setSelectedEdgeType(null)
    try {
      const params = {}
      if (filters.domainId) params.domain_id = filters.domainId
      if (filters.knowledgePointId) params.knowledge_point_id = filters.knowledgePointId
      const response = await axios.get(`${apiUrl}/knowledge-graph`, { params })
      
      // Transform nodes for InfiniteCanvas
      const nodes = response.data.nodes.map(node => ({
        ...node,
        radius: NODE_RADIUS[node.type] || 14,
        color: TYPE_STYLES[node.type]?.color || '#607d8b',
        icon: TYPE_STYLES[node.type]?.icon || '•',
      }))
      
      // Transform edges for InfiniteCanvas
      const edges = response.data.edges.map((edge, index) => ({
        ...edge,
        id: edge.id || `edge-${index}`,
        directed: false, // Knowledge graph edges are undirected
      }))
      
      setGraphData({ 
        nodes, 
        edges, 
        context: response.data.context || {} 
      })
    } catch (err) {
      console.error('Error loading graph data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleNodeClick = useCallback((node, event) => {
    if (node.url) {
      window.open(node.url, '_blank', 'noopener,noreferrer')
    }
  }, [])

  const handleNodeDoubleClick = useCallback((node, event) => {
    // Already handled by default behavior in InfiniteCanvas
  }, [])

  const selectEdgeType = (edgeType) => {
    setSelectedEdgeType(prev => prev === edgeType ? null : edgeType)
  }

  const getEdgesByType = (type) => {
    return graphData.edges.filter(edge => edge.type === type)
  }

  if (loading) {
    return (
      <div className="loading">
        <div style={{ textAlign: 'center', padding: '60px' }}>
          <div style={{ fontSize: '24px', marginBottom: '12px' }}>⏳</div>
          <div>Loading knowledge graph...</div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <h2>Knowledge Graph</h2>
      <p style={{ marginBottom: '10px', color: '#666' }}>
        Visualizing connections between articles, domains, and knowledge points.
        {graphData.nodes.length > 100 && (
          <span style={{ color: '#2f80ed', marginLeft: 8 }}>
            ⚡ High-performance mode: {graphData.nodes.length} nodes
          </span>
        )}
      </p>

      {/* Filter Controls */}
      <div className="graph-controls">
        <div className="graph-filter">
          <label>Domain</label>
          <select
            value={filters.domainId}
            title="Selecting a domain resets the knowledge point filter."
            onChange={(e) => setFilters({ domainId: e.target.value, knowledgePointId: '' })}
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
            title="Selecting a knowledge point resets the domain filter."
            onChange={(e) => setFilters({ domainId: '', knowledgePointId: e.target.value })}
          >
            <option value="">All knowledge points</option>
            {knowledgePoints.map(kp => (
              <option key={kp.id} value={kp.id}>{kp.name}</option>
            ))}
          </select>
        </div>
      </div>
      <div className="graph-filter-note">
        Choose a domain or knowledge point to focus the graph. 
        Use mouse wheel to zoom, drag to pan, search to find nodes.
      </div>

      {/* Context Info */}
      {graphData.context?.domain && (
        <div className="graph-context">Current domain: {graphData.context.domain}</div>
      )}
      {graphData.context?.knowledge_point && (
        <div className="graph-context">Current knowledge point: {graphData.context.knowledge_point}</div>
      )}

      {/* Infinite Canvas */}
      <div className="graph-container" style={{ height: 600 }}>
        {graphData.nodes.length > 0 ? (
          <InfiniteCanvas
            nodes={graphData.nodes}
            edges={graphData.edges}
            width={1100}
            height={600}
            onNodeClick={handleNodeClick}
            onNodeDoubleClick={handleNodeDoubleClick}
            showControls={true}
            showMinimap={true}
            showStats={true}
            showSearch={true}
            autoLayout={true}
            layoutType="force"
          />
        ) : (
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            height: '100%',
            color: '#666',
          }}>
            No graph data available. Add some articles first.
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="graph-legend">
        {Object.entries(TYPE_STYLES).map(([key, style]) => (
          <div key={key} className="legend-item">
            <span className="legend-icon" style={{ background: style.color }}>{style.icon}</span>
            {key.replace(/_/g, ' ')}
          </div>
        ))}
      </div>

      {/* Edge Type Selector */}
      <div className="graph-edge-details">
        <h3>Connections</h3>
        <div className="edge-tags">
          <button
            onClick={() => selectEdgeType('related_articles')}
            style={{
              background: selectedEdgeType === 'related_articles' ? '#e3f2fd' : '#f1f3f5',
              color: selectedEdgeType === 'related_articles' ? '#1976d2' : '#444',
            }}
          >
            Article ↔ Article ({getEdgesByType('related_articles').length})
          </button>
          <button
            onClick={() => selectEdgeType('belongs_to')}
            style={{
              background: selectedEdgeType === 'belongs_to' ? '#f3e5f5' : '#f1f3f5',
              color: selectedEdgeType === 'belongs_to' ? '#7b1fa2' : '#444',
            }}
          >
            Article → Domain ({getEdgesByType('belongs_to').length})
          </button>
          <button
            onClick={() => selectEdgeType('covers')}
            style={{
              background: selectedEdgeType === 'covers' ? '#fff3e0' : '#f1f3f5',
              color: selectedEdgeType === 'covers' ? '#e65100' : '#444',
            }}
          >
            Article → Knowledge Point ({getEdgesByType('covers').length})
          </button>
        </div>
        {selectedEdgeType && (
          <div className="edge-detail-card">
            <div className="edge-type">Selected: {selectedEdgeType.replace(/_/g, ' ')}</div>
            <div>Count: {getEdgesByType(selectedEdgeType).length} connections</div>
          </div>
        )}
      </div>

      {/* Keyboard Shortcuts Help */}
      <div style={{ marginTop: 20, fontSize: 12, color: '#888' }}>
        <strong>Keyboard shortcuts:</strong> Arrow keys to pan, +/- to zoom, F to fit all, 0 to reset, Esc to deselect
      </div>
    </div>
  )
}

export default KnowledgeGraph
