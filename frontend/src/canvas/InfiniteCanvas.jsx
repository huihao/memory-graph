/**
 * InfiniteCanvas - High-performance infinite canvas React component
 * 
 * Features:
 * - Infinite coordinate system with world/screen coordinate mapping
 * - Pan (drag), zoom (mouse wheel with pivot), keyboard navigation
 * - 10k+ node rendering with quadtree spatial indexing
 * - Node/edge interaction (click, drag, selection)
 * - Minimap for navigation
 * - Force-directed layout
 * - Extensible for knowledge graph / whiteboard / flowchart
 */

import { useRef, useEffect, useCallback, useState, useMemo } from 'react'
import { useCanvasStore } from './store'
import { CanvasRenderer } from './Renderer'
import { ForceLayout, initializePositions, arrangeByType } from './ForceLayout'

// Styles for the canvas component
const styles = {
  container: {
    position: 'relative',
    width: '100%',
    height: '100%',
    overflow: 'hidden',
    backgroundColor: '#fafafa',
  },
  canvas: {
    display: 'block',
    touchAction: 'none',
  },
  controls: {
    position: 'absolute',
    top: 10,
    right: 10,
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
    zIndex: 10,
  },
  controlButton: {
    width: 36,
    height: 36,
    border: '1px solid #ddd',
    borderRadius: 4,
    background: 'white',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 18,
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  stats: {
    position: 'absolute',
    bottom: 10,
    left: 10,
    background: 'rgba(255,255,255,0.9)',
    padding: '6px 10px',
    borderRadius: 4,
    fontSize: 11,
    color: '#666',
    fontFamily: 'monospace',
    zIndex: 10,
  },
  searchBox: {
    position: 'absolute',
    top: 10,
    left: 10,
    zIndex: 10,
    display: 'flex',
    gap: 8,
  },
  searchInput: {
    padding: '8px 12px',
    border: '1px solid #ddd',
    borderRadius: 4,
    width: 200,
    fontSize: 13,
  },
  searchResults: {
    position: 'absolute',
    top: 44,
    left: 10,
    background: 'white',
    border: '1px solid #ddd',
    borderRadius: 4,
    maxHeight: 200,
    overflow: 'auto',
    zIndex: 10,
    width: 250,
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
  },
  searchResult: {
    padding: '8px 12px',
    cursor: 'pointer',
    borderBottom: '1px solid #eee',
    fontSize: 13,
  },
}

export function InfiniteCanvas({
  nodes: initialNodes = [],
  edges: initialEdges = [],
  width = 1100,
  height = 650,
  onNodeClick,
  onNodeDoubleClick,
  onEdgeClick,
  onViewportChange,
  showControls = true,
  showMinimap = true,
  showStats = false,
  showSearch = true,
  autoLayout = true,
  layoutType = 'force', // 'force', 'radial', 'none'
}) {
  const canvasRef = useRef(null)
  const containerRef = useRef(null)
  const rendererRef = useRef(null)
  const layoutRef = useRef(null)
  const rafRef = useRef(null)
  
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [showSearchResults, setShowSearchResults] = useState(false)
  
  // Zustand store
  const store = useCanvasStore()
  const {
    nodes, edges, viewport, setGraph, setViewport, updateNodes,
    pan, zoom, zoomToFit, flyTo, resetView,
    getNodeAtPosition, screenToWorld, worldToScreen,
    selectNode, clearSelection, setHoveredNode,
    selectedNodeIds, hoveredNodeId,
    startDrag, endDrag, startPan, endPan,
    isDragging, isPanning, draggedNodeId, dragStart,
    setLayoutRunning, isLayoutRunning,
    setCanvasDimensions, canvasWidth, canvasHeight,
  } = store
  
  // Initialize graph data and layout
  useEffect(() => {
    if (initialNodes.length === 0) {
      setGraph([], initialEdges)
      return
    }
    
    let positionedNodes = initialNodes
    
    // Initialize positions if not set
    const needsPositioning = initialNodes.some(n => n.x === undefined || n.y === undefined)
    if (needsPositioning) {
      if (layoutType === 'radial') {
        positionedNodes = arrangeByType(initialNodes)
      } else {
        positionedNodes = initializePositions(initialNodes, width, height)
      }
    }
    
    setGraph(positionedNodes, initialEdges)
    
    // Apply force layout if enabled
    if (autoLayout && layoutType === 'force' && needsPositioning) {
      const layout = new ForceLayout({
        repulsionForce: 3000,
        attractionForce: 0.008,
        centerForce: 0.0005,
      })
      layoutRef.current = layout
      
      layout.setGraph(positionedNodes, initialEdges)
      setLayoutRunning(true)
      
      layout.start(
        (updatedNodes) => {
          const updates = new Map()
          updatedNodes.forEach(n => updates.set(n.id, { x: n.x, y: n.y }))
          updateNodes(updates)
        },
        () => {
          setLayoutRunning(false)
          // Fit view after layout
          setTimeout(() => zoomToFit(80), 100)
        }
      )
    } else if (!needsPositioning) {
      setTimeout(() => zoomToFit(80), 100)
    }
    
    return () => {
      if (layoutRef.current) {
        layoutRef.current.stop()
      }
    }
  }, [initialNodes, initialEdges])
  
  // Initialize renderer
  useEffect(() => {
    if (!canvasRef.current) return
    
    rendererRef.current = new CanvasRenderer(canvasRef.current)
    setCanvasDimensions(width, height)
    
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current)
      }
    }
  }, [])
  
  // Render loop
  useEffect(() => {
    if (!rendererRef.current) return
    
    const render = () => {
      const state = useCanvasStore.getState()
      const result = rendererRef.current.render(state)
      
      // Draw minimap if enabled
      if (showMinimap && state.showMinimap) {
        rendererRef.current.drawMinimap(state)
      }
      
      rafRef.current = requestAnimationFrame(render)
    }
    
    render()
    
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current)
      }
    }
  }, [showMinimap])
  
  // Handle resize
  useEffect(() => {
    setCanvasDimensions(width, height)
    if (canvasRef.current) {
      canvasRef.current.width = width
      canvasRef.current.height = height
    }
  }, [width, height])
  
  // ==================== Event Handlers ====================
  
  const getCanvasPosition = useCallback((event) => {
    const canvas = canvasRef.current
    const rect = canvas.getBoundingClientRect()
    return {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    }
  }, [])
  
  const handleMouseDown = useCallback((event) => {
    const pos = getCanvasPosition(event)
    const node = getNodeAtPosition(pos.x, pos.y)
    
    if (node) {
      // Start dragging node
      startDrag(node.id, pos.x, pos.y)
      selectNode(node.id, event.shiftKey)
    } else {
      // Start panning
      startPan(pos.x, pos.y)
      if (!event.shiftKey) {
        clearSelection()
      }
    }
  }, [getCanvasPosition, getNodeAtPosition, startDrag, startPan, selectNode, clearSelection])
  
  const handleMouseMove = useCallback((event) => {
    const pos = getCanvasPosition(event)
    
    if (isDragging && draggedNodeId) {
      // Drag node
      const worldPos = screenToWorld(pos.x, pos.y)
      const state = useCanvasStore.getState()
      const updates = new Map()
      updates.set(draggedNodeId, { x: worldPos.x, y: worldPos.y })
      updateNodes(updates)
    } else if (isPanning && dragStart) {
      // Pan canvas
      const dx = pos.x - dragStart.x
      const dy = pos.y - dragStart.y
      pan(-dx, -dy)
      useCanvasStore.setState({ dragStart: { x: pos.x, y: pos.y } })
    } else {
      // Hover detection
      const node = getNodeAtPosition(pos.x, pos.y)
      setHoveredNode(node?.id || null)
    }
  }, [
    getCanvasPosition, isDragging, isPanning, draggedNodeId, dragStart,
    screenToWorld, updateNodes, pan, getNodeAtPosition, setHoveredNode
  ])
  
  const handleMouseUp = useCallback(() => {
    endDrag()
    endPan()
  }, [endDrag, endPan])
  
  const handleClick = useCallback((event) => {
    const pos = getCanvasPosition(event)
    const node = getNodeAtPosition(pos.x, pos.y)
    
    if (node && onNodeClick) {
      onNodeClick(node, event)
    }
  }, [getCanvasPosition, getNodeAtPosition, onNodeClick])
  
  const handleDoubleClick = useCallback((event) => {
    const pos = getCanvasPosition(event)
    const node = getNodeAtPosition(pos.x, pos.y)
    
    if (node) {
      if (onNodeDoubleClick) {
        onNodeDoubleClick(node, event)
      } else if (node.url) {
        window.open(node.url, '_blank', 'noopener,noreferrer')
      }
    } else {
      // Double click on empty space: zoom to fit
      zoomToFit(80)
    }
  }, [getCanvasPosition, getNodeAtPosition, onNodeDoubleClick, zoomToFit])
  
  const handleWheel = useCallback((event) => {
    event.preventDefault()
    const pos = getCanvasPosition(event)
    const delta = event.deltaY > 0 ? 0.9 : 1.1
    zoom(delta, pos.x, pos.y)
  }, [getCanvasPosition, zoom])
  
  const handleKeyDown = useCallback((event) => {
    const step = 50 / viewport.scale
    
    switch (event.key) {
      case 'ArrowUp':
        pan(0, step)
        event.preventDefault()
        break
      case 'ArrowDown':
        pan(0, -step)
        event.preventDefault()
        break
      case 'ArrowLeft':
        pan(step, 0)
        event.preventDefault()
        break
      case 'ArrowRight':
        pan(-step, 0)
        event.preventDefault()
        break
      case '+':
      case '=':
        zoom(1.2, canvasWidth / 2, canvasHeight / 2)
        event.preventDefault()
        break
      case '-':
        zoom(0.8, canvasWidth / 2, canvasHeight / 2)
        event.preventDefault()
        break
      case '0':
        resetView()
        event.preventDefault()
        break
      case 'f':
        zoomToFit(80)
        event.preventDefault()
        break
      case 'Escape':
        clearSelection()
        break
    }
  }, [viewport, pan, zoom, resetView, zoomToFit, clearSelection, canvasWidth, canvasHeight])
  
  // ==================== Search ====================
  
  const handleSearch = useCallback((query) => {
    setSearchQuery(query)
    if (query.trim() === '') {
      setSearchResults([])
      setShowSearchResults(false)
      return
    }
    
    const lowerQuery = query.toLowerCase()
    const results = nodes.filter(node => 
      node.label?.toLowerCase().includes(lowerQuery) ||
      node.id?.toLowerCase().includes(lowerQuery)
    ).slice(0, 10)
    
    setSearchResults(results)
    setShowSearchResults(results.length > 0)
  }, [nodes])
  
  const handleSearchResultClick = useCallback((node) => {
    selectNode(node.id)
    flyTo(node.x, node.y, 1.5, 500)
    setShowSearchResults(false)
    setSearchQuery('')
  }, [selectNode, flyTo])
  
  // ==================== Controls ====================
  
  const handleZoomIn = useCallback(() => {
    zoom(1.3, canvasWidth / 2, canvasHeight / 2)
  }, [zoom, canvasWidth, canvasHeight])
  
  const handleZoomOut = useCallback(() => {
    zoom(0.7, canvasWidth / 2, canvasHeight / 2)
  }, [zoom, canvasWidth, canvasHeight])
  
  const handleFitView = useCallback(() => {
    zoomToFit(80)
  }, [zoomToFit])
  
  const handleResetView = useCallback(() => {
    resetView()
  }, [resetView])
  
  const handleRelayout = useCallback(() => {
    if (isLayoutRunning || nodes.length === 0) return
    
    const layout = new ForceLayout({
      repulsionForce: 3000,
      attractionForce: 0.008,
      centerForce: 0.0005,
    })
    layoutRef.current = layout
    
    layout.setGraph(nodes, edges)
    setLayoutRunning(true)
    
    layout.start(
      (updatedNodes) => {
        const updates = new Map()
        updatedNodes.forEach(n => updates.set(n.id, { x: n.x, y: n.y }))
        updateNodes(updates)
      },
      () => {
        setLayoutRunning(false)
        setTimeout(() => zoomToFit(80), 100)
      }
    )
  }, [nodes, edges, isLayoutRunning, updateNodes, setLayoutRunning, zoomToFit])
  
  // ==================== Render ====================
  
  const cursor = useMemo(() => {
    if (isDragging) return 'grabbing'
    if (isPanning) return 'grabbing'
    if (hoveredNodeId) return 'pointer'
    return 'grab'
  }, [isDragging, isPanning, hoveredNodeId])
  
  return (
    <div ref={containerRef} style={styles.container}>
      {/* Search box */}
      {showSearch && (
        <div style={styles.searchBox}>
          <input
            type="text"
            placeholder="Search nodes..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            onFocus={() => searchResults.length > 0 && setShowSearchResults(true)}
            onBlur={() => setTimeout(() => setShowSearchResults(false), 200)}
            style={styles.searchInput}
          />
          {showSearchResults && (
            <div style={styles.searchResults}>
              {searchResults.map(node => (
                <div
                  key={node.id}
                  style={styles.searchResult}
                  onClick={() => handleSearchResultClick(node)}
                  onMouseEnter={(e) => e.target.style.background = '#f5f5f5'}
                  onMouseLeave={(e) => e.target.style.background = 'white'}
                >
                  {node.label || node.id}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
      
      {/* Controls */}
      {showControls && (
        <div style={styles.controls}>
          <button 
            style={styles.controlButton} 
            onClick={handleZoomIn}
            title="Zoom in (+)"
          >
            +
          </button>
          <button 
            style={styles.controlButton} 
            onClick={handleZoomOut}
            title="Zoom out (-)"
          >
            −
          </button>
          <button 
            style={styles.controlButton} 
            onClick={handleFitView}
            title="Fit all nodes (F)"
          >
            ⊡
          </button>
          <button 
            style={styles.controlButton} 
            onClick={handleResetView}
            title="Reset view (0)"
          >
            ⌂
          </button>
          <button 
            style={{
              ...styles.controlButton,
              opacity: isLayoutRunning ? 0.5 : 1,
            }}
            onClick={handleRelayout}
            disabled={isLayoutRunning}
            title="Re-layout nodes"
          >
            🔄
          </button>
        </div>
      )}
      
      {/* Stats */}
      {showStats && (
        <div style={styles.stats}>
          Nodes: {nodes.length} | 
          Scale: {viewport.scale.toFixed(2)} | 
          Offset: ({viewport.offsetX.toFixed(0)}, {viewport.offsetY.toFixed(0)})
          {isLayoutRunning && ' | Layout running...'}
        </div>
      )}
      
      {/* Canvas */}
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{ ...styles.canvas, cursor }}
        tabIndex={0}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onClick={handleClick}
        onDoubleClick={handleDoubleClick}
        onWheel={handleWheel}
        onKeyDown={handleKeyDown}
      />
    </div>
  )
}

export default InfiniteCanvas
