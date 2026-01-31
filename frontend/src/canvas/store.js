/**
 * Zustand store for infinite canvas state management
 * Manages nodes, edges, groups, viewport, and selection state
 */
import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { createQuadtree, Rectangle } from './Quadtree'

/**
 * Node interface:
 * {
 *   id: string
 *   x: number
 *   y: number
 *   radius: number
 *   type: 'article' | 'domain' | 'knowledge_point' | 'group'
 *   label: string
 *   data: object (custom data)
 *   groupId?: string (parent group)
 *   collapsed?: boolean (for groups)
 * }
 * 
 * Edge interface:
 * {
 *   id: string
 *   source: string (node id)
 *   target: string (node id)
 *   type: string
 *   weight?: number
 *   data?: object
 * }
 */

const DEFAULT_VIEWPORT = {
  offsetX: 0,
  offsetY: 0,
  scale: 1,
  minScale: 0.1,
  maxScale: 5,
}

const initialState = {
  // Scene data
  nodes: [],
  edges: [],
  groups: [],
  
  // Spatial index
  quadtree: null,
  
  // Viewport (camera)
  viewport: { ...DEFAULT_VIEWPORT },
  
  // Canvas dimensions
  canvasWidth: 1100,
  canvasHeight: 650,
  
  // Selection state
  selectedNodeIds: new Set(),
  selectedEdgeIds: new Set(),
  hoveredNodeId: null,
  hoveredEdgeId: null,
  
  // Interaction state
  isDragging: false,
  isPanning: false,
  draggedNodeId: null,
  dragStart: null,
  
  // Layout state
  isLayoutRunning: false,
  
  // UI state
  showMinimap: true,
  showGrid: false,
  snapToGrid: false,
  gridSize: 20,
  
  // Performance tracking
  visibleNodeCount: 0,
  totalNodeCount: 0,
  lastRenderTime: 0,
}

