/**
 * Infinite Canvas Module
 * 
 * A high-performance, extensible infinite canvas for knowledge graphs,
 * whiteboards, and flowcharts.
 * 
 * Features:
 * - Infinite coordinate system (world/screen coordinate mapping)
 * - Pan/zoom/keyboard navigation
 * - 10k+ node rendering with quadtree spatial indexing
 * - Force-directed layout
 * - Node/edge interaction
 * - Minimap navigation
 * - Search with fly-to animation
 * - State management with Zustand
 */

export { InfiniteCanvas, default } from './InfiniteCanvas'
export { useCanvasStore } from './store'
export { CanvasRenderer } from './Renderer'
export { ForceLayout, initializePositions, arrangeByType } from './ForceLayout'
export { Quadtree, Rectangle, createQuadtree } from './Quadtree'
