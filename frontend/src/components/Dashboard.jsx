import { useState, useEffect } from 'react'
import axios from 'axios'

function Dashboard({ apiUrl }) {
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [stats, setStats] = useState(null)
  const [statsLoading, setStatsLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const response = await axios.get(`${apiUrl}/stats`)
      setStats(response.data)
    } catch (error) {
      console.error('Error loading stats:', error)
    } finally {
      setStatsLoading(false)
    }
  }

  const convertToMarkdown = async () => {
    setLoading(true)
    setMessage('')
    try {
      const response = await axios.post(`${apiUrl}/tasks/convert-to-markdown`)
      setMessage(`✅ Successfully converted ${response.data.converted} articles to Markdown!`)
    } catch (error) {
      setMessage(`❌ Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2>Dashboard</h2>
      <p>Welcome to Memory Graph! This tool helps you organize and visualize your bookmarked articles.</p>
      
      {/* Statistics Section */}
      {!statsLoading && stats && (
        <div style={{ marginTop: '30px' }}>
          <h3>📊 Overview</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px', marginTop: '15px' }}>
            <div style={{ padding: '20px', background: '#e3f2fd', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#1976d2' }}>{stats.total_articles}</div>
              <div style={{ color: '#666', marginTop: '5px' }}>Total Articles</div>
            </div>
            <div style={{ padding: '20px', background: '#f3e5f5', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#7b1fa2' }}>{stats.total_domains}</div>
              <div style={{ color: '#666', marginTop: '5px' }}>Domains</div>
            </div>
            <div style={{ padding: '20px', background: '#fff3e0', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#e65100' }}>{stats.total_knowledge_points}</div>
              <div style={{ color: '#666', marginTop: '5px' }}>Knowledge Points</div>
            </div>
            <div style={{ padding: '20px', background: '#e8f5e9', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#388e3c' }}>{stats.recent_articles}</div>
              <div style={{ color: '#666', marginTop: '5px' }}>Added This Week</div>
            </div>
          </div>
          
          {/* Top Domains */}
          {stats.top_domains && stats.top_domains.length > 0 && (
            <div style={{ marginTop: '25px' }}>
              <h4 style={{ marginBottom: '10px' }}>🏆 Top Domains</h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                {stats.top_domains.map(domain => (
                  <div 
                    key={domain.id} 
                    style={{ 
                      padding: '8px 16px', 
                      background: '#f5f5f5', 
                      borderRadius: '20px',
                      fontSize: '14px'
                    }}
                  >
                    {domain.name} <span style={{ color: '#666' }}>({domain.article_count})</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      <div style={{ marginTop: '30px' }}>
        <h3>Quick Actions</h3>
        <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
          <button onClick={convertToMarkdown} disabled={loading}>
            {loading ? 'Converting...' : '📝 Convert All to Markdown'}
          </button>
          <button onClick={loadStats} disabled={statsLoading}>
            🔄 Refresh Stats
          </button>
        </div>
        {message && (
          <div style={{ 
            marginTop: '15px', 
            padding: '15px', 
            background: message.startsWith('✅') ? '#d4edda' : '#f8d7da',
            borderRadius: '4px'
          }}>
            {message}
          </div>
        )}
      </div>

      <div style={{ marginTop: '40px' }}>
        <h3>How to Use</h3>
        <ol style={{ marginLeft: '20px', lineHeight: '1.8' }}>
          <li>Install the browser extension</li>
          <li>Configure the backend URL in extension settings</li>
          <li>Click "Process All Bookmarks" to analyze your bookmarks</li>
          <li>View and organize articles in this interface</li>
          <li>Export articles to Obsidian markdown format</li>
          <li>Explore the knowledge graph to see connections</li>
        </ol>
      </div>
    </div>
  )
}

export default Dashboard
