/**
 * High-performance Canvas 2D renderer
 * Supports 10k+ nodes with viewport culling and optimized rendering
 */

import { Rectangle } from './Quadtree'

const DEFAULT_STYLES = {
  article: { 
    fill: '#2f80ed', 
    stroke: '#1a5fb4', 
    icon: '📄',
    radius: 16 
  },
  domain: { 
    fill: '#9b51e0', 
    stroke: '#7b31b0', 
    icon: '🧭',
    radius: 20 
  },
  knowledge_point: { 
    fill: '#f2994a', 
    stroke: '#d27c3a', 
    icon: '💡',
    radius: 16 
  },
  group: { 
    fill: 'rgba(100, 100, 100, 0.1)', 
    stroke: '#888',
    icon: '📁',
    radius: 30 
  },
  default: { 
    fill: '#607d8b', 
    stroke: '#455a64', 
    icon: '•',
    radius: 14 
  },
}

const EDGE_STYLES = {
  related_articles: { color: '#94a3b8', width: 1.5, dash: [] },
  belongs_to: { color: '#a78bfa', width: 1.5, dash: [] },
  covers: { color: '#fb923c', width: 1.5, dash: [] },
  default: { color: '#cfd8dc', width: 1, dash: [] },
}

export class CanvasRenderer {
  constructor(canvas, options = {}) {
    this.canvas = canvas
    this.ctx = canvas.getContext('2d')
    this.options = {
      nodeStyles: { ...DEFAULT_STYLES, ...options.nodeStyles },
      edgeStyles: { ...EDGE_STYLES, ...options.edgeStyles },
      showLabels: options.showLabels !== false,
      showIcons: options.showIcons !== false,
      labelMinScale: options.labelMinScale || 0.3,
      antialiasing: options.antialiasing !== false,
      backgroundColor: options.backgroundColor || '#fafafa',
      gridColor: options.gridColor || '#e0e0e0',
      selectionColor: options.selectionColor || '#2196f3',
      hoverColor: options.hoverColor || '#64b5f6',
    }
    
    // Performance tracking
    this.lastRenderTime = 0
    this.frameCount = 0
    
    // Enable antialiasing
    if (this.options.antialiasing) {
      this.ctx.imageSmoothingEnabled = true
      this.ctx.imageSmoothingQuality = 'high'
    }
  }

  /**
   * Main render method
   */
  render(state) {
    const startTime = performance.now()
    const { 
      nodes, edges, viewport, canvasWidth, canvasHeight,
      selectedNodeIds, hoveredNodeId, showGrid, gridSize
    } = state
    
    const ctx = this.ctx
    
    // Clear and setup transform
    ctx.setTransform(1, 0, 0, 1, 0, 0)
    ctx.fillStyle = this.options.backgroundColor
    ctx.fillRect(0, 0, canvasWidth, canvasHeight)
    
    // Apply camera transform
    ctx.translate(-viewport.offsetX * viewport.scale, -viewport.offsetY * viewport.scale)
    ctx.scale(viewport.scale, viewport.scale)
    
    // Draw grid if enabled
    if (showGrid) {
      this.drawGrid(viewport, canvasWidth, canvasHeight, gridSize)
    }
    
    // Get visible nodes using quadtree
    const visibleNodes = this.getVisibleNodes(nodes, viewport, canvasWidth, canvasHeight)
    
    // Create node lookup for edge rendering
    const nodeMap = new Map()
    for (const node of nodes) {
      nodeMap.set(node.id, node)
    }
    
    // Draw edges (only those connecting visible nodes)
    const visibleNodeIds = new Set(visibleNodes.map(n => n.id))
    ctx.save()
    for (const edge of edges) {
      const source = nodeMap.get(edge.source)
      const target = nodeMap.get(edge.target)
      if (!source || !target) continue
      
      // Only draw if at least one endpoint is visible
      if (!visibleNodeIds.has(edge.source) && !visibleNodeIds.has(edge.target)) continue
      
      this.drawEdge(ctx, source, target, edge, state)
    }
    ctx.restore()
    
    // Draw nodes
    for (const node of visibleNodes) {
      const isSelected = selectedNodeIds.has(node.id)
      const isHovered = hoveredNodeId === node.id
      this.drawNode(ctx, node, { isSelected, isHovered, scale: viewport.scale })
    }
    
    this.lastRenderTime = performance.now() - startTime
    this.frameCount++
    
    return {
      visibleNodeCount: visibleNodes.length,
      renderTime: this.lastRenderTime,
    }
  }

