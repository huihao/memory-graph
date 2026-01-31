import { useState, useEffect } from 'react'
import ArticleList from './components/ArticleList'
import KnowledgeGraph from './components/KnowledgeGraphNew'
import Dashboard from './components/Dashboard'
import axios from 'axios'

const API_URL = 'http://localhost:8000/api'

function App() {
  const [view, setView] = useState('dashboard')
  const [stats, setStats] = useState({
    totalArticles: 0,
    totalDomains: 0,
    totalKnowledgePoints: 0
  })

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      // Use the optimized stats endpoint instead of multiple requests
      const response = await axios.get(`${API_URL}/stats`)
      
      setStats({
        totalArticles: response.data.total_articles,
        totalDomains: response.data.total_domains,
        totalKnowledgePoints: response.data.total_knowledge_points
      })
    } catch (error) {
      console.error('Error loading stats:', error)
      // Fallback to individual requests if stats endpoint fails
      try {
        const [articlesRes, domainsRes, kpRes] = await Promise.all([
          axios.get(`${API_URL}/articles`),
          axios.get(`${API_URL}/domains`),
          axios.get(`${API_URL}/knowledge-points`)
        ])
        
        setStats({
          totalArticles: articlesRes.data.total,
          totalDomains: domainsRes.data.length,
          totalKnowledgePoints: kpRes.data.length
        })
      } catch (fallbackError) {
        console.error('Error loading stats (fallback):', fallbackError)
      }
    }
  }

  return (
    <div className="container">
      <div className="header">
        <h1>📚 Memory Graph - Knowledge Manager</h1>
        <div className="stats">
          <div className="stat-item">
            <div className="stat-label">Articles</div>
            <div className="stat-value">{stats.totalArticles}</div>
          </div>
          <div className="stat-item">
            <div className="stat-label">Domains</div>
            <div className="stat-value">{stats.totalDomains}</div>
          </div>
          <div className="stat-item">
            <div className="stat-label">Knowledge Points</div>
            <div className="stat-value">{stats.totalKnowledgePoints}</div>
          </div>
        </div>
      </div>

      <div className="content">
        <div className="sidebar">
          <div 
            className={`nav-item ${view === 'dashboard' ? 'active' : ''}`}
            onClick={() => setView('dashboard')}
          >
            📊 Dashboard
          </div>
          <div 
            className={`nav-item ${view === 'articles' ? 'active' : ''}`}
            onClick={() => setView('articles')}
          >
            📄 Articles
          </div>
          <div 
            className={`nav-item ${view === 'graph' ? 'active' : ''}`}
            onClick={() => setView('graph')}
          >
            🕸️ Knowledge Graph
          </div>
        </div>

        <div className="main-content">
          {view === 'dashboard' && <Dashboard apiUrl={API_URL} />}
          {view === 'articles' && <ArticleList apiUrl={API_URL} />}
          {view === 'graph' && <KnowledgeGraph apiUrl={API_URL} />}
        </div>
      </div>
    </div>
  )
}

export default App
