import os
from typing import List, Dict, Any
import aiohttp
from bs4 import BeautifulSoup
import openai
import json

class LLMService:
    """Service for interacting with Large Language Models"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
    
    async def analyze_article(
        self,
        title: str,
        content: str,
        existing_domains: List[str] = None,
        existing_knowledge_points: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze article content to determine domains and knowledge points
        
        Args:
            title: Article title
            content: Article content
            
        Returns:
            Dictionary with 'domains' and 'knowledge_points' lists
        """
        domain_hint = ", ".join(existing_domains or [])
        knowledge_point_hint = ", ".join(existing_knowledge_points or [])
        prompt = f"""
        Analyze the following article and extract:
        1. The main domain(s) or field(s) it belongs to (e.g., "Machine Learning", "Web Development", "Cloud Computing")
        2. Key knowledge points or concepts covered in the article
        3. Prefer using existing domains/knowledge points when relevant to keep taxonomy consistent.
        
        Article Title: {title}
        
        Article Content (first 2000 chars):
        {content[:2000]}

        Existing Domains: [{domain_hint}]
        Existing Knowledge Points: [{knowledge_point_hint}]
        
        Please respond in JSON format:
        {{
            "domains": ["domain1", "domain2"],
            "knowledge_points": ["concept1", "concept2", "concept3"]
        }}
        """
        
        try:
            if self.openai_api_key:
                response = await self._call_openai(prompt)
            else:
                # Fallback to simple keyword-based analysis
                response = self._simple_analysis(title, content, existing_domains, existing_knowledge_points)
            
            return response
        except Exception as e:
            print(f"Error analyzing article: {e}")
            return {"domains": ["General"], "knowledge_points": []}
    
    async def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API"""
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes articles and extracts domains and knowledge points. Always respond in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            
            content = response.choices[0].message.content
            # Try to parse JSON from the response
            try:
                result = json.loads(content)
                return result
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                    return json.loads(json_str)
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                    return json.loads(json_str)
                else:
                    return {"domains": ["General"], "knowledge_points": []}
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return {"domains": ["General"], "knowledge_points": []}
    
    def _simple_analysis(
        self,
        title: str,
        content: str,
        existing_domains: List[str] = None,
        existing_knowledge_points: List[str] = None,
    ) -> Dict[str, Any]:
        """Simple keyword-based analysis as fallback"""
        # Keywords mapping to domains
        domain_keywords = {
            "Machine Learning": ["machine learning", "neural network", "deep learning", "ai", "model training"],
            "Web Development": ["javascript", "html", "css", "react", "vue", "frontend", "backend"],
            "Cloud Computing": ["aws", "azure", "gcp", "cloud", "kubernetes", "docker"],
            "Database": ["sql", "database", "postgresql", "mysql", "mongodb"],
            "DevOps": ["devops", "ci/cd", "jenkins", "github actions", "deployment"],
            "Security": ["security", "encryption", "authentication", "vulnerability"],
        }
        
        text = (title + " " + content).lower()
        detected_domains = []
        detected_knowledge_points = []
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in text for keyword in keywords):
                detected_domains.append(domain)

        for domain in existing_domains or []:
            if domain.lower() in text:
                detected_domains.append(domain)

        for kp in existing_knowledge_points or []:
            if kp.lower() in text:
                detected_knowledge_points.append(kp)
        
        if not detected_domains:
            detected_domains = ["General"]
        
        # Extract key phrases as knowledge points (simplified)
        words = text.split()
        knowledge_points = detected_knowledge_points

        return {
            "domains": detected_domains[:3],  # Limit to top 3 domains
            "knowledge_points": knowledge_points[:5]  # Limit to top 5 points
        }

class ContentExtractor:
    """Service for extracting content from web pages"""
    
    ALLOWED_SCHEMES = {'http', 'https'}
    BLOCKED_HOSTS = {'localhost', '127.0.0.1', '0.0.0.0', '169.254.169.254'}  # Block local and metadata IPs
    
    def _validate_url(self, url: str) -> bool:
        """
        Validate URL to prevent SSRF attacks
        
        Args:
            url: The URL to validate
            
        Returns:
            True if URL is safe, False otherwise
        """
        try:
            from urllib.parse import urlparse
            import ipaddress
            
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in self.ALLOWED_SCHEMES:
                return False
            
            # Check for blocked hosts
            hostname = parsed.hostname
            if not hostname:
                return False
            
            # Block localhost variations
            if hostname.lower() in self.BLOCKED_HOSTS:
                return False
            
            # Block private IP ranges
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local:
                    return False
            except ValueError:
                # Not an IP address, hostname is fine
                pass
            
            return True
        except Exception:
            return False
    
    async def extract_content(self, url: str) -> Dict[str, str]:
        """
        Extract title and content from a URL
        
        Args:
            url: The URL to extract content from
            
        Returns:
            Dictionary with 'title' and 'content'
        """
        # Validate URL to prevent SSRF
        if not self._validate_url(url):
            return {
                "title": "Invalid URL",
                "content": "URL validation failed. Only http/https URLs to public hosts are allowed."
            }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30, allow_redirects=True, max_redirects=5) as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract title
                    title = soup.title.string if soup.title else url
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # Get text content
                    text = soup.get_text()
                    
                    # Clean up text
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    content = ' '.join(chunk for chunk in chunks if chunk)
                    
                    return {
                        "title": title.strip(),
                        "content": content
                    }
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return {
                "title": url,
                "content": ""
            }