  /**
   * Get nodes visible in the viewport
   */
  getVisibleNodes(nodes, viewport, canvasWidth, canvasHeight) {
    // Calculate viewport bounds in world coordinates with some padding
    const padding = 50
    const viewportRect = new Rectangle(
      viewport.offsetX - padding / viewport.scale,
      viewport.offsetY - padding / viewport.scale,
      (canvasWidth + padding * 2) / viewport.scale,
      (canvasHeight + padding * 2) / viewport.scale
    )
    
    return nodes.filter(node => {
      const r = node.radius || 20
      return (
        node.x + r >= viewportRect.x &&
        node.x - r <= viewportRect.x + viewportRect.width &&
        node.y + r >= viewportRect.y &&
        node.y - r <= viewportRect.y + viewportRect.height
      )
    })
  }

  /**
   * Draw grid lines
   */
  drawGrid(viewport, canvasWidth, canvasHeight, gridSize) {
    const ctx = this.ctx
    const startX = Math.floor(viewport.offsetX / gridSize) * gridSize
    const startY = Math.floor(viewport.offsetY / gridSize) * gridSize
    const endX = viewport.offsetX + canvasWidth / viewport.scale
    const endY = viewport.offsetY + canvasHeight / viewport.scale
    
    ctx.strokeStyle = this.options.gridColor
    ctx.lineWidth = 0.5 / viewport.scale
    ctx.beginPath()
    
    // Vertical lines
    for (let x = startX; x <= endX; x += gridSize) {
      ctx.moveTo(x, startY)
      ctx.lineTo(x, endY)
    }
    
    // Horizontal lines
    for (let y = startY; y <= endY; y += gridSize) {
      ctx.moveTo(startX, y)
      ctx.lineTo(endX, y)
    }
    
    ctx.stroke()
  }

