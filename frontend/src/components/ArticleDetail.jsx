import { useState, useEffect } from 'react'

function ArticleDetail({ article, apiUrl }) {
  return (
    <div>
      <h2>{article.title}</h2>
      <p>View article details here</p>
    </div>
  )
}

export default ArticleDetail
