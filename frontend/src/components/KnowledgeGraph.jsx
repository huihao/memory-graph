import { useState, useEffect, useRef } from 'react'
import axios from 'axios'

function KnowledgeGraph({ apiUrl }) {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] })
  const [loading, setLoading] = useState(true)
  const canvasRef = useRef(null)

  useEffect(() => {
    loadGraphData()
  }, [])

  useEffect(() => {
    if (graphData.nodes.length > 0) {
      drawGraph()
    }
  }, [graphData])

  const loadGraphData = async () => {
    try {
      const response = await axios.get(`${apiUrl}/knowledge-graph`)
      setGraphData(response.data)
      setLoading(false)
    } catch (err) {
      console.error('Error loading graph data:', err)
      setLoading(false)
    }
  }

  const drawGraph = () => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    const width = canvas.width
    const height = canvas.height

    // Clear canvas
    ctx.clearRect(0, 0, width, height)

    // Simple force-directed layout simulation
    const nodePositions = {}
    graphData.nodes.forEach((node, i) => {
      const angle = (i / graphData.nodes.length) * 2 * Math.PI
      const radius = Math.min(width, height) * 0.3
      nodePositions[node.id] = {
        x: width / 2 + Math.cos(angle) * radius,
        y: height / 2 + Math.sin(angle) * radius
      }
    })

    // Draw edges
    ctx.strokeStyle = '#ccc'
    ctx.lineWidth = 1
    graphData.edges.forEach(edge => {
      const source = nodePositions[edge.source]
      const target = nodePositions[edge.target]
      if (source && target) {
        ctx.beginPath()
        ctx.moveTo(source.x, source.y)
        ctx.lineTo(target.x, target.y)
        ctx.stroke()
      }
    })

    // Draw nodes
    graphData.nodes.forEach(node => {
      const pos = nodePositions[node.id]
      if (!pos) return

      // Node color based on type
      let color = '#007bff'
      if (node.type === 'domain') color = '#7b1fa2'
      if (node.type === 'knowledge_point') color = '#f57c00'

      ctx.fillStyle = color
      ctx.beginPath()
      ctx.arc(pos.x, pos.y, 8, 0, 2 * Math.PI)
      ctx.fill()

      // Label
      ctx.fillStyle = '#333'
      ctx.font = '11px Arial'
      ctx.textAlign = 'center'
      ctx.fillText(node.label.substring(0, 20), pos.x, pos.y - 12)
    })
  }

  if (loading) return <div className="loading">Loading knowledge graph...</div>

  return (
    <div>
      <h2>Knowledge Graph</h2>
      <p style={{ marginBottom: '20px', color: '#666' }}>
        Visualizing connections between articles, domains, and knowledge points
      </p>

      <div className="graph-container">
        <canvas
          ref={canvasRef}
          width={1000}
          height={600}
          style={{ width: '100%', height: '100%' }}
        />
      </div>

      <div style={{ marginTop: '20px' }}>
        <h3>Legend</h3>
        <div style={{ display: 'flex', gap: '20px' }}>
          <div>
            <span style={{ 
              display: 'inline-block', 
              width: '12px', 
              height: '12px', 
              background: '#007bff',
              borderRadius: '50%',
              marginRight: '5px'
            }}></span>
            Articles
          </div>
          <div>
            <span style={{ 
              display: 'inline-block', 
              width: '12px', 
              height: '12px', 
              background: '#7b1fa2',
              borderRadius: '50%',
              marginRight: '5px'
            }}></span>
            Domains
          </div>
          <div>
            <span style={{ 
              display: 'inline-block', 
              width: '12px', 
              height: '12px', 
              background: '#f57c00',
              borderRadius: '50%',
              marginRight: '5px'
            }}></span>
            Knowledge Points
          </div>
        </div>
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
