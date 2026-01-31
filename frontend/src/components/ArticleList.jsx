import { useState, useEffect } from 'react'
import axios from 'axios'

function ArticleList({ apiUrl }) {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedArticle, setSelectedArticle] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedDomain, setSelectedDomain] = useState(null)
  const [domains, setDomains] = useState([])

  useEffect(() => {
    loadArticles()
    loadDomains()
  }, [])

  const loadArticles = async () => {
    try {
      const response = await axios.get(`${apiUrl}/articles?limit=1000`)
      setArticles(response.data.articles)
      setLoading(false)
    } catch (err) {
      setError(err.message)
      setLoading(false)
    }
  }

  const loadDomains = async () => {
    try {
      const response = await axios.get(`${apiUrl}/domains`)
      setDomains(response.data)
    } catch (err) {
      console.error('Error loading domains:', err)
    }
  }

  const filteredArticles = articles.filter(article => {
    const matchesSearch = article.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         article.url.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesDomain = !selectedDomain || 
                         article.domains.some(d => d.id === selectedDomain)
    return matchesSearch && matchesDomain
  })

  if (loading) return <div className="loading">Loading articles...</div>
  if (error) return <div className="error">Error: {error}</div>

  if (selectedArticle) {
    return (
      <div>
        <button onClick={() => setSelectedArticle(null)} style={{ marginBottom: '20px' }}>
          ← Back to List
        </button>
        <ArticleDetail article={selectedArticle} apiUrl={apiUrl} />
      </div>
    )
  }

  return (
    <div>
      <h2>Articles ({filteredArticles.length})</h2>
      
      <input
        type="text"
        className="search-box"
        placeholder="Search articles..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />

      {domains.length > 0 && (
        <div className="filter-section">
          <h3>Filter by Domain</h3>
          <div className="filter-item" onClick={() => setSelectedDomain(null)}>
            All Domains
          </div>
          {domains.map(domain => (
            <div
              key={domain.id}
              className={`filter-item ${selectedDomain === domain.id ? 'selected' : ''}`}
              onClick={() => setSelectedDomain(domain.id)}
            >
              {domain.name} ({domain.articles?.length || 0})
            </div>
          ))}
        </div>
      )}

      <div className="article-list">
        {filteredArticles.map(article => (
          <div 
            key={article.id} 
            className="article-card"
            onClick={() => setSelectedArticle(article)}
          >
            <div className="article-title">{article.title}</div>
            <div className="article-url">{article.url}</div>
            <div className="article-tags">
              {article.domains.map(domain => (
                <span key={domain.id} className="tag domain">
                  {domain.name}
                </span>
              ))}
              {article.knowledge_points.map(kp => (
                <span key={kp.id} className="tag">
                  {kp.name}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {filteredArticles.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          No articles found. Use the browser extension to add bookmarks.
        </div>
      )}
    </div>
  )
}

function ArticleDetail({ article, apiUrl }) {
  const [related, setRelated] = useState({ by_domain: [], by_knowledge_point: [] })

  useEffect(() => {
    loadRelated()
  }, [article.id])

  const loadRelated = async () => {
    try {
      const response = await axios.get(`${apiUrl}/articles/${article.id}/related`)
      setRelated(response.data)
    } catch (err) {
      console.error('Error loading related articles:', err)
    }
  }

  return (
    <div>
      <h2>{article.title}</h2>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        <a href={article.url} target="_blank" rel="noopener noreferrer">
          {article.url}
        </a>
      </p>

      {article.domains.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <h3>Domains</h3>
          <div className="article-tags">
            {article.domains.map(domain => (
              <span key={domain.id} className="tag domain">
                {domain.name}
              </span>
            ))}
          </div>
        </div>
      )}

      {article.knowledge_points.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <h3>Knowledge Points</h3>
          <div className="article-tags">
            {article.knowledge_points.map(kp => (
              <span key={kp.id} className="tag">
                {kp.name}
              </span>
            ))}
          </div>
        </div>
      )}

      {article.content && (
        <div style={{ marginBottom: '20px' }}>
          <h3>Content Preview</h3>
          <div style={{ 
            padding: '15px', 
            background: '#f8f9fa', 
            borderRadius: '4px',
            maxHeight: '400px',
            overflow: 'auto'
          }}>
            {article.content.substring(0, 2000)}...
          </div>
        </div>
      )}

      {(related.by_domain.length > 0 || related.by_knowledge_point.length > 0) && (
        <div>
          <h3>Related Articles</h3>
          {related.by_domain.length > 0 && (
            <div style={{ marginBottom: '15px' }}>
              <h4 style={{ fontSize: '14px', color: '#666' }}>Same Domain</h4>
              {related.by_domain.map(rel => (
                <div key={rel.id} style={{ padding: '5px 0' }}>
                  • <a href={rel.url} target="_blank" rel="noopener noreferrer">{rel.title}</a>
                </div>
              ))}
            </div>
          )}
          {related.by_knowledge_point.length > 0 && (
            <div>
              <h4 style={{ fontSize: '14px', color: '#666' }}>Same Knowledge Points</h4>
              {related.by_knowledge_point.map(rel => (
                <div key={rel.id} style={{ padding: '5px 0' }}>
                  • <a href={rel.url} target="_blank" rel="noopener noreferrer">{rel.title}</a>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ArticleList
