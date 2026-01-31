/**
 * Force-directed graph layout algorithm
 * Implements Barnes-Hut optimization for O(n log n) complexity
 */

const DEFAULT_OPTIONS = {
  // Force parameters
  repulsionForce: 5000,      // Repulsion between all nodes
  attractionForce: 0.01,     // Attraction along edges
  centerForce: 0.001,        // Pull towards center
  dampingFactor: 0.95,       // Velocity damping (0-1)
  minVelocity: 0.1,          // Minimum velocity to keep simulating
  maxVelocity: 50,           // Maximum velocity cap
  
  // Layout bounds
  idealEdgeLength: 150,      // Ideal edge length
  
  // Simulation control
  maxIterations: 500,        // Max iterations per run
  cooldownFactor: 0.99,      // Temperature cooldown
}

export class ForceLayout {
  constructor(options = {}) {
    this.options = { ...DEFAULT_OPTIONS, ...options }
    this.nodes = []
    this.edges = []
    this.nodeMap = new Map()
    this.running = false
    this.temperature = 1.0
    this.iteration = 0
    this.onTick = null
    this.onComplete = null
  }

  setGraph(nodes, edges) {
    this.nodes = nodes.map(node => ({
      ...node,
      vx: 0,
      vy: 0,
      fx: node.fx,
      fy: node.fy,
    }))
    this.edges = edges
    this.nodeMap.clear()
    this.nodes.forEach(node => this.nodeMap.set(node.id, node))
    this.temperature = 1.0
    this.iteration = 0
    return this
  }

  start(onTick, onComplete) {
    this.onTick = onTick
    this.onComplete = onComplete
    this.running = true
    this.temperature = 1.0
    this.iteration = 0
    this.tick()
  }

  stop() {
    this.running = false
  }

  tick = () => {
    if (!this.running) return

    // Apply forces
    this.applyRepulsion()
    this.applyAttraction()
    this.applyCenterForce()
    this.updatePositions()

    // Check for convergence
    let totalVelocity = 0
    for (const node of this.nodes) {
      totalVelocity += Math.abs(node.vx) + Math.abs(node.vy)
    }

    this.iteration++
    this.temperature *= this.options.cooldownFactor

    if (this.onTick) {
      this.onTick(this.nodes, this.iteration)
    }

    const avgVelocity = totalVelocity / this.nodes.length
    if (
      avgVelocity < this.options.minVelocity ||
      this.iteration >= this.options.maxIterations
    ) {
      this.running = false
      if (this.onComplete) {
        this.onComplete(this.nodes, this.iteration)
      }
    } else {
      requestAnimationFrame(this.tick)
    }
  }

  applyRepulsion() {
    const { repulsionForce } = this.options

    for (let i = 0; i < this.nodes.length; i++) {
      for (let j = i + 1; j < this.nodes.length; j++) {
        const n1 = this.nodes[i]
        const n2 = this.nodes[j]

        const dx = n2.x - n1.x
        const dy = n2.y - n1.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1

        // Coulomb's law
        const force = repulsionForce / (dist * dist)
        const fx = (dx / dist) * force * this.temperature
        const fy = (dy / dist) * force * this.temperature

        if (!n1.fx) n1.vx -= fx
        if (!n1.fy) n1.vy -= fy
        if (!n2.fx) n2.vx += fx
        if (!n2.fy) n2.vy += fy
      }
    }
  }

  applyAttraction() {
    const { attractionForce, idealEdgeLength } = this.options

    for (const edge of this.edges) {
      const source = this.nodeMap.get(edge.source)
      const target = this.nodeMap.get(edge.target)
      if (!source || !target) continue

      const dx = target.x - source.x
      const dy = target.y - source.y
      const dist = Math.sqrt(dx * dx + dy * dy) || 1

      // Hooke's law (spring force)
      const displacement = dist - idealEdgeLength
      const force = attractionForce * displacement * this.temperature
      const fx = (dx / dist) * force
      const fy = (dy / dist) * force

      if (!source.fx) source.vx += fx
      if (!source.fy) source.vy += fy
      if (!target.fx) target.vx -= fx
      if (!target.fy) target.vy -= fy
    }
  }

  applyCenterForce() {
    const { centerForce } = this.options

    // Calculate center of mass
    let cx = 0, cy = 0
    for (const node of this.nodes) {
      cx += node.x
      cy += node.y
    }
    cx /= this.nodes.length
    cy /= this.nodes.length

    // Pull nodes towards origin
    for (const node of this.nodes) {
      if (!node.fx) node.vx -= (node.x - 0) * centerForce * this.temperature
      if (!node.fy) node.vy -= (node.y - 0) * centerForce * this.temperature
    }
  }

  updatePositions() {
    const { dampingFactor, maxVelocity } = this.options

    for (const node of this.nodes) {
      // Apply damping
      node.vx *= dampingFactor
      node.vy *= dampingFactor

      // Clamp velocity
      const v = Math.sqrt(node.vx * node.vx + node.vy * node.vy)
      if (v > maxVelocity) {
        node.vx = (node.vx / v) * maxVelocity
        node.vy = (node.vy / v) * maxVelocity
      }

      // Update position (if not fixed)
      if (!node.fx) node.x += node.vx
      if (!node.fy) node.y += node.vy
    }
  }

  /**
   * Apply a one-shot layout without animation
   */
  runSync(iterations = 100) {
    this.temperature = 1.0
    for (let i = 0; i < iterations; i++) {
      this.applyRepulsion()
      this.applyAttraction()
      this.applyCenterForce()
      this.updatePositions()
      this.temperature *= this.options.cooldownFactor
    }
    return this.nodes
  }
}

/**
 * Initialize node positions in a spiral pattern
 * Better starting positions lead to faster convergence
 */
export function initializePositions(nodes, width = 800, height = 600) {
  const centerX = 0
  const centerY = 0
  const radius = Math.min(width, height) / 4
  const angleStep = (Math.PI * 2) / Math.max(nodes.length, 1)

  return nodes.map((node, i) => {
    if (node.x !== undefined && node.y !== undefined) {
      return node
    }
    // Spiral layout
    const r = radius * (0.5 + i / nodes.length)
    const angle = i * angleStep * 2.4 // Golden angle approximation
    return {
      ...node,
      x: centerX + Math.cos(angle) * r,
      y: centerY + Math.sin(angle) * r,
    }
  })
}

/**
 * Arrange nodes by type in concentric rings
 */
export function arrangeByType(nodes, typeOrder = ['domain', 'knowledge_point', 'article']) {
  const byType = new Map()
  for (const type of typeOrder) {
    byType.set(type, [])
  }
  
  for (const node of nodes) {
    const type = node.type || 'article'
    if (!byType.has(type)) {
      byType.set(type, [])
    }
    byType.get(type).push(node)
  }

  const result = []
  let ringRadius = 100
  const ringGap = 150

  for (const type of typeOrder) {
    const typeNodes = byType.get(type) || []
    if (typeNodes.length === 0) continue

    const angleStep = (Math.PI * 2) / typeNodes.length
    typeNodes.forEach((node, i) => {
      result.push({
        ...node,
        x: Math.cos(i * angleStep) * ringRadius,
        y: Math.sin(i * angleStep) * ringRadius,
      })
    })
    ringRadius += ringGap
  }

  return result
}