export const useCanvasStore = create(
  subscribeWithSelector((set, get) => ({
    ...initialState,
    
    // ==================== Scene Actions ====================
    
    setNodes: (nodes) => {
      const qt = createQuadtree(nodes)
      set({ 
        nodes, 
        quadtree: qt,
        totalNodeCount: nodes.length,
      })
    },
    
    setEdges: (edges) => set({ edges }),
    
    setGraph: (nodes, edges) => {
      const qt = createQuadtree(nodes)
      set({
        nodes,
        edges,
        quadtree: qt,
        totalNodeCount: nodes.length,
      })
    },
    
    updateNode: (nodeId, updates) => {
      const nodes = get().nodes.map(n => 
        n.id === nodeId ? { ...n, ...updates } : n
      )
      const qt = createQuadtree(nodes)
      set({ nodes, quadtree: qt })
    },
    
    updateNodes: (nodeUpdates) => {
      // nodeUpdates is a Map<nodeId, updates>
      const nodes = get().nodes.map(n => {
        const updates = nodeUpdates.get(n.id)
        return updates ? { ...n, ...updates } : n
      })
      const qt = createQuadtree(nodes)
      set({ nodes, quadtree: qt })
    },
    
    addNode: (node) => {
      const nodes = [...get().nodes, node]
      const qt = createQuadtree(nodes)
      set({ nodes, quadtree: qt, totalNodeCount: nodes.length })
    },
    
    removeNode: (nodeId) => {
      const nodes = get().nodes.filter(n => n.id !== nodeId)
      const edges = get().edges.filter(e => 
        e.source !== nodeId && e.target !== nodeId
      )
      const qt = createQuadtree(nodes)
      set({ nodes, edges, quadtree: qt, totalNodeCount: nodes.length })
    },
    
    addEdge: (edge) => {
      const edges = [...get().edges, edge]
      set({ edges })
    },
    
    removeEdge: (edgeId) => {
      const edges = get().edges.filter(e => e.id !== edgeId)
      set({ edges })
    },
    
    // ==================== Viewport Actions ====================
    
    setViewport: (viewport) => set({ viewport: { ...get().viewport, ...viewport } }),
    
    pan: (dx, dy) => {
      const { viewport } = get()
      // When mouse moves right (positive dx), we want to see content on the right
      // which means offsetX should increase (we're looking at higher world x coordinates)
      set({
        viewport: {
          ...viewport,
          offsetX: viewport.offsetX + dx / viewport.scale,
          offsetY: viewport.offsetY + dy / viewport.scale,
        }
      })
    },
    
    /**
     * Zoom centered on a point (mouse position)
     * @param {number} delta - Zoom factor (>1 zoom in, <1 zoom out)
     * @param {number} pivotX - Screen X coordinate of zoom center
     * @param {number} pivotY - Screen Y coordinate of zoom center
     */
    zoom: (delta, pivotX, pivotY) => {
      const { viewport } = get()
      const newScale = Math.max(
        viewport.minScale,
        Math.min(viewport.maxScale, viewport.scale * delta)
      )
      
      // Calculate the world position of the pivot before zoom
      const worldX = pivotX / viewport.scale + viewport.offsetX
      const worldY = pivotY / viewport.scale + viewport.offsetY
      
      // After zoom, we want the same world position to be at the pivot
      const newOffsetX = worldX - pivotX / newScale
      const newOffsetY = worldY - pivotY / newScale
      
      set({
        viewport: {
          ...viewport,
          scale: newScale,
          offsetX: newOffsetX,
          offsetY: newOffsetY,
        }
      })
    },
    
    zoomToFit: (padding = 50) => {
      const { nodes, canvasWidth, canvasHeight } = get()
      if (nodes.length === 0) {
        set({ viewport: { ...DEFAULT_VIEWPORT } })
        return
      }
      
      let minX = Infinity, minY = Infinity
      let maxX = -Infinity, maxY = -Infinity
      
      for (const node of nodes) {
        const r = node.radius || 20
        minX = Math.min(minX, node.x - r)
        minY = Math.min(minY, node.y - r)
        maxX = Math.max(maxX, node.x + r)
        maxY = Math.max(maxY, node.y + r)
      }
      
      const graphWidth = maxX - minX
      const graphHeight = maxY - minY
      const scale = Math.min(
        (canvasWidth - padding * 2) / graphWidth,
        (canvasHeight - padding * 2) / graphHeight,
        2 // Max scale
      )
      
      const offsetX = minX - (canvasWidth / scale - graphWidth) / 2
      const offsetY = minY - (canvasHeight / scale - graphHeight) / 2
      
      set({
        viewport: {
          ...get().viewport,
          scale,
          offsetX,
          offsetY,
        }
      })
    },
    
    flyTo: (x, y, targetScale = 1, duration = 500) => {
      const { viewport, canvasWidth, canvasHeight } = get()
      const startOffset = { x: viewport.offsetX, y: viewport.offsetY }
      const startScale = viewport.scale
      
      // Target: center the point on the canvas
      const targetOffset = {
        x: x - canvasWidth / (2 * targetScale),
        y: y - canvasHeight / (2 * targetScale),
      }
      
      const startTime = performance.now()
      
      const animate = (time) => {
        const elapsed = time - startTime
        const progress = Math.min(elapsed / duration, 1)
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3)
        
        const currentOffset = {
          x: startOffset.x + (targetOffset.x - startOffset.x) * eased,
          y: startOffset.y + (targetOffset.y - startOffset.y) * eased,
        }
        const currentScale = startScale + (targetScale - startScale) * eased
        
        set({
          viewport: {
            ...get().viewport,
            offsetX: currentOffset.x,
            offsetY: currentOffset.y,
            scale: currentScale,
          }
        })
        
        if (progress < 1) {
          requestAnimationFrame(animate)
        }
      }
      
      requestAnimationFrame(animate)
    },
    
    resetView: () => set({ viewport: { ...DEFAULT_VIEWPORT } }),
    
    setCanvasDimensions: (width, height) => set({
      canvasWidth: width,
      canvasHeight: height,
    }),
    
    // ==================== Selection Actions ====================
    
    selectNode: (nodeId, append = false) => {
      const { selectedNodeIds } = get()
      if (append) {
        const newSet = new Set(selectedNodeIds)
        if (newSet.has(nodeId)) {
          newSet.delete(nodeId)
        } else {
          newSet.add(nodeId)
        }
        set({ selectedNodeIds: newSet })
      } else {
        set({ selectedNodeIds: new Set([nodeId]) })
      }
    },
    
    selectNodes: (nodeIds) => set({ selectedNodeIds: new Set(nodeIds) }),
    
    clearSelection: () => set({
      selectedNodeIds: new Set(),
      selectedEdgeIds: new Set(),
    }),
    
    setHoveredNode: (nodeId) => set({ hoveredNodeId: nodeId }),
    
    // ==================== Interaction Actions ====================
    
    startDrag: (nodeId, x, y) => set({
      isDragging: true,
      draggedNodeId: nodeId,
      dragStart: { x, y },
    }),
    
    endDrag: () => set({
      isDragging: false,
      draggedNodeId: null,
      dragStart: null,
    }),
    
    startPan: (x, y) => set({
      isPanning: true,
      dragStart: { x, y },
    }),
    
    endPan: () => set({
      isPanning: false,
      dragStart: null,
    }),
    
    // ==================== Layout Actions ====================
    
    setLayoutRunning: (running) => set({ isLayoutRunning: running }),
    
    // ==================== UI Actions ====================
    
    toggleMinimap: () => set({ showMinimap: !get().showMinimap }),
    toggleGrid: () => set({ showGrid: !get().showGrid }),
    toggleSnapToGrid: () => set({ snapToGrid: !get().snapToGrid }),
    setGridSize: (size) => set({ gridSize: size }),
    
    // ==================== Query Helpers ====================
    
    /**
     * Get visible nodes in the current viewport
     */
    getVisibleNodes: () => {
      const { quadtree, viewport, canvasWidth, canvasHeight } = get()
      if (!quadtree) return []
      
      // Calculate viewport bounds in world coordinates
      const viewportRect = new Rectangle(
        viewport.offsetX,
        viewport.offsetY,
        canvasWidth / viewport.scale,
        canvasHeight / viewport.scale
      )
      
      return quadtree.query(viewportRect)
    },
    
    /**
     * Convert screen coordinates to world coordinates
     */
    screenToWorld: (screenX, screenY) => {
      const { viewport } = get()
      return {
        x: screenX / viewport.scale + viewport.offsetX,
        y: screenY / viewport.scale + viewport.offsetY,
      }
    },
    
    /**
     * Convert world coordinates to screen coordinates
     */
    worldToScreen: (worldX, worldY) => {
      const { viewport } = get()
      return {
        x: (worldX - viewport.offsetX) * viewport.scale,
        y: (worldY - viewport.offsetY) * viewport.scale,
      }
    },
    
    /**
     * Find node at a given screen position
     */
    getNodeAtPosition: (screenX, screenY) => {
      const { nodes, viewport } = get()
      const worldPos = get().screenToWorld(screenX, screenY)
      
      // Check in reverse order (topmost first)
      for (let i = nodes.length - 1; i >= 0; i--) {
        const node = nodes[i]
        const dx = worldPos.x - node.x
        const dy = worldPos.y - node.y
        const radius = node.radius || 20
        if (dx * dx + dy * dy <= radius * radius) {
          return node
        }
      }
      return null
    },
    
    /**
     * Find nodes within a rectangle (for box selection)
     */
    getNodesInRect: (x1, y1, x2, y2) => {
      const { nodes } = get()
      const minX = Math.min(x1, x2)
      const maxX = Math.max(x1, x2)
      const minY = Math.min(y1, y2)
      const maxY = Math.max(y1, y2)
      
      return nodes.filter(node => {
        return node.x >= minX && node.x <= maxX &&
               node.y >= minY && node.y <= maxY
      })
    },
    
    setVisibleNodeCount: (count) => set({ visibleNodeCount: count }),
    setLastRenderTime: (time) => set({ lastRenderTime: time }),
  }))
)

export default useCanvasStore