  /**
   * Draw a single node
   */
  drawNode(ctx, node, options = {}) {
    const { isSelected, isHovered, scale } = options
    const style = this.options.nodeStyles[node.type] || this.options.nodeStyles.default
    const radius = node.radius || style.radius
    
    // Draw selection ring
    if (isSelected) {
      ctx.beginPath()
      ctx.arc(node.x, node.y, radius + 4, 0, Math.PI * 2)
      ctx.strokeStyle = this.options.selectionColor
      ctx.lineWidth = 3
      ctx.stroke()
    }
    
    // Draw hover ring
    if (isHovered && !isSelected) {
      ctx.beginPath()
      ctx.arc(node.x, node.y, radius + 3, 0, Math.PI * 2)
      ctx.strokeStyle = this.options.hoverColor
      ctx.lineWidth = 2
      ctx.stroke()
    }
    
    // Draw node circle
    ctx.beginPath()
    ctx.arc(node.x, node.y, radius, 0, Math.PI * 2)
    ctx.fillStyle = node.color || style.fill
    ctx.fill()
    ctx.strokeStyle = style.stroke
    ctx.lineWidth = 1.5
    ctx.stroke()
    
    // Draw icon (at higher zoom levels)
    if (this.options.showIcons && scale >= 0.4) {
      ctx.fillStyle = '#fff'
      ctx.font = `${Math.max(10, radius * 0.7)}px sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(node.icon || style.icon, node.x, node.y + 1)
    }
    
    // Draw label (at higher zoom levels)
    if (this.options.showLabels && scale >= this.options.labelMinScale) {
      const label = node.label || node.id
      const maxLength = scale < 0.6 ? 15 : 30
      const displayLabel = label.length > maxLength 
        ? label.substring(0, maxLength - 2) + '…' 
        : label
      
      ctx.fillStyle = '#333'
      ctx.font = `${11 / scale}px sans-serif`
      ctx.textAlign = 'center'
      ctx.textBaseline = 'top'
      
      // Background for label readability
      const labelY = node.y + radius + 4
      const textWidth = ctx.measureText(displayLabel).width
      ctx.fillStyle = 'rgba(255, 255, 255, 0.85)'
      ctx.fillRect(
        node.x - textWidth / 2 - 2, 
        labelY - 1, 
        textWidth + 4, 
        14 / scale
      )
      
      ctx.fillStyle = '#333'
      ctx.fillText(displayLabel, node.x, labelY)
    }
  }

  /**
   * Draw a single edge
   */
  drawEdge(ctx, source, target, edge, state) {
    const style = this.options.edgeStyles[edge.type] || this.options.edgeStyles.default
    const isSelected = state.selectedEdgeIds?.has(edge.id)
    
    // Calculate direction
    const dx = target.x - source.x
    const dy = target.y - source.y
    const dist = Math.sqrt(dx * dx + dy * dy)
    if (dist === 0) return
    
    // Shorten edges to not overlap nodes
    const sourceRadius = source.radius || 16
    const targetRadius = target.radius || 16
    const unitX = dx / dist
    const unitY = dy / dist
    
    const startX = source.x + unitX * sourceRadius
    const startY = source.y + unitY * sourceRadius
    const endX = target.x - unitX * targetRadius
    const endY = target.y - unitY * targetRadius
    
    // Draw line
    ctx.beginPath()
    ctx.moveTo(startX, startY)
    
    // Curved edge option (using bezier for aesthetics)
    if (edge.curved) {
      const midX = (startX + endX) / 2
      const midY = (startY + endY) / 2
      const perpX = -unitY * 30
      const perpY = unitX * 30
      ctx.quadraticCurveTo(midX + perpX, midY + perpY, endX, endY)
    } else {
      ctx.lineTo(endX, endY)
    }
    
    ctx.strokeStyle = isSelected ? this.options.selectionColor : style.color
    ctx.lineWidth = isSelected ? style.width + 1 : style.width
    
    if (style.dash.length > 0) {
      ctx.setLineDash(style.dash)
    }
    
    ctx.stroke()
    ctx.setLineDash([])
    
    // Draw arrow (optional)
    if (edge.directed !== false) {
      const arrowLength = 8
      const arrowAngle = Math.PI / 6
      const angle = Math.atan2(endY - startY, endX - startX)
      
      ctx.beginPath()
      ctx.moveTo(endX, endY)
      ctx.lineTo(
        endX - arrowLength * Math.cos(angle - arrowAngle),
        endY - arrowLength * Math.sin(angle - arrowAngle)
      )
      ctx.moveTo(endX, endY)
      ctx.lineTo(
        endX - arrowLength * Math.cos(angle + arrowAngle),
        endY - arrowLength * Math.sin(angle + arrowAngle)
      )
      ctx.stroke()
    }
  }

  /**
   * Draw a selection rectangle
   */
  drawSelectionRect(x1, y1, x2, y2, viewport) {
    const ctx = this.ctx
    ctx.save()
    ctx.setTransform(1, 0, 0, 1, 0, 0)
    
    // Convert world coordinates to screen
    const sx1 = (x1 - viewport.offsetX) * viewport.scale
    const sy1 = (y1 - viewport.offsetY) * viewport.scale
    const sx2 = (x2 - viewport.offsetX) * viewport.scale
    const sy2 = (y2 - viewport.offsetY) * viewport.scale
    
    ctx.strokeStyle = this.options.selectionColor
    ctx.lineWidth = 1
    ctx.setLineDash([5, 3])
    ctx.strokeRect(
      Math.min(sx1, sx2),
      Math.min(sy1, sy2),
      Math.abs(sx2 - sx1),
      Math.abs(sy2 - sy1)
    )
    ctx.fillStyle = 'rgba(33, 150, 243, 0.1)'
    ctx.fillRect(
      Math.min(sx1, sx2),
      Math.min(sy1, sy2),
      Math.abs(sx2 - sx1),
      Math.abs(sy2 - sy1)
    )
    ctx.setLineDash([])
    ctx.restore()
  }

  /**
   * Draw minimap
   */
  drawMinimap(state, size = 150, margin = 10) {
    const { nodes, viewport, canvasWidth, canvasHeight } = state
    if (nodes.length === 0) return
    
    const ctx = this.ctx
    ctx.save()
    ctx.setTransform(1, 0, 0, 1, 0, 0)
    
    // Calculate bounds
    let minX = Infinity, minY = Infinity
    let maxX = -Infinity, maxY = -Infinity
    for (const node of nodes) {
      minX = Math.min(minX, node.x)
      minY = Math.min(minY, node.y)
      maxX = Math.max(maxX, node.x)
      maxY = Math.max(maxY, node.y)
    }
    
    const graphWidth = maxX - minX || 1
    const graphHeight = maxY - minY || 1
    const padding = 20
    const aspect = graphWidth / graphHeight
    
    let mapWidth = size
    let mapHeight = size / aspect
    if (mapHeight > size) {
      mapHeight = size
      mapWidth = size * aspect
    }
    
    // Position minimap in bottom-right corner
    const mapX = canvasWidth - mapWidth - margin
    const mapY = canvasHeight - mapHeight - margin
    
    // Draw background
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)'
    ctx.strokeStyle = '#ccc'
    ctx.lineWidth = 1
    ctx.fillRect(mapX - 5, mapY - 5, mapWidth + 10, mapHeight + 10)
    ctx.strokeRect(mapX - 5, mapY - 5, mapWidth + 10, mapHeight + 10)
    
    // Calculate scale for minimap
    const scaleX = (mapWidth - padding) / graphWidth
    const scaleY = (mapHeight - padding) / graphHeight
    const scale = Math.min(scaleX, scaleY)
    
    // Draw nodes as dots
    for (const node of nodes) {
      const x = mapX + padding / 2 + (node.x - minX) * scale
      const y = mapY + padding / 2 + (node.y - minY) * scale
      const style = this.options.nodeStyles[node.type] || this.options.nodeStyles.default
      
      ctx.fillStyle = style.fill
      ctx.beginPath()
      ctx.arc(x, y, 2, 0, Math.PI * 2)
      ctx.fill()
    }
    
    // Draw viewport rectangle
    const vpX = mapX + padding / 2 + (viewport.offsetX - minX) * scale
    const vpY = mapY + padding / 2 + (viewport.offsetY - minY) * scale
    const vpW = (canvasWidth / viewport.scale) * scale
    const vpH = (canvasHeight / viewport.scale) * scale
    
    ctx.strokeStyle = '#2196f3'
    ctx.lineWidth = 2
    ctx.strokeRect(vpX, vpY, vpW, vpH)
    
    ctx.restore()
  }

  /**
   * Resize canvas
   */
  resize(width, height, devicePixelRatio = 1) {
    const dpr = devicePixelRatio
    this.canvas.width = width * dpr
    this.canvas.height = height * dpr
    this.canvas.style.width = `${width}px`
    this.canvas.style.height = `${height}px`
    this.ctx.scale(dpr, dpr)
    
    if (this.options.antialiasing) {
      this.ctx.imageSmoothingEnabled = true
      this.ctx.imageSmoothingQuality = 'high'
    }
    
    return { width, height }
  }

  /**
   * Get performance stats
   */
  getStats() {
    return {
      lastRenderTime: this.lastRenderTime,
      frameCount: this.frameCount,
      fps: this.frameCount > 0 ? Math.round(1000 / this.lastRenderTime) : 0,
    }
  }
}

export default CanvasRenderer
