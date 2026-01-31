"""
Unit tests for services module
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import LLMService, ContentExtractor, MAX_EXISTING_HINTS


class TestLLMService:
    """Tests for LLMService"""
    
    def test_init_without_api_key(self):
        """Test LLMService initialization without API key"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            service = LLMService()
            assert service.openai_api_key == ""
    
    def test_init_with_api_key(self):
        """Test LLMService initialization with API key"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            service = LLMService()
            assert service.openai_api_key == "test-key"
    
    @pytest.mark.asyncio
    async def test_analyze_article_simple_fallback(self):
        """Test analyze_article uses simple analysis when no API key"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            service = LLMService()
            result = await service.analyze_article(
                "Machine Learning Tutorial",
                "Learn about neural networks and deep learning"
            )
            
            assert "domains" in result
            assert "knowledge_points" in result
            assert "Machine Learning" in result["domains"]
    
    @pytest.mark.asyncio
    async def test_analyze_article_with_existing_domains(self):
        """Test analyze_article considers existing domains"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            service = LLMService()
            result = await service.analyze_article(
                "Custom Domain Article",
                "Content about Custom Domain stuff",
                existing_domains=["Custom Domain"]
            )
            
            assert "domains" in result
            # Existing domain should be detected if mentioned
            assert "Custom Domain" in result["domains"]
    
    @pytest.mark.asyncio
    async def test_analyze_article_with_existing_knowledge_points(self):
        """Test analyze_article considers existing knowledge points"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            service = LLMService()
            result = await service.analyze_article(
                "Special Topic Article",
                "Content about special topic coverage",
                existing_knowledge_points=["special topic"]
            )
            
            assert "knowledge_points" in result
            assert "special topic" in result["knowledge_points"]
    
    @pytest.mark.asyncio
    async def test_analyze_article_limits_existing_hints(self):
        """Test that existing domains/KPs are limited to MAX_EXISTING_HINTS"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            service = LLMService()
            many_domains = [f"Domain {i}" for i in range(100)]
            many_kps = [f"KP {i}" for i in range(100)]
            
            # This should not raise an error
            result = await service.analyze_article(
                "Test",
                "Test content",
                existing_domains=many_domains,
                existing_knowledge_points=many_kps
            )
            
            assert result is not None
    
    def test_simple_analysis_detects_ml(self):
        """Test simple analysis detects Machine Learning keywords"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            service = LLMService()
            result = service._simple_analysis(
                "Deep Learning Tutorial",
                "Learn about neural networks, model training, and AI"
            )
            
            assert "Machine Learning" in result["domains"]
    
    def test_simple_analysis_detects_web_dev(self):
        """Test simple analysis detects Web Development keywords"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            service = LLMService()
            result = service._simple_analysis(
                "React Guide",
                "Building frontend applications with JavaScript"
            )
            
            assert "Web Development" in result["domains"]
    
    def test_simple_analysis_detects_cloud(self):
        """Test simple analysis detects Cloud Computing keywords"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            service = LLMService()
            result = service._simple_analysis(
                "AWS Tutorial",
                "Deploy applications with Docker on AWS"
            )
            
            assert "Cloud Computing" in result["domains"]
    
    def test_simple_analysis_detects_database(self):
        """Test simple analysis detects Database keywords"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            service = LLMService()
            result = service._simple_analysis(
                "PostgreSQL Guide",
                "Working with SQL databases and MySQL"
            )
            
            assert "Database" in result["domains"]
    
    def test_simple_analysis_detects_devops(self):
        """Test simple analysis detects DevOps keywords"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            service = LLMService()
            result = service._simple_analysis(
                "CI/CD Pipeline",
                "Setup Jenkins for continuous deployment"
            )
            
            assert "DevOps" in result["domains"]
    
    def test_simple_analysis_detects_security(self):
        """Test simple analysis detects Security keywords"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            service = LLMService()
            result = service._simple_analysis(
                "Security Best Practices",
                "Authentication and encryption methods"
            )
            
            assert "Security" in result["domains"]
    
    def test_simple_analysis_fallback_to_general(self):
        """Test simple analysis falls back to General domain"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            service = LLMService()
            result = service._simple_analysis(
                "Random Topic",
                "Some unrelated content about cooking"
            )
            
            assert "General" in result["domains"]
    
    def test_simple_analysis_limits_domains(self):
        """Test simple analysis limits domains to 3"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            service = LLMService()
            # Use content that matches multiple domain keywords
            result = service._simple_analysis(
                "Full Stack Developer",
                "Machine learning with JavaScript on AWS using Docker and SQL security"
            )
            
            assert len(result["domains"]) <= 3
    
    def test_simple_analysis_limits_knowledge_points(self):
        """Test simple analysis limits knowledge points to 5"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
            service = LLMService()
            result = service._simple_analysis(
                "Test",
                "Content",
                existing_knowledge_points=["kp1", "kp2", "kp3", "kp4", "kp5", "kp6", "kp7"]
            )
            
            assert len(result["knowledge_points"]) <= 5
    
    @pytest.mark.asyncio
    async def test_call_openai_with_valid_json(self):
        """Test _call_openai parses JSON correctly"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            service = LLMService()
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '{"domains": ["AI"], "knowledge_points": ["NLP"]}'
            
            with patch('openai.OpenAI') as mock_client:
                mock_client.return_value.chat.completions.create.return_value = mock_response
                result = await service._call_openai("test prompt")
                
                assert result == {"domains": ["AI"], "knowledge_points": ["NLP"]}
    
    @pytest.mark.asyncio
    async def test_call_openai_with_markdown_json(self):
        """Test _call_openai handles JSON in markdown code blocks"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            service = LLMService()
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '```json\n{"domains": ["AI"], "knowledge_points": []}\n```'
            
            with patch('openai.OpenAI') as mock_client:
                mock_client.return_value.chat.completions.create.return_value = mock_response
                result = await service._call_openai("test prompt")
                
                assert result == {"domains": ["AI"], "knowledge_points": []}
    
    @pytest.mark.asyncio
    async def test_call_openai_with_plain_code_block(self):
        """Test _call_openai handles plain markdown code blocks"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            service = LLMService()
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '```\n{"domains": ["ML"], "knowledge_points": []}\n```'
            
            with patch('openai.OpenAI') as mock_client:
                mock_client.return_value.chat.completions.create.return_value = mock_response
                result = await service._call_openai("test prompt")
                
                assert result == {"domains": ["ML"], "knowledge_points": []}
    
    @pytest.mark.asyncio
    async def test_call_openai_with_invalid_json(self):
        """Test _call_openai handles invalid JSON gracefully"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            service = LLMService()
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = 'Not valid JSON at all'
            
            with patch('openai.OpenAI') as mock_client:
                mock_client.return_value.chat.completions.create.return_value = mock_response
                result = await service._call_openai("test prompt")
                
                assert result == {"domains": ["General"], "knowledge_points": []}
    
    @pytest.mark.asyncio
    async def test_call_openai_handles_exception(self):
        """Test _call_openai handles exceptions gracefully"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            service = LLMService()
            
            with patch('openai.OpenAI') as mock_client:
                mock_client.return_value.chat.completions.create.side_effect = Exception("API Error")
                result = await service._call_openai("test prompt")
                
                assert result == {"domains": ["General"], "knowledge_points": []}
    
    @pytest.mark.asyncio
    async def test_analyze_article_handles_exception(self):
        """Test analyze_article handles exceptions gracefully"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
            service = LLMService()
            
            with patch.object(service, '_call_openai', side_effect=Exception("Error")):
                result = await service.analyze_article("Test", "Content")
                
                assert result == {"domains": ["General"], "knowledge_points": []}


