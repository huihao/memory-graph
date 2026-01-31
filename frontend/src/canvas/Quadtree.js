/**
 * Quadtree spatial index for efficient viewport culling
 * Supports 10k+ nodes with O(log n) query time
 */

export class Rectangle {
  constructor(x, y, width, height) {
    this.x = x
    this.y = y
    this.width = width
    this.height = height
  }

  contains(point) {
    return (
      point.x >= this.x &&
      point.x <= this.x + this.width &&
      point.y >= this.y &&
      point.y <= this.y + this.height
    )
  }

  intersects(range) {
    return !(
      range.x > this.x + this.width ||
      range.x + range.width < this.x ||
      range.y > this.y + this.height ||
      range.y + range.height < this.y
    )
  }
}

export class Quadtree {
  constructor(boundary, capacity = 8) {
    this.boundary = boundary
    this.capacity = capacity
    this.points = []
    this.divided = false
    this.northeast = null
    this.northwest = null
    this.southeast = null
    this.southwest = null
  }

  subdivide() {
    const x = this.boundary.x
    const y = this.boundary.y
    const w = this.boundary.width / 2
    const h = this.boundary.height / 2

    const ne = new Rectangle(x + w, y, w, h)
    const nw = new Rectangle(x, y, w, h)
    const se = new Rectangle(x + w, y + h, w, h)
    const sw = new Rectangle(x, y + h, w, h)

    this.northeast = new Quadtree(ne, this.capacity)
    this.northwest = new Quadtree(nw, this.capacity)
    this.southeast = new Quadtree(se, this.capacity)
    this.southwest = new Quadtree(sw, this.capacity)

    this.divided = true
  }

  insert(point) {
    if (!this.boundary.contains(point)) {
      return false
    }

    if (this.points.length < this.capacity && !this.divided) {
      this.points.push(point)
      return true
    }

    if (!this.divided) {
      this.subdivide()
      // Redistribute existing points
      const oldPoints = this.points
      this.points = []
      for (const p of oldPoints) {
        this.northeast.insert(p) ||
        this.northwest.insert(p) ||
        this.southeast.insert(p) ||
        this.southwest.insert(p)
      }
    }

    return (
      this.northeast.insert(point) ||
      this.northwest.insert(point) ||
      this.southeast.insert(point) ||
      this.southwest.insert(point)
    )
  }

  query(range, found = []) {
    if (!this.boundary.intersects(range)) {
      return found
    }

    for (const p of this.points) {
      if (range.contains(p)) {
        found.push(p)
      }
    }

    if (this.divided) {
      this.northwest.query(range, found)
      this.northeast.query(range, found)
      this.southwest.query(range, found)
      this.southeast.query(range, found)
    }

    return found
  }

  clear() {
    this.points = []
    this.divided = false
    this.northeast = null
    this.northwest = null
    this.southeast = null
    this.southwest = null
  }
}

/**
 * Create a quadtree from a list of nodes
 * @param {Array} nodes - Array of node objects with x, y properties
 * @param {Object} bounds - Optional custom bounds {x, y, width, height}
 * @returns {Quadtree}
 */
export function createQuadtree(nodes, bounds = null) {
  if (!bounds && nodes.length > 0) {
    // Calculate bounds from nodes with some padding
    let minX = Infinity, minY = Infinity
    let maxX = -Infinity, maxY = -Infinity
    
    for (const node of nodes) {
      const radius = node.radius || 20
      minX = Math.min(minX, node.x - radius)
      minY = Math.min(minY, node.y - radius)
      maxX = Math.max(maxX, node.x + radius)
      maxY = Math.max(maxY, node.y + radius)
    }
    
    const padding = 100
    bounds = new Rectangle(
      minX - padding,
      minY - padding,
      maxX - minX + padding * 2,
      maxY - minY + padding * 2
    )
  } else if (!bounds) {
    // Default bounds for empty graph
    bounds = new Rectangle(-10000, -10000, 20000, 20000)
  }

  const qt = new Quadtree(bounds)
  for (const node of nodes) {
    qt.insert(node)
  }
  return qt
}
