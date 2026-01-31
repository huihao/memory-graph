import { useState, useEffect } from 'react'
import axios from 'axios'

function Dashboard({ apiUrl }) {
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

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
      
      <div style={{ marginTop: '30px' }}>
        <h3>Quick Actions</h3>
        <div style={{ display: 'flex', gap: '10px', marginTop: '15px' }}>
          <button onClick={convertToMarkdown} disabled={loading}>
            {loading ? 'Converting...' : '📝 Convert All to Markdown'}
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