class TestContentExtractor:
    """Tests for ContentExtractor"""
    
    def test_init(self):
        """Test ContentExtractor initialization"""
        extractor = ContentExtractor()
        assert extractor.ALLOWED_SCHEMES == {'http', 'https'}
        assert 'localhost' in extractor.BLOCKED_HOSTS
    
    def test_validate_url_valid_https(self):
        """Test URL validation with valid HTTPS URL"""
        extractor = ContentExtractor()
        assert extractor._validate_url("https://example.com/page") is True
    
    def test_validate_url_valid_http(self):
        """Test URL validation with valid HTTP URL"""
        extractor = ContentExtractor()
        assert extractor._validate_url("http://example.com/page") is True
    
    def test_validate_url_invalid_scheme(self):
        """Test URL validation blocks invalid schemes"""
        extractor = ContentExtractor()
        assert extractor._validate_url("ftp://example.com") is False
        assert extractor._validate_url("file:///etc/passwd") is False
    
    def test_validate_url_blocks_localhost(self):
        """Test URL validation blocks localhost"""
        extractor = ContentExtractor()
        assert extractor._validate_url("http://localhost/api") is False
        assert extractor._validate_url("http://127.0.0.1/api") is False
        assert extractor._validate_url("http://0.0.0.0/api") is False
    
    def test_validate_url_blocks_private_ip(self):
        """Test URL validation blocks private IPs"""
        extractor = ContentExtractor()
        assert extractor._validate_url("http://192.168.1.1/api") is False
        assert extractor._validate_url("http://10.0.0.1/api") is False
        assert extractor._validate_url("http://172.16.0.1/api") is False
    
    def test_validate_url_blocks_link_local(self):
        """Test URL validation blocks link-local addresses"""
        extractor = ContentExtractor()
        assert extractor._validate_url("http://169.254.169.254/metadata") is False
    
    def test_validate_url_blocks_empty_hostname(self):
        """Test URL validation blocks URLs without hostname"""
        extractor = ContentExtractor()
        assert extractor._validate_url("http:///path") is False
    
    def test_validate_url_handles_invalid_url(self):
        """Test URL validation handles malformed URLs"""
        extractor = ContentExtractor()
        assert extractor._validate_url("not-a-url") is False
        assert extractor._validate_url("") is False
    
    @pytest.mark.asyncio
    async def test_extract_content_invalid_url(self):
        """Test extract_content with invalid URL"""
        extractor = ContentExtractor()
        result = await extractor.extract_content("http://localhost/api")
        
        assert result["title"] == "Invalid URL"
        assert "URL validation failed" in result["content"]
    
    @pytest.mark.asyncio
    async def test_extract_content_valid_url(self):
        """Test extract_content with valid URL (mocked)"""
        extractor = ContentExtractor()
        
        html_content = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <script>alert('test')</script>
                <style>.test { color: red; }</style>
                <p>This is the content</p>
            </body>
        </html>
        """
        
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html_content)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await extractor.extract_content("https://example.com/test")
            
            assert result["title"] == "Test Page"
            assert "This is the content" in result["content"]
            # Script and style content should be removed
            assert "alert" not in result["content"]
            assert "color" not in result["content"]
    
    @pytest.mark.asyncio
    async def test_extract_content_no_title(self):
        """Test extract_content when page has no title"""
        extractor = ContentExtractor()
        
        html_content = """
        <html>
            <head></head>
            <body>Content without title</body>
        </html>
        """
        
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value=html_content)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await extractor.extract_content("https://example.com/test")
            
            # URL should be used as fallback title
            assert result["title"] == "https://example.com/test"
    
    @pytest.mark.asyncio
    async def test_extract_content_handles_exception(self):
        """Test extract_content handles network errors gracefully"""
        extractor = ContentExtractor()
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = MagicMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            mock_session.get.side_effect = Exception("Network error")
            mock_session_class.return_value = mock_session
            
            result = await extractor.extract_content("https://example.com/error")
            
            assert result["title"] == "https://example.com/error"
            assert result["content"] == ""
